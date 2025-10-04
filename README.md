# 📨 AI Email Assistant  
**LLM-powered Gmail triage and reply automation using OpenAI / Anthropic models + Streamlit**

[![Streamlit App](https://img.shields.io/badge/🚀_Launch_on-Streamlit_Cloud-FF4B4B?style=for-the-badge&logo=streamlit)](https://email-assistant-anmitra.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

## ✨ Overview
**AI Email Assistant** is a production-grade demo showcasing how **Generative AI** can automate **email triage and response workflows**.  
It connects to Gmail via OAuth or a sandbox “demo mailbox” and leverages **LLMs (OpenAI / Anthropic)** to:
- Read and summarize emails  
- Prioritize them by urgency (high / medium / low)  
- Suggest next actions  
- Compose replies automatically  

This project highlights **end-to-end AI integration** — from OAuth authentication and Gmail API handling, to structured LLM outputs (JSON) and a polished Streamlit frontend.

---

## 🧠 Key Features

| Category | Description |
|-----------|-------------|
| 🧩 **LLM Integration** | Works with **OpenAI GPT-4o** and **Anthropic Claude 3.5 Sonnet** via unified JSON schema |
| 📬 **Gmail API** | OAuth2 authentication + read/send access, with both local & demo modes |
| 🪄 **Smart Triage** | LLM classifies priority, extracts summary, and recommends next actions |
| ✍️ **Reply Generator** | Draft replies directly within Streamlit UI |
| 🧱 **Polished UI** | Modern tabbed layout, clean cards, badges, dark/light theme friendly |
| 🧰 **Safe State Handling** | Uses session buffer pattern to avoid widget state mutation errors |
| 🕐 **Timeout-Resilient Gmail** | Uses `AuthorizedHttp(httplib2.Http(timeout=10))` for reliable API calls |
| 🔐 **Environment/Secrets Ready** | Works with `.env` (local) and `secrets.toml` (Streamlit Cloud) |

---

## 🧭 App Structure

```plaintext
email-assistant/
├── app/
│   └── streamlit_app.py        # Main Streamlit UI + Gmail/LLM logic
├── .env                        # Local environment variables
├── .streamlit/
│   └── config.toml             # Optional UI theme overrides
├── .oauth/
│   ├── client_secret.json      # Local OAuth credentials (dev only)
│   └── token.json              # Auto-generated Gmail token
├── requirements.txt            # Dependencies
└── README.md                   # This file

## Local Setup
1. Clone & Setup
git clone https://github.com/anmitra/Email-Assistant.git
cd Email-Assistant
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

