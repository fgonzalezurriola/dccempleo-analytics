from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import reflex as rx


def _load_insights() -> dict[str, Any]:
    env_path = os.environ.get("INSIGHTS_JSON_PATH")
    candidates = [
        Path(env_path) if env_path else None,
        Path("data/processed/insights.json"),
        Path("assets/datasets/insights.json"),
    ]

    for candidate in candidates:
        if candidate and candidate.exists():
            with candidate.open("r", encoding="utf-8") as handle:
                return json.load(handle)

    return {
        "generated_at_utc": "",
        "source": {"raw_dataset": "", "messages_analyzed": 0, "date_span": "sin datos"},
        "kpis": {
            "total_messages": 0,
            "entry_level_messages": 0,
            "entry_level_share_percent": 0,
            "unique_technologies": 0,
        },
        "charts": [],
    }


INSIGHTS = _load_insights()


def kpi_card(label: str, value: str, hint: str) -> rx.Component:
    return rx.box(
        rx.text(label, font_size="0.8rem", color="#475569"),
        rx.text(value, font_size="1.7rem", font_weight="700", color="#0f172a"),
        rx.text(hint, font_size="0.75rem", color="#64748b"),
        width=["100%", "48%", "24%"],
        border="1px solid #e2e8f0",
        border_radius="12px",
        padding="1rem",
        background_color="#ffffff",
    )


def chart_plot(chart: dict[str, Any]) -> rx.Component:
    data = chart.get("data", [])
    if not data:
        return rx.box(
            rx.text("Sin datos para este grafico.", color="#64748b"),
            padding_y="1rem",
        )

    if chart.get("kind") == "line":
        return rx.recharts.line_chart(
            rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
            rx.recharts.x_axis(
                data_key="name", interval=0, angle=-35, text_anchor="end", height=90
            ),
            rx.recharts.y_axis(),
            rx.recharts.graphing_tooltip(),
            rx.recharts.line(
                data_key="count",
                type_="monotone",
                stroke="#0f766e",
                stroke_width=2,
            ),
            data=data,
            width="100%",
            height=320,
        )

    return rx.recharts.bar_chart(
        rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
        rx.recharts.x_axis(data_key="name", interval=0, angle=-35, text_anchor="end", height=90),
        rx.recharts.y_axis(),
        rx.recharts.graphing_tooltip(),
        rx.recharts.bar(data_key="count", fill="#0284c7"),
        data=data,
        width="100%",
        height=320,
    )


def exact_occurrences(chart: dict[str, Any]) -> rx.Component:
    rows = chart.get("data", [])[:30]
    return rx.box(
        rx.text("Ocurrencias exactas", font_weight="600", margin_bottom="0.4rem"),
        rx.vstack(
            *[
                rx.hstack(
                    rx.text(str(row.get("name", "")), color="#0f172a"),
                    rx.spacer(),
                    rx.code(str(row.get("count", 0))),
                    width="100%",
                )
                for row in rows
            ],
            width="100%",
            spacing="2",
        ),
        background_color="#f8fafc",
        border="1px solid #e2e8f0",
        border_radius="10px",
        padding="0.9rem",
        margin_top="0.75rem",
    )


def chart_card(chart: dict[str, Any]) -> rx.Component:
    return rx.box(
        rx.text(
            chart.get("title", "Grafico"), font_size="1.2rem", font_weight="700", color="#0f172a"
        ),
        rx.text(chart.get("description", ""), color="#334155", margin_bottom="0.3rem"),
        rx.text(
            f"Eje X: {chart.get('x_axis_label', '-')}. Eje Y: {chart.get('y_axis_label', '-')}.",
            font_size="0.82rem",
            color="#475569",
            margin_bottom="0.7rem",
        ),
        chart_plot(chart),
        exact_occurrences(chart),
        border="1px solid #e2e8f0",
        border_radius="14px",
        padding="1rem",
        background_color="#ffffff",
    )


def index() -> rx.Component:
    kpis = INSIGHTS.get("kpis", {})
    source = INSIGHTS.get("source", {})
    charts = INSIGHTS.get("charts", [])

    return rx.box(
        rx.vstack(
            rx.heading("DCC Empleo Analytics", size="7", color="#0f172a"),
            rx.text(
                "Dashboard estatico de ofertas de DCCEmpleoSinFiltro.",
                color="#334155",
            ),
            rx.text(
                f"Rango analizado: {source.get('date_span', 'sin datos')} | "
                f"Mensajes: {source.get('messages_analyzed', 0)}",
                font_size="0.85rem",
                color="#475569",
            ),
            rx.flex(
                kpi_card(
                    "Total mensajes", str(kpis.get("total_messages", 0)), "Mensajes procesados"
                ),
                kpi_card(
                    "Entry-level",
                    str(kpis.get("entry_level_messages", 0)),
                    "PRACTICE + JUNIOR",
                ),
                kpi_card(
                    "Share entry-level",
                    f"{kpis.get('entry_level_share_percent', 0)}%",
                    "Porcentaje del total",
                ),
                kpi_card(
                    "Tecnologias unicas",
                    str(kpis.get("unique_technologies", 0)),
                    "Stack normalizado",
                ),
                kpi_card(
                    "Ofertas con dev-AI",
                    str(kpis.get("messages_with_ai_dev_tools", 0)),
                    "Codex/Cursor/Claude Code/Copilot",
                ),
                kpi_card(
                    "Share dev-AI",
                    f"{kpis.get('ai_dev_tools_share_percent', 0)}%",
                    "Porcentaje del total",
                ),
                wrap="wrap",
                gap="1rem",
                width="100%",
                margin_top="0.3rem",
                margin_bottom="1rem",
            ),
            *[chart_card(chart) for chart in charts],
            rx.text(
                f"Generado en UTC: {INSIGHTS.get('generated_at_utc', '')}",
                font_size="0.75rem",
                color="#64748b",
                margin_top="0.5rem",
            ),
            width="100%",
            max_width="1100px",
            padding="1.2rem",
            spacing="4",
        ),
        min_height="100vh",
        background="linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)",
        display="flex",
        justify_content="center",
    )


app = rx.App(stylesheets=["/base.css"])
app.add_page(index, title="DCC Empleo Analytics")
