from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import List


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class RecipeData:
    title: str
    cook_time: str
    ingredients: List[str]
    steps: List[str]
    missing_items: List[str]
    variations: List[str]
    serving_tips: List[str]


def parse_recipes_payload(raw: str) -> List[RecipeData]:
    normalized = _extract_json_block(raw)
    try:
        payload = json.loads(normalized)
    except json.JSONDecodeError as exc:
        LOGGER.debug("Raw model output that failed to parse: %s", raw)
        raise ValueError("Ответ модели имеет неверный JSON формат") from exc

    items = payload.get("recipes")
    if not isinstance(items, list) or not items:
        raise ValueError("JSON не содержит списка рецептов")

    recipes: List[RecipeData] = []
    for entry in items:
        if not isinstance(entry, dict):
            continue

        recipes.append(
            RecipeData(
                title=_get_text(entry, "title"),
                cook_time=_get_text(entry, "cook_time"),
                ingredients=_get_list(entry, "ingredients"),
                steps=_get_list(entry, "steps"),
                missing_items=_get_list(entry, "missing_items"),
                variations=_get_list(entry, "variations"),
                serving_tips=_get_list(entry, "serving_tips"),
            )
        )

    if not recipes:
        raise ValueError("Не удалось распарсить рецепты из JSON")

    return recipes


def _extract_json_block(raw: str) -> str:
    """Try to recover JSON even if the model added extra text or fences."""

    if not raw:
        return raw

    stripped = raw.strip()
    if stripped.startswith("```"):
        # remove all code fence markers like ```json / ```
        stripped = "\n".join(
            line for line in stripped.splitlines() if not line.strip().startswith("```")
        ).strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and start < end:
        return stripped[start : end + 1]

    return stripped


def _get_text(entry: dict, key: str) -> str:
    value = entry.get(key) or ""
    return str(value).strip()


def _get_list(entry: dict, key: str) -> List[str]:
    value = entry.get(key) or []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []

