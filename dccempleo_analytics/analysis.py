from __future__ import annotations

import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

TECH_ALIASES: dict[str, str] = {
    "python": "python",
    "java": "java",
    "c": "c",
    "c++": "c++",
    "cpp": "c++",
    "c plus plus": "c++",
    "js": "javascript",
    "javascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "bash": "bash",
    "shell": "bash",
    "sh": "bash",
    "node.js": "node.js",
    "nodejs": "node.js",
    "node": "node.js",
    "react": "react",
    "react.js": "react",
    "reactjs": "react",
    "next.js": "next.js",
    "nextjs": "next.js",
    "vue": "vue",
    "angular": "angular",
    "c#": "c#",
    "csharp": "c#",
    ".net": ".net",
    "dotnet": ".net",
    "asp.net": ".net",
    "golang": "go",
    "ruby": "ruby",
    "rails": "ruby on rails",
    "ruby on rails": "ruby on rails",
    "ror": "ruby on rails",
    "php": "php",
    "kotlin": "kotlin",
    "dart": "dart",
    "flutter": "flutter",
    "swift": "swift",
    "rust": "rust",
    "sql": "sql",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "mysql": "mysql",
    "mariadb": "mariadb",
    "mongodb": "mongodb",
    "nosql": "nosql",
    "dynamodb": "dynamodb",
    "dynamo db": "dynamodb",
    "elasticsearch": "elasticsearch",
    "firestore": "firestore",
    "cosmosdb": "cosmosdb",
    "cosmos db": "cosmosdb",
    "redis": "redis",
    "firebase": "firebase",
    "supabase": "supabase",
    "sql server": "sql server",
    "oracle": "oracle",
    "sqlite": "sqlite",
    "docker": "docker",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "aws": "aws",
    "ec2": "aws",
    "aws ec2": "aws",
    "eks": "aws",
    "aws eks": "aws",
    "amazon web services": "aws",
    "gcp": "gcp",
    "google cloud": "gcp",
    "azure": "azure",
    "railway": "railway",
    "render": "render",
    "fly.io": "fly.io",
    "flyio": "fly.io",
    "digital ocean": "digitalocean",
    "digitalocean": "digitalocean",
    "hetzner": "hetzner",
    "ovh": "ovh",
    "netlify": "netlify",
    "airflow": "airflow",
    "apollo": "apollo",
    "bigquery": "bigquery",
    "bootstrap": "bootstrap",
    "celery": "celery",
    "cloudflare": "cloudflare",
    "spark": "spark",
    "hadoop": "hadoop",
    "express": "express",
    "express.js": "express",
    "fast api": "fastapi",
    "fastapi": "fastapi",
    "graphql": "graphql",
    "kafka": "kafka",
    "linux": "linux",
    "lumen": "lumen",
    "nuxt": "nuxt",
    "numpy": "numpy",
    "opencv": "opencv",
    "pandas": "pandas",
    "pytorch": "pytorch",
    "rabbitmq": "rabbitmq",
    "react native": "react native",
    "redshift": "redshift",
    "scikit learn": "scikit-learn",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "spring boot": "spring boot",
    "sqs": "sqs",
    "tailwind": "tailwind",
    "tailwind css": "tailwind",
    "tensorflow": "tensorflow",
    "vercel": "vercel",
    "windows": "windows",
    "tableau": "tableau",
    "power bi": "power bi",
    "snowflake": "snowflake",
    "dbt": "dbt",
    "git": "git",
    "linux": "linux",
}

LANGUAGE_TECH = {
    "bash",
    "c",
    "c++",
    "dart",
    "flutter",
    "python",
    "java",
    "javascript",
    "typescript",
    "c#",
    "go",
    "ruby",
    "php",
    "kotlin",
    "swift",
    "rust",
}

DATABASE_TECH = {
    "sql",
    "nosql",
    "postgresql",
    "mysql",
    "mariadb",
    "mongodb",
    "dynamodb",
    "elasticsearch",
    "firestore",
    "cosmosdb",
    "redis",
    "firebase",
    "supabase",
    "bigquery",
    "redshift",
    "snowflake",
    "sql server",
    "oracle",
    "sqlite",
}

CLOUD_TECH = {
    "aws",
    "gcp",
    "azure",
    "railway",
    "render",
    "fly.io",
    "digitalocean",
    "hetzner",
    "ovh",
    "netlify",
    "cloudflare",
    "vercel",
}

AI_DEV_TOOL_ALIASES: dict[str, str] = {
    "codex": "codex",
    "cursor": "cursor",
    "claude code": "claude code",
    "claude desktop": "claude desktop",
    "github copilot": "github copilot",
    "antigravity": "antigravity",
}

EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}\b")
URL_RE = re.compile(r"(https?://[^\s]+|www\.[^\s]+)")
PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
TG_HANDLE_RE = re.compile(r"@\w+")
WHITESPACE_RE = re.compile(r"\s+")


def anonymize_text(raw_text: str) -> str:
    text = EMAIL_RE.sub("[email]", raw_text)
    text = URL_RE.sub("[url]", text)
    text = PHONE_RE.sub("[phone]", text)
    text = TG_HANDLE_RE.sub("[telegram]", text)
    text = WHITESPACE_RE.sub(" ", text)
    return text.strip()


def _contains_phrase(text_lower: str, phrase: str) -> bool:
    escaped = re.escape(phrase)
    pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
    return re.search(pattern, text_lower) is not None


def detect_seniority(text: str) -> str:
    text_lower = text.lower()
    matches: set[str] = set()

    if any(k in text_lower for k in ("practica", "práctica", "internship", "alumno en practica")):
        matches.add("INTERN")
    if re.search(r"(?<![a-z])intern(?![a-z])", text_lower):
        matches.add("INTERN")
    if "trainee" in text_lower:
        matches.add("TRAINEE")
    if any(k in text_lower for k in ("junior", "entry level", "0-2 años", "0-2 years")):
        matches.add("JUNIOR")
    if any(k in text_lower for k in ("semi senior", "semi-senior", "ssr", "mid-level")):
        matches.add("MID_SENIOR")
    has_mid = any(k in text_lower for k in ("semi senior", "semi-senior", "ssr", "mid-level"))
    if (re.search(r"(?<![a-z])(senior|sr|lead)(?![a-z])", text_lower) is not None) and not has_mid:
        matches.add("SENIOR")

    if not matches:
        return "UNKNOWN"
    if len(matches) == 1:
        return matches.pop()
    return "MIXED"


def detect_offer_type(text: str) -> str:
    text_lower = text.lower()
    if any(k in text_lower for k in ("practica", "práctica", "internship")):
        return "PRACTICE"
    if "bootcamp" in text_lower:
        return "BOOTCAMP"
    if any(k in text_lower for k in ("curso", "course", "certificacion", "certificación")):
        return "COURSE"
    return "JOB"


def extract_tech_stack(text: str) -> list[str]:
    text_lower = text.lower()
    found: set[str] = set()

    for alias in sorted(TECH_ALIASES, key=len, reverse=True):
        if _contains_phrase(text_lower, alias):
            canonical = TECH_ALIASES[alias]
            found.add(canonical)

    if "typescript" in found and "javascript" in found:
        found.remove("javascript")

    return sorted(found)


def normalize_tech_stack(values: list[str]) -> list[str]:
    normalized: set[str] = set()
    for value in values:
        key = value.strip().lower()
        if not key:
            continue
        normalized.add(TECH_ALIASES.get(key, key))
    if "typescript" in normalized and "javascript" in normalized:
        normalized.remove("javascript")
    return sorted(normalized)


def extract_ai_dev_tools(text: str) -> list[str]:
    text_lower = text.lower()
    found: set[str] = set()
    for alias in sorted(AI_DEV_TOOL_ALIASES, key=len, reverse=True):
        if _contains_phrase(text_lower, alias):
            found.add(AI_DEV_TOOL_ALIASES[alias])
    return sorted(found)


def bucket_seniority(seniority: str, offer_type: str, raw_text: str) -> str:
    seniority_upper = seniority.upper().strip()
    offer_type_upper = offer_type.upper().strip()
    text_lower = raw_text.lower()

    if seniority_upper in {"INTERN", "TRAINEE"}:
        return "PRACTICE"
    if offer_type_upper == "PRACTICE":
        return "PRACTICE"
    if any(
        keyword in text_lower
        for keyword in ("práctica", "practica", "practicante", "internship", "intern", "estudiante")
    ):
        return "PRACTICE"
    if seniority_upper == "JUNIOR":
        return "JUNIOR"
    if seniority_upper in {"MID_SENIOR", "MIXED"}:
        return "SEMI_SENIOR"
    if seniority_upper == "SENIOR":
        return "SENIOR"
    return "UNKNOWN"


def parse_month(date_utc: str) -> str:
    if not date_utc:
        return "unknown"
    try:
        return datetime.fromisoformat(date_utc.replace("Z", "+00:00")).strftime("%Y-%m")
    except ValueError:
        return "unknown"


