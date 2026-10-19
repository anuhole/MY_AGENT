"""
AutoTestAI - LLM Orchestrator
Routes AI requests to configured providers (OpenAI, Gemini, Ollama).
Handles retries, fallback, and response caching.
"""
import logging
import json
import base64
from typing import Optional, Dict, Any, List
from pathlib import Path

from app.config import settings, AIProvider

logger = logging.getLogger(__name__)


class LLMOrchestrator:
    """
    Multi-provider LLM orchestrator.
    Supports OpenAI GPT-4, Google Gemini, and local Ollama models.
    """

    def __init__(self, provider: Optional[AIProvider] = None):
        self.provider = provider or settings.ACTIVE_AI_PROVIDER
        self._client = None
        self._init_client()

    def _init_client(self):
        """Initialize the appropriate LLM client."""
        if self.provider == AIProvider.OPENAI:
            self._init_openai()
        elif self.provider == AIProvider.GEMINI:
            self._init_gemini()
        elif self.provider == AIProvider.OLLAMA:
            self._init_ollama()

    def _init_openai(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not set in environment")
            self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info(f"OpenAI client initialized (model: {settings.OPENAI_MODEL})")
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    def _init_gemini(self):
        """Initialize Google Gemini client."""
        try:
            import google.generativeai as genai
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not set in environment")
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._client = genai.GenerativeModel(settings.GEMINI_MODEL)
            logger.info(f"Gemini client initialized (model: {settings.GEMINI_MODEL})")
        except ImportError:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")

    def _init_ollama(self):
        """Initialize Ollama client (uses OpenAI-compatible API)."""
        try:
            from openai import OpenAI
            self._client = OpenAI(
                base_url=f"{settings.OLLAMA_BASE_URL}/v1",
                api_key="ollama",  # Ollama doesn't need real API key
            )
            logger.info(f"Ollama client initialized (model: {settings.OLLAMA_MODEL})")
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        response_format: Optional[str] = None,
    ) -> str:
        """
        Generate a response from the configured LLM.

        Args:
            system_prompt: System/role instructions
            user_prompt: User's request/context
            temperature: Creativity control (0.0 = deterministic, 1.0 = creative)
            max_tokens: Maximum response tokens
            response_format: Optional "json" for structured responses

        Returns:
            Generated text response
        """
        logger.info(f"Generating response via {self.provider.value}...")

        try:
            if self.provider == AIProvider.OPENAI or self.provider == AIProvider.OLLAMA:
                return await self._generate_openai(
                    system_prompt, user_prompt, temperature, max_tokens, response_format
                )
            elif self.provider == AIProvider.GEMINI:
                return await self._generate_gemini(
                    system_prompt, user_prompt, temperature, max_tokens
                )
        except Exception as e:
            logger.error(f"LLM generation failed ({self.provider.value}): {e}")
            # Try fallback provider
            return await self._try_fallback(system_prompt, user_prompt, temperature, max_tokens, e)

    async def _generate_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        response_format: Optional[str] = None,
    ) -> str:
        """Generate using OpenAI/Ollama API."""
        model = settings.OPENAI_MODEL if self.provider == AIProvider.OPENAI else settings.OLLAMA_MODEL

        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format == "json" and self.provider == AIProvider.OPENAI:
            kwargs["response_format"] = {"type": "json_object"}

        response = self._client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    async def _generate_gemini(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate using Google Gemini API."""
        import google.generativeai as genai

        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = self._client.generate_content(
            full_prompt,
            generation_config=generation_config,
        )
        return response.text

    async def generate_with_vision(
        self,
        system_prompt: str,
        user_prompt: str,
        image_paths: List[str],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """
        Generate response using vision capabilities (for screenshot analysis).

        Args:
            system_prompt: System instructions
            user_prompt: Description of what to analyze
            image_paths: List of image file paths to analyze
            temperature: Creativity control
            max_tokens: Max response length

        Returns:
            AI analysis of the screenshots
        """
        logger.info(f"Generating vision response with {len(image_paths)} images...")

        if self.provider == AIProvider.OPENAI:
            return await self._vision_openai(
                system_prompt, user_prompt, image_paths, temperature, max_tokens
            )
        elif self.provider == AIProvider.GEMINI:
            return await self._vision_gemini(
                system_prompt, user_prompt, image_paths, temperature, max_tokens
            )
        else:
            raise ValueError(f"Vision not supported for provider: {self.provider.value}")

    async def _vision_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        image_paths: List[str],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Vision generation using OpenAI GPT-4V."""
        content = [{"type": "text", "text": user_prompt}]

        for img_path in image_paths:
            path = Path(img_path)
            if not path.exists():
                logger.warning(f"Image not found: {img_path}")
                continue

            with open(path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            # Detect mime type
            suffix = path.suffix.lower()
            mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
            mime = mime_map.get(suffix, "image/png")

            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{image_data}"},
            })

        response = self._client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    async def _vision_gemini(
        self,
        system_prompt: str,
        user_prompt: str,
        image_paths: List[str],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Vision generation using Gemini Vision."""
        import google.generativeai as genai
        from PIL import Image

        parts = [f"{system_prompt}\n\n{user_prompt}"]

        for img_path in image_paths:
            path = Path(img_path)
            if path.exists():
                img = Image.open(path)
                parts.append(img)

        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        response = self._client.generate_content(
            parts,
            generation_config=generation_config,
        )
        return response.text

    async def _try_fallback(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        original_error: Exception,
    ) -> str:
        """Try fallback AI provider if primary fails."""
        fallback_order = [AIProvider.OPENAI, AIProvider.GEMINI, AIProvider.OLLAMA]
        fallback_order = [p for p in fallback_order if p != self.provider]

        for fallback in fallback_order:
            try:
                logger.info(f"Trying fallback provider: {fallback.value}")
                fallback_orchestrator = LLMOrchestrator(provider=fallback)
                result = await fallback_orchestrator.generate(
                    system_prompt, user_prompt, temperature, max_tokens
                )
                logger.info(f"Fallback to {fallback.value} successful")
                return result
            except Exception as e:
                logger.warning(f"Fallback {fallback.value} also failed: {e}")
                continue

        raise RuntimeError(
            f"All AI providers failed. Primary error: {original_error}"
        )


# Singleton instance
llm = LLMOrchestrator()
