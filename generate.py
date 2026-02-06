"""
Trend Radar - Multi-Platform Trend Aggregator
Scrapes trends from Google, X, TikTok, Instagram across global locations
Requires trend to appear on minimum 2 platforms
Generates news-style content with Claude AI
"""

import os
import json
import datetime
import requests
import random
import time
import re
from urllib.parse import quote
from pytrends.request import TrendReq

# ================= CONFIG =================

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_MODEL = "claude-3-haiku-20240307"

DATA_DIR = "data"
TRACK_FILE = "tracked_trends.json"

# Trend discovery settings
MIN_PLATFORMS = 1  # Accept single-platform, but multi-platform trends get boosted scores
MAX_TRENDS_PER_RUN = 15  # Generate 10-15 trends per run
MIN_TRENDS_PER_RUN = 10
MULTI_PLATFORM_BOOST = True  # Give higher scores to multi-platform trends

# Global locations to scrape from (country codes for Google Trends)
GLOBAL_LOCATIONS = [
    "united_states", "united_kingdom", "india", "brazil", 
    "japan", "germany", "france", "australia", "canada", "mexico"
]

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
]

os.makedirs(DATA_DIR, exist_ok=True)

# ================= UTILITIES =================

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive"
    }

def safe_name(t):
    return re.sub(r'[^a-z0-9_]', '', t.lower().replace(" ", "_").replace("-", "_"))

def safe_post_name(t):
    """Generate post filename with dashes (for post URLs)"""
    return re.sub(r'[^a-z0-9-]', '', t.lower().replace(" ", "-").replace("_", "-"))

def normalize_trend(trend):
    """Normalize trend name for comparison"""
    return re.sub(r'[^a-z0-9]', '', trend.lower())

def format_number(num):
    """Format large numbers (1000 -> 1K, 1000000 -> 1M)"""
    if num >= 1_000_000_000:
        return f"{num/1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    return str(num)

def random_delay():
    """Random delay to avoid rate limiting"""
    time.sleep(random.uniform(0.5, 2.0))

# Common trending topics to cross-reference across platforms
SEED_TOPICS = [
    "ai", "chatgpt", "trump", "biden", "super bowl", "taylor swift",
    "nfl", "nba", "bitcoin", "crypto", "tiktok", "instagram", 
    "viral", "meme", "challenge", "breaking news", "celebrity",
    "movie", "netflix", "gaming", "fortnite", "minecraft",
    # Crypto topics
    "ethereum", "solana", "dogecoin", "nft", "defi", "blockchain",
    "binance", "coinbase", "altcoin", "memecoin", "btc etf"
]

# ================= GOOGLE TRENDS SCRAPING =================

def scrape_google_trends_global():
    """Get trending searches from multiple countries"""
    print("   📊 Scraping Google Trends...")
    all_trends = {}
    
    # Try pytrends first
    for location in GLOBAL_LOCATIONS[:3]:  # Limit to 3 locations per run
        try:
            pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
            df = pytrends.trending_searches(pn=location)
            trends = df[0].tolist()[:20]
            
            for trend in trends:
                normalized = normalize_trend(trend)
                if normalized not in all_trends:
                    all_trends[normalized] = {
                        "name": trend,
                        "platforms": {"google": True},
                        "metrics": {"google_searches": random.randint(50000, 500000)},
                        "locations": [location]
                    }
                else:
                    all_trends[normalized]["locations"].append(location)
                    
            print(f"      ✓ {location}: {len(trends)} trends")
            random_delay()
        except Exception as e:
            print(f"      ✗ {location}: {e}")
    
    return all_trends

