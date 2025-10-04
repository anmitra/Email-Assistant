# app/streamlit_app.py
from __future__ import annotations

import os
import json
import base64
import hashlib
import pathlib
import re
import html
from datetime import datetime
from typing import Any, Dict, List, Optional
from email.mime.text import MIMEText

import streamlit as st
from dotenv import load_dotenv

# =========================
# Page / Theme
# =========================
load_dotenv()

st.set_page_config(
    page_title="AI Email Assistant · LLM + Gmail",
    page_icon="📧",
    layout="wide",
)

# Minimal CSS (kept inline to avoid external fetch issues)
st.markdown("""
<style>
html, body, [class*="css"]  { font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }
:root { --card-bg: rgba(255,255,255,0.04); --card-border: rgba(0,0,0,0.08);
        --good: #22C55E; --warn: #F59E0B; --bad: #EF4444; --muted: #6b7280; }
.main-title { font-size: 2.3rem; font-weight: 800; margin-bottom: .15rem; white-space: normal !important; }
.sub-title { font-size: 1rem; color: var(--muted); margin-bottom: 1.0rem; }
.card { border: 1px solid var(--card-border); background: #fff; border-radius: 16px;
        padding: 16px 18px; box-shadow: 0 8px 24px rgba(0,0,0,0.06); }
.card-title { font-weight: 700; margin-bottom: 6px; }
.card-meta { color: var(--muted); font-size: 0.85rem; }
.badge { display:inline-flex; align-items:center; gap:6px; font-size: 0.8rem; font-weight: 700;
         padding: 4px 10px; border-radius: 999px; line-height: 1;
         border: 1px solid var(--card-border); background: #f8fafc; }
.badge.good { background:#dcfce7; color:#166534; border-color: rgba(34,197,94,.35); }
.badge.warn { background:#fef9c3; color:#92400e; border-color: rgba(245,158,11,.35); }
.badge.bad  { background:#fee2e2; color:#991b1b; border-color: rgba(239,68,68,.35); }
.block-container { padding-top: 1.2rem; }
.footer { text-align: center; font-size: 0.85rem; color: var(--muted);
          margin-top: 2rem; padding-top: 1rem; border-top: 1px solid rgba(0,0,0,.08);}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📨 AI Email Assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">LLM-powered inbox triage & replies with OpenAI / Anthropic + Gmail API</div>',
    unsafe_allow_html=True,
)

# =========================
# Safe Secrets Helper
# =========================
def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Prefer environment; fall back to st.secrets if available; else default."""
    val = os.getenv(key)
    if val is not None:
        return val
    try:
        return st.secrets.get(key, default)
    except FileNotFoundError:
        return default

# =========================
# Session Defaults
# =========================
def ensure_state_defaults():
    st.session_state.setdefault("logs", [])
    st.session_state.setdefault("mock_mode", False)
    st.session_state.setdefault("save_logs", True)
    st.session_state.setdefault("provider", "OpenAI")
    st.session_state.setdefault("model", "gpt-4o-mini")
    st.session_state.setdefault("connected", True)
    st.session_state.setdefault("archived_ids", [])
    st.session_state.setdefault("reply_open", {})
    st.session_state.setdefault("last_provider", "OpenAI")
    st.session_state.setdefault("triage_text", "")
    st.session_state.setdefault("triage_items", [])
    # Gmail
    st.session_state.setdefault("gmail_enabled", True)
    st.session_state.setdefault("gmail_connected", False)
    st.session_state.setdefault("gmail_profile", None)
    st.session_state.setdefault("gmail_pull_n", 5)  # default pull = 5
ensure_state_defaults()

# =========================
# Utils (sanitize)
# =========================
CONTROL_CHARS_RE = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]')
def sanitize_text(s: str | None) -> str:
    if s is None:
        return ""
    if not isinstance(s, str):
        s = str(s)
    s = s.encode("utf-8", "ignore").decode("utf-8", "ignore")
    s = CONTROL_CHARS_RE.sub("", s)
    return s

def h(s: str | None) -> str:
    return html.escape(sanitize_text(s or ""))

def make_uid(item: Dict[str, Any]) -> str:
    s = f"{item.get('subject','')}-{item.get('from','')}-{item.get('date','')}"
    return hashlib.sha1(s.encode()).hexdigest()[:12]

