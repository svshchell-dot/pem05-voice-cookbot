from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Optional, Sequence

from services.recipes.schemas import RecipeData, parse_recipes_payload

from .openai_client import OpenAIClient

JSON_SCHEMA = """
Когда рецепт готов, верни JSON без пояснений:
{
  "recipes": [
    {
      "title": "...",
      "cook_time": "...",
      "ingredients": ["..."],
      "steps": ["..."],
      "missing_items": ["..."],
      "variations": ["..."],
      "serving_tips": ["..."]
    }
  ]
}
""".strip().replace("{", "{{").replace("}", "}}")

INTERACTIVE_PROMPT = """
Ты — персональный интерактивный шеф. Ты ведёшь диалог с пользователем, чтобы
получить все детали о том, что он хочет приготовить, а затем выдаёшь точный
рецепт.

История диалога (формат "роль: сообщение"):
{history}

Осталось уточняющих вопросов: {remaining}
Максимум вопросов за сессию: {max_questions}

Правила:
1. Если осталось хотя бы 1 уточняющий вопрос и информации мало — задай один
   наводящий вопрос строго в формате `ASK: <текст вопроса>`.
2. Если информации достаточно или вопросы закончились — ответь только JSON по
   схеме ниже, без дополнительного текста.
3. В рецепте используй все ответы пользователя.
4. Не задавай больше одного вопроса за раз.
5. Если история пуста, начни с вопроса, что пользователь хочет приготовить.

{json_schema}
""".strip()


@dataclass(slots=True)
class InteractiveResponse:
    kind: Literal["ask", "recipe"]
    content: Optional[str] = None
    recipes: Optional[List[RecipeData]] = None


class InteractiveChef:
    """Manages multistep recipe clarification powered by GPT."""

    def __init__(self, client: OpenAIClient, *, max_questions: int = 3) -> None:
        self._client = client
        self._max_questions = max_questions

    @property
    def max_questions(self) -> int:
        return self._max_questions

    async def next_step(
        self,
        history: Sequence[dict[str, str]],
        remaining_questions: int,
    ) -> InteractiveResponse:
        serialized = self._serialize_history(history)
        prompt = INTERACTIVE_PROMPT.format(
            history=serialized,
            remaining=max(0, remaining_questions),
            max_questions=self._max_questions,
            json_schema=JSON_SCHEMA,
        )
        raw = await self._client.generate_text(prompt)
        return self._parse_response(raw)

    @staticmethod
    def _serialize_history(history: Sequence[dict[str, str]]) -> str:
        if not history:
            return "assistant: Привет! Что хочешь приготовить?"
        return "\n".join(f"{item['role']}: {item['content']}" for item in history)

    @staticmethod
    def _parse_response(raw: str) -> InteractiveResponse:
        cleaned = raw.strip()
        normalized = cleaned.lower()

        if normalized.startswith("ask:"):
            question = cleaned[4:].strip()
            return InteractiveResponse(kind="ask", content=question)

        payload = cleaned
        if normalized.startswith("json:"):
            payload = cleaned.split(":", 1)[1].strip()
        elif not cleaned.lstrip().startswith("{") and ":" in cleaned:
            payload = cleaned.split(":", 1)[1].strip()

        try:
            recipes = parse_recipes_payload(payload)
        except ValueError as exc:
            raise ValueError("Интерактивный рецепт не соответствует JSON-схеме") from exc

        return InteractiveResponse(kind="recipe", recipes=recipes)

