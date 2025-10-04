# app/streamlit_app.py
from __future__ import annotations

import os
import json
import base64
import hashlib
import pathlib
import re, html
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import streamlit as st
from dotenv import load_dotenv

# =========================
# Env & Page Setup
# =========================
load_dotenv()  # loads OPENAI_API_KEY / ANTHROPIC_API_KEY from .env (if present)

st.set_page_config(
    page_title="AI Email Secretary",
    page_icon="📬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Minimal CSS (no @import to avoid frontend InvalidCharacterError)
st.markdown("""
<style>
html, body, [class*="css"]  {
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial, sans-serif;
}
:root { --card-bg: rgba(255,255,255,0.04); --card-border: rgba(255,255,255,0.08);
        --good: #22C55E; --warn: #F59E0B; --bad: #EF4444; --muted: #9CA3AF; }
.app-title { font-weight: 700; letter-spacing: .2px; margin-bottom: .25rem; }
.app-subtitle { color: var(--muted); font-size: 0.95rem; margin-top: -4px; }
.card { border: 1px solid var(--card-border); background: var(--card-bg); border-radius: 16px;
        padding: 16px 18px; box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        transition: border-color .2s ease, transform .05s ease; }
.card:hover { border-color: rgba(139,92,246,.45); transform: translateY(-1px); }
.card-title { font-weight: 600; margin-bottom: 6px; }
.card-meta { color: var(--muted); font-size: 0.85rem; }
.badge { display:inline-flex; align-items:center; gap:6px; font-size: 0.8rem; font-weight: 600;
         padding: 4px 10px; border-radius: 999px; line-height: 1;
         border: 1px solid var(--card-border); background: rgba(255,255,255,0.06); }
.badge.good { border-color: rgba(34,197,94,.35); }
.badge.warn { border-color: rgba(245,158,11,.35); }
.badge.bad  { border-color: rgba(239,68,68,.35); }
.header-actions > div button { border-radius: 999px !important; }
details, .streamlit-expanderHeader:focus { outline: none; }
.block-container { padding-top: 1.6rem; }
</style>
""", unsafe_allow_html=True)

# =========================
# Session Defaults (JSON-friendly types only)
# =========================
def ensure_state_defaults():
    st.session_state.setdefault("logs", [])
    st.session_state.setdefault("mock_mode", False)
    st.session_state.setdefault("save_logs", True)
    st.session_state.setdefault("provider", "OpenAI")
    st.session_state.setdefault("model", "gpt-4o-mini")
    st.session_state.setdefault("connected", True)
    st.session_state.setdefault("archived_ids", [])   # list (not set)
    st.session_state.setdefault("reply_open", {})     # dict ok
    st.session_state.setdefault("last_provider", "OpenAI")
    st.session_state.setdefault("triage_text", "")
    st.session_state.setdefault("triage_items", [])   # persist results across reruns
    # Gmail
    st.session_state.setdefault("gmail_enabled", True)
    st.session_state.setdefault("gmail_connected", False)
    st.session_state.setdefault("gmail_profile", None)
    st.session_state.setdefault("gmail_pull_n", 5)    # default pull

ensure_state_defaults()

# =========================
# Helpers (Sanitization & UI)
# =========================
CONTROL_CHARS_RE = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]')

def sanitize_text(s: str | None) -> str:
    """Remove problematic control chars; keep valid UTF-8 and emojis."""
    if s is None:
        return ""
    if not isinstance(s, str):
        s = str(s)
    s = s.encode("utf-8", "ignore").decode("utf-8", "ignore")
    s = CONTROL_CHARS_RE.sub("", s)
    return s

def h(s: str | None) -> str:
    """HTML-escape after sanitization for safe injection into st.markdown HTML."""
    return html.escape(sanitize_text(s or ""))

def status_badge(level: str) -> str:
    level = (level or "").lower()
    cls = "good" if level in ("ok", "info", "success", "low") else "warn" if level in ("warn","medium") else "bad"
    text = "Low" if cls=="good" else "Medium" if cls=="warn" else "High"
    return f'<span class="badge {cls}">● {text} priority</span>'

def make_uid(item: Dict[str, Any]) -> str:
    s = f"{item.get('subject','')}-{item.get('from','')}-{item.get('date','')}"
    return hashlib.sha1(s.encode()).hexdigest()[:12]

def default_model_for(provider: str) -> str:
    return "claude-3-5-sonnet" if provider == "Anthropic" else "gpt-4o-mini"

