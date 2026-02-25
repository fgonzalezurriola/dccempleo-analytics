from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.custom.message import Message


@dataclass(frozen=True)
class ExportRow:
    """Exported Telegram row with the fields required for downstream analysis."""

    channel: str
    message_id: int
    date_utc: str
    text: str
    raw_text: str
    entities: list[dict[str, Any]]
    urls: list[str]
    has_media: bool


def parse_date_yyyy_mm_dd(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)


def message_to_row(channel: str, msg: Message) -> ExportRow:
    raw_text = msg.message or ""

    entities_out: list[dict[str, Any]] = []
    urls: list[str] = []
    if msg.entities:
        for entity in msg.entities:
            entity_dict: dict[str, Any] = {
                "type": entity.__class__.__name__,
                "offset": getattr(entity, "offset", None),
                "length": getattr(entity, "length", None),
            }
            url = getattr(entity, "url", None)
            if url:
                entity_dict["url"] = url
                urls.append(url)
            entities_out.append(entity_dict)

    dt_utc = msg.date.astimezone(UTC) if msg.date else datetime.now(UTC)

    return ExportRow(
        channel=channel,
        message_id=msg.id,
        date_utc=dt_utc.isoformat().replace("+00:00", "Z"),
        text=raw_text,
        raw_text=raw_text,
        entities=entities_out,
        urls=sorted(set(urls)),
        has_media=msg.media is not None,
    )


async def run_export() -> Path:
    load_dotenv(override=True)

    api_id = os.environ.get("TELEGRAM_API_ID")
    api_hash = os.environ.get("TELEGRAM_API_HASH")
    phone = os.environ.get("TELEGRAM_PHONE")
    session_name = os.environ.get("TELEGRAM_SESSION_NAME", "dccempleo")
    channel = os.environ.get("TELEGRAM_CHANNEL", "DCCEmpleoSinFiltro")
    since_raw = os.environ.get("EXPORT_SINCE", "2024-01-01")
    output_path = Path(os.environ.get("RAW_EXPORT_PATH", "data/raw/telegram_export.jsonl"))

    if not api_id or not api_hash:
        raise RuntimeError("Faltan TELEGRAM_API_ID o TELEGRAM_API_HASH en .env")
    if not phone:
        raise RuntimeError("Falta TELEGRAM_PHONE en .env (requerido para login inicial).")

    since_dt = parse_date_yyyy_mm_dd(since_raw)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    client = TelegramClient(session_name, int(api_id), api_hash)
    written = 0
    scanned = 0

    await client.start(phone=lambda: phone)

    try:
        entity = await client.get_entity(channel)

        with output_path.open("w", encoding="utf-8") as handle:
            async for msg in client.iter_messages(entity):
                scanned += 1
                if msg.date and msg.date.astimezone(UTC) < since_dt:
                    break

                if not msg.message and not msg.media:
                    continue

                row = message_to_row(channel=channel, msg=msg)
                handle.write(json.dumps(asdict(row), ensure_ascii=False) + "\n")
                written += 1

                if written % 250 == 0:
                    print(f"exportados {written} mensajes (escaneados {scanned})...")

    finally:
        await client.disconnect()

    print(f"Export finalizado: {written} mensajes -> {output_path}")
    return output_path


def main() -> None:
    try:
        asyncio.run(run_export())
    except FloodWaitError as exc:
        raise SystemExit(
            f"Telegram devolvio FloodWait. Espera el tiempo indicado y vuelve a correr. {exc}"
        ) from exc


if __name__ == "__main__":
    main()
