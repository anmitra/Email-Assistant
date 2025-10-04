from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Email:
    id: str
    thread_id: str
    when: int     # epoch seconds
    sender: str
    subject: str
    body_text: str
    labels: List[str]

class Provider(ABC):
    @abstractmethod
    def list_messages(self, limit: int = 100) -> List[Email]: ...
    @abstractmethod
    def get_message(self, id: str) -> Email: ...
    @abstractmethod
    def apply_labels(self, id: str, add: List[str], remove: Optional[List[str]] = None) -> None: ...
    @abstractmethod
    def create_draft(self, thread_id: str, body: str) -> str: ...
