import os
import requests
from datetime import datetime

# --- CONFIGURATION & SECRETS ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_open_web3_drops():
    """
    Pulls open Web3 drop campaigns from a public, unblocked JSON source 
    hosted securely on GitHub (bypassing all Cloudflare and firewall bot blocks).
    """
    # This URL points to an open drop directory JSON file
    source_json_url = "https://raw.githubusercontent.com/ActionAirdrop/crypto-drops/main/drops.json"
    
    extracted_drops = []
    try:
        response = requests.get(source_json_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        # Parse JSON drop records safely
        drop_data = response.json()
        for drop in drop_data.get("campaigns", [])[:10]:
            extracted_drops.append({
                "id": drop.get("id", str(hash(drop.get("url")))),
                "project": drop.get("project_name", "Open Web3 Project"),
                "content": drop.get("description", "New retroactive drop or questing campaign found."),
                "url": drop.get("url", "https://github.com")
            })
            
    except Exception as e:
        print(f"Failed pulling unblocked drop directory: {str(e)}")
        
    return extracted_drops

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
        "category": "Decentralized Drop Directory"
    }
    base_url = SUPABASE_URL.rstrip('/') if SUPABASE_URL else ""
    response = requests.post(f"{base_url}/rest/v1/airdrop_gems", json=payload, headers=headers)
    return response.status_code in [201, 409]

def main():
    print("Ingesting public decentralized Drop Database (Unrestricted)...")
    
    items = fetch_open_web3_drops()
    print(f"Ingested {len(items)} items. Pushing entries securely to your Supabase instance...")
    
    success_counter = 0
    for item in items:
        success = save_to_supabase(
            item["id"], 
            item["project"],
            item["content"], 
            item["url"]
        )
        if success:
            success_counter += 1
            print(f"Successfully saved drop item: {item['id']}")
                
    print(f"Execution complete. Successfully processed and saved {success_counter} drops.")

if __name__ == "__main__":
    main()
