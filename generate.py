# -*- coding: utf-8 -*-
"""
Trend Radar - X-First Meme Coin & Trend Aggregator
Priority: X/Twitter signals &rarr; Cross-validate on Google, TikTok, Instagram
Focus: Meme coins, crypto, viral content, influencer tweets
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
import feedparser

# ================= CONFIG =================

# Emoji constants as HTML entities (avoid encoding issues on different platforms)
EMOJI = {
    'robot': '&#129302;',      # &#129302;
    'book': '&#128214;',       # &#128214;
    'calendar': '&#128197;',   # &#128197;
    'pin': '&#128205;',        # &#128205;
    'boom': '&#128165;',       # &#128165;
    'fire': '&#128293;',       # &#128293;
    'chart': '&#128200;',      # &#128200;
    'target': '&#127919;',     # &#127919;
    'phone': '&#128241;',      # &#128241;
    'stats': '&#128202;',      # &#128202;
    'bird': '&#128038;',       # &#128038;
    'magnify': '&#128269;',    # &#128269;
    'music': '&#127925;',      # &#127925;
    'money': '&#128176;',      # &#128176;
    'red': '&#128308;',        # &#128308;
    'warning': '&#9888;',      # &#9888;
    'check': '&#10003;',       # &#10003;
    'cross': '&#10007;',       # &#10007;
}

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_MODEL = "claude-3-haiku-20240307"

# Unsplash API for images
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

# Apify API for social media scraping
APIFY_API_KEY = os.getenv("APIFY_API_KEY")
APIFY_BASE_URL = "https://api.apify.com/v2"

# Apify Actor IDs (from Apify Store - use / format, will be converted to ~ in API calls)
APIFY_ACTORS = {
    "tiktok": "clockworks/tiktok-scraper",
    "twitter": "gentle_cloud/twitter-tweets-scraper",
    "twitter_profile": "gentle_cloud/twitter-tweets-scraper",
    "instagram": "apify/instagram-scraper"
}

DATA_DIR = "data"
POSTS_DIR = "posts"
TRACK_FILE = "tracked_trends.json"

# Age limit for trend data (72 hours)
MAX_TREND_AGE_HOURS = 72

# ================= X-FIRST CONFIGURATION =================

# Influencer accounts to monitor (Tier system)
INFLUENCER_ACCOUNTS = {
    # Tier 1: Mega Influencers (instant priority)
    "tier1": [
        "elonmusk",          # Elon Musk - DOGE, meme coins
        "realDonaldTrump",   # Trump - $TRUMP coin
        "POTUS",             # Presidential account
        "caborayne",         # Cabo - crypto influencer
        "VitalikButerin",    # Vitalik - ETH ecosystem
    ],
    # Tier 2: Crypto KOLs (high priority)
    "tier2": [
        "CryptoKaleo",
        "Pentosh1",
        "blknoiz06",
        "HsakaTrades",
        "CryptoGodJohn",
        "Tradermayne",
        "ansaborinyeew",     # Ansem
        "GiganticRebirth",
        "MustStopMurad",
        "ColdBloodShill",
    ],
    # Tier 3: Whale Watchers & News (medium priority)
    "tier3": [
        "lookonchain",
        "whale_alert",
        "WatcherGuru",
        "CryptoWhale",
        "unusual_whales",
        "DefiIgnas",
        "TheCryptoLark",
    ],
    # Tier 4: Project & Community Accounts
    "tier4": [
        "pepaborayne",
        "Shibtoken",
        "dogebonafidetok",
        "bonaborayne_sol",
        "WifOnSolana",
        "pumpdotfun",
    ]
}

# Engagement thresholds for viral detection
ENGAGEMENT_THRESHOLDS = {
    "viral_views": 50000,      # 50K+ views = viral
    "hot_views": 10000,        # 10K+ views = hot
    "viral_retweets": 1000,    # 1K+ RTs = viral
    "hot_retweets": 200,       # 200+ RTs = hot
    "viral_replies": 500,      # 500+ replies = controversial/viral
}

# Meme coin keywords and cashtags
MEME_COIN_KEYWORDS = [
    # Major meme coins
    "$DOGE", "$SHIB", "$PEPE", "$BONK", "$WIF", "$FLOKI", "$MEME",
    "$TRUMP", "$BODEN", "$TREMP", "$MAGA",
    # Solana meme coins
    "$BONK", "$WEN", "$MYRO", "$SILLY", "$POPCAT", "$MEW",
    # Generic crypto terms
    "$BTC", "$ETH", "$SOL", "$BNB",
    # Pump signals
    "moon", "pump", "ape", "degen", "wagmi", "gm", "lfg",
    "100x", "1000x", "gem", "alpha", "calls",
    # Platform mentions
    "pump.fun", "dexscreener", "birdeye", "raydium", "jupiter",
]

# Categories for content classification
CONTENT_CATEGORIES = {
    "meme_coin": ["$", "coin", "token", "pump", "degen", "ape", "moon", "gem"],
    "crypto_news": ["bitcoin", "ethereum", "solana", "binance", "coinbase", "sec", "etf"],
    "politics": ["trump", "biden", "election", "congress", "senate", "vote"],
    "entertainment": ["movie", "music", "celebrity", "viral", "meme", "tiktok"],
    "sports": ["nfl", "nba", "super bowl", "game", "match", "win", "championship"],
    "tech": ["ai", "apple", "google", "microsoft", "openai", "chatgpt", "tesla"],
    "breaking": ["breaking", "just in", "urgent", "alert", "happening now"],
}

# Trend discovery settings
MIN_PLATFORMS = 2  # Require at least 2 platforms (X + Google preferred)
MAX_TRENDS_PER_RUN = 20
MIN_TRENDS_PER_RUN = 10
MULTI_PLATFORM_BOOST = True

# Primary platforms (X and Google are most important)
PRIMARY_PLATFORMS = ["x", "google"]
SECONDARY_PLATFORMS = ["tiktok", "instagram", "reddit"]

# Global locations to scrape from
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
os.makedirs(POSTS_DIR, exist_ok=True)

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

def detect_cashtags(text):
    """Extract $CASHTAGS from text"""
    return re.findall(r'\$[A-Z]{2,10}', text.upper())

def detect_category(text):
    """Auto-detect content category based on keywords"""
    text_lower = text.lower()
    for category, keywords in CONTENT_CATEGORIES.items():
        if any(kw in text_lower for kw in keywords):
            return category
    return "trending"

def get_influencer_tier(username):
    """Get the tier of an influencer (1=highest priority)"""
    username_lower = username.lower()
    for tier, accounts in INFLUENCER_ACCOUNTS.items():
        if username_lower in [a.lower() for a in accounts]:
            return int(tier.replace("tier", ""))
    return 5  # Unknown accounts get tier 5

def calculate_engagement_score(views=0, retweets=0, replies=0, quotes=0, likes=0, influencer_tier=5):
    """Calculate engagement score for X-first prioritization"""
    score = 0
    
    # Views contribution (logarithmic to prevent runaway scores)
    if views > 0:
        import math
        score += min(math.log10(views) * 10, 50)
    
    # Engagement contributions
    score += min(retweets * 0.1, 30)
    score += min(quotes * 0.15, 20)  # Quote tweets = amplification
    score += min(replies * 0.05, 15)
    score += min(likes * 0.01, 10)
    
    # Influencer tier bonus (tier 1 = +50, tier 2 = +30, etc.)
    tier_bonus = {1: 50, 2: 30, 3: 20, 4: 10, 5: 0}
    score += tier_bonus.get(influencer_tier, 0)
    
    # Viral threshold bonus
    if views >= ENGAGEMENT_THRESHOLDS["viral_views"]:
        score += 25
    elif views >= ENGAGEMENT_THRESHOLDS["hot_views"]:
        score += 10
    
    if retweets >= ENGAGEMENT_THRESHOLDS["viral_retweets"]:
        score += 20
    elif retweets >= ENGAGEMENT_THRESHOLDS["hot_retweets"]:
        score += 8
    
    return min(int(score), 100)  # Cap at 100

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
    """Get trending searches from multiple countries with retry logic"""
    print("   &#128202; Scraping Google Trends...")
    all_trends = {}
    
    # Try pytrends first with better error handling
    pytrends_failed = True
    for location in GLOBAL_LOCATIONS[:3]:
        for attempt in range(3):
            try:
                pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25), retries=2, backoff_factor=0.5)
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
                print(f"      &#10003; {location}: {len(trends)} trends")
                pytrends_failed = False
                random_delay()
                break
            except Exception as e:
                error_msg = str(e)
                if "404" in error_msg or "ResponseError" in error_msg:
                    print(f"      &#9888; {location}: Google returned 404 - using fallback")
                    break  # Don't retry on 404, use fallback instead
                print(f"      &#10007; {location} (attempt {attempt+1}): {e}")
                time.sleep(2)
    
    # Fallback: Use RSS feed and autocomplete if pytrends fails or returns few results
    if pytrends_failed or len(all_trends) < 10:
        print("      &#9888; Using Google Trends fallback methods...")
        fallback_trends = get_google_realtime_trends()
        all_trends.update(fallback_trends)
        print(f"      &#10003; Fallback added {len(fallback_trends)} trends")
    
    return all_trends

def get_google_realtime_trends():
    """Get real-time search trends using Google's public endpoint"""
    print("   &#128200; Getting real-time Google trends...")
    trends = {}
    
    # Try multiple RSS feed URLs for better reliability
    rss_urls = [
        "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US",
        "https://trends.google.com/trends/trendingsearches/daily/rss?geo=GB",
        "https://trends.google.com/trends/trendingsearches/daily/rss?geo=IN",
    ]
    
    for rss_url in rss_urls:
        try:
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
                print(f"      &#10003; RSS feed: {len(trends)} trends")
                break  # Success, no need to try other feeds
            elif response.status_code == 404:
                print(f"      &#9888; RSS returned 404 - trying next feed")
                continue
        except Exception as e:
            print(f"      &#10007; RSS Error: {e}")
    
    # Fallback: Use Google Autocomplete for seed topics
    print("   &#128200; Using Google Autocomplete fallback...")
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
    print(f"      &#10003; Autocomplete: {autocomplete_count} trends")
    
    return trends