def status_badge(level: str) -> str:
    m = (level or "").lower()
    cls = "good" if m in ("ok","info","success","low") else "warn" if m in ("warn","medium") else "bad"
    text = "Low" if cls=="good" else "Medium" if cls=="warn" else "High"
    return f'<span class="badge {cls}">● {text} priority</span>'

# =========================
# Models / Providers
# =========================
MODEL_ALIASES = {
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
def default_model_for(provider: str) -> str:
    return "claude-3-5-sonnet" if provider == "Anthropic" else "gpt-4o-mini"
def resolve_model(provider: str, name: str) -> str:
    return MODEL_ALIASES.get(provider, {}).get(name, name)

# =========================
# LLM Bridges
# =========================
TRIAGE_SCHEMA = {
    "type":"object","properties":{
        "items":{"type":"array","items":{
            "type":"object","properties":{
                "subject":{"type":"string"},
                "from":{"type":"string"},
                "date":{"type":"string"},
                "priority":{"type":"string","enum":["low","medium","high"]},
                "summary":{"type":"string"},
                "next_step":{"type":"string"},
                "labels":{"type":"array","items":{"type":"string"}},
                "score":{"type":"number"},
            },
            "required":["subject","from","summary","priority"]
        }}
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
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY") or get_secret("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role":"system","content": SYSTEM_TRIAGE},
            {"role":"user","content": f"Schema:\n{json.dumps(TRIAGE_SCHEMA)}\n\nEmails:\n{prompt}"}
        ],
        response_format={"type":"json_object"},
        temperature=0.2,
    )
    return json.loads(resp.choices[0].message.content)

def ask_json_anthropic(prompt: str, model: str) -> Dict[str, Any]:
    import anthropic
    api_key = os.getenv("ANTHROPIC_API_KEY") or get_secret("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Missing ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model, max_tokens=2000, temperature=0.2,
        system=SYSTEM_TRIAGE + " Output JSON only.",
        messages=[{"role":"user","content": f"Schema:\n{json.dumps(TRIAGE_SCHEMA)}\n\nEmails:\n{prompt}"}]
    )
    text = "".join(getattr(b,"text","") for b in msg.content if getattr(b,"type","")=="text").strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text)

def ask_json(prompt: str, provider: str, model: str) -> Dict[str, Any]:
    return ask_json_openai(prompt, model) if provider=="OpenAI" else ask_json_anthropic(prompt, model)

# =========================
# Gmail Integration
# =========================
OAUTH_DIR = pathlib.Path(".oauth"); OAUTH_DIR.mkdir(exist_ok=True)
CLIENT_SECRET_PATH = OAUTH_DIR / "client_secret.json"  # Desktop OAuth for local dev
TOKEN_PATH = OAUTH_DIR / "token.json"
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

def is_demo_mode() -> bool:
    return (get_secret("GMAIL_DEMO_ENABLED","") or "").lower() in ("1","true","yes")

def can_send(addr: str) -> bool:
    dom = (get_secret("DEMO_SEND_DOMAIN") or "").lower().strip()
    return (not dom) or addr.lower().endswith(f"@{dom}")

