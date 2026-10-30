#!/usr/bin/env python3
"""Однократная авторизация YouTube. Откроет браузер, войди в аккаунт канала и разреши доступ.
Нужен файл ~/VideoAutomation/yt_client_secret.json (OAuth-клиент типа «Приложение для ПК»)."""
import os
from google_auth_oauthlib.flow import InstalledAppFlow
BASE = os.path.expanduser("~/VideoAutomation")
SC = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]
flow = InstalledAppFlow.from_client_secrets_file(f"{BASE}/yt_client_secret.json", SC)
creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
open(f"{BASE}/yt_token.json", "w").write(creds.to_json()); os.chmod(f"{BASE}/yt_token.json", 0o600)
print("✓ yt_token.json сохранён — YouTube подключён")