def process_message(row: dict[str, Any]) -> dict[str, Any]:
    raw_text = str(row.get("text") or row.get("raw_text") or "")
    label = row.get("label") if isinstance(row.get("label"), dict) else {}

    seniority = str(label.get("seniority") or detect_seniority(raw_text)).upper()
    offer_type = str(label.get("offer_type") or detect_offer_type(raw_text)).upper()

    labeled_stack = label.get("tech_stack") if isinstance(label.get("tech_stack"), list) else []
    raw_stack = extract_tech_stack(raw_text)
    if labeled_stack:
        labeled_normalized = normalize_tech_stack(labeled_stack)
        tech_stack = sorted(set(labeled_normalized) | set(raw_stack))
    else:
        tech_stack = raw_stack
    languages = sorted([tech for tech in tech_stack if tech in LANGUAGE_TECH])
    databases = sorted([tech for tech in tech_stack if tech in DATABASE_TECH])
    clouds = sorted([tech for tech in tech_stack if tech in CLOUD_TECH])
    ai_dev_tools = extract_ai_dev_tools(raw_text)
    seniority_bucket = bucket_seniority(
        seniority=seniority, offer_type=offer_type, raw_text=raw_text
    )

    return {
        "channel": row.get("channel"),
        "message_id": row.get("message_id"),
        "date_utc": row.get("date_utc"),
        "month": parse_month(str(row.get("date_utc") or "")),
        "seniority": seniority,
        "seniority_bucket": seniority_bucket,
        "offer_type": offer_type,
        "tech_stack": tech_stack,
        "languages": languages,
        "databases": databases,
        "clouds": clouds,
        "ai_dev_tools": ai_dev_tools,
        "has_media": bool(row.get("has_media")),
        "anonymized_text": anonymize_text(raw_text),
    }


def _counter_to_chart_data(counter: Counter[str], top_n: int = 20) -> list[dict[str, Any]]:
    return [{"name": key, "count": value} for key, value in counter.most_common(top_n)]


