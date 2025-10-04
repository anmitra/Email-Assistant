<div align="center" id="top">

# 📨 AI Email Assistant  
**Transforming Inbox Chaos into Actionable Productivity**

[![Streamlit App](https://img.shields.io/badge/🚀_Launch_on-Streamlit_Cloud-FF4B4B?style=for-the-badge&logo=streamlit)](https://email-assistant-anmitra.streamlit.app)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
![Anthropic](https://img.shields.io/badge/Anthropic-191919?style=for-the-badge&logo=Anthropic&logoColor=white)
![Gmail API](https://img.shields.io/badge/Gmail_API-EA4335?style=for-the-badge&logo=gmail&logoColor=white)

</div>

---

## ✨ Overview

**AI Email Assistant** is an intelligent Gmail-connected Streamlit app powered by **OpenAI GPT-4o** and **Anthropic Claude 3.5 Sonnet** that helps you:
- 🧠 **Summarize, prioritize, and tag** incoming emails  
- ✍️ **Draft professional replies** automatically  
- 📬 **Integrate securely with Gmail** via OAuth 2.0  
- 🎨 Use a sleek, responsive **Streamlit dashboard**

This project demonstrates **end-to-end Generative AI engineering** — from retrieval (Gmail API) and reasoning (LLMs) to production-grade UI and secure deployment.

---

## 🧠 Features

| Category | Description |
|-----------|-------------|
| 📬 **Gmail Integration** | OAuth2 read/send access — list, preview, and reply to real emails |
| 🧩 **AI-Powered Triage** | Summaries, priority (Low / Medium / High), next actions, and tags |
| ✍️ **Reply Composer** | Drafts contextual replies with one click |
| 🎨 **Modern UI** | Tabs, cards, badges, and keyboard-friendly design |
| 🔐 **Demo Mode** | Pre-connected mailbox for recruiter showcase |
| ⚙️ **Reliable Backend** | Timeout-resilient Gmail API with safe reruns |
| 🧰 **Cross-Model Support** | Seamless switch between GPT-4o and Claude 3.5 Sonnet |

---

## 🏗️ Architecture

```plaintext
📂 email-assistant/
├── app/
│   └── streamlit_app.py        # Streamlit UI + business logic
├── assistant/
│   ├── llm.py                  # LLM orchestration
│   ├── prompts.py              # Email triage system prompts
│   ├── pipeline.py             # Email triage + reply flow
│   ├── schema.py               # JSON structure enforcement
│   └── providers/              # Gmail / Demo backends
├── scripts/
│   └── get_gmail_token_web.py  # OAuth helper (for local testing)
├── .streamlit/config.toml      # Theming configuration
├── requirements.txt
└── README.md
