"""LLM client with support for vLLM and OpenAI.

Provides unified interface for:
- Local vLLM server
- OpenAI API
- Automatic fallback
"""

from typing import Optional

from src.config import (
    VLLM_API_BASE,
    VLLM_MODEL,
    USE_VLLM,
    MAX_GENERATION_TOKENS,
    GENERATION_TEMPERATURE,
)


class LLMClient:
    """Unified LLM client with vLLM and OpenAI support."""

    def __init__(self, use_vllm: bool = USE_VLLM):
        """Initialize LLM client.

        Args:
            use_vllm: Whether to use vLLM (if available).
        """
        self.use_vllm = use_vllm
        self._openai_client = None
        self._vllm_client = None

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = MAX_GENERATION_TOKENS,
        temperature: float = GENERATION_TEMPERATURE,
    ) -> str:
        """Generate text from prompts.

        Args:
            system_prompt: System prompt.
            user_prompt: User prompt.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            Generated text.
        """
        if self.use_vllm:
            try:
                return self._generate_vllm(
                    system_prompt, user_prompt, max_tokens, temperature
                )
            except Exception as e:
                # Fall back to OpenAI on vLLM failure
                print(f"vLLM generation failed ({e}), falling back to OpenAI")
                return self._generate_openai(
                    system_prompt, user_prompt, max_tokens, temperature
                )
        else:
            return self._generate_openai(
                system_prompt, user_prompt, max_tokens, temperature
            )

    def _generate_vllm(
        self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float
    ) -> str:
        """Generate using vLLM server."""
        if self._vllm_client is None:
            try:
                import openai
                # vLLM exposes OpenAI-compatible API
                self._vllm_client = openai.OpenAI(
                    api_key="EMPTY",  # vLLM doesn't require API key
                    base_url=VLLM_API_BASE,
                )
            except ImportError:
                raise ImportError(
                    "openai package not installed. "
                    "Install with: pip install openai"
                )

        response = self._vllm_client.chat.completions.create(
            model=VLLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return response.choices[0].message.content.strip()

    def _generate_openai(
        self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float
    ) -> str:
        """Generate using OpenAI API."""
        if self._openai_client is None:
            try:
                import openai
                self._openai_client = openai.OpenAI()
            except ImportError:
                raise ImportError(
                    "openai package not installed. "
                    "Install with: pip install openai"
                )

        response = self._openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return response.choices[0].message.content.strip()


def create_client(use_vllm: Optional[bool] = None) -> LLMClient:
    """Create an LLM client with appropriate configuration.

    Args:
        use_vllm: Whether to use vLLM. If None, uses config default.

    Returns:
        Configured LLMClient instance.
    """
    if use_vllm is None:
        use_vllm = USE_VLLM

    return LLMClient(use_vllm=use_vllm)