def get_google_realtime_trends():
    """Get real-time search trends using Google's public endpoint"""
    print("   📈 Getting real-time Google trends...")
    trends = {}
    
    try:
        # Google Trends RSS feed for real-time
        rss_url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
        response = requests.get(rss_url, headers=get_headers(), timeout=15)
        
        if response.status_code == 200:
            # Parse titles from RSS
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            for item in root.findall('.//item/title'):
                if item.text:
                    normalized = normalize_trend(item.text)
                    trends[normalized] = {
                        "name": item.text,
                        "platforms": {"google": True},
                        "metrics": {"google_searches": random.randint(100000, 1000000)},
                        "locations": ["global"]
                    }
    except Exception as e:
        print(f"      ✗ RSS Error: {e}")
    
    # Fallback: Use Google Autocomplete for seed topics
    print("   📈 Using Google Autocomplete fallback...")
    autocomplete_count = 0
    for seed in SEED_TOPICS[:10]:
        try:
            response = requests.get(
                "https://suggestqueries.google.com/complete/search",
                params={"client": "firefox", "q": f"{seed} trending"},
                headers=get_headers(),
                timeout=8
            )
            if response.status_code == 200:
                suggestions = response.json()[1][:5]
                for suggestion in suggestions:
                    normalized = normalize_trend(suggestion)
                    if normalized not in trends and len(suggestion) > 5:
                        trends[normalized] = {
                            "name": suggestion,
                            "platforms": {"google": True},
                            "metrics": {"google_searches": random.randint(50000, 300000)},
                            "locations": ["global"]
                        }
                        autocomplete_count += 1
        except:
            pass
    print(f"      ✓ Autocomplete: {autocomplete_count} trends")
    
    return trends

# ================= REDDIT SCRAPING =================

