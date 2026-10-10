from app.llm.provider import LLMProvider


class MockLLMProvider(LLMProvider):
    """Deterministic provider used in tests. No network, no API key."""

    async def parse_statement_question(self, question: str) -> dict:
        q = question.lower()

        # Match both present and past tense: "send to" and "sent to"
        if "sent to" in q or "send to" in q:
            return {"type": 1, "counterparty": "Rahul",
                    "from": "2026-01-01", "to": "2026-12-31"}

        # Match both "receive" and "received"
        if "received" in q or "receive" in q:
            return {"type": 2, "from": "2026-01-01", "to": "2026-12-31"}

        # Match both "largest" and "biggest"
        if "largest" in q or "biggest" in q:
            return {"type": 3, "from": "2026-01-01", "to": "2026-12-31"}

        # Match "how many" and "number of"
        if "how many" in q or "number" in q:
            return {"type": 4, "from": "2026-01-01", "to": "2026-12-31"}

        return {"type": 0}

    async def explain_flag(self, rule: str, recent: list[dict]) -> dict:
        return {
            "explanation": f"Transfer flagged by rule: {rule}.",
            "label": "review",
        }
