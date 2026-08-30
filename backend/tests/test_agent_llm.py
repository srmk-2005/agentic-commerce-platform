"""Tests for multi-provider LLM Manager and failover mechanism."""
from unittest.mock import MagicMock, patch
from app.agent.llm import LLMManager


def test_llm_manager_fallback_when_unconfigured():
    manager = LLMManager()
    manager.gemini_key = None
    manager.groq_key = None
    manager.force_mock = False

    def dummy_fallback():
        return "Deterministic fallback response"

    response, provider, is_fallback = manager.invoke_with_fallback(
        prompt="Test query",
        system_prompt="Test system",
        fallback_generator=dummy_fallback,
    )

    assert response == "Deterministic fallback response"
    assert is_fallback is True
    assert "Deterministic Engine" in provider


def test_llm_manager_gemini_to_groq_failover():
    manager = LLMManager()
    manager.primary_provider = "gemini"
    manager.gemini_key = "fake_gemini_key"
    manager.groq_key = "fake_groq_key"
    manager.force_mock = False

    # Simulate Gemini failing with exception and Groq succeeding
    with patch.object(manager, "_call_gemini", side_effect=RuntimeError("Gemini Quota Exceeded")):
        with patch.object(manager, "_call_groq", return_value="Groq response success"):
            response, provider, is_fallback = manager.invoke_with_fallback(
                prompt="Hello",
                system_prompt="System",
            )
            assert response == "Groq response success"
            assert "Groq" in provider
            assert is_fallback is False


def test_llm_manager_groq_to_gemini_failover():
    manager = LLMManager()
    manager.primary_provider = "groq"
    manager.gemini_key = "fake_gemini_key"
    manager.groq_key = "fake_groq_key"
    manager.force_mock = False

    # Simulate Groq failing and Gemini succeeding
    with patch.object(manager, "_call_groq", side_effect=RuntimeError("Groq 429 Rate Limit")):
        with patch.object(manager, "_call_gemini", return_value="Gemini response success"):
            response, provider, is_fallback = manager.invoke_with_fallback(
                prompt="Hello",
                system_prompt="System",
            )
            assert response == "Gemini response success"
            assert "Gemini" in provider
            assert is_fallback is False


def test_llm_manager_mock_mode():
    manager = LLMManager()
    manager.force_mock = True

    response, provider, is_fallback = manager.invoke_with_fallback(
        prompt="Hello",
        system_prompt="System",
        fallback_generator=lambda: "Mocked output",
    )
    assert response == "Mocked output"
    assert is_fallback is True
    assert "Mock Mode" in provider
