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

# List of trusted verified project handles you want to track
TRACKED_PROJECTS = ["arbitrum", "optimism", "solana", "starknet", "layerzero_labs"]

# Simple Rule-Based Filter Keywords
AIRDROP_KEYWORDS = ["airdrop", "snapshot", "claim", "retroactive", "token drop"]

def fetch_live_tweets_rss(project_username):
    """
    Fetches the latest tweets for $0 using Twitter's public Syndication RSS endpoint.
    Parses the feed and extracts text and perma-links.
    """
    rss_url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{project_username}"
    feed = feedparser.parse(rss_url)
    
    extracted_tweets = []
    for entry in feed.entries[:3]: # Look at the 3 most recent tweets per project
        # Tweet ID can be extracted from the link URL
        tweet_id = entry.id.split("/")[-1] if hasattr(entry, 'id') else str(hash(entry.title))
        
        extracted_tweets.append({
            "id": tweet_id,
            "username": project_username,
            "text": entry.title, # RSS entry title holds the raw tweet text
            "link": entry.link
        })
        
    return extracted_tweets

def filter_and_verify_tweet(text):
    """Applies Regex rules to verify if it's an actual airdrop gem."""
    text_lower = text.lower()
    
    if not any(word in text_lower for word in AIRDROP_KEYWORDS):
        return False, None

    category = "General Event"
    if "snapshot" in text_lower: 
        category = "Snapshot 📸"
    elif "claim" in text_lower: 
        category = "Token Claim 🪂"
    elif "airdrop" in text_lower:
        category = "Airdrop Event 💎"
    
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
    payload = {
        "content": "🚨 **New Airdrop Gem Alert!** 🚨",
        "embeds": [
            {
                "title": f"🪂 Event: {category}",
                "description": content,
                "color": 16711680, # Red integer for alerts
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
    print("Checking live project timelines for airdrop alpha...")
    
    for project in TRACKED_PROJECTS:
        try:
            live_tweets = fetch_live_tweets_rss(project)
            
            for tweet in live_tweets:
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
                        print(f"Live Discord alert sent for {tweet['username']}")
        except Exception as e:
            print(f"Failed parsing feed for {project}: {str(e)}")

if __name__ == "__main__":
    main()
