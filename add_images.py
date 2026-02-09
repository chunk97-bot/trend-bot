"""Add Unsplash images to all trend files"""
import json
import os
import requests
import re
import time

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

# Category-based fallback queries for better image matching
CATEGORY_QUERIES = {
    "politics": "politics government capitol",
    "technology": "technology computer digital",
    "crypto": "cryptocurrency bitcoin blockchain",
    "gaming": "video games controller esports",
    "entertainment": "entertainment movies television",
    "memes": "internet culture social media",
    "sports": "sports stadium athletics",
    "news": "breaking news journalism",
    "music": "music concert performance",
    "culture": "pop culture trends",
    "other": "trending viral social"
}

# Keyword fallbacks for specific topics
KEYWORD_FALLBACKS = {
    "ai": "artificial intelligence technology",
    "npc": "video game character gaming",
    "meme": "internet meme funny",
    "stream": "live streaming video",
    "viral": "social media viral trending",
    "trump": "american politics",
    "biden": "american politics",
    "tiktok": "social media smartphone",
    "twitter": "social media technology",
    "youtube": "video streaming platform",
    "chatgpt": "artificial intelligence chatbot",
    "super_bowl": "american football superbowl",
    "breaking_bad": "television drama series",
    "skull": "skull emoji internet",
    "airport": "airplane airport travel",
    "christmas": "christmas holiday festive",
    "terraria": "video game pixel art",
    "instagram": "social media photography",
    "reddit": "social media community",
    "netflix": "streaming entertainment",
}


def get_search_query(trend_data, filename):
    """Get the best search query for a trend"""
    # Try headline first (most descriptive)
    headline = trend_data.get("analysis", {}).get("headline", "")
    if headline and len(headline) > 10:
        # Extract key nouns from headline
        words = re.sub(r'[^a-zA-Z\s]', '', headline).split()
        # Skip common words
        skip = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or', 'but', 'with', 'as', 'by', 'this', 'that', 'it', 'its', 'into', 'across', 'over', 'how', 'why', 'what', 'who', 'when', 'takes', 'trend', 'trending', 'viral', 'internet', 'sparks'}
        key_words = [w for w in words if w.lower() not in skip and len(w) > 2][:4]
        if key_words:
            return ' '.join(key_words)
    
    # Try trend name
    trend_name = trend_data.get("trend", "").lower()
    
    # Check keyword fallbacks
    for key, query in KEYWORD_FALLBACKS.items():
        if key in trend_name:
            return query
    
    # Use category as fallback
    category = trend_data.get("category", "other")
    if category in CATEGORY_QUERIES:
        return CATEGORY_QUERIES[category]
    
    # Last resort: use filename
    return filename.replace('.json', '').replace('_', ' ')


def fetch_unsplash_image(query):
    """Fetch an image from Unsplash"""
    if not UNSPLASH_ACCESS_KEY:
        print("ERROR: No UNSPLASH_ACCESS_KEY set")
        return None
    
    search_query = re.sub(r'[^a-zA-Z0-9 ]', '', query)[:50]
    
    try:
        response = requests.get(
            "https://api.unsplash.com/search/photos",
            headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
            params={
                "query": search_query,
                "per_page": 1,
                "orientation": "landscape"
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                photo = data["results"][0]
                return {
                    "url": photo["urls"]["regular"],
                    "thumb": photo["urls"]["small"],
                    "credit": photo["user"]["name"],
                    "credit_link": photo["user"]["links"]["html"]
                }
            else:
                print(f"    No results for: {search_query}")
        elif response.status_code == 403:
            print(f"    Rate limit exceeded. Remaining: {response.headers.get('X-Ratelimit-Remaining', '?')}")
            return "RATE_LIMITED"
        else:
            print(f"    API error: {response.status_code}")
    except Exception as e:
        print(f"    Request error: {e}")
    
    return None


def main():
    data_dir = "data"
    updated = 0
    skipped = 0
    failed = 0
    
    print(f"Unsplash API Key: {UNSPLASH_ACCESS_KEY[:10]}..." if UNSPLASH_ACCESS_KEY else "No API key!")
    print()
    
    # Get all JSON files
    files = [f for f in sorted(os.listdir(data_dir)) if f.endswith('.json') and f != 'index.json']
    print(f"Found {len(files)} trend files\n")
    
    for filename in files:
        filepath = os.path.join(data_dir, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Skip if already has image
        if data.get("image"):
            skipped += 1
            continue
        
        # Get search query
        query = get_search_query(data, filename)
        print(f"[{filename}] Query: {query}")
        
        # Fetch image
        image = fetch_unsplash_image(query)
        
        if image == "RATE_LIMITED":
            print("Rate limited! Waiting 60 seconds...")
            time.sleep(60)
            image = fetch_unsplash_image(query)
        
        if image and image != "RATE_LIMITED":
            data["image"] = image
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"    ✓ Added image by {image['credit']}")
            updated += 1
        else:
            failed += 1
        
        # Rate limit: 50 requests/hour for demo apps
        time.sleep(0.5)
    
    print(f"\n{'='*50}")
    print(f"Done! Updated: {updated}, Skipped (had image): {skipped}, Failed: {failed}")


if __name__ == "__main__":
    main()
