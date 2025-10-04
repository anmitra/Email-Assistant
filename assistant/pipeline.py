from .prompts import TRIAGE_PROMPT
from .llm import ask_json
from .schema import TriageOut
from .providers.base import Email, Provider

PRIORITY_TO_LABEL = {
    "high": "EA/Priority/High",
    "medium": "EA/Priority/Med",
    "low": "EA/Priority/Low"
}

def triage_message(p: Provider, msg: Email) -> TriageOut:
    prompt = TRIAGE_PROMPT.format(subject=msg.subject, sender=msg.sender, body=msg.body_text)
    data = ask_json(prompt)
    out = TriageOut(**data)

    # apply labels (idempotent in DemoProvider)
    labels_to_add = ["EA/Summary", PRIORITY_TO_LABEL[out.priority]]
    p.apply_labels(msg.id, add=labels_to_add)

    return out