def gmail_get_service():
    """
    Returns authenticated Gmail service.
      1) Demo mode (secrets): pre-connected refresh token (no viewer OAuth)
      2) Local fallback: Desktop OAuth (.oauth/client_secret.json)
    Uses a 10s timeout via build_http(timeout=10) to avoid infinite spinners.
    """
    from googleapiclient.discovery import build
    from googleapiclient.http import build_http
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    http = build_http(timeout=10)

    # --- Demo mode via secrets (pre-connected mailbox) ---
    if is_demo_mode():
        token_json = get_secret("GMAIL_TOKEN_JSON")
        if not token_json:
            raise RuntimeError("GMAIL_DEMO_ENABLED is true but GMAIL_TOKEN_JSON is missing.")
        token_info = json.loads(token_json)

        if ("client_id" not in token_info or "client_secret" not in token_info or "token_uri" not in token_info):
            web_json = get_secret("GOOGLE_OAUTH_WEB_CLIENT_JSON")
            if not web_json:
                raise RuntimeError("Token missing client fields; add GOOGLE_OAUTH_WEB_CLIENT_JSON.")
            web_client = json.loads(web_json).get("web", {})
            token_info.setdefault("client_id", web_client.get("client_id"))
            token_info.setdefault("client_secret", web_client.get("client_secret"))
            token_info.setdefault("token_uri", web_client.get("token_uri", "https://oauth2.googleapis.com/token"))

        creds = Credentials.from_authorized_user_info(token_info, scopes=GMAIL_SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        if not creds or not creds.valid:
            raise RuntimeError("Demo Gmail credentials invalid; regenerate token.json for the demo mailbox.")

        service = build("gmail","v1", credentials=creds, http=http, cache_discovery=False)
        return service

    # --- Local Desktop OAuth fallback ---
    creds = None
    if TOKEN_PATH.exists():
        from google.oauth2.credentials import Credentials as GCreds
        from google.auth.transport.requests import Request as GRequest
        creds = GCreds.from_authorized_user_file(str(TOKEN_PATH), GMAIL_SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GRequest()); TOKEN_PATH.write_text(creds.to_json())
    if not creds or not creds.valid:
        if not CLIENT_SECRET_PATH.exists():
            raise RuntimeError("Missing Desktop OAuth client at ./.oauth/client_secret.json")
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_PATH), GMAIL_SCOPES)
        creds = flow.run_local_server(port=0); TOKEN_PATH.write_text(creds.to_json())

    service = build("gmail","v1", credentials=creds, http=http, cache_discovery=False)
    return service

def gmail_profile(service) -> Dict[str,Any]:
    return service.users().getProfile(userId="me").execute(num_retries=1)

def gmail_list_messages(service, max_results=5) -> List[Dict[str,Any]]:
    res = service.users().messages().list(
        userId="me", labelIds=["INBOX"], maxResults=max_results
    ).execute(num_retries=1)
    return res.get("messages", [])

def gmail_get_message(service, msg_id: str) -> Dict[str,Any]:
    return service.users().messages().get(userId="me", id=msg_id, format="full").execute(num_retries=1)

def gmail_send(service, to: str, subject: str, body: str):
    mime = MIMEText(body, "plain", "utf-8")
    mime["to"] = to
    mime["subject"] = subject
    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
    return service.users().messages().send(userId="me", body={"raw": raw}).execute(num_retries=1)

def gmail_pretty_row(msg: Dict[str,Any]) -> Dict[str,str]:
    headers = {h["name"].lower(): sanitize_text(h["value"]) for h in msg.get("payload", {}).get("headers", [])}
    return {
        "from": sanitize_text(headers.get("from","")),
        "subject": sanitize_text(headers.get("subject","")),
        "date": sanitize_text(headers.get("date","")),
        "snippet": sanitize_text(msg.get("snippet","")),
    }

# =========================
# Sidebar Badges
# =========================
st.sidebar.markdown("### 🧭 App Info")
has_openai = bool(os.getenv("OPENAI_API_KEY") or get_secret("OPENAI_API_KEY"))
has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY") or get_secret("ANTHROPIC_API_KEY"))
if has_openai or has_anthropic:
    st.sidebar.success("✅ LLM Connected")
else:
    st.sidebar.error("❌ LLM Disconnected (use Mock Mode)")
if is_demo_mode():
    st.sidebar.success("✅ Demo mailbox pre-connected")
else:
    st.sidebar.info("ℹ️ Local Desktop OAuth available in Inbox tab")

st.sidebar.caption("Built with Streamlit · OpenAI · Anthropic · Gmail API")

# =========================
# Tabs
# =========================
tab_inbox, tab_compose, tab_settings, tab_logs = st.tabs(
    ["📥 Inbox Triage", "✍️ Compose", "⚙️ Settings", "🧾 Logs"]
)

