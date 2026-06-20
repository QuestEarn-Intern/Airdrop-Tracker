def save_to_supabase(item_id, source_platform, content, url, category):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=ignore"
    }
    # Ensure there is a slash between SUPABASE_URL and the rest endpoint
    payload = {
        "tweet_id": item_id, 
        "project_name": f"Tracker: {source_platform}",
        "content": content[:250], 
        "event_url": url,
        "category": category
    }
    response = requests.post(f"{SUPABASE_URL.rstrip('/')}/rest/v1/airdrop_gems", json=payload, headers=headers)
    return response.status_code in [201, 409]
