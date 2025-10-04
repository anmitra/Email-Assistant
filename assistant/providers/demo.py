import json, pathlib
from typing import List, Optional
from .base import Provider, Email

class DemoProvider(Provider):
    def __init__(self, path: str = "data/sample_inbox.json"):
        raw = pathlib.Path(path).read_text(encoding="utf-8")
        self._msgs = json.loads(raw)

    def _find(self, id: str) -> dict:
        return next(m for m in self._msgs if m["id"] == id)

    def list_messages(self, limit: int = 100) -> List[Email]:
        return [Email(**m) for m in self._msgs[:limit]]

    def get_message(self, id: str) -> Email:
        return Email(**self._find(id))

    def apply_labels(self, id: str, add: List[str], remove: Optional[List[str]] = None) -> None:
        m = self._find(id)
        labels = set(m.get("labels", []))
        labels.update(add or [])
        for r in (remove or []):
            labels.discard(r)
        m["labels"] = sorted(labels)

    def create_draft(self, thread_id: str, body: str) -> str:
        # Demo mode: pretend we created a draft
        return f"draft_{thread_id}"
