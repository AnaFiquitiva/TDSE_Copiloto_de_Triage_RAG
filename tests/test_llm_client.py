"""Pruebas del cliente de Gemini SIN llamadas de red reales: se simula
`urllib.request.urlopen` para mantener la suite de pruebas rápida,
determinista y sin necesitar una API key."""
import json
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from src import llm_client


class _FakeResponse:
    def __init__(self, payload: dict):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class TestGetApiKey(unittest.TestCase):
    def test_missing_key_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(llm_client.LLMUnavailableError):
                llm_client.get_api_key()

    def test_present_key_is_returned(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "fake-key"}):
            self.assertEqual(llm_client.get_api_key(), "fake-key")


class TestEmbedText(unittest.TestCase):
    def test_parses_embedding_values(self):
        fake_payload = {"embedding": {"values": [0.1, 0.2, 0.3]}}
        with patch("urllib.request.urlopen", return_value=_FakeResponse(fake_payload)):
            result = llm_client.embed_text("dolor de cabeza", api_key="fake-key")
        self.assertEqual(result, [0.1, 0.2, 0.3])

    def test_malformed_response_raises(self):
        with patch("urllib.request.urlopen", return_value=_FakeResponse({"unexpected": True})):
            with self.assertRaises(llm_client.LLMUnavailableError):
                llm_client.embed_text("texto", api_key="fake-key")

    def test_task_type_is_sent_in_request_payload(self):
        """GeminiRetriever depende de que task_type efectivamente viaje en el
        payload para lograr la codificación asimétrica consulta/documento."""
        fake_payload = {"embedding": {"values": [0.1]}}
        captured = {}

        def fake_urlopen(request, timeout=None):
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return _FakeResponse(fake_payload)

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            llm_client.embed_text("texto", api_key="fake-key", task_type="RETRIEVAL_DOCUMENT")
        self.assertEqual(captured["body"].get("taskType"), "RETRIEVAL_DOCUMENT")

    def test_no_task_type_omits_field_from_payload(self):
        captured = {}

        def fake_urlopen(request, timeout=None):
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return _FakeResponse({"embedding": {"values": [0.1]}})

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            llm_client.embed_text("texto", api_key="fake-key")
        self.assertNotIn("taskType", captured["body"])


class TestGenerateStructured(unittest.TestCase):
    def test_parses_json_from_candidate_text(self):
        inner_json = json.dumps({"citation": "N2", "abstain": False, "reasoning": "porque si"})
        fake_payload = {"candidates": [{"content": {"parts": [{"text": inner_json}]}}]}
        with patch("urllib.request.urlopen", return_value=_FakeResponse(fake_payload)):
            result = llm_client.generate_structured("un prompt", api_key="fake-key")
        self.assertEqual(result["citation"], "N2")
        self.assertFalse(result["abstain"])


class TestRetryBehavior(unittest.TestCase):
    def test_retries_on_retryable_status_then_succeeds(self):
        fake_payload = {"embedding": {"values": [1.0]}}
        error_503 = urllib.error.HTTPError(
            url="http://x", code=503, msg="unavailable", hdrs=None, fp=MagicMock(read=lambda: b"{}")
        )
        with patch(
            "urllib.request.urlopen", side_effect=[error_503, _FakeResponse(fake_payload)]
        ), patch("time.sleep"):
            result = llm_client.embed_text("texto", api_key="fake-key")
        self.assertEqual(result, [1.0])

    def test_non_retryable_status_raises_immediately(self):
        error_404 = urllib.error.HTTPError(
            url="http://x", code=404, msg="not found", hdrs=None, fp=MagicMock(read=lambda: b"{}")
        )
        with patch("urllib.request.urlopen", side_effect=error_404):
            with self.assertRaises(llm_client.LLMUnavailableError):
                llm_client.embed_text("texto", api_key="fake-key")


if __name__ == "__main__":
    unittest.main()
