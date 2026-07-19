from __future__ import annotations

from typing import Any

from engine.ai.provider import AIProvider, AIProviderInfo, AIResult


class DisabledProvider(AIProvider):
    def info(self) -> AIProviderInfo:
        return AIProviderInfo(
            provider_id="none",
            display_name="No provider",
            configured=False,
            local=True,
            description="Configure OpenAI, Ollama, or LM Studio later.",
        )

    def ask(self, prompt: str, context: dict[str, Any]) -> AIResult:
        raise RuntimeError("No AI provider is configured.")