# --- Model aliases & resolver ---
MODEL_ALIASES: Dict[str, Dict[str, str]] = {
    "Anthropic": {
        "claude-3-5-sonnet": "claude-3-5-sonnet-latest",
        "claude-3-5-haiku":  "claude-3-5-haiku-latest",
        "claude-3-opus":     "claude-3-opus-latest",
    },
    "OpenAI": {
        "gpt-4o-mini": "gpt-4o-mini",
        "gpt-4o":      "gpt-4o",
        "o4-mini":     "o4-mini",
    },
}

def resolve_model(provider: str, name: str) -> str:
    """Translate friendly model names to provider API IDs."""
    return MODEL_ALIASES.get(provider, {}).get(name, name)

# =========================
# LLM Bridges (OpenAI / Anthropic)
# =========================
TRIAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type":"object",
                "properties":{
                    "subject":{"type":"string"},
                    "from":{"type":"string"},
                    "date":{"type":"string"},
                    "priority":{"type":"string", "enum":["low","medium","high"]},
                    "summary":{"type":"string"},
                    "next_step":{"type":"string"},
                    "labels":{"type":"array","items":{"type":"string"}},
                    "score":{"type":"number"}
                },
                "required":["subject","from","summary","priority"]
            }
        }
    },
    "required":["items"]
}

SYSTEM_TRIAGE = (
    "You are an email triage assistant. "
    "Return STRICT JSON conforming to the provided schema. "
    "Summarize, classify priority (low|medium|high), suggest next_step, and propose labels. "
    "Never include explanations outside JSON."
)

def ask_json_openai(prompt: str, model: str) -> Dict[str, Any]:
    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError("OpenAI SDK not installed. pip install openai") from e
    if not os.environ.get("OPENAI_API_KEY") and not st.secrets.get("OPENAI_API_KEY"):
        raise RuntimeError("Missing OPENAI_API_KEY in environment/secrets.")

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role":"system","content": SYSTEM_TRIAGE},
            {"role":"user","content": f"Schema:\n{json.dumps(TRIAGE_SCHEMA)}\n\nEmails:\n{prompt}"}
        ],
        response_format={"type":"json_object"},
        temperature=0.2,
    )
    content = resp.choices[0].message.content
    return json.loads(content)

def ask_json_anthropic(prompt: str, model: str) -> Dict[str, Any]:
    try:
        import anthropic
    except Exception as e:
        raise RuntimeError("Anthropic SDK not installed. pip install anthropic") from e
    if not os.environ.get("ANTHROPIC_API_KEY") and not st.secrets.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("Missing ANTHROPIC_API_KEY in environment/secrets.")

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY"))
    msg = client.messages.create(
        model=model,
        max_tokens=2000,
        temperature=0.2,
        system=SYSTEM_TRIAGE + " Output JSON only.",
        messages=[{"role": "user", "content": f"Schema:\n{json.dumps(TRIAGE_SCHEMA)}\n\nEmails:\n{prompt}"}]
    )
    text = "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "") == "text").strip()
    text = text.removeprefix("```json").removesuffix("```").strip()
    return json.loads(text)

def ask_json(prompt: str, provider: str, model: str) -> Dict[str, Any]:
    return ask_json_openai(prompt, model) if provider == "OpenAI" else ask_json_anthropic(prompt, model)

# =========================
# Gmail Integration (Demo mode / Desktop OAuth)
# =========================
OAUTH_DIR = pathlib.Path(".oauth")
OAUTH_DIR.mkdir(exist_ok=True)
CLIENT_SECRET_PATH = OAUTH_DIR / "client_secret.json"  # Desktop OAuth (local dev)
TOKEN_PATH = OAUTH_DIR / "token.json"
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

