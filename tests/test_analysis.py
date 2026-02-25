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
)


class AnalysisTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