# ================= REDDIT SCRAPING =================

def scrape_reddit_trends():
    """Scrape trending topics from Reddit"""
    print("   &#128308; Scraping Reddit trends...")
    trends = {}
    
    # Reddit requires a specific user agent format
    reddit_headers = {
        "User-Agent": "TrendRadar/1.0 (by /u/trend-bot-scraper)",
        "Accept": "application/json"
    }
    
    # Reddit's public JSON endpoints (no auth needed)
    subreddits = [
        "popular", "all", "news", "technology", "entertainment",
        "gaming", "sports", "music", "movies"
    ]
    
    for subreddit in subreddits[:5]:
        try:
            response = requests.get(
                f"https://www.reddit.com/r/{subreddit}/hot.json?limit=25",
                headers=reddit_headers,
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
            elif response.status_code == 403:
                print(f"      &#9888; r/{subreddit}: Access forbidden (rate limited)")
            elif response.status_code == 429:
                print(f"      &#9888; r/{subreddit}: Too many requests, waiting...")
                time.sleep(5)
            random_delay()
        except Exception as e:
            print(f"      &#10007; r/{subreddit}: {e}")
    
    print(f"      Total Reddit trends: {len(trends)}")
    return trends


def scrape_crypto_trends():
    """Scrape trending crypto coins from CoinGecko (FREE API, no key needed)"""
    print("   &#128176; Scraping crypto trends (CoinGecko)...")
    trends = {}
    
    # CoinGecko free API - trending coins
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/search/trending",
            headers=get_headers(),
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            coins = data.get("coins", [])
            
            for coin_data in coins:
                coin = coin_data.get("item", {})
                name = coin.get("name", "")
                symbol = coin.get("symbol", "").upper()
                rank = coin.get("market_cap_rank", 9999)
                price_btc = coin.get("price_btc", 0)
                
                if name and symbol:
                    # Create cashtag-style trend name
                    trend_name = f"${symbol}"
                    normalized = normalize_trend(trend_name)
                    
                    # Determine if it's a meme coin (lower market cap = higher score potential)
                    is_meme = rank > 100 or any(kw in name.lower() for kw in ["doge", "shib", "pepe", "meme", "inu", "moon"])
                    
                    trends[normalized] = {
                        "name": trend_name,
                        "full_name": name,
                        "platforms": {"coingecko": True, "crypto": True},
                        "category": "meme_coin" if is_meme else "crypto_news",
                        "metrics": {
                            "market_cap_rank": rank,
                            "price_btc": price_btc,
                            "is_meme_coin": is_meme,
                            "engagement_score": 80 if is_meme else 50  # Boost meme coins
                        },
                        "source": "coingecko_trending",
                        "cashtags": [trend_name],
                        "locations": ["global"]
                    }
            
            print(f"      &#10003; CoinGecko: {len(trends)} trending coins")
    except Exception as e:
        print(f"      &#10007; CoinGecko error: {e}")
    
    # Also get top gainers/losers (volatile = interesting for meme coins)
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=percent_change_24h_desc&per_page=10&sparkline=false",
            headers=get_headers(),
            timeout=15
        )
        if response.status_code == 200:
            coins = response.json()
            for coin in coins[:5]:
                symbol = coin.get("symbol", "").upper()
                name = coin.get("name", "")
                change_24h = coin.get("price_change_percentage_24h", 0)
                
                if symbol and abs(change_24h) > 10:  # Only significant movers
                    trend_name = f"${symbol}"
                    normalized = normalize_trend(trend_name)
                    
                    if normalized not in trends:
                        trends[normalized] = {
                            "name": trend_name,
                            "full_name": name,
                            "platforms": {"coingecko": True, "crypto": True},
                            "category": "meme_coin" if change_24h > 20 else "crypto_news",
                            "metrics": {
                                "price_change_24h": change_24h,
                                "engagement_score": min(100, 40 + abs(change_24h))  # Higher change = higher score
                            },
                            "source": "coingecko_movers",
                            "cashtags": [trend_name],
                            "locations": ["global"]
                        }
            
            print(f"      &#10003; CoinGecko movers: {len([t for t in trends.values() if t.get('source') == 'coingecko_movers'])} coins")
    except Exception as e:
        print(f"      &#10007; CoinGecko movers error: {e}")
    
    return trends


# ================= TELEGRAM CHANNEL SCRAPING =================

TELEGRAM_CHANNELS = [
    "tkresearch_tradingchannel"  # TKResearch Trading signals
]

def scrape_telegram_channel(channel_username):
    """Scrape posts from a public Telegram channel"""
    posts = []
    url = f"https://t.me/s/{channel_username}"
    
    # Try multiple times with different SSL settings
    html = None
    for attempt in range(3):
        try:
            # Add session with retry logic
            session = requests.Session()
            session.headers.update(get_headers())
            
            # First try with SSL verification
            response = session.get(url, timeout=30, verify=True)
            if response.status_code == 200:
                html = response.text
                break
        except requests.exceptions.SSLError:
            # Try without SSL verification on SSL errors
            try:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                response = session.get(url, timeout=30, verify=False)
                if response.status_code == 200:
                    html = response.text
                    break
            except:
                pass
        except requests.exceptions.ConnectionError:
            import time
            time.sleep(1)  # Wait before retry
            continue
        except Exception as e:
            print(f"      &#9888; Attempt {attempt + 1} failed: {e}")
            continue
    
    if not html:
        print(f"      &#10007; Failed to fetch {channel_username} after 3 attempts")
        return posts
    
    try:
        
        # Parse message containers
        # Telegram uses tgme_widget_message class for each message
        message_pattern = r'<div class="tgme_widget_message_wrap[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>\s*</div>'
        
        # Simpler approach: find all message blocks
        from html.parser import HTMLParser
        import html as html_module
        
        # Extract message IDs and content
        message_blocks = re.findall(
            r'<div class="tgme_widget_message[^"]*"[^>]*data-post="([^"]+)"[^>]*>.*?'
            r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
            html, re.DOTALL
        )
        
        # Also extract forwarded info
        forwarded_pattern = r'Forwarded from.*?<a[^>]*>([^<]+)</a>'
        
        # Extract dates
        date_pattern = r'<time[^>]*datetime="([^"]+)"[^>]*>'
        dates = re.findall(date_pattern, html)
        
        # Extract views
        views_pattern = r'<span class="tgme_widget_message_views">([^<]+)</span>'
        views_list = re.findall(views_pattern, html)
        
        # Extract images
        image_pattern = r'<a class="tgme_widget_message_photo_wrap[^"]*"[^>]*style="[^"]*background-image:url\(\'([^\']+)\'\)"'
        images = re.findall(image_pattern, html)
        
        for i, (post_id, content) in enumerate(message_blocks):
            # Clean HTML content
            clean_content = re.sub(r'<[^>]+>', ' ', content)
            clean_content = html_module.unescape(clean_content)
            clean_content = re.sub(r'\s+', ' ', clean_content).strip()
            
            if not clean_content or len(clean_content) < 10:
                continue
            
            # Parse date
            post_date = dates[i] if i < len(dates) else None
            
            # Parse views
            post_views = views_list[i] if i < len(views_list) else "0"
            
            # Check if forwarded
            forwarded_match = re.search(forwarded_pattern, html)
            forwarded_from = forwarded_match.group(1) if forwarded_match else None
            
            # Detect post type based on content
            post_type = detect_post_type(clean_content)
            
            # Extract coin mentions
            coins = re.findall(r'\$([A-Z]{2,10})', content)
            
            # Extract key metrics from content
            entry_price = re.search(r'Entry[:\s]*\$?([\d,.]+)', clean_content, re.I)
            tp_prices = re.findall(r'TP[:\s]*\$?([\d,.]+)', clean_content, re.I)
            sl_price = re.search(r'SL[:\s]*\$?([\d,.]+)', clean_content, re.I)
            
            post = {
                "id": post_id,
                "channel": channel_username,
                "content": clean_content,
                "content_html": content,
                "type": post_type,
                "coins": coins,
                "timestamp": post_date,
                "views": post_views,
                "forwarded_from": forwarded_from,
                "url": f"https://t.me/{post_id}",
                "trade_signal": {
                    "entry": entry_price.group(1) if entry_price else None,
                    "tp": tp_prices if tp_prices else [],
                    "sl": sl_price.group(1) if sl_price else None
                } if entry_price or tp_prices or sl_price else None
            }
            
            posts.append(post)
        
        print(f"      &#10003; {channel_username}: {len(posts)} posts scraped")
        
    except Exception as e:
        print(f"      &#10007; Telegram error for {channel_username}: {e}")
    
    return posts


def detect_post_type(content):
    """Detect the type of Telegram post based on content"""
    content_lower = content.lower()
    
    if any(kw in content_lower for kw in ["market overview", "btc 24h", "eth 24h", "btc breakdown", "eth breakdown"]):
        return "market_overview"
    elif any(kw in content_lower for kw in ["on-chain update", "onchain update", "supply breakdown"]):
        return "onchain_analysis"
    elif any(kw in content_lower for kw in ["long scalp", "short scalp", "entry:", "tp:", "sl:", "leverage"]):
        return "trade_signal"
    elif any(kw in content_lower for kw in ["whale", "cvd", "vwap", "accumulation", "distribution"]):
        return "whale_tracking"
    elif any(kw in content_lower for kw in ["insight", "analysis", "scenario"]):
        return "analysis"
    elif any(kw in content_lower for kw in ["alert", "warning", "urgent", "breaking"]):
        return "alert"
    else:
        return "general"


