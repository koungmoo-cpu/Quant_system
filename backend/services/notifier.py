import os
import requests
import json
from datetime import datetime
import pytz

def get_discord_webhook_url():
    return os.environ.get('DISCORD_WEBHOOK_URL')

def send_discord_alert(title: str, description: str, color: int = 0x3498db, fields: list = None):
    webhook_url = get_discord_webhook_url()
    if not webhook_url:
        print('DISCORD_WEBHOOK_URL is not set. Skipping Discord alert.')
        return False
        
    kst = pytz.timezone('Asia/Seoul')
    timestamp = datetime.now(kst).isoformat()
    
    embed = {
        'title': title,
        'description': description,
        'color': color,
        'timestamp': timestamp,
        'footer': {
            'text': 'AI Stock Trading Quant System'
        }
    }
    
    if fields:
        embed['fields'] = fields
        
    payload = {
        'embeds': [embed]
    }
    
    try:
        response = requests.post(
            webhook_url, 
            data=json.dumps(payload), 
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f'Failed to send Discord alert: {e}')
        return False
