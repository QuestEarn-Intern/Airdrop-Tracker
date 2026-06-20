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
TARGET_KEYWORDS = ["airdrop", "quest", "earn", "fcfs", "snapshot", "claim", "retroactive"]

def fetch_general_tweets():
    """
    Pulls recent public feed updates using Twitter's syndication endpoint.
    (You can swap the screen-name endpoint to a general search/syndication URL if needed,
    or we pull from an aggregate list of top accounts).
    """
    # For a general feed search without restricting to a single project, 
    # we'll use a public general syndication timeline (e.g., aggregating top Web3 builders)
    # Using 'crypto' or general aggregator as an example feed
    rss_url = "https://syndication.twitter.com/srv/timeline-profile/screen-name/arbitrum"
    feed = feedparser.parse(rss_url)
    
    extracted_tweets = []
    for entry in feed.entries[:15]: # Scan the 15 most recent general entries
        tweet_id = entry.id.split("/")[-1] if hasattr(entry, 'id') else str(hash(entry.title))
        
        extracted_tweets.append({
            "id": tweet_id,
            "text": entry.title, # RSS entry title holds the tweet text
            "link": entry.link
        })
        
    return extracted_tweets

def filter_tweet_keywords(text):
    """Checks if the text contains any of the required keywords."""
    text_lower = text.lower()
    
    # Check if ANY of our target keywords exist in the tweet
    if not any(word in text_lower for word in TARGET_KEYWORDS):
        return False, None

    # Categorize based on matched intent
    category = "Web3 Alpha 💎"
    if "airdrop" in text_lower: 
        category = "🪂 Airdrop Event"
    elif "quest" in text_lower: 
        category = "⚔️ Quest/Campaign"
    elif "earn" in text_lower: 
        category = "💰 Yield/Earn Opportunity"
    elif "fcfs" in text_lower: 
        category = "🏃 FCFS Allocation"
    
    return True, category

def save_to_supabase(tweet_id, content, url, category):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=ignore"
    }
    payload = {
        "tweet_id": tweet_id,
        "project_name": "General Feed",
        "content": content,
        "event_url": url,
        "category": category
    }
    response = requests.post(f"{SUPABASE_URL}/rest/v1/airdrop_gems", json=payload, headers=headers)
    return response.status_code in [201, 409]

def send_discord_alert(content, url, category):
    """Sends a rich Discord embed message via Webhook"""
    payload = {
        "content": "🚨 **New Alpha / Airdrop Event Detected!** 🚨",
        "embeds": [
            {
                "title": f"✨ Type: {category}",
                "description": content,
                "color": 16753920, # Orange/Gold color for general alpha
                "fields": [
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
    print("Scanning global Web3 feeds for Airdrop, Quest, Earn, and FCFS opportunities...")
    
    try:
        tweets = fetch_general_tweets()
        
        for tweet in tweets:
            is_match, category = filter_tweet_keywords(tweet["text"])
            
            if is_match:
                success = save_to_supabase(
                    tweet["id"], 
                    tweet["text"], 
                    tweet["link"],
                    category
                )
                
                if success:
                    send_discord_alert(
                        tweet["text"], 
                        tweet["link"],
                        category
                    )
                    print(f"Alert sent for match: {tweet['id']}")
    except Exception as e:
        print(f"Error parsing general feed: {str(e)}")

if __name__ == "__main__":
    main()
