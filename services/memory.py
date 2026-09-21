from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, Iterable, List


@dataclass(slots=True)
class MemoryRecord:
    role: str
    content: str


class ConversationMemory:
    """Simple in-memory storage for recent user/bot messages."""

    def __init__(self, limit: int = 10) -> None:
        self._limit = limit
        self._storage: Dict[int, Deque[MemoryRecord]] = {}

    def add(self, chat_id: int, role: str, content: str) -> None:
        entry = MemoryRecord(role=role, content=content.strip())
        history = self._storage.setdefault(chat_id, deque(maxlen=self._limit))
        history.append(entry)

    def get_history(self, chat_id: int) -> List[MemoryRecord]:
        return list(self._storage.get(chat_id, []))

    def format_history(self, chat_id: int) -> str:
        history: Iterable[MemoryRecord] = self._storage.get(chat_id, [])
        return "\n".join(f"{record.role}: {record.content}" for record in history)

    def clear(self, chat_id: int) -> None:
        self._storage.pop(chat_id, None)

