from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract LLM provider. One small interface, two implementations."""

    @abstractmethod
    async def parse_statement_question(self, question: str) -> dict:
        """Return JSON like {"type": 1, "counterparty": "Rahul", ...}."""
        ...

    @abstractmethod
    async def explain_flag(self, rule: str, recent: list[dict]) -> dict:
        """Return {"explanation": "...", "label": "likely_ok"}."""
        ...
