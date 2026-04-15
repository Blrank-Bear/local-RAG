"""Base agent interface."""
from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    name: str
    role: str

    @abstractmethod
    async def run(self, context: dict) -> dict:
        """Execute agent logic. Returns updated context dict."""
        ...
