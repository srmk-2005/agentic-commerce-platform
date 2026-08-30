"""Multi-Provider LLM Manager with automatic Gemini <-> Groq failover and deterministic fallback."""
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Type
from pydantic import BaseModel
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMManager:
    """
    Manages LLM invocations across multiple providers with resilient automatic failover.
    
    Failover Hierarchy:
    1. Primary Provider (e.g. Gemini or Groq, as configured in settings.PRIMARY_LLM_PROVIDER)
    2. Secondary Provider (e.g. Groq if Gemini is primary, or Gemini if Groq is primary)
    3. Deterministic Mock Fallback Engine (computes data-driven insights using real database facts)
    """

    def __init__(self):
        self.primary_provider = settings.PRIMARY_LLM_PROVIDER.lower()
        self.gemini_key = settings.GEMINI_API_KEY
        self.gemini_model = settings.GEMINI_MODEL
        self.groq_key = settings.GROQ_API_KEY
        self.groq_model = settings.GROQ_MODEL
        self.force_mock = settings.MOCK_AI_MODE

    def _get_provider_sequence(self) -> List[str]:
        """Determine order of providers based on settings."""
        if self.primary_provider == "groq":
            return ["groq", "gemini"]
        return ["gemini", "groq"]

    def _call_gemini(self, prompt: str, system_prompt: str = "") -> str:
        """Invoke Google Gemini model via langchain_google_genai."""
        if not self.gemini_key or not self.gemini_key.strip() or self.gemini_key == "your_gemini_api_key_here":
            raise ValueError("Gemini API key is not configured.")

        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage, SystemMessage

            llm = ChatGoogleGenerativeAI(
                model=self.gemini_model,
                google_api_key=self.gemini_key,
                temperature=0.2,
            )
            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=prompt))
            
            res = llm.invoke(messages)
            return res.content if isinstance(res.content, str) else str(res.content)
        except Exception as e:
            logger.warning(f"Gemini LLM call failed: {str(e)}")
            raise e

    def _call_groq(self, prompt: str, system_prompt: str = "") -> str:
        """Invoke Groq model via langchain_groq."""
        if not self.groq_key or not self.groq_key.strip() or self.groq_key == "your_groq_api_key_here":
            raise ValueError("Groq API key is not configured.")

        try:
            from langchain_groq import ChatGroq
            from langchain_core.messages import HumanMessage, SystemMessage

            llm = ChatGroq(
                model_name=self.groq_model,
                groq_api_key=self.groq_key,
                temperature=0.2,
            )
            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=prompt))

            res = llm.invoke(messages)
            return res.content if isinstance(res.content, str) else str(res.content)
        except Exception as e:
            logger.warning(f"Groq LLM call failed: {str(e)}")
            raise e

    def invoke_with_fallback(
        self,
        prompt: str,
        system_prompt: str = "",
        fallback_generator: Optional[Any] = None,
    ) -> Tuple[str, str, bool]:
        """
        Execute LLM call across providers with bi-directional failover.
        
        Returns:
            Tuple of (response_text, provider_name, is_fallback_mode)
        """
        if self.force_mock:
            fallback_text = fallback_generator() if fallback_generator else "Analysis generated via deterministic rules."
            return fallback_text, "Deterministic Engine (Mock Mode)", True

        providers = self._get_provider_sequence()
        errors = []

        for provider in providers:
            try:
                if provider == "gemini":
                    result = self._call_gemini(prompt, system_prompt)
                    return result, f"Google Gemini ({self.gemini_model})", False
                elif provider == "groq":
                    result = self._call_groq(prompt, system_prompt)
                    return result, f"Groq ({self.groq_model})", False
            except Exception as e:
                errors.append(f"{provider}: {str(e)}")
                logger.info(f"Provider {provider} failed, attempting next available provider...")

        # All LLM providers failed or unconfigured -> Use Deterministic Fallback Engine
        logger.info(f"All LLM providers unavailable ({'; '.join(errors)}). Engaging deterministic engine.")
        fallback_text = (
            fallback_generator()
            if fallback_generator
            else "Generated via deterministic revenue optimization rules."
        )
        return fallback_text, "Deterministic Engine (Fallback)", True


# Global LLM Manager instance
llm_manager = LLMManager()
