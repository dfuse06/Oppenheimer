from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AIProviderInfo:
    provider_id: str
    display_name: str
    configured: bool
    local: bool
    description: str


@dataclass(frozen=True)
class AIResult:
    text: str
    provider_id: str
    model: str | None = None
    metadata: dict[str, Any] | None = None


class AIProvider(ABC):
    @abstractmethod
    def info(self) -> AIProviderInfo:
        raise NotImplementedError

    @abstractmethod
    def ask(self, prompt: str, context: dict[str, Any]) -> AIResult:
        raise NotImplementedError
