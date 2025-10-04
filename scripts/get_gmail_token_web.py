# scripts/get_gmail_token_web.py
# Generate a token.json with a refresh_token for a demo Gmail account (free Gmail OK).
# Uses a Web OAuth client (downloaded from Google Cloud Console) and the local loopback flow.

import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes: read mail + send mail (adjust if you only need readonly)
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

# Location of the Web OAuth client JSON you downloaded from GCP
WEB_CLIENT_PATH = Path(".oauth/web_client.json")
OUT_TOKEN_PATH = Path(".oauth/token.json")

def main():
    if not WEB_CLIENT_PATH.exists():
        raise SystemExit(
            f"Missing {WEB_CLIENT_PATH}. Download your Web OAuth client JSON from "
            "Google Cloud Console → APIs & Services → Credentials, and save it here."
        )

    # NOTE: run_local_server uses the loopback IP + http on localhost and handles the redirect safely.
    # Make sure http://localhost:8080/ is added to 'Authorized redirect URIs' in your Web client.
    flow = InstalledAppFlow.from_client_secrets_file(str(WEB_CLIENT_PATH), SCOPES)
    creds = flow.run_local_server(port=8080, prompt="consent")  # opens browser; log in as the DEMO Gmail

    # Write a token.json compatible with your Streamlit app (contains refresh_token)
    token = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": flow.client_config["client_id"],
        "client_secret": flow.client_config["client_secret"],
        "scopes": list(creds.scopes),
    }
    OUT_TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_TOKEN_PATH.write_text(json.dumps(token, indent=2), encoding="utf-8")
    print(f"\n✅ Saved refreshable token to {OUT_TOKEN_PATH}\n"
          "   Next: copy its JSON into your hosting secrets as GMAIL_TOKEN_JSON.")

if __name__ == "__main__":
    main()
