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

# Expanded Rule-Based Filter Keywords
TARGET_KEYWORDS = ["airdrop", "quest", "earn", "fcfs", "snapshot", "claim", "retroactive", "token", "retrodrop"]

# List of multiple reliable RSS endpoints covering Drop Hunting & General Crypto Alpha
RSS_FEEDS = [
    {"name": "Airdrop Alert", "url": "https://airdropalert.com/feed/rssfeed"},
    {"name": "CoinTelegraph", "url": "https://cointelegraph.com/rss"},
    {"name": "CryptoRank News", "url": "https://cryptorank.io/news/tag/airdrop/rss"}, 
    {"name": "CryptoNews", "url": "https://cryptonews.com/news/feed"}
]

def fetch_all_feeds():
    """
    Pulls real-time tracking updates by iterating over multiple RSS feeds.
    """
    extracted_items = []
    
    for source in RSS_FEEDS:
        try:
            feed = feedparser.parse(source["url"])
            # Pull the 5 most recent items from each platform
            for entry in feed.entries[:5]:
                item_id = entry.id.split("/")[-1] if hasattr(entry, 'id') else str(hash(entry.title))
                
                content_text = ""
                if hasattr(entry, 'summary'):
                    content_text = entry.summary
                elif hasattr(entry, 'title'):
                    content_text = entry.title
                    
                extracted_items.append({
                    "id": f"{source['name'].lower().replace(' ','-')}-{item_id}",
                    "source_platform": source['name'],
                    "text": content_text,
                    "link": entry.link
                })
        except Exception as e:
            print(f"Failed to parse feed for {source['name']}: {str(e)}")
            
    return extracted_items

def filter_content_keywords(text):
    """Checks if the text contains any of the required keywords."""
    text_lower = text.lower()
    
    if not any(word in text_lower for word in TARGET_KEYWORDS):
        return False, None

    # Categorize based on matched intent
    category = "Multi-Source Alpha 💎"
    if "airdrop" in text_lower: 
        category = "🪂 Confirmed/Potential Airdrop"
    elif "quest" in text_lower or "earn" in text_lower: 
        category = "⚔️ Active Quest / Campaign"
    elif "snapshot" in text_lower or "claim" in text_lower:
        category = "📸 Snapshot / Token Claim"
    elif "fcfs" in text_lower:
        category = "🏃 FCFS Allocation"
    
    return True, category

def save_to_supabase(item_id, source_platform, content, url, category):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=ignore"
    }
    payload = {
        "tweet_id": item_id, 
        "project_name": f"Tracker: {source_platform}",
        "content": content[:250], 
        "event_url": url,
        "category": category
    }
    response = requests.post(f"{SUPABASE_URL}/rest/v1/airdrop_gems", json=payload, headers=headers)
    return response.status_code in [201, 409]

def send_discord_alert(source_platform, content, url, category):
    """Sends a rich Discord embed message via Webhook"""
    payload = {
        "content": "🚨 **New Airdrop Gem / Alpha Opportunity Detected!** 🚨",
        "embeds": [
            {
                "title": f"✨ Category: {category}",
                "description": content[:200],
                "color": 16753920, 
                "fields": [
                    {"name": "Source Platform", "value": source_platform, "inline": True},
                    {"name": "Direct Link", "value": f"[View Update]({url})", "inline": True}
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
    print("Scanning aggregated multi-source drop hunting feeds...")
    
    items = fetch_all_feeds()
    print(f"Extracted {len(items)} total raw updates from aggregators. Applying rule filters...")
    
    alert_counter = 0
    for item in items:
        is_match, category = filter_content_keywords(item["text"])
        
        if is_match:
            success = save_to_supabase(
                item["id"], 
                item["source_platform"],
                item["text"], 
                item["link"],
                category
            )
            
            if success:
                send_discord_alert(
                    item["source_platform"],
                    item["text"], 
                    item["link"],
                    category
                )
                alert_counter += 1
                print(f"Alert sent for match: {item['id']}")
                
    print(f"Execution complete. Successfully processed and alerted {alert_counter} drops.")

if __name__ == "__main__":
    main()