def gmail_get_service():
    """
    Returns an authenticated Gmail service.

    Modes:
    1) Demo mode (GMAIL_DEMO_ENABLED=true) - loads authorized user creds from secrets (GMAIL_TOKEN_JSON)
       and refreshes automatically (no viewer OAuth).
    2) Fallback (local dev) - Desktop OAuth from ./.oauth/client_secret.json
    """
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    demo_mode = (str(st.secrets.get("GMAIL_DEMO_ENABLED","")).lower() in ("1","true","yes")
                 or str(os.getenv("GMAIL_DEMO_ENABLED","")).lower() in ("1","true","yes"))

    if demo_mode:
        if "GMAIL_TOKEN_JSON" not in st.secrets:
            raise RuntimeError("GMAIL_DEMO_ENABLED is true but GMAIL_TOKEN_JSON secret is missing.")
        token_info = json.loads(st.secrets["GMAIL_TOKEN_JSON"])

        # token.json sometimes lacks client fields — fill from Web client
        if ("client_id" not in token_info or "client_secret" not in token_info or "token_uri" not in token_info):
            if "GOOGLE_OAUTH_WEB_CLIENT_JSON" not in st.secrets:
                raise RuntimeError("Token missing client fields; add GOOGLE_OAUTH_WEB_CLIENT_JSON secret.")
            web_client = json.loads(st.secrets["GOOGLE_OAUTH_WEB_CLIENT_JSON"]).get("web", {})
            token_info.setdefault("client_id", web_client.get("client_id"))
            token_info.setdefault("client_secret", web_client.get("client_secret"))
            token_info.setdefault("token_uri", web_client.get("token_uri", "https://oauth2.googleapis.com/token"))

        creds = Credentials.from_authorized_user_info(token_info, scopes=GMAIL_SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        if not creds or not creds.valid:
            raise RuntimeError("Demo Gmail credentials invalid; regenerate token.json for the demo mailbox.")
        return build("gmail", "v1", credentials=creds)

    # ---- Local Desktop OAuth fallback ----
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), GMAIL_SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request()); TOKEN_PATH.write_text(creds.to_json())
    if not creds or not creds.valid:
        if not CLIENT_SECRET_PATH.exists():
            raise RuntimeError("Missing Desktop OAuth client at ./.oauth/client_secret.json")
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_PATH), GMAIL_SCOPES)
        creds = flow.run_local_server(port=0); TOKEN_PATH.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def gmail_profile(service) -> Dict[str,Any]:
    return service.users().getProfile(userId="me").execute()

def gmail_list_messages(service, max_results=5) -> List[Dict[str,Any]]:
    res = service.users().messages().list(userId="me", labelIds=["INBOX"], maxResults=max_results).execute()
    return res.get("messages", [])

def gmail_get_message(service, msg_id: str) -> Dict[str,Any]:
    return service.users().messages().get(userId="me", id=msg_id, format="full").execute()

def gmail_send(service, to: str, subject: str, body: str):
    mime = MIMEText(body, "plain", "utf-8")
    mime["to"] = to
    mime["subject"] = subject
    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
    return service.users().messages().send(userId="me", body={"raw": raw}).execute()

def gmail_pretty_row(msg: Dict[str,Any]) -> Dict[str,str]:
    headers = {h["name"].lower(): sanitize_text(h["value"]) for h in msg.get("payload", {}).get("headers", [])}
    return {
        "from": sanitize_text(headers.get("from","")),
        "subject": sanitize_text(headers.get("subject","")),
        "date": sanitize_text(headers.get("date","")),
        "snippet": sanitize_text(msg.get("snippet","")),
    }

# Optional: restrict sends in demo mode
def is_demo_mode() -> bool:
    return (str(st.secrets.get("GMAIL_DEMO_ENABLED","")).lower() in ("1","true","yes")
            or str(os.getenv("GMAIL_DEMO_ENABLED","")).lower() in ("1","true","yes"))

def can_send(addr: str) -> bool:
    dom = (st.secrets.get("DEMO_SEND_DOMAIN") or os.getenv("DEMO_SEND_DOMAIN") or "").lower().strip()
    return (not dom) or addr.lower().endswith(f"@{dom}")

# =========================
# UI: Header
# =========================
left, right = st.columns([0.7, 0.3])
with left:
    st.markdown('<div class="app-title">📬 AI Email Secretary</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">Triage, summarize, and action your inbox—calmly.</div>', unsafe_allow_html=True)