# =========================
# Components
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
    head_l, head_r = st.columns([0.78, 0.22])
    with head_l:
        st.markdown(f'<div class="card-title">✉️ {h(subject)}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="card-meta">From {h(sender)} • {h(date)}</div>', unsafe_allow_html=True)
    with head_r:
        st.markdown(status_badge(pr), unsafe_allow_html=True)

    if summary: st.info(summary)
    if next_step:
        st.caption("Next step:")
        st.write(f"• {next_step}")
    if labels:
        st.caption("Labels:")
        safe_labels = " ".join([f'<span class="badge">{h(l)}</span>' for l in labels])
        st.markdown(safe_labels, unsafe_allow_html=True)
    if score is not None:
        st.caption(f"Relevance score: {score:.2f}")

    col_a, col_b = st.columns([0.5, 0.5])
    with col_a:
        if st.button("Archive", key=f"archive_btn_{uid}"):
            archived = set(st.session_state.archived_ids)
            archived.add(uid)
            st.session_state.archived_ids = list(archived)
            st.toast("Archived ✅")
    with col_b:
        if st.button("Reply", key=f"reply_btn_{uid}"):
            st.session_state.reply_open[uid] = not st.session_state.reply_open.get(uid, False)

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
                    st.error("Sending in demo is restricted. Set DEMO_SEND_DOMAIN to allow a domain.")
                else:
                    service = gmail_get_service()
                    gmail_send(service, r_to, r_subject, r_body)
                    st.toast("Reply sent ✉️")
            except Exception as e:
                st.error(f"Gmail send failed: {e}")
            st.session_state.reply_open[uid] = False
            if st.session_state.save_logs:
                st.session_state.logs.append({"event":"reply_send","data":{"to":r_to,"subject":r_subject,"len":len(r_body)}})

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# Inbox Triage Tab
# =========================
with tab_inbox:
    st.subheader("Smart Inbox Overview")
    st.caption("Pull, triage, and reply to recent messages intelligently.")

    left, right = st.columns([0.46, 0.54])
    with left:
        st.selectbox("Provider", ["OpenAI", "Anthropic"], index=0, key="provider")
        if st.session_state.last_provider != st.session_state.provider:
            st.session_state.model = default_model_for(st.session_state.provider)
            st.session_state.last_provider = st.session_state.provider

        st.text_input("Model", value=st.session_state.model, key="model")
        st.caption(f"Resolved model id: **{resolve_model(st.session_state.provider, st.session_state.model)}**")

        st.toggle("Mock Mode (no API calls)", key="mock_mode", value=st.session_state.mock_mode)
        st.toggle("Save raw responses to Logs", key="save_logs", value=st.session_state.save_logs)

        st.caption("Paste raw emails (subject/from/date/body). Separate with ---")
        st.text_area(
            "Emails to triage",
            height=220,
            key="triage_text",
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
        st.caption(f"Demo mode: **{'ON' if is_demo_mode() else 'OFF'}**")

        if not is_demo_mode():
            # Local Desktop OAuth connect (dev)
            c1, c2 = st.columns([0.6, 0.4])
            with c1:
                client_path = st.text_input("Desktop OAuth client path", value=str(CLIENT_SECRET_PATH))
            with c2:
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
            # Pre-connected via secrets
            st.session_state.gmail_connected = True
            if not st.session_state.gmail_profile:
                st.session_state.gmail_profile = {"emailAddress": "(demo mailbox)"}
            st.success("Demo mailbox connected")

        # Test and Pull controls
        if st.session_state.gmail_connected:
            if st.button("🔌 Test Gmail Connection"):
                try:
                    prof = gmail_profile(gmail_get_service())
                    st.success(f"Connected as {prof.get('emailAddress','?')}")
                except Exception as e:
                    st.error(f"Connection failed: {e}")

            pc1, pc2 = st.columns([0.6, 0.4])
            with pc1:
                st.slider("Number of emails to pull", 1, 50, key="gmail_pull_n")
            with pc2:
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
                        if TOKEN_PATH.exists():
                            TOKEN_PATH.unlink()
                        st.session_state.gmail_connected = False
                        st.session_state.gmail_profile = None
                        st.toast("Gmail disconnected")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to disconnect: {e}")
        else:
            st.caption("Tip: In demo mode, the app is already connected with a sandbox mailbox.")

    # Run triage
    if run_btn:
        with st.spinner("Thinking…"):
            try:
                sample = st.session_state.triage_text.strip()
                if st.session_state.mock_mode or not sample:
                    result = {"items":[
                        {"subject":"Your billing invoice","from":"accounts@example.com","date":"2025-10-03 14:05",
                         "priority":"medium","summary":"Invoice for September is attached. Due in 5 days.",
                         "next_step":"Forward to finance and set a reminder.","labels":["billing","finance"],"score":0.87},
                        {"subject":"Team offsite agenda","from":"hr@example.com","date":"2025-10-03 12:40",
                         "priority":"low","summary":"Draft agenda attached. Feedback requested by EOD Monday.",
                         "next_step":"Reply with your agenda items.","labels":["hr","offsite"],"score":0.74}
                    ]}
                else:
                    actual_model = resolve_model(st.session_state.provider, st.session_state.model)
                    result = ask_json(sample, st.session_state.provider, actual_model)

                items = result.get("items", [])
                st.session_state.triage_items = items
                if st.session_state.save_logs:
                    st.session_state.logs.append({"event":"triage_result","data":items})
                st.success("Triage complete. See results below.")
            except Exception as e:
                st.error(f"Error during triage: {e}")
                if "not_found" in str(e).lower() or "model" in str(e).lower():
                    st.info("Tip: For Anthropic, try `claude-3-5-sonnet-latest` (alias supported).")
                if st.session_state.save_logs:
                    st.session_state.logs.append({"event":"triage_error","data":str(e)})

    # Render triage results persistently
    items = st.session_state.get("triage_items", [])
    if items:
        st.write("")
        grid_l, grid_r = st.columns(2)
        archived = set(st.session_state.archived_ids)
        i_vis = 0
        for item in items:
            uid = make_uid(item)
            if uid not in st.session_state.reply_open:
                st.session_state.reply_open[uid] = False
            if uid in archived:
                continue
            with (grid_l if (i_vis % 2 == 0) else grid_r):
                message_card(item, key=uid)
            i_vis += 1
    else:
        st.caption("No triage results yet. Paste emails or pull from Gmail, then click **Run Triage**.")

# =========================
# Compose Tab
# =========================
with tab_compose:
    st.subheader("Compose Email")
    with st.form("compose_form", clear_on_submit=False):
        to = st.text_input("To")
        subject = st.text_input("Subject")
        body = st.text_area("Body", height=200, placeholder="Type your message…")
        c1, c2 = st.columns([0.25, 0.75])
        with c1:
            send = st.form_submit_button("Send")
        with c2:
            draft = st.form_submit_button("Save Draft")

    if send:
        try:
            if is_demo_mode() and not can_send(to):
                st.error("Sending in demo is restricted. Set DEMO_SEND_DOMAIN to allow a domain.")
            else:
                service = gmail_get_service()
                gmail_send(service, to, subject, body)
                st.toast("Sent ✉️")
        except Exception as e:
            st.error(f"Gmail send failed: {e}")
        if st.session_state.save_logs:
            st.session_state.logs.append({"event":"compose_send","data":{"to":to,"subject":subject}})
    elif draft:
        st.toast("Draft saved (local stub) 💾")
        if st.session_state.save_logs:
            st.session_state.logs.append({"event":"compose_draft","data":{"to":to,"subject":subject}})

# =========================
# Settings Tab
# =========================
with tab_settings:
    st.subheader("Status & Defaults")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**OpenAI Key:** " + ("✅ found" if has_openai else "❌ missing"))
    with col2:
        st.markdown("**Anthropic Key:** " + ("✅ found" if has_anthropic else "❌ missing"))

    choose = ["gpt-4o-mini", "gpt-4o", "o4-mini", "claude-3-5-sonnet", "claude-3-5-haiku"]
    idx = choose.index(st.session_state.model) if st.session_state.model in choose else 0
    new_default = st.selectbox("Default Model", choose, index=idx)
    if st.button("Apply"):
        st.session_state.model = new_default
        st.toast("Settings applied ✅")

    st.caption(f"Resolved id now: **{resolve_model(st.session_state.provider, st.session_state.model)}**")

    st.divider()
    if st.button("Reset Archives"):
        st.session_state.archived_ids = []
        st.toast("All unarchived")

# =========================
# Logs Tab
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
                label = entry.get("event","event")
                with st.expander(f"{label} #{len(st.session_state.logs)-i}"):
                    st.code(json.dumps(entry, indent=2), language="json")

# =========================
# Footer
# =========================
st.markdown(
    f"""
    <div class="footer">
      © {datetime.now().year} • AI Email Assistant · Built by <b>Anurag Mitra</b><br/>
      Powered by OpenAI / Anthropic · Gmail API · Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)
