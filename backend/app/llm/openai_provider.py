import json
from openai import AsyncOpenAI

from app.config import settings
from app.llm.provider import LLMProvider


class OpenAIProvider(LLMProvider):
    """Real LLM provider. Requires OPENAI_API_KEY."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def parse_statement_question(self, question: str) -> dict:
        prompt = f"""
You are a JSON-only parser. The user asked:
"{question}"

Return ONLY JSON in this format:
{{"type": 1, "counterparty": "Rahul", "from": "YYYY-MM-DD", "to": "YYYY-MM-DD"}}

Types:
  1 = total sent to a person in a date range
  2 = total received in a date range
  3 = largest transfer in a date range
  4 = number of transfers in a date range
  0 = unsupported question

Return JSON only.
"""
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        try:
            return json.loads(response.choices[0].message.content)
        except Exception:
            return {"type": 0}

    async def explain_flag(self, rule: str, recent: list[dict]) -> dict:
        prompt = f"""
A transfer was flagged by rule: {rule}.
Last 10 transfers of the wallet:
{json.dumps(recent)}

Return ONLY JSON:
{{"explanation": "Two sentences.", "label": "likely_ok" | "review" | "likely_fraud"}}
"""
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        try:
            return json.loads(response.choices[0].message.content)
        except Exception:
            return {"explanation": "", "label": "review"}