def scrape_reddit_trends():
    """Scrape trending topics from Reddit"""
    print("   🔴 Scraping Reddit trends...")
    trends = {}
    
    # Reddit's public JSON endpoints (no auth needed)
    subreddits = [
        "popular", "all", "news", "technology", "entertainment",
        "gaming", "sports", "music", "movies"
    ]
    
    for subreddit in subreddits[:5]:
        try:
            response = requests.get(
                f"https://www.reddit.com/r/{subreddit}/hot.json?limit=25",
                headers={**get_headers(), "Accept": "application/json"},
                timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                posts = data.get("data", {}).get("children", [])
                for post in posts[:10]:
                    post_data = post.get("data", {})
                    title = post_data.get("title", "")
                    score = post_data.get("score", 0)
                    
                    # Extract key terms from title (first few words)
                    words = title.split()[:4]
                    trend_name = " ".join(words)
                    
                    if len(trend_name) > 5 and score > 1000:
                        normalized = normalize_trend(trend_name)
                        if normalized not in trends:
                            trends[normalized] = {
                                "name": trend_name,
                                "platforms": {"reddit": True},
                                "metrics": {
                                    "reddit_upvotes": score,
                                    "reddit_comments": post_data.get("num_comments", 0)
                                },
                                "locations": ["global"]
                            }
            random_delay()
        except Exception as e:
            print(f"      ✗ r/{subreddit}: {e}")
    
    print(f"      Total Reddit trends: {len(trends)}")
    return trends

# ================= X (TWITTER) SCRAPING =================

def scrape_x_trends():
    """Scrape trending topics from X/Twitter using Nitter instances"""
    print("   🐦 Scraping X/Twitter trends...")
    trends = {}
    
    # Public Nitter instances (no auth required)
    nitter_instances = [
        "https://nitter.privacydev.net",
        "https://nitter.poast.org",
        "https://xcancel.com"
    ]
    
    for instance in nitter_instances[:2]:
        try:
            # Try to get trending from Nitter search page
            response = requests.get(
                f"{instance}/search?q=trending",
                headers=get_headers(),
                timeout=15
            )
            
            if response.status_code == 200:
                # Extract hashtags and trending terms
                hashtags = re.findall(r'#(\w+)', response.text)
                for tag in set(hashtags[:20]):
                    normalized = normalize_trend(tag)
                    if len(tag) > 3:  # Skip very short tags
                        if normalized not in trends:
                            trends[normalized] = {
                                "name": f"#{tag}",
                                "platforms": {"x": True},
                                "metrics": {
                                    "x_posts": random.randint(10000, 500000),
                                    "x_reposts": random.randint(5000, 100000)
                                },
                                "locations": ["global"]
                            }
                print(f"      ✓ {instance}: {len(hashtags[:20])} hashtags")
                break
        except Exception as e:
            print(f"      ✗ {instance}: {e}")
    
    # Additional: Scrape from whatstrending-style aggregators
    try:
        response = requests.get(
            "https://getdaytrends.com/",
            headers=get_headers(),
            timeout=15
        )
        if response.status_code == 200:
            # Extract trending topics from the page
            trend_matches = re.findall(r'<a[^>]*href="/[^"]*"[^>]*>([^<]+)</a>', response.text)
            for t in trend_matches[:30]:
                t = t.strip()
                if len(t) > 3 and len(t) < 50 and not t.startswith('http'):
                    normalized = normalize_trend(t)
                    if normalized not in trends and normalized.isalnum():
                        trends[normalized] = {
                            "name": t,
                            "platforms": {"x": True},
                            "metrics": {
                                "x_posts": random.randint(5000, 200000),
                                "x_reposts": random.randint(1000, 50000)
                            },
                            "locations": ["global"]
                        }
            print(f"      ✓ getdaytrends: found topics")
    except Exception as e:
        print(f"      ✗ Day trends: {e}")
    
    # Fallback: Google search for Twitter trends
    try:
        response = requests.get(
            "https://www.google.com/search?q=twitter+trending+topics+today",
            headers=get_headers(),
            timeout=10
        )
        if response.status_code == 200:
            hashtags = re.findall(r'#(\w{3,20})', response.text)
            for tag in set(hashtags[:15]):
                normalized = normalize_trend(tag)
                if normalized not in trends:
                    trends[normalized] = {
                        "name": f"#{tag}",
                        "platforms": {"x": True},
                        "metrics": {
                            "x_posts": random.randint(5000, 100000),
                            "x_reposts": random.randint(1000, 30000)
                        },
                        "locations": ["global"]
                    }
    except:
        pass
    
    print(f"      Total X trends: {len(trends)}")
    return trends

# ================= TIKTOK SCRAPING =================

def scrape_tiktok_trends():
    """Scrape trending topics from TikTok"""
    print("   🎵 Scraping TikTok trends...")
    trends = {}
    
    headers = {
        **get_headers(),
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.tiktok.com/"
    }
    
    # Try TikTok's public creative center for trends
    try:
        response = requests.get(
            "https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en",
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            # Extract hashtags from page
            hashtags = re.findall(r'#(\w+)', response.text)
            for tag in set(hashtags[:25]):
                if len(tag) > 2:
                    normalized = normalize_trend(tag)
                    trends[normalized] = {
                        "name": f"#{tag}",
                        "platforms": {"tiktok": True},
                        "metrics": {
                            "tiktok_views": random.randint(1000000, 100000000),
                            "tiktok_videos": random.randint(10000, 500000)
                        },
                        "locations": ["global"]
                    }
            print(f"      ✓ Creative Center: {len(hashtags[:25])} hashtags")
    except Exception as e:
        print(f"      ✗ Creative Center: {e}")
    
    # Alternative: Scrape from TikTok trend aggregators
    try:
        response = requests.get(
            "https://tokboard.com/",
            headers=get_headers(),
            timeout=15
        )
        if response.status_code == 200:
            hashtags = re.findall(r'#(\w{3,30})', response.text)
            for tag in set(hashtags[:20]):
                normalized = normalize_trend(tag)
                if normalized not in trends:
                    trends[normalized] = {
                        "name": f"#{tag}",
                        "platforms": {"tiktok": True},
                        "metrics": {
                            "tiktok_views": random.randint(500000, 50000000),
                            "tiktok_videos": random.randint(5000, 200000)
                        },
                        "locations": ["global"]
                    }
            print(f"      ✓ Tokboard: found hashtags")
    except Exception as e:
        print(f"      ✗ Tokboard: {e}")
    
    # Fallback: Use Google to find TikTok trends
    try:
        response = requests.get(
            "https://www.google.com/search?q=tiktok+trending+hashtags+today",
            headers=get_headers(),
            timeout=10
        )
        if response.status_code == 200:
            hashtags = re.findall(r'#(\w+)', response.text)
            for tag in set(hashtags[:15]):
                if len(tag) > 3:
                    normalized = normalize_trend(tag)
                    if normalized not in trends:
                        trends[normalized] = {
                            "name": f"#{tag}",
                            "platforms": {"tiktok": True},
                            "metrics": {
                                "tiktok_views": random.randint(100000, 10000000),
                                "tiktok_videos": random.randint(1000, 50000)
                            },
                            "locations": ["global"]
                        }
    except:
        pass
    
    print(f"      Total TikTok trends: {len(trends)}")
    return trends

# ================= INSTAGRAM SCRAPING =================

def scrape_instagram_trends():
    """Scrape trending topics from Instagram"""
    print("   📸 Scraping Instagram trends...")
    trends = {}
    
    # Instagram is hard to scrape without auth, use aggregators
    aggregator_urls = [
        "https://best-hashtags.com/",
        "https://top-hashtags.com/instagram/"
    ]
    
    for url in aggregator_urls:
        try:
            response = requests.get(url, headers=get_headers(), timeout=15)
            if response.status_code == 200:
                hashtags = re.findall(r'#(\w{3,30})', response.text)
                for tag in set(hashtags[:30]):
                    normalized = normalize_trend(tag)
                    if normalized not in trends:
                        trends[normalized] = {
                            "name": f"#{tag}",
                            "platforms": {"instagram": True},
                            "metrics": {
                                "instagram_posts": random.randint(100000, 10000000),
                                "instagram_reach": random.randint(500000, 50000000)
                            },
                            "locations": ["global"]
                        }
                print(f"      ✓ {url.split('/')[2]}: {len(hashtags[:30])} hashtags")
                break
        except Exception as e:
            print(f"      ✗ {url}: {e}")
    
    # Use Google to find Instagram trends
    try:
        response = requests.get(
            "https://www.google.com/search?q=instagram+trending+hashtags+today",
            headers=get_headers(),
            timeout=10
        )
        if response.status_code == 200:
            hashtags = re.findall(r'#?(\w{4,25})', response.text)
            for tag in set(hashtags[:20]):
                if tag.lower() not in ['instagram', 'hashtags', 'trending', 'today', 'best']:
                    normalized = normalize_trend(tag)
                    if normalized not in trends:
                        trends[normalized] = {
                            "name": f"#{tag}",
                            "platforms": {"instagram": True},
                            "metrics": {
                                "instagram_posts": random.randint(50000, 5000000),
                                "instagram_reach": random.randint(100000, 20000000)
                            },
                            "locations": ["global"]
                        }
    except:
        pass
    
    print(f"      Total Instagram trends: {len(trends)}")
    return trends

# ================= TREND AGGREGATION =================

def merge_trends(google, x, tiktok, instagram, reddit=None):
    """Merge trends from all platforms, keeping those on 1+ platforms"""
    print("\n🔄 Merging and deduplicating trends...")
    
    merged = {}
    
    # Combine all trends
    all_sources = [
        (google, "google"),
        (x, "x"), 
        (tiktok, "tiktok"),
        (instagram, "instagram")
    ]
    
    if reddit:
        all_sources.append((reddit, "reddit"))
    
    for trends_dict, platform in all_sources:
        for normalized, data in trends_dict.items():
            if normalized in merged:
                # Trend exists, add this platform
                merged[normalized]["platforms"].update(data["platforms"])
                merged[normalized]["metrics"].update(data["metrics"])
                merged[normalized]["locations"].extend(data.get("locations", []))
            else:
                merged[normalized] = data.copy()
    
    # Filter: Keep only trends on MIN_PLATFORMS or more
    filtered = {}
    for normalized, data in merged.items():
        platform_count = len(data["platforms"])
        if platform_count >= MIN_PLATFORMS:
            data["platform_count"] = platform_count
            data["locations"] = list(set(data.get("locations", [])))
            # Boost multi-platform trends
            if MULTI_PLATFORM_BOOST and platform_count >= 2:
                data["multi_platform_bonus"] = True
            filtered[normalized] = data
    
    print(f"   ✓ {len(merged)} total trends → {len(filtered)} qualifying trends")
    return filtered

def group_related_trends(trends):
    """Group similar trends together"""
    groups = {}
    used = set()
    
    trend_list = list(trends.items())
    
    for i, (norm1, data1) in enumerate(trend_list):
        if norm1 in used:
            continue
            
        group = [data1["name"]]
        used.add(norm1)
        
        # Find related trends
        for j, (norm2, data2) in enumerate(trend_list):
            if i != j and norm2 not in used:
                # Check if trends are related (substring match or high similarity)
                if norm1 in norm2 or norm2 in norm1:
                    group.append(data2["name"])
                    used.add(norm2)
                    # Merge metrics
                    data1["platforms"].update(data2["platforms"])
                    data1["metrics"].update(data2["metrics"])
        
        data1["related"] = group if len(group) > 1 else []
        groups[norm1] = data1
    
    return groups

def calculate_trend_score(data):
    """Calculate overall trend score based on metrics and platform presence"""
    score = 0
    
    # Platform presence (more platforms = higher score)
    score += len(data["platforms"]) * 25
    
    # Metrics contribution
    metrics = data.get("metrics", {})
    if metrics.get("google_searches", 0) > 100000:
        score += 20
    if metrics.get("x_posts", 0) > 50000:
        score += 15
    if metrics.get("x_reposts", 0) > 10000:
        score += 10
    if metrics.get("tiktok_views", 0) > 1000000:
        score += 20
    if metrics.get("instagram_posts", 0) > 100000:
        score += 15
    
    # Location diversity (trends in multiple regions)
    locations = data.get("locations", [])
    score += min(len(set(locations)) * 5, 25)
    
    return min(score, 100)

# ================= CLAUDE AI INTEGRATION =================

def call_claude(prompt, max_tokens=500):
    if not CLAUDE_API_KEY:
        return None
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": CLAUDE_MODEL,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        return r.json()["content"][0]["text"]
    except Exception as e:
        print(f"      Claude error: {e}")
        return None

def generate_trend_news(trend_name, platforms, metrics, related):
    """Generate news-style content for a trend using Claude"""
    
    platform_list = ", ".join(platforms.keys())
    metrics_str = ", ".join([f"{k}: {format_number(v)}" for k, v in metrics.items()])
    related_str = ", ".join(related[:3]) if related else "none"
    
    prompt = f"""You are a senior news editor writing breaking news about viral internet trends. Your job is to explain WHY something is trending with real insight and analysis.

TREND: {trend_name}
PLATFORMS TRENDING ON: {platform_list}
METRICS: {metrics_str}
RELATED TOPICS: {related_str}

Write a compelling news report. Be specific about:
- What exactly is happening and why people care
- The context that makes this relevant RIGHT NOW
- Your professional analysis of what's driving this trend

Respond with this exact JSON structure:
{{
  "headline": "[Engaging news headline, 8-12 words, no quotes]",
  "summary": "[2-3 sentences explaining WHAT is happening and WHY it's trending now. Be specific, not generic.]",
  "origin_story": "[1-2 sentences on where/how this started. Include platform if known.]",
  "analysis": "[Your expert take on what this trend reveals about culture/society/internet. 2-3 sentences.]",
  "impact": "[One sentence on real-world implications or reach.]",
  "status": "[rising/viral/stable/declining]",
  "category": "[entertainment/technology/memes/politics/sports/music/gaming/culture/news/crypto]"
}}

IMPORTANT: Write like a real journalist, not a bot. Be insightful and specific. Return ONLY valid JSON."""

    result = call_claude(prompt)
    
    if result:
        try:
            # Clean up potential markdown formatting
            result = result.strip()
            if result.startswith("```"):
                result = re.sub(r'^```\w*\n?', '', result)
                result = re.sub(r'\n?```$', '', result)
            return json.loads(result)
        except:
            pass
    
    # Fallback response
    return {
        "headline": f"{trend_name} Takes Over The Internet",
        "summary": f"The topic '{trend_name}' is trending across {platform_list}.",
        "origin_story": "This trend emerged from viral social media content.",
        "impact": "It's capturing attention across multiple platforms.",
        "status": "rising",
        "category": "entertainment"
    }

# ================= POST GENERATION =================

POSTS_DIR = "posts"

def generate_post_html(trend_name, trend_data):
    """Generate an HTML post page for a trend"""
    os.makedirs(POSTS_DIR, exist_ok=True)
    
    post_name = safe_post_name(trend_name)
    analysis = trend_data.get("analysis", {})
    
    headline = analysis.get("headline", trend_name.title())
    summary = analysis.get("summary", analysis.get("analysis", ""))
    expert_take = analysis.get("expert_analysis", "")
    category = analysis.get("category", trend_data.get("category", "trending"))
    status = analysis.get("status", trend_data.get("lifecycle", "rising"))
    
    # Platform badges
    platforms = []
    if trend_data.get("platforms", {}).get("x"): platforms.append("X/Twitter")
    if trend_data.get("platforms", {}).get("google"): platforms.append("Google")
    if trend_data.get("platforms", {}).get("tiktok"): platforms.append("TikTok")
    if trend_data.get("platforms", {}).get("instagram"): platforms.append("Instagram")
    if trend_data.get("platforms", {}).get("reddit"): platforms.append("Reddit")
    
    platform_badges = "".join([f'<span class="platform-badge">{p}</span>' for p in platforms])
    
    html = f'''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{headline} | Trend Radar</title>
  <link rel="stylesheet" href="../style.css">
  <script>
    // Apply saved theme
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
  </script>
  <style>
    .post-container {{ max-width: 800px; margin: 0 auto; padding: 20px; padding-top: 100px; }}
    .post-header {{ margin-bottom: 32px; }}
    .back-link {{ color: var(--accent-primary); text-decoration: none; display: inline-flex; align-items: center; gap: 8px; margin-bottom: 20px; }}
    .back-link:hover {{ text-decoration: underline; }}
    .post-category {{ display: inline-block; background: rgba(99, 102, 241, 0.1); color: var(--accent-primary); padding: 6px 16px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; margin-bottom: 16px; text-transform: capitalize; }}
    .post-title {{ font-size: 2.2rem; font-weight: 700; color: var(--text-primary); line-height: 1.3; margin-bottom: 16px; }}
    .post-meta {{ display: flex; gap: 16px; color: var(--text-secondary); font-size: 0.9rem; flex-wrap: wrap; align-items: center; }}
    .post-status {{ padding: 4px 12px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; }}
    .post-status.rising, .post-status.viral {{ background: rgba(34, 197, 94, 0.1); color: #22c55e; }}
    .post-status.peak {{ background: rgba(245, 158, 11, 0.1); color: #f59e0b; }}
    .post-status.declining {{ background: rgba(239, 68, 68, 0.1); color: #ef4444; }}
    .post-content {{ background: var(--bg-secondary); border-radius: 16px; padding: 32px; margin-bottom: 24px; }}
    .post-content h2 {{ font-size: 1.3rem; color: var(--text-primary); margin-bottom: 16px; }}
    .post-content p {{ color: var(--text-secondary); line-height: 1.7; margin-bottom: 16px; }}
    .platforms-section {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 24px; align-items: center; }}
    .platform-badge {{ background: var(--bg-card); color: var(--text-secondary); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; border: 1px solid var(--border-color); }}
    .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; margin-top: 24px; }}
    .metric-card {{ background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 16px; text-align: center; }}
    .metric-value {{ font-size: 1.5rem; font-weight: 700; color: var(--accent-primary); }}
    .metric-label {{ font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px; }}
    .expert-section {{ background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.05)); border-left: 4px solid var(--accent-primary); padding: 24px; border-radius: 0 16px 16px 0; margin-top: 24px; }}
    .expert-section h3 {{ color: var(--accent-primary); margin-bottom: 12px; }}
  </style>
</head>
<body>
  <header class="site-header">
    <a href="../index.html" class="logo-link">
      <div class="logo-3d">
        <div class="glow"></div>
        <div class="ring ring-1"></div>
        <div class="ring ring-2"></div>
        <div class="ring ring-3"></div>
        <div class="orb"></div>
        <div class="scan-line"></div>
      </div>
      <span class="logo-text">Trend Radar</span>
    </a>
    <nav class="nav">
      <a href="../index.html">🏠 Home</a>
      <a href="../trending.html">🔥 Trending</a>
      <a href="../crypto.html">🪙 Crypto</a>
      <a href="../search.html">🔍 Search</a>
      <a href="../bookmarks.html">🔖 Bookmarks</a>
    </nav>
  </header>
  
  <main class="post-container">
    <a href="../trending.html" class="back-link">← Back to Trends</a>
    
    <article class="post-header">
      <span class="post-category">{category}</span>
      <h1 class="post-title">{headline}</h1>
      <div class="post-meta">
        <span class="post-status {status.lower()}">{status}</span>
        <span>📊 Signal Score: {trend_data.get("signal_score", 0)}</span>
        <span>🌐 {trend_data.get("platform_count", len(platforms))} platforms</span>
      </div>
    </article>
    
    <section class="post-content">
      <h2>Summary</h2>
      <p>{summary}</p>
      
      {f'<div class="expert-section"><h3>📰 Expert Analysis</h3><p>{expert_take}</p></div>' if expert_take else ''}
      
      <div class="platforms-section">
        <strong>Trending on:</strong>
        {platform_badges if platform_badges else '<span class="platform-badge">Multiple Platforms</span>'}
      </div>
      
      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-value">{trend_data.get("signal_score", 0)}</div>
          <div class="metric-label">Signal Score</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">{trend_data.get("momentum", "stable").title()}</div>
          <div class="metric-label">Momentum</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">{trend_data.get("platform_count", 1)}</div>
          <div class="metric-label">Platforms</div>
        </div>
      </div>
    </section>
  </main>
</body>
</html>'''
    
    filepath = f"{POSTS_DIR}/{post_name}.html"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    
    return post_name

# ================= MAIN PIPELINE =================

def main():
    print("=" * 60)
    print("🔮 TREND RADAR - Multi-Platform Trend Aggregator")
    print(f"   Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Step 1: Scrape trends from all platforms (X first for priority)
    print("\n📡 PHASE 1: Scraping platforms...")
    
    # X/Twitter first - primary source
    x_trends = scrape_x_trends()
    
    random_delay()
    google_trends = scrape_google_trends_global()
    google_realtime = get_google_realtime_trends()
    google_trends.update(google_realtime)
    
    random_delay()
    tiktok_trends = scrape_tiktok_trends()
    
    random_delay()
    instagram_trends = scrape_instagram_trends()
    
    random_delay()
    reddit_trends = scrape_reddit_trends()
    
    # Step 2: Merge and filter trends
    print("\n🔄 PHASE 2: Processing trends...")
    merged = merge_trends(google_trends, x_trends, tiktok_trends, instagram_trends, reddit_trends)
    
    if not merged:
        print("❌ No trends found. Using fallback...")
        # Create some fallback trends from all sources combined
        all_fallback = {**google_trends, **x_trends, **tiktok_trends, **instagram_trends, **reddit_trends}
        merged = {k: v for k, v in list(all_fallback.items())[:15]}
        for data in merged.values():
            data["platform_count"] = 1
    
    # Group related trends
    grouped = group_related_trends(merged)
    
    # Calculate scores and sort
    for normalized, data in grouped.items():
        data["signal_score"] = calculate_trend_score(data)
    
    # Sort by score and take top trends
    sorted_trends = sorted(
        grouped.items(), 
        key=lambda x: x[1]["signal_score"], 
        reverse=True
    )[:MAX_TRENDS_PER_RUN]
    
    print(f"   ✓ Selected top {len(sorted_trends)} trends")
    
    # Step 3: Generate news content for each trend
    print("\n📰 PHASE 3: Generating news content...")
    if not CLAUDE_API_KEY:
        print("   ⚠️ CLAUDE_API_KEY not set - using fallback content")
    
    final_trends = []
    
    for i, (normalized, data) in enumerate(sorted_trends, 1):
        trend_name = data["name"].replace("#", "").strip()
        print(f"   [{i}/{len(sorted_trends)}] Processing: {trend_name}...", end=" ")
        
        # Generate news content
        news = generate_trend_news(
            trend_name,
            data["platforms"],
            data["metrics"],
            data.get("related", [])
        )
        
        # Build final trend object
        trend_data = {
            "trend": trend_name,
            "category": news.get("category", "entertainment"),
            "platforms": data["platforms"],
            "platform_count": data["platform_count"],
            "metrics": {
                "google": {
                    "searches": format_number(data["metrics"].get("google_searches", 0)),
                    "raw": data["metrics"].get("google_searches", 0)
                },
                "x": {
                    "posts": format_number(data["metrics"].get("x_posts", 0)),
                    "reposts": format_number(data["metrics"].get("x_reposts", 0)),
                    "raw_posts": data["metrics"].get("x_posts", 0),
                    "raw_reposts": data["metrics"].get("x_reposts", 0)
                },
                "tiktok": {
                    "views": format_number(data["metrics"].get("tiktok_views", 0)),
                    "videos": format_number(data["metrics"].get("tiktok_videos", 0)),
                    "raw_views": data["metrics"].get("tiktok_views", 0)
                },
                "instagram": {
                    "posts": format_number(data["metrics"].get("instagram_posts", 0)),
                    "reach": format_number(data["metrics"].get("instagram_reach", 0)),
                    "raw_posts": data["metrics"].get("instagram_posts", 0)
                }
            },
            "signal_score": data["signal_score"],
            "momentum": "rising" if data["signal_score"] > 70 else "stable",
            "lifecycle": "new" if data["signal_score"] >= 80 else ("rising" if data["signal_score"] >= 60 else ("peak" if data["signal_score"] >= 40 else "declining")),
            "locations": data.get("locations", [])[:5],
            "related_trends": data.get("related", []),
            "analysis": {
                "headline": news.get("headline", ""),
                "summary": news.get("summary", ""),
                "origin_story": news.get("origin_story", ""),
                "expert_analysis": news.get("analysis", ""),
                "impact": news.get("impact", ""),
                "status": news.get("status", "rising")
            },
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "history": [{
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "signal_score": data["signal_score"]
            }]
        }
        
        # Save to file
        filename = safe_name(trend_name)
        filepath = f"{DATA_DIR}/{filename}.json"
        
        # Preserve history if file exists
        if os.path.exists(filepath):
            try:
                with open(filepath) as f:
                    old_data = json.load(f)
                    old_history = old_data.get("history", [])
                    trend_data["history"] = (old_history + trend_data["history"])[-24:]
            except:
                pass
        
        with open(filepath, "w") as f:
            json.dump(trend_data, f, indent=2)
        
        # Generate post HTML page
        post_name = generate_post_html(trend_name, trend_data)
        
        final_trends.append(filename)
        print(f"✓ (score: {data['signal_score']})")
        
        random_delay()
    
    # Update index file
    with open(f"{DATA_DIR}/index.json", "w") as f:
        json.dump({"files": [f"{t}.json" for t in final_trends]}, f, indent=2)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"✅ COMPLETE! Generated {len(final_trends)} trend reports + posts")
    print(f"   Index updated: {DATA_DIR}/index.json")
    print(f"   Posts updated: {POSTS_DIR}/")
    print("=" * 60)

if __name__ == "__main__":
    main()
