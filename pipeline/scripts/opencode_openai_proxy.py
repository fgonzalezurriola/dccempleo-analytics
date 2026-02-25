from __future__ import annotations

import base64
import json
import os
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import httpx
from dotenv import load_dotenv


def _normalize_base_url(raw_base_url: str) -> str:
    base_url = raw_base_url.rstrip("/")
    if base_url.endswith("/v1"):
        return base_url[:-3]
    return base_url


def _model_to_provider_model(model: str) -> tuple[str, str]:
    parts = model.split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid model '{model}'. Expected provider/model format.")
    # BAML can send nested provider models prefixed as: opencode/<provider>/<model>.
    # Example: opencode/llm-proxy/cli_gemini-3-flash
    if len(parts) >= 3 and parts[0] == "opencode":
        return parts[1], "/".join(parts[2:])
    return parts[0], "/".join(parts[1:])


def _build_opencode_auth_headers() -> dict[str, str]:
    password = os.environ.get("OPENCODE_SERVER_PASSWORD", "").strip()
    username = os.environ.get("OPENCODE_SERVER_USERNAME", "opencode").strip() or "opencode"
    if not password:
        return {}
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return {"Authorization": f"Basic {token}"}


def _messages_to_text(messages: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role") or "user").strip().lower()
        content = str(message.get("content") or "").strip()
        if not content:
            continue
        if role == "system":
            lines.append(f"System:\n{content}")
        elif role == "assistant":
            lines.append(f"Assistant context:\n{content}")
        else:
            lines.append(f"User:\n{content}")
    return "\n\n".join(lines).strip()


def _extract_message_text(message_payload: dict[str, Any]) -> str:
    def collect_texts(node: Any) -> list[str]:
        texts: list[str] = []
        if isinstance(node, str):
            value = node.strip()
            if value:
                texts.append(value)
            return texts
        if isinstance(node, list):
            for item in node:
                texts.extend(collect_texts(item))
            return texts
        if isinstance(node, dict):
            part_type = str(node.get("type") or "").strip().lower()
            if part_type in {"text", "output_text"}:
                for key in ("text", "content"):
                    value = node.get(key)
                    if isinstance(value, str) and value.strip():
                        texts.append(value.strip())
            for key in ("text", "content", "message", "parts", "choices", "output"):
                if key in node:
                    texts.extend(collect_texts(node[key]))
        return texts

    parts = message_payload.get("parts")
    if isinstance(parts, list):
        part_texts: list[str] = []
        for part in parts:
            if not isinstance(part, dict):
                continue
            part_type = str(part.get("type") or "").strip().lower()
            if part_type in {"text", "output_text"}:
                text = str(part.get("text") or part.get("content") or "").strip()
                if text:
                    part_texts.append(text)
        if part_texts:
            return "\n\n".join(part_texts)

    fallback_texts = collect_texts(message_payload)
    if fallback_texts:
        return "\n\n".join(fallback_texts)
    raise RuntimeError(
        "OpenCode response had no textual content. "
        f"Payload keys: {sorted(message_payload.keys())}"
    )


def _call_opencode_chat(model_name: str, prompt_text: str) -> str:
    base_url = _normalize_base_url(
        os.environ.get(
            "OPENCODE_SERVER_BASE_URL",
            f"http://127.0.0.1:{os.environ.get('OPENCODE_SERVER_PORT', '4099')}",
        )
    )
    timeout_seconds = float(os.environ.get("OPENCODE_MESSAGE_TIMEOUT_SECONDS", "120"))
    auth_headers = _build_opencode_auth_headers()
    provider_id, model_id = _model_to_provider_model(model_name)

    last_error: RuntimeError | None = None
    with httpx.Client(timeout=timeout_seconds) as client:
        for attempt in range(2):
            try:
                session_response = client.post(
                    f"{base_url}/session",
                    headers={"Content-Type": "application/json", **auth_headers},
                    json={},
                )
                if session_response.status_code >= 400:
                    raise RuntimeError(
                        "OpenCode session error: "
                        f"HTTP {session_response.status_code} {session_response.text[:300]}"
                    )
                try:
                    session_payload = session_response.json()
                except json.JSONDecodeError as exc:
                    raise RuntimeError(
                        "OpenCode session returned non-JSON response: "
                        f"HTTP {session_response.status_code} {session_response.text[:300]}"
                    ) from exc

                session_id = str(session_payload.get("id") or "")
                if not session_id:
                    raise RuntimeError("OpenCode session response missing id.")

                message_body: dict[str, Any] = {
                    "model": {"providerID": provider_id, "modelID": model_id},
                    "parts": [{"type": "text", "text": prompt_text}],
                }
                message_response = client.post(
                    f"{base_url}/session/{session_id}/message",
                    headers={"Content-Type": "application/json", **auth_headers},
                    json=message_body,
                )
                if message_response.status_code >= 400:
                    raise RuntimeError(
                        "OpenCode message error: "
                        f"HTTP {message_response.status_code} {message_response.text[:300]}"
                    )
                try:
                    message_payload = message_response.json()
                except json.JSONDecodeError as exc:
                    raise RuntimeError(
                        "OpenCode message returned non-JSON response: "
                        f"HTTP {message_response.status_code} {message_response.text[:300]}"
                    ) from exc
                if not isinstance(message_payload, dict):
                    raise RuntimeError("OpenCode message response was not a JSON object.")
                return _extract_message_text(message_payload)
            except RuntimeError as exc:
                last_error = exc
                if attempt == 0:
                    time.sleep(0.8)
                    continue
                break
    raise RuntimeError(str(last_error) if last_error else "OpenCode request failed.")


class OpenAICompatHandler(BaseHTTPRequestHandler):
    server_version = "OpenCodeOpenAIProxy/1.0"

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON payload.") from exc
        if not isinstance(payload, dict):
            raise ValueError("Expected JSON object body.")
        return payload

    def _is_authorized(self) -> bool:
        expected = os.environ.get("BAML_PROXY_API_KEY", "dummy").strip()
        if not expected:
            return True
        auth_header = self.headers.get("Authorization", "")
        return auth_header == f"Bearer {expected}"

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/health":
            self._send_json(HTTPStatus.OK, {"ok": True, "service": "opencode-openai-proxy"})
            return
        if self.path.rstrip("/") == "/v1/models":
            model_name = os.environ.get("BAML_MODEL") or os.environ.get(
                "OPENCODE_MODEL", "opencode/trinity-large-preview-free"
            )
            self._send_json(
                HTTPStatus.OK,
                {
                    "object": "list",
                    "data": [{"id": model_name, "object": "model", "owned_by": "opencode"}],
                },
            )
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/v1/chat/completions":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return

        if not self._is_authorized():
            self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "Unauthorized"})
            return

        try:
            payload = self._read_json_body()
            model = str(
                payload.get("model")
                or os.environ.get("BAML_MODEL")
                or os.environ.get("OPENCODE_MODEL", "opencode/trinity-large-preview-free")
            ).strip()
            messages = payload.get("messages")
            if not isinstance(messages, list):
                raise ValueError("Field 'messages' must be an array.")

            prompt_text = _messages_to_text(messages)
            if not prompt_text:
                raise ValueError("Request has no textual messages to forward.")

            content = _call_opencode_chat(model_name=model, prompt_text=prompt_text)
            now_ts = int(time.time())
            completion = {
                "id": f"chatcmpl-{now_ts}",
                "object": "chat.completion",
                "created": now_ts,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }
            self._send_json(HTTPStatus.OK, completion)
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except Exception as exc:
            self._send_json(HTTPStatus.BAD_GATEWAY, {"error": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return


def main() -> None:
    load_dotenv(override=True)
    host = os.environ.get("OPENCODE_PROXY_HOST", "127.0.0.1")
    port = int(os.environ.get("OPENCODE_PROXY_PORT", "4100"))

    model_name = os.environ.get("BAML_MODEL") or os.environ.get(
        "OPENCODE_MODEL", "opencode/trinity-large-preview-free"
    )
    print(f"OpenCode OpenAI proxy listening on http://{host}:{port}/v1 (model={model_name})")
    server = ThreadingHTTPServer((host, port), OpenAICompatHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
