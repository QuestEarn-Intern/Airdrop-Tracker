import os
import re
import json
import requests
import feedparser
from datetime import datetime

# --- CONFIGURATION & SECRETS ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# Added User-Agent headers to prevent any connection drops
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Unrestricted syndicated community feed for drops and campaigns
RSS_SOURCE = {"name": "Web3 Drop Aggregator", "url": "https://syndication.twitter.com/srv/timeline-profile/screen-name/airdrop_io"}

def fetch_feed_with_ua(url):
    """Fetches feed data with a standard browser User-Agent."""
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return feedparser.parse(response.content)

def get_all_updates():
    extracted_items = []
    try:
        feed = fetch_feed_with_ua(RSS_SOURCE["url"])
        # Process the 5 most recent updates
        for entry in feed.entries[:5]:
            item_id = entry.id.split("/")[-1] if hasattr(entry, 'id') else str(hash(entry.title))
            
            content_text = ""
            if hasattr(entry, 'summary'):
                content_text = entry.summary
            elif hasattr(entry, 'title'):
                content_text = entry.title
                
            extracted_items.append({
                "id": f"drop-{item_id}",
                "text": content_text,
                "link": entry.link
            })
    except Exception as e:
        print(f"Failed parsing syndication feed: {str(e)}")
        
    return extracted_items

def save_to_supabase(item_id, content, url):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=ignore"
    }
    payload = {
        "tweet_id": item_id, 
        "project_name": "Unrestricted Drop Feed",
        "content": content[:250], 
        "event_url": url,
        "category": "Airdrop / Retroactive Update"
    }
    base_url = SUPABASE_URL if SUPABASE_URL else ""
    response = requests.post(f"{base_url.rstrip('/')}/rest/v1/airdrop_gems", json=payload, headers=headers)
    return response.status_code in [201, 409]

def send_discord_alert(content, url):
    """Sends a rich Discord embed message via Webhook"""
    payload = {
        "content": "🚨 **New Airdrop / Retroactive Update Detected!** 🚨",
        "embeds": [
            {
                "title": "🪂 Direct Web3 Drop Update",
                "description": content[:200],
                "color": 16711680, # Red embed color for Drop Alerts
                "fields": [
                    {"name": "Direct Link", "value": f"[View Campaign Guide]({url})", "inline": True}
                ],
                "footer": {
                    "text": "⚠️ Always DYOR & verify contracts before connecting wallets!"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    }
    headers = {"Content-Type": "application/json"}
    requests.post(DISCORD_WEBHOOK_URL, json=payload, headers=headers)

def main():
    print("Ingesting unrestricted Drop Syndication feed...")
    
    items = get_all_updates()
    print(f"Extracted {len(items)} updates. Pushing entries directly to database & Discord...")
    
    alert_counter = 0
    for item in items:
        success = save_to_supabase(
            item["id"], 
            item["text"], 
            item["link"]
        )
        
        if success:
            send_discord_alert(
                item["text"], 
                item["link"]
            )
            alert_counter += 1
            print(f"Alert successfully sent for: {item['id']}")
                
    print(f"Execution complete. Successfully processed and alerted {alert_counter} items.")

if __name__ == "__main__":
    main()
