from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from dccempleo_analytics.baml_runtime import prepare_baml_env


class BamlRuntimeTests(unittest.TestCase):
    def test_prepare_baml_env_sets_defaults(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            prepare_baml_env(model_name="opencode/trinity-large-preview-free")
            self.assertEqual(os.environ["BAML_MODEL"], "opencode/trinity-large-preview-free")
            self.assertEqual(os.environ["BAML_PROXY_API_KEY"], "dummy")
            self.assertEqual(os.environ["BAML_PROXY_BASE_URL"], "http://127.0.0.1:4100/v1")

    def test_prepare_baml_env_respects_existing_values(self) -> None:
        with patch.dict(
            os.environ,
            {
                "BAML_MODEL": "custom/model",
                "BAML_PROXY_API_KEY": "secret",
                "BAML_PROXY_BASE_URL": "http://127.0.0.1:4999/v1",
            },
            clear=True,
        ):
            prepare_baml_env(model_name="opencode/ignored-model")
            self.assertEqual(os.environ["BAML_MODEL"], "custom/model")
            self.assertEqual(os.environ["BAML_PROXY_API_KEY"], "secret")
            self.assertEqual(os.environ["BAML_PROXY_BASE_URL"], "http://127.0.0.1:4999/v1")


if __name__ == "__main__":
    unittest.main()
