import os
import requests
from dotenv import load_dotenv

load_dotenv()

def send_discord_alert(title: str, description: str, color: int = 0x3498db, fields: list = None):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("Warning: DISCORD_WEBHOOK_URL is not set.")
        return

    embed = {
        "title": title,
        "description": description,
        "color": color
    }
    
    if fields:
        embed["fields"] = fields

    payload = {
        "embeds": [embed]
    }

    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to send discord alert: {e}")
