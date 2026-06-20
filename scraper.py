import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- CONFIGURATION & SECRETS ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_open_drops():
    """Directly scrapes an unblocked, open-source drop directory page (e.g. public static web3 drops pages)."""
    # Using a placeholder open drop link – replace with your target open drop-hunting static page/directory
    target_url = "https://raw.githubusercontent.com/not-applicable/open-drops/main/README.md" 
    
    scraped_items = []
    try:
        response = requests.get(target_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        # Simple text parsing for markdown-based drop boards
        lines = response.text.split("\n")
        for idx, line in enumerate(lines):
            if "- [" in line or "* [" in line:
                # Extracts markdown link format: [Project Name](URL)
                import re
                match = re.search(r'\[(.*?)\]\((.*?)\)', line)
                if match:
                    project_name = match.group(1)
                    project_url = match.group(2)
                    scraped_items.append({
                        "id": f"open-drop-{hash(project_url) & 0xffffffff}",
                        "name": project_name,
                        "content": f"Open Drop Campaign: {project_name}",
                        "url": project_url
                    })
    except Exception as e:
        print(f"Failed to scrape open drops directory: {str(e)}")
        
    return scraped_items[:5]

def save_to_supabase(item_id, project_name, content, url):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=ignore"
    }
    payload = {
        "tweet_id": item_id, 
        "project_name": project_name,
        "content": content[:250], 
        "event_url": url,
        "category": "Direct Open Drop Update"
    }
    base_url = SUPABASE_URL if SUPABASE_URL else ""
    response = requests.post(f"{base_url.rstrip('/')}/rest/v1/airdrop_gems", json=payload, headers=headers)
    return response.status_code in [201, 409]

def main():
    print("Ingesting unblocked Open Drop directory...")
    
    items = fetch_open_drops()
    print(f"Extracted {len(items)} items. Pushing entries directly to Supabase...")
    
    success_counter = 0
    for item in items:
        success = save_to_supabase(
            item["id"], 
            item["name"],
            item["content"], 
            item["url"]
        )
        if success:
            success_counter += 1
            print(f"Successfully saved drop: {item['id']}")
                
    print(f"Execution complete. Successfully processed and saved {success_counter} items.")

if __name__ == "__main__":
    main()
