import unittest

from dccempleo_analytics.analysis import (
    anonymize_text,
    bucket_seniority,
    detect_offer_type,
    detect_seniority,
    extract_ai_dev_tools,
    extract_tech_stack,
    normalize_tech_stack,
    process_message,
    _build_ai_tools_timeline,
)


class AnalysisTests(unittest.TestCase):
    def test_ai_tools_timeline_counts_an_offer_once(self) -> None:
        timeline = _build_ai_tools_timeline([
            {"month": "2026-06", "ai_dev_tools": ["cursor", "claude code"]},
            {"month": "2026-06", "ai_dev_tools": ["cursor"]},
        ])

        self.assertEqual(timeline["total_per_month"], [3])
        self.assertEqual(timeline["offers_with_ai_per_month"], [2])

    def test_anonymize_text(self) -> None:
        text = (
            "Escribe a hola@empresa.cl o +56 9 1234 5678 y revisa https://example.com @reclutador"
        )
        out = anonymize_text(text)
        self.assertIn("[email]", out)
        self.assertIn("[phone]", out)
        self.assertIn("[url]", out)
        self.assertIn("[telegram]", out)

    def test_seniority_and_offer_type(self) -> None:
        text = "Buscamos perfil junior para practica profesional."
        self.assertEqual(detect_seniority(text), "MIXED")
        self.assertEqual(detect_offer_type(text), "PRACTICE")

    def test_extract_tech_stack(self) -> None:
        text = "Stack: Python, React, PostgreSQL, AWS y Docker."
        stack = extract_tech_stack(text)
        self.assertIn("python", stack)
        self.assertIn("react", stack)
        self.assertIn("postgresql", stack)
        self.assertIn("aws", stack)
        self.assertIn("docker", stack)

    def test_extract_tech_stack_does_not_infer_c_from_csharp_or_c_slash(self) -> None:
        stack_csharp = extract_tech_stack("Stack: C#, .NET y SQL Server.")
        self.assertIn("c#", stack_csharp)
        self.assertNotIn("c", stack_csharp)

        stack_c_slash = extract_tech_stack("Backend c/ experiencia en Python y Docker.")
        self.assertNotIn("c", stack_c_slash)

    def test_extract_tech_stack_does_not_infer_c_from_spanish_words(self) -> None:
        stack = extract_tech_stack("Buscamos dev para construir soluciones, como parte del equipo.")
        self.assertNotIn("c", stack)

    def test_process_message_uses_label_if_available(self) -> None:
        row = {
            "date_utc": "2025-01-01T00:00:00Z",
            "text": "Buscamos dev backend",
            "label": {
                "seniority": "JUNIOR",
                "offer_type": "JOB",
                "tech_stack": ["Python", "Postgres"],
            },
        }
        out = process_message(row)
        self.assertEqual(out["seniority"], "JUNIOR")
        self.assertEqual(out["offer_type"], "JOB")
        self.assertIn("python", out["tech_stack"])
        self.assertIn("postgresql", out["tech_stack"])

    def test_normalize_stack_prefers_typescript_over_javascript(self) -> None:
        normalized = normalize_tech_stack(["TypeScript", "JavaScript", "NodeJS"])
        self.assertIn("typescript", normalized)
        self.assertIn("node.js", normalized)
        self.assertNotIn("javascript", normalized)

    def test_bucket_seniority_practice_detection(self) -> None:
        bucket = bucket_seniority(
            seniority="UNKNOWN",
            offer_type="JOB",
            raw_text="Buscamos practicante de software con seguro escolar.",
        )
        self.assertEqual(bucket, "PRACTICE")

    def test_process_message_classifies_extended_languages_and_databases(self) -> None:
        row = {
            "date_utc": "2025-01-01T00:00:00Z",
            "text": "Stack: C++, Bash, Dart, SQL, Firestore, DynamoDB, Cosmos DB.",
            "label": {
                "seniority": "JUNIOR",
                "offer_type": "JOB",
                "tech_stack": ["C++", "Bash", "Dart", "SQL", "Firestore", "DynamoDB", "Cosmos DB"],
            },
        }
        out = process_message(row)
        self.assertIn("c++", out["languages"])
        self.assertIn("bash", out["languages"])
        self.assertIn("dart", out["languages"])
        self.assertIn("sql", out["databases"])
        self.assertIn("firestore", out["databases"])
        self.assertIn("dynamodb", out["databases"])
        self.assertIn("cosmosdb", out["databases"])

    def test_process_message_classifies_frontend_frameworks(self) -> None:
        row = {
            "date_utc": "2025-01-01T00:00:00Z",
            "text": "Frontend con React, Next.js, Vue, Angular, Svelte, Nuxt y Astro.",
            "label": {
                "seniority": "JUNIOR",
                "offer_type": "JOB",
                "tech_stack": ["React", "Next.js", "Vue", "Angular", "Svelte", "Nuxt", "Astro"],
            },
        }
        out = process_message(row)
        self.assertIn("react", out["frontend_frameworks"])
        self.assertIn("next.js", out["frontend_frameworks"])
        self.assertIn("vue", out["frontend_frameworks"])
        self.assertIn("angular", out["frontend_frameworks"])
        self.assertIn("svelte", out["frontend_frameworks"])
        self.assertIn("nuxt", out["frontend_frameworks"])
        self.assertIn("astro", out["frontend_frameworks"])

    def test_extract_ai_dev_tools_strict_detection(self) -> None:
        text = (
            "Buscamos dev que use Cursor, GitHub Copilot y Claude Code. "
            "Mencionamos copiloto del proyecto pero no la herramienta."
        )
        tools = extract_ai_dev_tools(text)
        self.assertIn("cursor", tools)
        self.assertIn("github copilot", tools)
        self.assertIn("claude code", tools)
        self.assertNotIn("copilot", tools)

    def test_extract_ai_dev_tools_detects_github_copilot_with_punctuation(self) -> None:
        text = "Cuentas corporativas para Github, Copilot/Cursor y otras herramientas."
        tools = extract_ai_dev_tools(text)
        self.assertIn("github copilot", tools)
        self.assertIn("cursor", tools)

    def test_extract_ai_dev_tools_detects_ab_separator_forms(self) -> None:
        text = "Stack AI: Claude/Code, Claude-Desktop y Github/Copilot."
        tools = extract_ai_dev_tools(text)
        self.assertIn("claude code", tools)
        self.assertIn("claude desktop", tools)
        self.assertIn("github copilot", tools)

    def test_extract_ai_dev_tools_ignores_bare_copilot_brand(self) -> None:
        text = "Buscamos iOS dev para Copilot Money, startup fintech."
        tools = extract_ai_dev_tools(text)
        self.assertNotIn("github copilot", tools)

    def test_extract_ai_dev_tools_detects_herramientas_de_ia_singular_and_plural(self) -> None:
        plural = extract_ai_dev_tools("Buscamos perfil con uso de herramientas de IA en el flujo.")
        singular = extract_ai_dev_tools("Se valora herramienta de IA para productividad.")
        self.assertIn("herramientas de ia", plural)
        self.assertIn("herramientas de ia", singular)


if __name__ == "__main__":
    unittest.main()