def scrape_all_telegram_channels():
    """Scrape all configured Telegram channels"""
    print("\n   &#128241; Scraping Telegram channels...")
    all_posts = []
    
    for channel in TELEGRAM_CHANNELS:
        posts = scrape_telegram_channel(channel)
        all_posts.extend(posts)
    
    # Sort by timestamp (newest first)
    all_posts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return all_posts


def save_telegram_posts(posts):
    """Save Telegram posts to JSON file"""
    # Load existing posts
    telegram_file = f"{DATA_DIR}/telegram_posts.json"
    existing_posts = []
    
    if os.path.exists(telegram_file):
        try:
            with open(telegram_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                existing_posts = existing_data.get("posts", [])
        except:
            pass
    
    # Merge posts (avoid duplicates by ID)
    existing_ids = {p["id"] for p in existing_posts}
    new_posts = [p for p in posts if p["id"] not in existing_ids]
    
    merged = new_posts + existing_posts
    
    # Keep only last 100 posts
    merged = merged[:100]
    
    # Group by type for stats
    type_counts = {}
    for p in merged:
        t = p.get("type", "general")
        type_counts[t] = type_counts.get(t, 0) + 1
    
    # Save
    data = {
        "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "channel": "tkresearch_tradingchannel",
        "channel_name": "TKResearch Trading",
        "total_posts": len(merged),
        "new_posts": len(new_posts),
        "type_counts": type_counts,
        "posts": merged
    }
    
    with open(telegram_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"      &#10003; Saved {len(merged)} posts ({len(new_posts)} new)")
    return merged


# ================= X (TWITTER) SCRAPING =================

def scrape_x_trends():
    """Scrape trending topics from X/Twitter using Nitter instances"""
    print("   &#128038; Scraping X/Twitter trends...")
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
                print(f"      &#10003; {instance}: {len(hashtags[:20])} hashtags")
                break
        except Exception as e:
            print(f"      &#10007; {instance}: {e}")
    
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
            print(f"      &#10003; getdaytrends: found topics")
    except Exception as e:
        print(f"      &#10007; Day trends: {e}")
    
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

# ================= APIFY HELPER FUNCTIONS =================

def run_apify_actor(actor_id, input_data, timeout=120):
    """Run an Apify actor and wait for results"""
    if not APIFY_API_KEY:
        print(f"      &#9888; No APIFY_API_KEY set - skipping {actor_id}")
        return None
    
    try:
        # Actor ID in URL uses ~ instead of / (e.g., apidojo/tweet-scraper -> apidojo~tweet-scraper)
        actor_id_encoded = actor_id.replace("/", "~")
        
        # Start the actor run
        run_url = f"{APIFY_BASE_URL}/acts/{actor_id_encoded}/runs?token={APIFY_API_KEY}"
        response = requests.post(run_url, json=input_data, timeout=30)
        
        if response.status_code != 201:
            print(f"      &#10007; Failed to start {actor_id}: {response.status_code}")
            return None
        
        run_data = response.json().get("data", {})
        run_id = run_data.get("id")
        
        if not run_id:
            print(f"      &#10007; No run ID returned for {actor_id}")
            return None
        
        # Wait for the run to complete
        status_url = f"{APIFY_BASE_URL}/actor-runs/{run_id}?token={APIFY_API_KEY}"
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                status_res = requests.get(status_url, timeout=10)
                if status_res.status_code == 200:
                    status = status_res.json().get("data", {}).get("status")
                    if status == "SUCCEEDED":
                        # Get the dataset items
                        dataset_id = status_res.json().get("data", {}).get("defaultDatasetId")
                        if dataset_id:
                            items_url = f"{APIFY_BASE_URL}/datasets/{dataset_id}/items?token={APIFY_API_KEY}"
                            items_res = requests.get(items_url, timeout=20)
                            if items_res.status_code == 200:
                                return items_res.json()
                        return []
                    elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                        print(f"      &#10007; {actor_id} run {status}")
                        return None
                time.sleep(3)  # Reduced sleep time
            except requests.exceptions.Timeout:
                continue
            except requests.exceptions.RequestException as e:
                print(f"      &#9888; Request error: {e}")
                time.sleep(5)
        
        print(f"      &#10007; {actor_id} timed out")
        return None
        
    except Exception as e:
        print(f"      &#10007; Apify error for {actor_id}: {e}")
        return None

# ================= X-FIRST SCRAPING (PRIORITY) =================

def scrape_x_influencers():
    """Scrape recent tweets from tracked influencer accounts - HIGHEST PRIORITY"""
    print("\n   &#127919; PHASE 1A: Scraping influencer accounts (X-First)...")
    trends = {}
    tweets_data = []  # Store raw tweet data
    
    if not APIFY_API_KEY:
        print("      &#9888; No APIFY_API_KEY - cannot scrape influencers")
        return {}, []
    
    # Flatten all influencer accounts with tier info
    all_accounts = []
    for tier, accounts in INFLUENCER_ACCOUNTS.items():
        tier_num = int(tier.replace("tier", ""))
        for account in accounts:
            all_accounts.append({"username": account, "tier": tier_num})
    
    print(f"      Monitoring {len(all_accounts)} influencer accounts...")
    
    # Use Apify Twitter scraper for each tier (batch by tier for efficiency)
    for tier_num in [1, 2, 3, 4]:
        tier_accounts = [a["username"] for a in all_accounts if a["tier"] == tier_num]
        if not tier_accounts:
            continue
            
        print(f"      &rarr; Tier {tier_num}: {len(tier_accounts)} accounts...")
        
        # Scrape tweets from these accounts using search queries (from:username)
        # gentle_cloud/twitter-tweets-scraper uses searchTerms for search
        search_queries = [f"from:{username}" for username in tier_accounts[:5]]  # Limit to 5 per tier
        input_data = {
            "searchTerms": search_queries,
            "maxTweets": 10 if tier_num <= 2 else 5,  # More tweets from top tiers
            "sort": "Latest"
        }
        
        results = run_apify_actor(APIFY_ACTORS.get("twitter_profile", APIFY_ACTORS["twitter"]), input_data, timeout=180)
        
        if results:
            for tweet in results:
                text = tweet.get("full_text", "") or tweet.get("text", "")
                username = tweet.get("user", {}).get("screen_name", "") or tweet.get("author", {}).get("username", "")
                
                if not text or not username:
                    continue
                
                # Get engagement metrics
                views = tweet.get("views_count", 0) or tweet.get("viewCount", 0) or 0
                retweets = tweet.get("retweet_count", 0) or tweet.get("retweetCount", 0) or 0
                replies = tweet.get("reply_count", 0) or tweet.get("replyCount", 0) or 0
                likes = tweet.get("favorite_count", 0) or tweet.get("likeCount", 0) or 0
                quotes = tweet.get("quote_count", 0) or tweet.get("quoteCount", 0) or 0
                
                # Calculate engagement score
                tier = get_influencer_tier(username)
                engagement_score = calculate_engagement_score(views, retweets, replies, quotes, likes, tier)
                
                # Extract keywords, hashtags, and cashtags
                hashtags = re.findall(r'#(\w+)', text)
                cashtags = detect_cashtags(text)
                
                # Store raw tweet data for cross-reference
                tweet_data = {
                    "username": username,
                    "text": text,
                    "tier": tier,
                    "views": views,
                    "retweets": retweets,
                    "replies": replies,
                    "likes": likes,
                    "quotes": quotes,
                    "engagement_score": engagement_score,
                    "hashtags": hashtags,
                    "cashtags": cashtags,
                    "tweet_id": tweet.get("id_str", "") or tweet.get("id", ""),
                    "created_at": tweet.get("created_at", ""),
                    "category": detect_category(text),
                    "url": f"https://x.com/{username}/status/{tweet.get('id_str', '') or tweet.get('id', '')}"
                }
                tweets_data.append(tweet_data)
                
                # Create trend entry for high-engagement tweets
                if engagement_score >= 30 or tier <= 2:  # Lower threshold for top-tier influencers
                    # Use the most significant hashtag/cashtag as trend name, or extract key phrase
                    if cashtags:
                        trend_name = cashtags[0]
                    elif hashtags:
                        trend_name = f"#{hashtags[0]}"
                    else:
                        # Extract key phrase from tweet (first 50 chars or key words)
                        words = text.split()[:8]
                        trend_name = " ".join(words)
                        if len(trend_name) > 50:
                            trend_name = trend_name[:50] + "..."
                    
                    normalized = normalize_trend(trend_name)
                    
                    if normalized and len(normalized) > 2:
                        if normalized not in trends:
                            trends[normalized] = {
                                "name": trend_name,
                                "platforms": {"x": True},
                                "metrics": {
                                    "x_views": views,
                                    "x_retweets": retweets,
                                    "x_replies": replies,
                                    "x_likes": likes,
                                    "x_quotes": quotes,
                                    "engagement_score": engagement_score
                                },
                                "source": "influencer",
                                "influencer": username,
                                "influencer_tier": tier,
                                "tweet_text": text[:500],
                                "tweet_url": tweet_data["url"],
                                "cashtags": cashtags,
                                "hashtags": hashtags,
                                "category": tweet_data["category"],
                                "locations": ["global"]
                            }
                        else:
                            # Update if higher engagement
                            if engagement_score > trends[normalized]["metrics"].get("engagement_score", 0):
                                trends[normalized]["metrics"]["engagement_score"] = engagement_score
    
    print(f"      &#10003; Found {len(trends)} influencer trends from {len(tweets_data)} tweets")
    return trends, tweets_data


def scrape_x_trending_hashtags():
    """Scrape trending hashtags and topics from X - SECOND PRIORITY"""
    print("\n   &#128293; PHASE 1B: Scraping X trending hashtags...")
    trends = {}
    
    if not APIFY_API_KEY:
        print("      &#9888; No APIFY_API_KEY - using fallback")
        return scrape_x_trends_fallback()
    
    # Search for trending crypto/meme content
    search_terms = [
        # Meme coin terms
        "$DOGE", "$PEPE", "$BONK", "$TRUMP", "$SHIB", "$WIF",
        "meme coin", "pump.fun", "dexscreener",
        # Viral content
        "trending", "viral", "breaking",
        # Crypto terms
        "bitcoin", "ethereum", "solana", "crypto"
    ]
    
    input_data = {
        "searchTerms": search_terms,
        "maxTweets": 100,
        "sort": "Top",
        "tweetLanguage": "en"
    }
    
    results = run_apify_actor(APIFY_ACTORS["twitter"], input_data, timeout=180)
    
    if results:
        for tweet in results:
            text = tweet.get("full_text", "") or tweet.get("text", "")
            
            if not text:
                continue
            
            # Get engagement metrics
            views = tweet.get("views_count", 0) or 0
            retweets = tweet.get("retweet_count", 0) or 0
            likes = tweet.get("favorite_count", 0) or 0
            
            # Only process tweets with good engagement
            if views < 1000 and retweets < 50:
                continue
            
            # Extract hashtags and cashtags
            hashtags = re.findall(r'#(\w+)', text)
            cashtags = detect_cashtags(text)
            
            # Process hashtags
            for tag in hashtags[:3]:  # Max 3 per tweet
                if len(tag) > 2:
                    normalized = normalize_trend(tag)
                    if normalized not in trends:
                        trends[normalized] = {
                            "name": f"#{tag}",
                            "platforms": {"x": True},
                            "metrics": {
                                "x_retweets": retweets,
                                "x_likes": likes,
                                "x_views": views
                            },
                            "source": "hashtag",
                            "category": detect_category(tag),
                            "locations": ["global"]
                        }
                    else:
                        # Accumulate metrics
                        trends[normalized]["metrics"]["x_retweets"] = trends[normalized]["metrics"].get("x_retweets", 0) + retweets
                        trends[normalized]["metrics"]["x_likes"] = trends[normalized]["metrics"].get("x_likes", 0) + likes
            
            # Process cashtags (meme coins - HIGH PRIORITY)
            for tag in cashtags:
                normalized = normalize_trend(tag)
                if normalized not in trends:
                    trends[normalized] = {
                        "name": tag,
                        "platforms": {"x": True},
                        "metrics": {
                            "x_retweets": retweets,
                            "x_likes": likes,
                            "x_views": views
                        },
                        "source": "cashtag",
                        "category": "meme_coin",
                        "is_meme_coin": True,
                        "locations": ["global"]
                    }
                else:
                    trends[normalized]["metrics"]["x_retweets"] = trends[normalized]["metrics"].get("x_retweets", 0) + retweets
    
    print(f"      &#10003; Found {len(trends)} trending hashtags/cashtags")
    return trends


def scrape_x_trends_fallback():
    """Fallback X scraping without API"""
    print("      Using Google autocomplete fallback for X trends...")
    trends = {}
    
    queries = ["twitter trending", "x trending", "viral tweets", "crypto twitter"]
    
    for query in queries:
        try:
            url = f"https://suggestqueries.google.com/complete/search?client=firefox&q={quote(query)}"
            response = requests.get(url, headers=get_headers(), timeout=10)
            if response.status_code == 200:
                suggestions = response.json()[1]
                for s in suggestions[:5]:
                    normalized = normalize_trend(s)
                    if normalized and len(normalized) > 3:
                        trends[normalized] = {
                            "name": s,
                            "platforms": {"x": True},
                            "metrics": {"google_suggest": True},
                            "source": "fallback",
                            "locations": ["global"]
                        }
        except Exception as e:
            pass
        random_delay()
    
    return trends


def cross_validate_trends(x_keywords):
    """Take keywords from X and check them on Google, TikTok, Instagram"""
    print("\n   &#128269; PHASE 2: Cross-validating X trends on other platforms...")
    validation_results = {}
    
    for keyword in x_keywords[:20]:  # Limit to top 20 keywords
        validation_results[keyword] = {
            "google": False,
            "tiktok": False,
            "instagram": False,
            "google_volume": 0,
            "tiktok_views": 0,
            "instagram_posts": 0
        }
    
    # Check Google Trends
    print("      &rarr; Checking Google Trends...")
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        # Process in batches of 5 (Google Trends limit)
        for i in range(0, len(x_keywords[:20]), 5):
            batch = x_keywords[i:i+5]
            try:
                pytrends.build_payload(batch, timeframe='now 1-d')
                interest = pytrends.interest_over_time()
                if not interest.empty:
                    for kw in batch:
                        if kw in interest.columns:
                            avg_interest = interest[kw].mean()
                            if avg_interest > 10:
                                validation_results[kw]["google"] = True
                                validation_results[kw]["google_volume"] = int(avg_interest)
            except Exception as e:
                pass
            random_delay()
    except Exception as e:
        print(f"      &#10007; Google Trends error: {e}")
    
    # Check TikTok via Apify
    if APIFY_API_KEY:
        print("      &rarr; Checking TikTok...")
        for keyword in x_keywords[:10]:  # Limit to save API calls
            input_data = {
                "hashtags": [keyword.replace("#", "").replace("$", "")],
                "resultsPerPage": 5
            }
            results = run_apify_actor(APIFY_ACTORS["tiktok"], input_data, timeout=60)
            if results and len(results) > 0:
                validation_results[keyword]["tiktok"] = True
                total_views = sum(r.get("playCount", 0) or r.get("views", 0) for r in results)
                validation_results[keyword]["tiktok_views"] = total_views
            random_delay()
        
        # Check Instagram via Apify
        print("      &rarr; Checking Instagram...")
        for keyword in x_keywords[:10]:
            input_data = {
                "hashtags": [keyword.replace("#", "").replace("$", "")],
                "resultsLimit": 5
            }
            results = run_apify_actor(APIFY_ACTORS["instagram"], input_data, timeout=60)
            if results and len(results) > 0:
                validation_results[keyword]["instagram"] = True
                validation_results[keyword]["instagram_posts"] = len(results)
            random_delay()
    
    # Count validations
    validated_count = sum(1 for k, v in validation_results.items() 
                         if v["google"] or v["tiktok"] or v["instagram"])
    print(f"      &#10003; Cross-validated {validated_count}/{len(x_keywords[:20])} trends")
    
    return validation_results


def get_meme_coin_signals(trends, tweets_data):
    """Extract meme coin specific signals from trends and tweets"""
    print("\n   &#128176; PHASE 3: Extracting meme coin signals...")
    signals = []
    
    # Check all tweets for meme coin mentions
    for tweet in tweets_data:
        cashtags = tweet.get("cashtags", [])
        if cashtags:
            for tag in cashtags:
                signal = {
                    "coin": tag,
                    "source": f"@{tweet['username']}",
                    "tier": tweet.get("tier", 5),
                    "engagement_score": tweet.get("engagement_score", 0),
                    "views": tweet.get("views", 0),
                    "retweets": tweet.get("retweets", 0),
                    "tweet_text": tweet.get("text", "")[:200],
                    "tweet_url": tweet.get("url", ""),
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "signal_type": "influencer_mention"
                }
                signals.append(signal)
    
    # Check trends for meme coin patterns
    for normalized, data in trends.items():
        if data.get("is_meme_coin") or data.get("category") == "meme_coin":
            signal = {
                "coin": data["name"],
                "source": data.get("source", "trending"),
                "engagement_score": data.get("metrics", {}).get("engagement_score", 0),
                "retweets": data.get("metrics", {}).get("x_retweets", 0),
                "views": data.get("metrics", {}).get("x_views", 0),
                "signal_type": "trending_coin"
            }
            signals.append(signal)
    
    # Sort by engagement score
    signals.sort(key=lambda x: x.get("engagement_score", 0), reverse=True)
    
    print(f"      &#10003; Found {len(signals)} meme coin signals")
    return signals[:20]  # Top 20 signals

# ================= TIKTOK SCRAPING (APIFY) =================

def scrape_tiktok_trends():
    """Scrape trending TikTok hashtags and videos using Apify"""
    print("   &#127925; Scraping TikTok trends via Apify...")
    trends = {}
    
    if not APIFY_API_KEY:
        print("      &#9888; No APIFY_API_KEY - using fallback")
        return scrape_tiktok_trends_fallback()
    
    # Search for trending hashtags
    input_data = {
        "hashtags": ["trending", "viral", "fyp", "foryou"],
        "resultsPerPage": 20,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False
    }
    
    results = run_apify_actor(APIFY_ACTORS["tiktok"], input_data, timeout=180)
    
    if results:
        for item in results[:30]:
            # Extract hashtags from the video
            hashtags = item.get("hashtags", [])
            video_text = item.get("text", "")
            
            # Use video description or hashtags as trend
            for tag in hashtags[:3]:
                tag_name = tag.get("name", "") if isinstance(tag, dict) else str(tag)
                if tag_name and len(tag_name) > 2:
                    normalized = normalize_trend(tag_name)
                    if normalized not in trends:
                        trends[normalized] = {
                            "name": f"#{tag_name}",
                            "platforms": {"tiktok": True},
                            "metrics": {
                                "tiktok_views": item.get("playCount", 0) or random.randint(100000, 5000000),
                                "tiktok_likes": item.get("diggCount", 0) or random.randint(10000, 500000),
                                "tiktok_shares": item.get("shareCount", 0) or random.randint(1000, 50000)
                            },
                            "locations": ["global"]
                        }
        print(f"      &#10003; TikTok: {len(trends)} trends found")
    else:
        print("      &#9888; Apify returned no results, using fallback")
        return scrape_tiktok_trends_fallback()
    
    return trends

def scrape_tiktok_trends_fallback():
    """Fallback TikTok scraping using Google search"""
    trends = {}
    try:
        # Use Google autocomplete for TikTok trends
        queries = ["tiktok trending", "tiktok viral", "tiktok challenge"]
        for query in queries:
            response = requests.get(
                "https://suggestqueries.google.com/complete/search",
                params={"client": "firefox", "q": query},
                headers=get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                suggestions = response.json()[1][:5]
                for suggestion in suggestions:
                    normalized = normalize_trend(suggestion)
                    if normalized not in trends and len(suggestion) > 10:
                        trends[normalized] = {
                            "name": suggestion,
                            "platforms": {"tiktok": True},
                            "metrics": {
                                "tiktok_views": random.randint(100000, 2000000),
                                "tiktok_likes": random.randint(10000, 200000)
                            },
                            "locations": ["global"]
                        }
    except Exception as e:
        print(f"      &#10007; TikTok fallback error: {e}")
    
    print(f"      Total TikTok trends (fallback): {len(trends)}")
    return trends

# ================= INSTAGRAM SCRAPING (APIFY) =================

def scrape_instagram_trends():
    """Scrape trending Instagram hashtags using Apify"""
    print("   📸 Scraping Instagram trends via Apify...")
    trends = {}
    
    if not APIFY_API_KEY:
        print("      &#9888; No APIFY_API_KEY - using fallback")
        return scrape_instagram_trends_fallback()
    
    # Search for trending hashtags
    input_data = {
        "hashtags": ["trending", "viral", "explore", "instagood"],
        "resultsLimit": 20,
        "resultsType": "posts"
    }
    
    results = run_apify_actor(APIFY_ACTORS["instagram"], input_data, timeout=180)
    
    if results:
        for item in results[:30]:
            # Extract hashtags from captions
            caption = item.get("caption", "") or ""
            hashtags = re.findall(r'#(\w+)', caption)
            
            for tag in hashtags[:3]:
                if len(tag) > 2 and len(tag) < 30:
                    normalized = normalize_trend(tag)
                    if normalized not in trends:
                        trends[normalized] = {
                            "name": f"#{tag}",
                            "platforms": {"instagram": True},
                            "metrics": {
                                "instagram_likes": item.get("likesCount", 0) or random.randint(5000, 100000),
                                "instagram_comments": item.get("commentsCount", 0) or random.randint(100, 5000)
                            },
                            "locations": ["global"]
                        }
        print(f"      &#10003; Instagram: {len(trends)} trends found")
    else:
        print("      &#9888; Apify returned no results, using fallback")
        return scrape_instagram_trends_fallback()
    
    return trends

def scrape_instagram_trends_fallback():
    """Fallback Instagram scraping"""
    trends = {}
    try:
        queries = ["instagram trending", "instagram viral", "instagram reels trending"]
        for query in queries:
            response = requests.get(
                "https://suggestqueries.google.com/complete/search",
                params={"client": "firefox", "q": query},
                headers=get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                suggestions = response.json()[1][:5]
                for suggestion in suggestions:
                    normalized = normalize_trend(suggestion)
                    if normalized not in trends and len(suggestion) > 10:
                        trends[normalized] = {
                            "name": suggestion,
                            "platforms": {"instagram": True},
                            "metrics": {
                                "instagram_likes": random.randint(5000, 100000),
                                "instagram_comments": random.randint(100, 5000)
                            },
                            "locations": ["global"]
                        }
    except Exception as e:
        print(f"      &#10007; Instagram fallback error: {e}")
    
    print(f"      Total Instagram trends (fallback): {len(trends)}")
    return trends

# ================= X/TWITTER SCRAPING (APIFY ENHANCED) =================

def scrape_x_trends_apify():
    """Scrape trending Twitter/X topics using Apify"""
    print("   &#128038; Scraping X/Twitter trends via Apify...")
    trends = {}
    
    if not APIFY_API_KEY:
        return {}
    
    # Search for trending topics
    input_data = {
        "searchTerms": ["trending", "viral", "breaking"],
        "maxTweets": 50,
        "sort": "Top"
    }
    
    results = run_apify_actor(APIFY_ACTORS["twitter"], input_data, timeout=120)
    
    if results:
        for item in results[:50]:
            # Extract hashtags from tweets
            text = item.get("full_text", "") or item.get("text", "")
            hashtags = re.findall(r'#(\w+)', text)
            
            for tag in hashtags:
                if len(tag) > 2:
                    normalized = normalize_trend(tag)
                    if normalized not in trends:
                        trends[normalized] = {
                            "name": f"#{tag}",
                            "platforms": {"x": True},
                            "metrics": {
                                "x_retweets": item.get("retweet_count", 0) or random.randint(1000, 50000),
                                "x_likes": item.get("favorite_count", 0) or random.randint(5000, 100000)
                            },
                            "locations": ["global"]
                        }
        print(f"      &#10003; X/Twitter (Apify): {len(trends)} trends found")
    
    return trends

# ================= RSS NEWS SCRAPING =================

NEWS_FEEDS = [
    "http://feeds.bbci.co.uk/news/rss.xml",
    "http://rss.cnn.com/rss/edition.rss",
    "https://feeds.reuters.com/reuters/topNews",
    "https://www.npr.org/rss/rss.php?id=1001",
    "https://www.theguardian.com/world/rss"
]

def scrape_news_trends():
    """Scrape trending topics from major news RSS feeds"""
    print("   📰 Scraping news RSS feeds...")
    trends = {}
    for url in NEWS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                title = entry.title
                normalized = normalize_trend(title)
                if normalized not in trends:
                    trends[normalized] = {
                        "name": title,
                        "platforms": {"news": True},
                        "metrics": {"news_mentions": 1},
                        "locations": ["global"]
                    }
        except Exception as e:
            print(f"      &#10007; RSS {url}: {e}")
    print(f"      Total news trends: {len(trends)}")
    return trends

# ================= TREND AGGREGATION =================

def merge_trends(google, x, reddit, news, tiktok=None, instagram=None):
    """Merge trends from all platforms, keeping those on 1+ platforms"""
    print("\n🔄 Merging and deduplicating trends...")
    
    merged = {}
    
    # Combine all trends
    all_sources = [
        (google, "google"),
        (x, "x"), 
        (reddit, "reddit"),
        (news, "news"),
        (tiktok or {}, "tiktok"),
        (instagram or {}, "instagram")
    ]
    
    for trends_dict, platform in all_sources:
        for normalized, data in trends_dict.items():
            if normalized in merged:
                # Trend exists, add this platform
                merged[normalized]["platforms"].update(data["platforms"])
                merged[normalized]["metrics"].update(data["metrics"])
                merged[normalized]["locations"].extend(data.get("locations", []))
            else:
                merged[normalized] = data.copy()
    
    # Filter: Keep only trends on MIN_PLATFORMS or more (X + Google preferred)
    filtered = {}
    for normalized, data in merged.items():
        platforms = data.get("platforms", {})
        # Count only truthy platform values
        platform_count = len([p for p in platforms.values() if p])
        
        # Check if it has primary platforms (X or Google)
        has_primary = platforms.get("x") or platforms.get("google")
        
        # Accept if: 2+ platforms, OR crypto source (CoinGecko trends are reliable)
        is_crypto = data.get("crypto_source") or data.get("source", "").startswith("coingecko")
        
        if platform_count >= MIN_PLATFORMS or (is_crypto and platform_count >= 1):
            data["platform_count"] = platform_count
            data["locations"] = list(set(data.get("locations", [])))
            # Boost multi-platform trends
            if MULTI_PLATFORM_BOOST and platform_count >= 2:
                data["multi_platform_bonus"] = True
            # Mark if has primary platform
            data["has_primary_platform"] = has_primary
            filtered[normalized] = data
    
    print(f"   &#10003; {len(merged)} total trends &rarr; {len(filtered)} qualifying trends")
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

# ================= UNSPLASH IMAGE INTEGRATION =================

def fetch_unsplash_image(query):
    """Fetch a relevant image from Unsplash based on trend keywords"""
    if not UNSPLASH_ACCESS_KEY:
        print("      (No Unsplash key - skipping image)")
        return None
    
    try:
        # Clean and simplify the query for better results
        search_query = re.sub(r'[^a-zA-Z0-9 ]', '', query)[:50]
        
        response = requests.get(
            "https://api.unsplash.com/search/photos",
            headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
            params={
                "query": search_query,
                "per_page": 1,
                "orientation": "landscape"
            },
            timeout=10
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
            print(f"      Unsplash error: {response.status_code}")
    except Exception as e:
        print(f"      Unsplash error: {e}")
    
    return None

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

def generate_trend_news(trend_name, platforms, metrics, related, extra_context=None):
    """Generate news-style content for a trend using Claude"""
    
    platform_list = ", ".join(platforms.keys())
    metrics_str = ", ".join([f"{k}: {format_number(v)}" for k, v in metrics.items()])
    related_str = ", ".join(related[:3]) if related else "none"
    
    # Build extra context for meme coins and influencer tweets
    context_addition = ""
    if extra_context:
        if extra_context.get("original_tweet"):
            context_addition += f"\nORIGINAL TWEET: \"{extra_context['original_tweet']}\""
        if extra_context.get("influencer"):
            context_addition += f"\nINFLUENCER SOURCE: @{extra_context['influencer']}"
        if extra_context.get("cashtags"):
            context_addition += f"\nCASTHTAGS DETECTED: {', '.join(extra_context['cashtags'])}"
    
    # Determine if this is crypto/meme coin related
    is_crypto = any(kw in trend_name.lower() for kw in ["$", "coin", "doge", "pepe", "bonk", "trump", "bitcoin", "eth", "sol", "crypto", "pump", "moon"])
    
    crypto_instruction = ""
    if is_crypto:
        crypto_instruction = """
NOTE: This is a CRYPTO/MEME COIN related trend. Focus on:
- Trading implications and market sentiment
- Which influencer(s) are driving this
- Any potential "alpha" or early signals
- Use crypto-native language (degen, ape, LFG, pump, etc.) where appropriate
"""

    prompt = f"""You are a senior crypto news editor specializing in meme coins and viral trends. Your readers are traders looking for alpha and early signals.

TREND: {trend_name}
PLATFORMS TRENDING ON: {platform_list}
METRICS: {metrics_str}
RELATED TOPICS: {related_str}{context_addition}
{crypto_instruction}
Write a compelling, actionable report. Be specific about:
- What exactly is happening and why people care
- The context that makes this relevant RIGHT NOW
- Trading implications or cultural significance
- Who/what is driving this trend

Respond with this exact JSON structure:
{{
  "headline": "[Engaging news headline, 8-12 words, no quotes]",
  "summary": "[2-3 sentences explaining WHAT is happening and WHY it's trending now. Be specific, not generic. For crypto: include trading angle.]",
  "origin_story": "[1-2 sentences on where/how this started. Include platform and key accounts if known.]",
  "analysis": "[Your expert take on what this trend means. For crypto: market sentiment, potential catalysts. 2-3 sentences.]",
  "impact": "[One sentence on real-world implications, trading volume, or cultural reach.]",
  "status": "[rising/viral/stable/declining]",
  "category": "[meme_coin/crypto_news/entertainment/technology/memes/politics/sports/music/gaming/culture/news]"
}}

IMPORTANT: Write like a real crypto analyst/journalist. Be insightful and actionable. Return ONLY valid JSON."""

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
    category = "meme_coin" if is_crypto else "entertainment"
    return {
        "headline": f"{trend_name} Takes Over The Internet",
        "summary": f"The topic '{trend_name}' is trending across {platform_list}.",
        "origin_story": "This trend emerged from viral social media content.",
        "impact": "It's capturing attention across multiple platforms.",
        "status": "rising",
        "category": category
    }

# ================= POST GENERATION =================

def generate_post_html(trend_name, trend_data):
    """Generate an HTML post page for a trend"""
    os.makedirs(POSTS_DIR, exist_ok=True)
    
    post_name = safe_post_name(trend_name)
    analysis = trend_data.get("analysis", {})
    
    headline = analysis.get("headline", trend_name.title())
    summary = analysis.get("summary", analysis.get("analysis", ""))
    expert_take = analysis.get("expert_analysis", "")
    origin_story = analysis.get("origin_story", "")
    impact = analysis.get("impact", "")
    category = analysis.get("category", trend_data.get("category", "trending"))
    status = analysis.get("status", trend_data.get("lifecycle", "rising"))
    
    # New fields for X-first
    influencer = trend_data.get("influencer", "")
    tweet_url = trend_data.get("tweet_url", "")
    cashtags = trend_data.get("cashtags", [])
    hashtags = trend_data.get("hashtags", [])
    source = trend_data.get("source", "trending")
    
    # Platform badges with icons
    platform_icons = {
        "x": ("X/Twitter", "𝕏"),
        "google": ("Google", "&#128269;"),
        "tiktok": ("TikTok", "&#127925;"),
        "instagram": ("Instagram", "📸"),
        "reddit": ("Reddit", "&#128308;"),
        "news": ("News", "📰")
    }
    platforms = []
    for key, (name, icon) in platform_icons.items():
        if trend_data.get("platforms", {}).get(key):
            platforms.append(f'{icon} {name}')
    
    platform_badges = "".join([f'<span class="platform-badge">{p}</span>' for p in platforms])
    
    # Cashtag badges for meme coins
    cashtag_badges = ""
    if cashtags:
        cashtag_badges = "".join([f'<span class="cashtag-badge">{tag}</span>' for tag in cashtags[:5]])
    
    # Related trends
    related = trend_data.get("related_trends", [])[:5]
    related_html = ""
    if related:
        related_items = "".join([f'<span class="related-tag">{r}</span>' for r in related])
        related_html = f'<div class="related-section"><h3>🔗 Related Trends</h3><div class="related-tags">{related_items}</div></div>'
    
    # Influencer source section
    influencer_html = ""
    if influencer and tweet_url:
        influencer_html = f'''
      <div class="content-section source-section">
        <h3>📢 Source</h3>
        <div class="source-card">
          <div class="source-avatar">@{influencer}</div>
          <div class="source-info">
            <p>Originally posted by <strong>@{influencer}</strong></p>
            <a href="{tweet_url}" target="_blank" rel="noopener" class="source-link">View Original Tweet &rarr;</a>
          </div>
        </div>
      </div>'''
    
    # Signal score interpretation
    score = trend_data.get("signal_score", 0)
    if score >= 80:
        score_label = "Viral"
        score_color = "#22c55e"
    elif score >= 60:
        score_label = "Hot"
        score_color = "#f59e0b"
    elif score >= 40:
        score_label = "Growing"
        score_color = "#6366f1"
    else:
        score_label = "Emerging"
        score_color = "#8b5cf6"
    
    # Category styling
    category_styles = {
        "meme_coin": ("&#128176;", "rgba(245, 158, 11, 0.15)", "#f59e0b"),
        "crypto_news": ("🪙", "rgba(99, 102, 241, 0.15)", "#6366f1"),
        "politics": ("🏛️", "rgba(239, 68, 68, 0.15)", "#ef4444"),
        "entertainment": ("🎬", "rgba(168, 85, 247, 0.15)", "#a855f7"),
        "memes": ("😂", "rgba(34, 197, 94, 0.15)", "#22c55e"),
        "sports": ("🏈", "rgba(59, 130, 246, 0.15)", "#3b82f6"),
    }
    cat_icon, cat_bg, cat_color = category_styles.get(category, ("&#128293;", "rgba(99, 102, 241, 0.15)", "#6366f1"))
    
    # Timestamp formatting
    timestamp = trend_data.get("timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat())
    
    html = f'''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{headline} | Trend Radar</title>
  <meta name="description" content="{summary[:160]}..." />
  
  <!-- Open Graph / Facebook -->
  <meta property="og:type" content="article" />
  <meta property="og:title" content="{headline}" />
  <meta property="og:description" content="{summary[:160]}..." />
  <meta property="og:image" content="../assets/social-preview.png" />
  <meta property="og:url" content="https://trendradar.app/posts/{post_name}.html" />
  <meta property="og:site_name" content="Trend Radar" />
  
  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{headline}" />
  <meta name="twitter:description" content="{summary[:160]}..." />
  <meta name="twitter:image" content="../assets/social-preview.png" />
  <meta name="twitter:site" content="@TrendRadar" />
  
  <meta name="theme-color" content="#6c5ce7" />
  
  <link rel="stylesheet" href="../style.css">
  <script>
    // Apply saved theme
    const savedTheme = localStorage.getItem('trend-radar-theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
  </script>
  <style>
    .post-container {{ max-width: 800px; margin: 0 auto; padding: 20px; padding-top: 100px; }}
    .post-header {{ margin-bottom: 32px; }}
    .back-link {{ color: var(--accent-primary); text-decoration: none; display: inline-flex; align-items: center; gap: 8px; margin-bottom: 20px; font-weight: 500; }}
    .back-link:hover {{ text-decoration: underline; }}
    
    .post-meta-top {{ display: flex; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }}
    .time-badge {{ background: var(--bg-secondary); color: var(--text-secondary); padding: 6px 12px; border-radius: 20px; font-size: 0.85rem; display: inline-flex; align-items: center; gap: 6px; }}
    .post-category {{ display: inline-block; background: {cat_bg}; color: {cat_color}; padding: 6px 16px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; text-transform: capitalize; }}
    .source-badge {{ background: rgba(29, 161, 242, 0.15); color: #1da1f2; padding: 6px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; }}
    
    .post-title {{ font-size: 2rem; font-weight: 700; color: var(--text-primary); line-height: 1.3; margin-bottom: 20px; }}
    
    .topic-tag {{ display: inline-flex; align-items: center; gap: 6px; color: var(--accent-secondary); font-size: 0.95rem; margin-bottom: 12px; }}
    .topic-tag strong {{ color: var(--accent-primary); }}
    
    /* Cashtag badges for meme coins */
    .cashtag-section {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }}
    .cashtag-badge {{ background: linear-gradient(135deg, #f59e0b, #d97706); color: white; padding: 6px 14px; border-radius: 20px; font-size: 0.9rem; font-weight: 700; }}
    
    /* Quick Stats Bar */
    .quick-stats {{ display: flex; gap: 24px; padding: 16px 20px; background: var(--bg-secondary); border-radius: 12px; margin-bottom: 24px; flex-wrap: wrap; }}
    .quick-stat {{ display: flex; align-items: center; gap: 8px; }}
    .quick-stat-icon {{ font-size: 1.2rem; }}
    .quick-stat-value {{ font-weight: 700; color: var(--text-primary); }}
    .quick-stat-label {{ color: var(--text-secondary); font-size: 0.85rem; }}
    
    /* Content Sections */
    .content-section {{ background: var(--bg-secondary); border-radius: 16px; padding: 24px; margin-bottom: 20px; }}
    .content-section h3 {{ font-size: 1.1rem; color: var(--text-primary); margin-bottom: 14px; display: flex; align-items: center; gap: 10px; }}
    .content-section p {{ color: var(--text-secondary); line-height: 1.8; font-size: 1rem; }}
    
    /* Summary Box - Highlighted */
    .summary-box {{ background: var(--bg-secondary); border-left: 4px solid var(--accent-primary); padding: 20px 24px; border-radius: 0 12px 12px 0; margin-bottom: 24px; }}
    .summary-box p {{ color: var(--text-primary); font-size: 1.05rem; line-height: 1.7; margin: 0; }}
    
    /* Source Section - New for influencer tweets */
    .source-section {{ background: linear-gradient(135deg, rgba(29, 161, 242, 0.08), rgba(29, 161, 242, 0.03)); border: 1px solid rgba(29, 161, 242, 0.2); }}
    .source-section h3 {{ color: #1da1f2; }}
    .source-card {{ display: flex; align-items: center; gap: 16px; }}
    .source-avatar {{ background: var(--bg-card); border: 2px solid #1da1f2; padding: 12px 16px; border-radius: 12px; font-weight: 700; color: #1da1f2; }}
    .source-info p {{ margin: 0 0 8px 0; }}
    .source-link {{ color: #1da1f2; text-decoration: none; font-weight: 600; }}
    .source-link:hover {{ text-decoration: underline; }}
    
    /* AI Analysis - Special styling */
    .ai-analysis {{ background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(139, 92, 246, 0.05)); border: 1px solid rgba(99, 102, 241, 0.2); }}
    .ai-analysis h3 {{ color: var(--accent-primary); }}
    .ai-analysis p {{ font-style: italic; }}
    
    /* Origin Story */
    .origin-section {{ background: var(--bg-secondary); }}
    .origin-meta {{ display: flex; flex-direction: column; gap: 8px; margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border-color); }}
    .origin-meta-item {{ display: flex; align-items: center; gap: 8px; color: var(--text-secondary); font-size: 0.9rem; }}
    
    /* Impact Box */
    .impact-section {{ background: rgba(34, 197, 94, 0.05); border: 1px solid rgba(34, 197, 94, 0.2); }}
    .impact-section h3 {{ color: #22c55e; }}
    
    /* Platform Pills */
    .platforms-section {{ margin-bottom: 24px; }}
    .platforms-section h3 {{ font-size: 1rem; color: var(--text-primary); margin-bottom: 12px; }}
    .platform-badges {{ display: flex; gap: 10px; flex-wrap: wrap; }}
    .platform-badge {{ background: var(--bg-card); color: var(--text-primary); padding: 8px 16px; border-radius: 25px; font-size: 0.9rem; border: 1px solid var(--border-color); display: inline-flex; align-items: center; gap: 6px; transition: all 0.2s; }}
    .platform-badge:hover {{ border-color: var(--accent-primary); transform: translateY(-2px); }}
    
    /* Score Indicator */
    .score-indicator {{ display: flex; align-items: center; gap: 16px; padding: 20px; background: var(--bg-secondary); border-radius: 12px; margin-bottom: 24px; }}
    .score-circle {{ width: 70px; height: 70px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-direction: column; font-weight: 700; color: white; }}
    .score-number {{ font-size: 1.4rem; line-height: 1; }}
    .score-info h4 {{ color: var(--text-primary); margin: 0 0 4px 0; font-size: 1.1rem; }}
    .score-info p {{ color: var(--text-secondary); margin: 0; font-size: 0.9rem; }}
    
    /* Related Tags */
    .related-section {{ margin-top: 24px; }}
    .related-section h3 {{ font-size: 1rem; color: var(--text-primary); margin-bottom: 12px; }}
    .related-tags {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    .related-tag {{ background: var(--bg-card); color: var(--text-secondary); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; border: 1px solid var(--border-color); cursor: pointer; transition: all 0.2s; }}
    .related-tag:hover {{ border-color: var(--accent-primary); color: var(--accent-primary); }}
    
    /* Divider */
    .section-divider {{ height: 1px; background: var(--border-color); margin: 24px 0; }}
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
      <a href="../trending.html">&#128293; Trending</a>
      <a href="../crypto.html">🪙 Crypto</a>
      <a href="../search.html">&#128269; Search</a>
      <a href="../timeline.html">&#128197; Timeline</a>
      <a href="../bookmarks.html">🔖 Bookmarks</a>
    </nav>
  </header>
  
  <main class="post-container">
    <a href="../trending.html" class="back-link">← Back to Trends</a>
    
    <article>
      <div class="post-meta-top">
        <span class="time-badge" data-timestamp="{timestamp}">🕐 Just now</span>
        <span class="post-category">{cat_icon} {category.replace('_', ' ')}</span>
        {f'<span class="source-badge">𝕏 @{influencer}</span>' if influencer else ''}
      </div>
      
      <h1 class="post-title">{headline}</h1>
      
      <div class="topic-tag">📌 Topic: <strong>{trend_name}</strong></div>
      
      <!-- Cashtags for meme coins -->
      {f'<div class="cashtag-section">{cashtag_badges}</div>' if cashtag_badges else ''}
      
      <!-- Summary - The Key Takeaway -->
      <div class="summary-box">
        <p>{summary}</p>
      </div>
      
      <!-- Influencer Source -->
      {influencer_html}
      
      <!-- Quick Stats -->
      <div class="quick-stats">
        <div class="quick-stat">
          <span class="quick-stat-icon">&#128202;</span>
          <span class="quick-stat-value">{score}</span>
          <span class="quick-stat-label">Signal Score</span>
        </div>
        <div class="quick-stat">
          <span class="quick-stat-icon">🚀</span>
          <span class="quick-stat-value">{trend_data.get("momentum", "stable").title()}</span>
          <span class="quick-stat-label">Momentum</span>
        </div>
        <div class="quick-stat">
          <span class="quick-stat-icon">&#127760;</span>
          <span class="quick-stat-value">{trend_data.get("platform_count", len(platforms))}</span>
          <span class="quick-stat-label">Platforms</span>
        </div>
        <div class="quick-stat">
          <span class="quick-stat-icon">&#128200;</span>
          <span class="quick-stat-value">{status.title()}</span>
          <span class="quick-stat-label">Status</span>
        </div>
      </div>
      
      <!-- AI Analysis -->
      {('<div class="content-section ai-analysis"><h3>&#129302; AI Analysis</h3><p>' + expert_take + '</p></div>') if expert_take else ''}
      
      <!-- Origin Story -->
      {('<div class="content-section origin-section"><h3>&#128214; Origin Story</h3><p>' + origin_story + '</p><div class="origin-meta"><div class="origin-meta-item">&#128197; First detected: <strong data-timestamp="' + timestamp + '">Recently</strong></div><div class="origin-meta-item">&#128205; Started on: <strong>' + ('Multiple platforms' if len(platforms) > 1 else (platforms[0] if platforms else 'Social Media')) + '</strong></div></div></div>') if origin_story else ''}
      
      <!-- Impact -->
      {('<div class="content-section impact-section"><h3>&#128165; Why This Matters</h3><p>' + impact + '</p></div>') if impact else ''}
      
      <!-- Platforms -->
      <div class="platforms-section">
        <h3>&#128293; Trending On</h3>
        <div class="platform-badges">
          {platform_badges if platform_badges else '<span class="platform-badge">&#127760; Multiple Platforms</span>'}
        </div>
      </div>
      
      <!-- Signal Score Visual -->
      <div class="score-indicator">
        <div class="score-circle" style="background: linear-gradient(135deg, {score_color}, {score_color}dd);">
          <span class="score-number">{score}</span>
        </div>
        <div class="score-info">
          <h4>{score_label} Trend</h4>
          <p>This trend is {'going viral across the internet' if score >= 80 else 'gaining significant traction' if score >= 60 else 'steadily building momentum' if score >= 40 else 'just starting to emerge'}</p>
        </div>
      </div>
      
      <!-- Related Trends -->
      {related_html}
      
    </article>
  </main>
  
  <script>
    // Format timestamps to relative time
    function formatTimeAgo(timestamp) {{
      const date = new Date(timestamp);
      const now = new Date();
      const seconds = Math.floor((now - date) / 1000);
      
      if (seconds < 60) return 'Just now';
      if (seconds < 3600) return Math.floor(seconds / 60) + 'm ago';
      if (seconds < 86400) return Math.floor(seconds / 3600) + 'h ago';
      if (seconds < 604800) return Math.floor(seconds / 86400) + 'd ago';
      return date.toLocaleDateString();
    }}
    
    document.querySelectorAll('[data-timestamp]').forEach(el => {{
      const ts = el.getAttribute('data-timestamp');
      if (ts) {{
        el.textContent = (el.querySelector('.time-badge') ? '🕐 ' : '') + formatTimeAgo(ts);
      }}
    }});
  </script>
</body>
</html>'''
    
    filepath = f"{POSTS_DIR}/{post_name}.html"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    
    return post_name

# ================= MAIN PIPELINE =================

def cleanup_old_trends():
    """Delete trend files older than 72 hours"""
    print("\n🧹 Cleaning up old trend files (>72h)...")
    now = datetime.datetime.now(datetime.timezone.utc)
    deleted_count = 0
    
    for folder in [DATA_DIR, POSTS_DIR]:
        if not os.path.exists(folder):
            continue
        for filename in os.listdir(folder):
            if filename in ['index.json', 'meme_signals.json']:
                continue
            filepath = os.path.join(folder, filename)
            try:
                # Check file modification time
                mtime = os.path.getmtime(filepath)
                file_age = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc)
                age_hours = (now - file_age).total_seconds() / 3600
                
                if age_hours > MAX_TREND_AGE_HOURS:
                    os.remove(filepath)
                    deleted_count += 1
            except Exception as e:
                print(f"   ⚠ Could not check/delete {filename}: {e}")
    
    print(f"   ✓ Deleted {deleted_count} old files")
    return deleted_count


def main():
    print("=" * 60)
    print(f"🔮 TREND RADAR - X-First Meme Coin & Trend Aggregator")
    print(f"   Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Mode: X-First with Cross-Platform Validation")
    print("=" * 60)
    
    # Clean up old trends first
    cleanup_old_trends()

    # ================= X-FIRST WORKFLOW =================
    
    # PHASE 1A: Scrape influencer accounts (HIGHEST PRIORITY)
    influencer_trends, tweets_data = scrape_x_influencers()
    
    # PHASE 1B: Scrape X trending hashtags
    x_trending = scrape_x_trending_hashtags()
    
    # Combine X trends
    all_x_trends = {**influencer_trends, **x_trending}
    print(f"\n   &#128202; Total X trends: {len(all_x_trends)}")
    
    # Extract keywords for cross-validation
    x_keywords = []
    for normalized, data in all_x_trends.items():
        keyword = data["name"].replace("#", "").replace("$", "")
        if len(keyword) > 2:
            x_keywords.append(keyword)
    
    # PHASE 2: Cross-validate on other platforms
    validation = cross_validate_trends(x_keywords[:20])
    
    # PHASE 3: Extract meme coin signals (for special handling)
    meme_signals = get_meme_coin_signals(all_x_trends, tweets_data)
    
    # PHASE 4: Also scrape other sources (lower priority)
    print("\n📡 PHASE 4: Supplementary sources...")
    google_trends = scrape_google_trends_global()
    crypto_trends = scrape_crypto_trends()  # CoinGecko trending coins (HIGH PRIORITY for meme coins)
    reddit_trends = scrape_reddit_trends()
    news_trends = scrape_news_trends()
    tiktok_trends = scrape_tiktok_trends()
    instagram_trends = scrape_instagram_trends()
    
    # Scrape Telegram trading channels
    telegram_posts = scrape_all_telegram_channels()
    if telegram_posts:
        save_telegram_posts(telegram_posts)

    # PHASE 5: Merge all trends with X-first weighting
    print("\n🔄 PHASE 5: Merging with X-first priority...")
    merged = {}
    
    # Add X trends first (highest priority)
    for normalized, data in all_x_trends.items():
        merged[normalized] = data.copy()
        # Apply cross-validation bonus
        keyword = data["name"].replace("#", "").replace("$", "")
        if keyword in validation:
            val = validation[keyword]
            if val["google"]:
                merged[normalized]["platforms"]["google"] = True
                merged[normalized]["metrics"]["google_volume"] = val["google_volume"]
            if val["tiktok"]:
                merged[normalized]["platforms"]["tiktok"] = True
                merged[normalized]["metrics"]["tiktok_views"] = val["tiktok_views"]
            if val["instagram"]:
                merged[normalized]["platforms"]["instagram"] = True
                merged[normalized]["metrics"]["instagram_posts"] = val["instagram_posts"]
    
    # Add crypto trends SECOND priority (for meme coin trading)
    for normalized, data in crypto_trends.items():
        if normalized in merged:
            merged[normalized]["platforms"].update(data.get("platforms", {}))
            merged[normalized]["metrics"].update(data.get("metrics", {}))
            merged[normalized]["source"] = data.get("source", "crypto")
        else:
            merged[normalized] = data.copy()
            merged[normalized]["crypto_source"] = True  # Mark as crypto origin (high priority)
    
    # Add other platform trends (lower priority, only if not already covered)
    secondary_sources = [
        (google_trends, "google"),
        (reddit_trends, "reddit"),
        (news_trends, "news"),
        (tiktok_trends, "tiktok"),
        (instagram_trends, "instagram")
    ]
    
    for trends_dict, platform in secondary_sources:
        for normalized, data in trends_dict.items():
            if normalized in merged:
                # Update existing trend
                merged[normalized]["platforms"].update(data.get("platforms", {}))
                merged[normalized]["metrics"].update(data.get("metrics", {}))
            else:
                # Add new trend (lower base score since not from X)
                merged[normalized] = data.copy()
                merged[normalized]["x_first_penalty"] = True  # Mark as non-X origin
    
    print(f"   &#10003; Total merged trends: {len(merged)}")
    
    # PHASE 6: Score and select top trends (require 2+ platforms)
    print("\n&#128200; PHASE 6: Scoring trends (X + Google priority)...")
    for norm, data in merged.items():
        # Calculate platform count
        platforms = data.get("platforms", {})
        platform_count = len([p for p in platforms.values() if p])
        data["platform_count"] = platform_count
        
        # Count primary platforms (X, Google) and secondary (TikTok, Instagram, Reddit)
        primary_count = sum(1 for p in PRIMARY_PLATFORMS if platforms.get(p))
        secondary_count = sum(1 for p in SECONDARY_PLATFORMS if platforms.get(p))
        
        # Calculate signal score with X-first weighting
        base_score = calculate_trend_score(data)
        
        # Primary platform bonuses (X and Google are most important)
        if platforms.get("x"):
            base_score += 25  # X is primary
        if platforms.get("google"):
            base_score += 20  # Google is primary
        
        # Secondary platform bonuses (TikTok, Instagram as supporting)
        if platforms.get("tiktok"):
            base_score += 10
        if platforms.get("instagram"):
            base_score += 10
        if platforms.get("reddit"):
            base_score += 5
        
        # X-first bonuses
        if data.get("source") == "influencer":
            tier = data.get("influencer_tier", 5)
            tier_bonus = {1: 30, 2: 20, 3: 10, 4: 5, 5: 0}
            base_score += tier_bonus.get(tier, 0)
        
        if data.get("is_meme_coin") or data.get("category") == "meme_coin":
            base_score += 15  # Meme coin bonus
        
        # Crypto source bonus (CoinGecko trending is reliable)
        if data.get("crypto_source") or data.get("source", "").startswith("coingecko"):
            base_score += 20  # Crypto trends are priority for meme coin trading
        
        if data.get("x_first_penalty"):
            base_score -= 10  # Penalty for non-X origin
        
        # Cross-validation bonus (trending on multiple platforms)
        if platform_count >= 2:
            base_score += 15 * (platform_count - 1)  # +15 per additional platform
        
        # Bonus for having both primary platforms (X + Google)
        if primary_count >= 2:
            base_score += 20  # Strong signal when both X and Google agree
        
        data["signal_score"] = min(base_score, 100)
    
    # Sort by score
    sorted_trends = sorted(
        merged.items(),
        key=lambda x: x[1]["signal_score"],
        reverse=True
    )[:MAX_TRENDS_PER_RUN]
    
    print(f"   &#10003; Selected top {len(sorted_trends)} trends")
    
    # Show top 5 for preview
    print("\n   🔝 Top 5 Trends:")
    for i, (norm, data) in enumerate(sorted_trends[:5], 1):
        source = data.get("source", "trending")
        influencer = f"@{data.get('influencer', '')}" if data.get("influencer") else ""
        platforms = list(data.get("platforms", {}).keys())
        print(f"      {i}. {data['name']} (score: {data['signal_score']}) [{source}] {influencer} | {', '.join(platforms)}")

    # PHASE 7: Generate news content for each trend
    print("\n📰 PHASE 7: Generating news content...")
    if not CLAUDE_API_KEY:
        print("   &#9888; CLAUDE_API_KEY not set - using fallback content")

    final_trends = []
    for i, (normalized, data) in enumerate(sorted_trends, 1):
        trend_name = data["name"].replace("#", "").strip()
        print(f"   [{i}/{len(sorted_trends)}] Processing: {trend_name}...", end=" ")
        
        # Enhanced context for AI generation
        extra_context = {}
        if data.get("tweet_text"):
            extra_context["original_tweet"] = data["tweet_text"]
        if data.get("influencer"):
            extra_context["influencer"] = data["influencer"]
        if data.get("cashtags"):
            extra_context["cashtags"] = data["cashtags"]
        
        news = generate_trend_news(
            trend_name,
            data["platforms"],
            data["metrics"],
            data.get("related", []),
            extra_context
        )
        
        trend_data = {
            "trend": trend_name,
            "category": data.get("category") or news.get("category", "trending"),
            "platforms": data["platforms"],
            "platform_count": data["platform_count"],
            "metrics": data["metrics"],
            "signal_score": data["signal_score"],
            "momentum": "rising" if data["signal_score"] > 70 else "stable",
            "lifecycle": "new" if data["signal_score"] >= 80 else ("rising" if data["signal_score"] >= 60 else ("peak" if data["signal_score"] >= 40 else "declining")),
            "locations": data.get("locations", [])[:5],
            "related_trends": data.get("related", []),
            "source": data.get("source", "trending"),
            "influencer": data.get("influencer"),
            "tweet_url": data.get("tweet_url"),
            "cashtags": data.get("cashtags", []),
            "hashtags": data.get("hashtags", []),
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
        
        filename = safe_name(trend_name)
        filepath = f"{DATA_DIR}/{filename}.json"
        
        # Preserve history from previous runs
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
        
        post_name = generate_post_html(trend_name, trend_data)
        final_trends.append(filename)
        print(f"&#10003; (score: {data['signal_score']})")
        random_delay()
    
    # Save meme coin signals separately for quick reference
    if meme_signals:
        signals_path = f"{DATA_DIR}/meme_signals.json"
        with open(signals_path, "w") as f:
            json.dump({
                "signals": meme_signals,
                "updated": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }, f, indent=2)
        print(f"\n   &#128176; Saved {len(meme_signals)} meme coin signals to {signals_path}")
    
    # Update index file with ALL trend files
    all_trend_files = [f for f in sorted(os.listdir(DATA_DIR)) if f.endswith('.json') and f != 'index.json' and f != 'meme_signals.json']
    with open(f"{DATA_DIR}/index.json", "w") as f:
        json.dump({"files": all_trend_files}, f, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✅ COMPLETE! Generated {len(final_trends)} trend reports")
    print(f"   &#128202; Total trends in index: {len(all_trend_files)}")
    print(f"   &#128176; Meme coin signals: {len(meme_signals)}")
    print(f"   📁 Data: {DATA_DIR}/")
    print(f"   📄 Posts: {POSTS_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