with right:
    st.write(""); st.write("")
    has_openai = bool(os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY"))
    has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY"))
    connected = has_openai or has_anthropic
    st.session_state.connected = connected
    st.markdown(
        f'<span class="badge {"good" if connected else "bad"}">'
        f'{"● LLM Connected" if connected else "● LLM Disconnected"}</span>',
        unsafe_allow_html=True
    )
    if is_demo_mode():
        st.markdown('<span class="badge good">● Demo mailbox pre-connected</span>', unsafe_allow_html=True)

# =========================
# Tabs
# =========================
tab_inbox, tab_compose, tab_settings, tab_logs = st.tabs(
    ["📥 Inbox Triage", "✍️ Compose", "⚙️ Settings", "🧾 Logs"]
)

# =========================
# Reusable Card Component
# =========================
def message_card(item: Dict[str, Any], key: Optional[str] = None):
    uid = key or make_uid(item)
    subject = sanitize_text(item.get("subject","(No subject)"))
    sender  = sanitize_text(item.get("from",""))
    date    = sanitize_text(item.get("date",""))
    pr      = (item.get("priority","") or "").lower()
    summary = sanitize_text(item.get("summary",""))
    next_step = sanitize_text(item.get("next_step",""))
    labels = [sanitize_text(l) for l in (item.get("labels") or [])]
    score  = item.get("score")

    st.markdown('<div class="card">', unsafe_allow_html=True)

    # Header
    top_l, top_r = st.columns([0.8, 0.2])
    with top_l:
        st.markdown(f'<div class="card-title">{h(subject)}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="card-meta">From {h(sender)} • {h(date)}</div>', unsafe_allow_html=True)
    with top_r:
        st.markdown(status_badge(pr), unsafe_allow_html=True)

    # Body
    if summary: st.write(summary)
    if next_step:
        st.caption("Next step:")
        st.write(f"• {next_step}")
    if labels:
        st.caption("Labels:")
        safe_labels = " ".join([f'<span class="badge">{h(l)}</span>' for l in labels])
        st.markdown(safe_labels, unsafe_allow_html=True)

    # Footer
    foot_a, foot_b, foot_c = st.columns([0.55, 0.225, 0.225])
    with foot_a:
        if score is not None:
            st.caption(f"Relevance score: {score:.2f}")

    with foot_b:
        if st.button("Archive", key=f"archive_btn_{uid}"):
            archived = set(st.session_state.archived_ids)
            archived.add(uid)
            st.session_state.archived_ids = list(archived)
            st.toast("Archived ✅")

    with foot_c:
        # Inline handler: flipping state is enough; Streamlit reruns automatically
        if st.button("Reply", key=f"reply_btn_{uid}"):
            st.session_state.reply_open[uid] = not st.session_state.reply_open.get(uid, False)

    # Inline reply form
    if st.session_state.reply_open.get(uid, False):
        st.divider()
        st.caption("Reply")
        default_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"
        with st.form(f"reply_form_{uid}", clear_on_submit=False):
            r_to = st.text_input("To", value=sender, key=f"reply_to_{uid}")
            r_subject = st.text_input("Subject", value=default_subject, key=f"reply_subj_{uid}")
            r_body = st.text_area("Message", height=150, placeholder="Type your reply…", key=f"reply_body_{uid}")
            send = st.form_submit_button("Send Reply")

        if send:
            try:
                if is_demo_mode() and not can_send(r_to):
                    st.error("Sending in demo is restricted. Set DEMO_SEND_DOMAIN to allow specific domain.")
                else:
                    service = gmail_get_service()
                    gmail_send(service, r_to, r_subject, r_body)
                    st.toast("Reply sent ✉️")
            except Exception as e:
                st.error(f"Gmail send failed: {e}")

            # close the form; Streamlit will rerun due to form submission
            st.session_state.reply_open[uid] = False
            if st.session_state.save_logs:
                st.session_state.logs.append({
                    "event": "reply_send",
                    "data": {"to": r_to, "subject": r_subject, "len": len(r_body)}
                })

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# Inbox Triage (Gmail connect & pull here)
# =========================
with tab_inbox:
    st.subheader("Inbox Triage")

    left, right = st.columns([0.42, 0.58])
    with left:
        st.session_state.provider = st.selectbox("Provider", ["OpenAI", "Anthropic"], index=0)

        if st.session_state.last_provider != st.session_state.provider:
            st.session_state.model = default_model_for(st.session_state.provider)
            st.session_state.last_provider = st.session_state.provider

        st.session_state.model = st.text_input("Model", value=st.session_state.model)
        st.caption(f"Resolved model id: **{resolve_model(st.session_state.provider, st.session_state.model)}**")
        st.toggle("Mock Mode (no API calls)", key="mock_mode", value=st.session_state.mock_mode)
        st.toggle("Save raw responses to Logs", key="save_logs", value=st.session_state.save_logs)

        st.caption("Paste one or more raw emails below (subject/from/date/body). Separate with ---")
        st.session_state.triage_text = st.text_area(
            "Emails to triage",
            height=220,
            value=st.session_state.triage_text,
            placeholder=(
                "Subject: Invoice for September\nFrom: accounts@example.com\nDate: 2025-10-03 14:05\nBody: ...\n"
                "---\n"
                "Subject: Team offsite agenda\nFrom: hr@example.com\nDate: 2025-10-03 12:40\nBody: ..."
            ),
        )
        run_btn = st.button("Run Triage", type="primary")

    with right:
        st.subheader("Gmail")
        st.checkbox("Enable Gmail features (read/send)", key="gmail_enabled", value=st.session_state.gmail_enabled)

        demo_flag = "ON" if is_demo_mode() else "OFF"
        st.caption(f"Demo mode: **{demo_flag}** (no viewer OAuth)")

        if not is_demo_mode():
            # Local-only Desktop OAuth connect (for development)
            oauth_col1, oauth_col2 = st.columns([0.6, 0.4])
            with oauth_col1:
                client_path = st.text_input("Desktop OAuth client path", value=str(CLIENT_SECRET_PATH))
            with oauth_col2:
                if st.button("Connect to Gmail (local dev)"):
                    try:
                        new_path = pathlib.Path(client_path)
                        if new_path != CLIENT_SECRET_PATH:
                            globals()["CLIENT_SECRET_PATH"] = new_path
                        service = gmail_get_service()
                        prof = gmail_profile(service)
                        st.session_state.gmail_connected = True
                        st.session_state.gmail_profile = prof
                        st.toast(f"Connected as {prof.get('emailAddress','me')} ✅")
                        st.rerun()
                    except Exception as e:
                        st.session_state.gmail_connected = False
                        st.error(f"Gmail connection failed: {e}")
        else:
            # In demo mode, we assume pre-connected via secrets
            st.session_state.gmail_connected = True
            if not st.session_state.gmail_profile:
                st.session_state.gmail_profile = {"emailAddress": "(demo mailbox)"}

        if st.session_state.gmail_connected:
            pull_cols = st.columns([0.6, 0.4])
            with pull_cols[0]:
                st.session_state.gmail_pull_n = st.slider(
                    "Number of emails to pull",
                    min_value=1, max_value=50, step=1,
                    value=st.session_state.gmail_pull_n
                )
            with pull_cols[1]:
                if st.button(f"📥 Pull {st.session_state.gmail_pull_n} recent Gmail messages"):
                    try:
                        service = gmail_get_service()
                        ids = gmail_list_messages(service, max_results=st.session_state.gmail_pull_n)
                        rows: List[str] = []
                        for m in ids:
                            full = gmail_get_message(service, m["id"])
                            row = gmail_pretty_row(full)
                            rows.append(
                                "Subject: {sub}\nFrom: {frm}\nDate: {dt}\nBody: {snip}".format(
                                    sub=sanitize_text(row["subject"]),
                                    frm=sanitize_text(row["from"]),
                                    dt=sanitize_text(row["date"]),
                                    snip=sanitize_text(row["snippet"]),
                                )
                            )
                        st.session_state.triage_text = "\n---\n".join(rows)
                        st.toast(f"Pulled {len(rows)} from Gmail ✅")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gmail fetch failed: {e}")
            if not is_demo_mode():
                if st.button("Disconnect Gmail"):
                    try:
                        token_path = TOKEN_PATH
                        if token_path.exists():
                            token_path.unlink()
                        st.session_state.gmail_connected = False
                        st.session_state.gmail_profile = None
                        st.toast("Gmail disconnected")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to disconnect: {e}")
        else:
            st.caption("Tip: In demo mode, the app is already connected with a sandbox mailbox.")

    # --- Run triage (updates session_state.triage_items) ---
    if run_btn:
        with st.spinner("Thinking…"):
            try:
                sample = st.session_state.triage_text.strip()
                if st.session_state.mock_mode or not sample:
                    result = {
                        "items": [
                            {
                                "subject":"Your billing invoice",
                                "from":"accounts@example.com",
                                "date":"2025-10-03 14:05",
                                "priority":"medium",
                                "summary":"Invoice for September is attached. Due in 5 days.",
                                "next_step":"Forward to finance and set a reminder.",
                                "labels":["billing","finance"],
                                "score":0.87
                            },
                            {
                                "subject":"Team offsite agenda",
                                "from":"hr@example.com",
                                "date":"2025-10-03 12:40",
                                "priority":"low",
                                "summary":"Draft agenda attached. Feedback requested by EOD Monday.",
                                "next_step":"Reply with your agenda items.",
                                "labels":["hr","offsite"],
                                "score":0.74
                            }
                        ]
                    }
                else:
                    actual_model = resolve_model(st.session_state.provider, st.session_state.model)
                    result = ask_json(
                        prompt=sample,
                        provider=st.session_state.provider,
                        model=actual_model
                    )

                items = result.get("items", [])
                st.session_state.triage_items = items  # persist

                if st.session_state.save_logs:
                    st.session_state.logs.append({"event": "triage_result", "data": items})

                st.success("Triage complete. See results below.")
            except Exception as e:
                st.error(f"Error during triage: {e}")
                if "not_found" in str(e).lower() or "model" in str(e).lower():
                    st.info("Tip: For Anthropic, try IDs like `claude-3-5-sonnet-latest` or use the provided aliases.")
                if st.session_state.save_logs:
                    st.session_state.logs.append(
                        {"event": "triage_error", "data": str(e)}
                    )

    # --- Always render current triage results (so Reply works on rerun) ---
    items = st.session_state.get("triage_items", [])
    if items:
        st.write("")
        grid_l, grid_r = st.columns(2)
        archived = set(st.session_state.archived_ids)
        i_vis = 0
        for item in items:
            uid = make_uid(item)
            if uid not in st.session_state.reply_open:
                st.session_state.reply_open[uid] = False  # pre-init
            if uid in archived:
                continue
            with (grid_l if (i_vis % 2 == 0) else grid_r):
                message_card(item, key=uid)
            i_vis += 1
    else:
        st.caption("No triage results yet. Paste emails and click **Run Triage**.")

# =========================
# Compose
# =========================
with tab_compose:
    st.subheader("Compose Email")
    with st.form("compose_form", clear_on_submit=False):
        to = st.text_input("To")
        subject = st.text_input("Subject")
        body = st.text_area("Body", height=200, placeholder="Type your message…")
        col_a, col_b = st.columns([0.2, 0.8])
        with col_a:
            send = st.form_submit_button("Send")
        with col_b:
            draft = st.form_submit_button("Save Draft")

    if send:
        try:
            if is_demo_mode() and not can_send(to):
                st.error("Sending in demo is restricted. Set DEMO_SEND_DOMAIN to allow a specific domain.")
            else:
                service = gmail_get_service()
                gmail_send(service, to, subject, body)
                st.toast("Sent ✉️")
        except Exception as e:
            st.error(f"Gmail send failed: {e}")
        if st.session_state.save_logs:
            st.session_state.logs.append({"event": "compose_send", "data": {"to": to, "subject": subject}})
    elif draft:
        st.toast("Draft saved 💾 (local stub)")
        if st.session_state.save_logs:
            st.session_state.logs.append({"event": "compose_draft", "data": {"to": to, "subject": subject}})

# =========================
# Settings (LLM defaults & housekeeping)
# =========================
with tab_settings:
    st.subheader("Status & Behavior")

    has_openai = bool(os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY"))
    has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY"))
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**OpenAI Key:** " + ("✅ found" if has_openai else "❌ missing"))
    with col2:
        st.markdown("**Anthropic Key:** " + ("✅ found" if has_anthropic else "❌ missing"))

    default_model_val = st.selectbox(
        "Default Model",
        ["gpt-4o-mini", "gpt-4o", "o4-mini", "claude-3-5-sonnet", "claude-3-5-haiku"],
        index=["gpt-4o-mini","gpt-4o","o4-mini","claude-3-5-sonnet","claude-3-5-haiku"].index(st.session_state.model)
            if st.session_state.model in ["gpt-4o-mini","gpt-4o","o4-mini","claude-3-5-sonnet","claude-3-5-haiku"]
            else 0
    )
    if st.button("Apply"):
        st.session_state.model = default_model_val
        st.toast("Settings applied ✅")

    resolved = resolve_model(st.session_state.provider, st.session_state.model)
    st.caption(f"Resolved model id: **{resolved}**")

    st.divider()
    if st.button("Reset Archives"):
        st.session_state.archived_ids = []
        st.toast("All unarchived")

# =========================
# Logs
# =========================
with tab_logs:
    st.subheader("Recent Runs")
    if not st.session_state.logs:
        st.info("No logs yet. Run a triage, send, or reply to see entries.")
    else:
        if st.button("Clear Logs"):
            st.session_state.logs.clear()
            st.toast("Logs cleared")
        else:
            for i, entry in enumerate(reversed(st.session_state.logs)):
                label = entry.get("event", "event")
                with st.expander(f"{label} #{len(st.session_state.logs)-i}"):
                    st.code(json.dumps(entry, indent=2), language="json")