def analyze_messages(messages: list[dict[str, Any]], source_path: Path) -> dict[str, Any]:
    monthly_counter: Counter[str] = Counter()
    seniority_counter: Counter[str] = Counter()
    seniority_bucket_counter: Counter[str] = Counter()
    tech_counter: Counter[str] = Counter()
    tech_entry_counter: Counter[str] = Counter()
    lang_counter: Counter[str] = Counter()
    lang_entry_counter: Counter[str] = Counter()
    db_counter: Counter[str] = Counter()
    cloud_counter: Counter[str] = Counter()
    ai_dev_tool_counter: Counter[str] = Counter()
    monthly_ai_dev_counter: Counter[str] = Counter()

    for msg in messages:
        month = msg["month"]
        seniority = msg["seniority"]
        seniority_bucket = str(msg.get("seniority_bucket") or "UNKNOWN")
        monthly_counter[month] += 1
        seniority_counter[seniority] += 1
        seniority_bucket_counter[seniority_bucket] += 1

        seen_tech = set(msg["tech_stack"])
        for tech in seen_tech:
            tech_counter[tech] += 1
            if seniority_bucket in {"PRACTICE", "JUNIOR"}:
                tech_entry_counter[tech] += 1
        for lang in set(msg["languages"]):
            lang_counter[lang] += 1
            if seniority_bucket in {"PRACTICE", "JUNIOR"}:
                lang_entry_counter[lang] += 1
        for db in set(msg["databases"]):
            db_counter[db] += 1
        for cloud in set(msg.get("clouds") or []):
            cloud_counter[cloud] += 1
        ai_tools = set(msg.get("ai_dev_tools") or [])
        if ai_tools:
            monthly_ai_dev_counter[month] += 1
        for ai_tool in ai_tools:
            ai_dev_tool_counter[ai_tool] += 1

    total_messages = len(messages)
    entry_level_messages = sum(
        1
        for msg in messages
        if str(msg.get("seniority_bucket") or "").upper() in {"PRACTICE", "JUNIOR"}
    )
    entry_level_share = (
        round((entry_level_messages / total_messages) * 100, 2) if total_messages else 0
    )
    messages_with_ai_dev_tools = sum(1 for msg in messages if msg.get("ai_dev_tools"))
    ai_dev_tools_share = (
        round((messages_with_ai_dev_tools / total_messages) * 100, 2) if total_messages else 0
    )

    date_span = "sin datos"
    months_sorted = sorted([month for month in monthly_counter if month != "unknown"])
    if months_sorted:
        date_span = f"{months_sorted[0]} a {months_sorted[-1]}"

    monthly_data = [
        {"name": month, "count": monthly_counter[month]}
        for month in sorted(monthly_counter)
        if month != "unknown"
    ]
    monthly_ai_dev_data = [
        {"name": month, "count": monthly_ai_dev_counter.get(month, 0)}
        for month in sorted(monthly_counter)
        if month != "unknown"
    ]

    charts = [
        {
            "id": "monthly_postings",
            "kind": "line",
            "title": "Publicaciones mensuales",
            "description": "Cantidad de ofertas publicadas por mes en UTC.",
            "x_axis_label": "Mes (YYYY-MM)",
            "y_axis_label": "Nro. de publicaciones",
            "data": monthly_data,
        },
        {
            "id": "seniority_distribution",
            "kind": "bar",
            "title": "Distribucion de seniority",
            "description": "Cantidad de ofertas por nivel de experiencia.",
            "x_axis_label": "Seniority",
            "y_axis_label": "Nro. de publicaciones",
            "data": _counter_to_chart_data(seniority_counter, top_n=10),
        },
        {
            "id": "seniority_bucket_distribution",
            "kind": "bar",
            "title": "Distribucion de seniority (agrupada)",
            "description": "Categorias agregadas para practica, junior, semi-senior, senior y unknown.",
            "x_axis_label": "Categoria",
            "y_axis_label": "Nro. de publicaciones",
            "data": _counter_to_chart_data(seniority_bucket_counter, top_n=10),
        },
        {
            "id": "top_technologies",
            "kind": "bar",
            "title": "Top tecnologias",
            "description": "Tecnologias mas mencionadas en las ofertas.",
            "x_axis_label": "Tecnologia",
            "y_axis_label": "Nro. de menciones",
            "data": _counter_to_chart_data(tech_counter, top_n=25),
        },
        {
            "id": "top_technologies_entry_level",
            "kind": "bar",
            "title": "Top tecnologias entry-level",
            "description": "Tecnologias mas mencionadas en ofertas PRACTICE/JUNIOR.",
            "x_axis_label": "Tecnologia",
            "y_axis_label": "Nro. de menciones",
            "data": _counter_to_chart_data(tech_entry_counter, top_n=25),
        },
        {
            "id": "top_languages",
            "kind": "bar",
            "title": "Top lenguajes",
            "description": "Lenguajes de programacion mas mencionados.",
            "x_axis_label": "Lenguaje",
            "y_axis_label": "Nro. de menciones",
            "data": _counter_to_chart_data(lang_counter, top_n=20),
        },
        {
            "id": "top_databases",
            "kind": "bar",
            "title": "Top bases de datos",
            "description": "Bases de datos mas mencionadas en ofertas.",
            "x_axis_label": "Base de datos",
            "y_axis_label": "Nro. de menciones",
            "data": _counter_to_chart_data(db_counter, top_n=20),
        },
        {
            "id": "top_cloud_platforms",
            "kind": "bar",
            "title": "Top cloud",
            "description": "Plataformas cloud mas mencionadas en ofertas.",
            "x_axis_label": "Cloud",
            "y_axis_label": "Nro. de menciones",
            "data": _counter_to_chart_data(cloud_counter, top_n=10),
        },
        {
            "id": "top_ai_dev_tools",
            "kind": "bar",
            "title": "Top herramientas dev-AI",
            "description": "Menciones de Codex, Cursor, Claude Code y GitHub Copilot.",
            "x_axis_label": "Herramienta",
            "y_axis_label": "Nro. de menciones",
            "data": _counter_to_chart_data(ai_dev_tool_counter, top_n=10),
        },
        {
            "id": "monthly_ai_dev_adoption",
            "kind": "line",
            "title": "Aparicion mensual de herramientas dev-AI",
            "description": "Cantidad de ofertas por mes que mencionan al menos una herramienta dev-AI.",
            "x_axis_label": "Mes (YYYY-MM)",
            "y_axis_label": "Nro. de ofertas con dev-AI",
            "data": monthly_ai_dev_data,
        },
    ]

    return {
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "source": {
            "raw_dataset": str(source_path),
            "messages_analyzed": total_messages,
            "date_span": date_span,
        },
        "kpis": {
            "total_messages": total_messages,
            "entry_level_messages": entry_level_messages,
            "entry_level_share_percent": entry_level_share,
            "unique_technologies": len(tech_counter),
            "messages_with_ai_dev_tools": messages_with_ai_dev_tools,
            "ai_dev_tools_share_percent": ai_dev_tools_share,
        },
        "charts": charts,
    }
