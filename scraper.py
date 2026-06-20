import os
import re
import json
import requests
from datetime import datetime

# --- CONFIGURATION & SECRETS ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# List of trusted verified projects you want to track
TRACKED_PROJECTS = ["arbitrum", "optimism", "solana", "starknet", "layerzero_labs"]

# Simple Rule-Based Filter
AIRDROP_KEYWORDS = ["airdrop", "snapshot", "claim", "retroactive", "token drop"]

def fetch_crypto_twitter_mock():
    """
    Mock fetch function (Replace with actual RSS/Scraping logic targeting verified project timelines)
    """
    mock_fetched_tweets = [
        {
            "id": "178239482301",
            "username": "arbitrum",
            "text": "Season 3 Retroactive drop is live! Claim your tokens here: arbitrator-link.com/claim",
            "link": "https://twitter.com/arbitrum/status/178239482301"
        },
        {
            "id": "178239482302",
            "username": "optimism",
            "text": "Gm anon, go vote in our snapshot proposal today.",
            "link": "https://twitter.com/optimism/status/178239482302"
        }
    ]
    return mock_fetched_tweets

def filter_and_verify_tweet(text):
    """Applies Regex rules to verify if it's an actual airdrop gem."""
    text_lower = text.lower()
    
    if not any(word in text_lower for word in AIRDROP_KEYWORDS):
        return False, None

    category = "General Event"
    if "snapshot" in text_lower: category = "Snapshot 📸"
    elif "claim" in text_lower: category = "Token Claim"
    
    return True, category

def save_to_supabase(tweet_id, project, content, url, category):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=ignore"
    }
    payload = {
        "tweet_id": tweet_id,
        "project_name": project,
        "content": content,
        "event_url": url,
        "category": category
    }
    response = requests.post(f"{SUPABASE_URL}/rest/v1/airdrop_gems", json=payload, headers=headers)
    return response.status_code in [201, 409]

def send_discord_alert(project, content, url, category):
    """Sends a rich Discord embed message via Webhook"""
    
    # Discord Embed payload structure
    payload = {
        "content": "🚨 **New Airdrop Gem Alert!** 🚨",
        "embeds": [
            {
                "title": f"🪂 Event: {category}",
                "description": content,
                "color": 16711680, # Red color integer for alerts
                "fields": [
                    {"name": "Project", "value": project.upper(), "inline": True},
                    {"name": "Source Link", "value": f"[View Tweet]({url})", "inline": True}
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
    print("Starting hourly airdrop scrape...")
    tweets = fetch_crypto_twitter_mock()
    
    for tweet in tweets:
        if tweet["username"] in TRACKED_PROJECTS:
            is_gem, category = filter_and_verify_tweet(tweet["text"])
            
            if is_gem:
                success = save_to_supabase(
                    tweet["id"], 
                    tweet["username"], 
                    tweet["text"], 
                    tweet["link"],
                    category
                )
                
                if success:
                    send_discord_alert(
                        tweet["username"], 
                        tweet["text"], 
                        tweet["link"], 
                        category
                    )
                    print(f"Discord alert sent for {tweet['username']}")

if __name__ == "__main__":
    main()
