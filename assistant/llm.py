# assistant/llm.py
import os, json, re
from typing import Any, Dict, Optional
from functools import lru_cache
from dotenv import load_dotenv
from openai import OpenAI

# load .env even if streamlit forgot to do it before import
load_dotenv()

@lru_cache()
def _get_client(api_key: Optional[str] = None) -> OpenAI:
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Set it in your environment or .env, "
            "or pass api_key= explicitly to ask_json()."
        )
    return OpenAI(api_key=key)

def ask_json(prompt: str, model: str = "gpt-4o-mini", api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Sends a prompt and returns a parsed JSON object.
    Assumes the model replies with JSON. Strips code fences if present.
    """
    client = _get_client(api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    ).choices[0].message.content

    clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", resp.strip(), flags=re.I)
    if not clean.lstrip().startswith(("{", "[")):
        m = re.search(r"(\{.*\}|\[.*\])\s*$", clean, flags=re.S)
        if m:
            clean = m.group(0).strip()

    return json.loads(clean)

__all__ = ["ask_json"]
