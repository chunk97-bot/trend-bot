import os
import json
import datetime
import requests
from pytrends.request import TrendReq

# =====================================================
# CONFIG
# =====================================================

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_MODEL = "claude-3-haiku-20240307"

DATA_DIR = "data"
TRACK_FILE = "tracked_trends.json"

ENABLE_AUTO_DISCOVERY = True
MAX_NEW_TRENDS_PER_RUN = 2
DISCOVERY_SCORE_THRESHOLD = 30

SEED_KEYWORDS = [
    "npc", "ai", "meme", "viral",
    "trend", "internet", "live",
    "photo", "stream"
]

HEADERS = {"User-Agent": "Mozilla/5.0"}
os.makedirs(DATA_DIR, exist_ok=True)

# =====================================================
# UTIL
# =====================================================

def safe_name(t):
    return t.lower().replace(" ", "_").replace("-", "_")

def load_tracked_trends():
    if not os.path.exists(TRACK_FILE):
        return []
    with open(TRACK_FILE) as f:
        return json.load(f).get("trends", [])

def save_tracked_trends(trends):
    with open(TRACK_FILE, "w") as f:
        json.dump({"trends": sorted(set(trends))}, f, indent=2)

def check_url(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        return r.status_code == 200
    except:
        return False

# =====================================================
# SOCIAL PRESENCE (NO APIs)
# =====================================================

def get_social_presence(trend):
    tag = trend.replace(" ", "")
    return {
        "x": "high" if check_url(f"https://x.com/search?q={trend}") else "low",
        "tiktok": "high" if check_url(f"https://www.tiktok.com/tag/{tag}") else "low",
        "instagram": "high" if check_url(
            f"https://www.instagram.com/explore/tags/{tag}/"
        ) else "low"
    }

# =====================================================
# GOOGLE DISCOVERY
# =====================================================

def google_autocomplete(seed):
    try:
        r = requests.get(
            "https://suggestqueries.google.com/complete/search",
            params={"client": "firefox", "q": seed},
            headers=HEADERS,
            timeout=10
        )
        return r.json()[1][:10]
    except:
        return []

def trending_searches():
    try:
        pytrends = TrendReq(hl="en-US", tz=360)
        df = pytrends.trending_searches(pn="united_states")
        return df[0].tolist()[:10]
    except:
        return []

def discover_trends():
    candidates = set()
    for seed in SEED_KEYWORDS:
        for term in google_autocomplete(seed):
            candidates.add(term.lower())
    for term in trending_searches():
        candidates.add(term.lower())
    return [t for t in candidates if score_trend(t) >= DISCOVERY_SCORE_THRESHOLD]

# =====================================================
# GOOGLE TRENDS METRICS
# =====================================================

def get_google_trends(keyword):
    try:
        pytrends = TrendReq(hl="en-US", tz=360)
        pytrends.build_payload([keyword], timeframe="now 7-d")
        df = pytrends.interest_over_time()

        if df.empty:
            return {"interest_score": 0, "trend_direction": "flat"}

        values = df[keyword].tolist()
        latest = values[-1]
        prev = values[-2] if len(values) > 1 else latest

        direction = "flat"
        if latest > prev:
            direction = "rising"
        elif latest < prev:
            direction = "falling"

        return {
            "interest_score": int(latest),
            "trend_direction": direction
        }
    except:
        return {"interest_score": 0, "trend_direction": "flat"}

# =====================================================
# SCORING + MOMENTUM
# =====================================================

def score_trend(keyword):
    score = 0
    if len(keyword.split()) >= 2:
        score += 10
    if any(w in keyword for w in ["npc", "ai", "meme", "viral", "stream"]):
        score += 20
    if len(keyword) < 35:
        score += 10
    return score

def social_weight(level):
    return {"low": 5, "medium": 15, "high": 30}.get(level, 0)

def compute_signal_score(google, social):
    score = google.get("interest_score", 0)
    for v in social.values():
        score += social_weight(v)
    return min(score, 100)

def compute_momentum(history, current):
    if not history:
        return "0%"
    prev = history[-1]["signal_score"]
    if prev == 0:
        return "0%"
    delta = ((current - prev) / prev) * 100
    return f"{delta:+.0f}%"

def determine_lifecycle(history, signal_score, momentum):
    if len(history) < 3:
        return "new"
    try:
        delta = int(momentum.replace("%", ""))
    except:
        delta = 0

    if signal_score < 20:
        return "dead"
    if delta >= 10:
        return "rising"
    if -5 <= delta <= 5:
        return "peak"
    if delta <= -10:
        return "fading"
    return "stable"

# =====================================================
# MEME COIN (ONLY WHEN RELEVANT)
# =====================================================

def search_meme_coin(trend):
    try:
        q = trend.split()[0]
        r = requests.get(
            f"https://api.dexscreener.com/latest/dex/search/?q={q}",
            timeout=10
        )
        pairs = r.json().get("pairs", [])
        if not pairs:
            return None
        top = pairs[0]
        return {
            "name": top["baseToken"]["name"],
            "symbol": top["baseToken"]["symbol"],
            "chain": top["chainId"],
            "dex": top["dexId"],
            "liquidity_usd": top.get("liquidity", {}).get("usd"),
            "url": top.get("url")
        }
    except:
        return None

# =====================================================
# CLAUDE
# =====================================================

def call_claude(prompt, max_tokens=400):
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
    except:
        return None

def claude_analysis(trend, google, social, momentum, token):
    prompt = f"""
Trend: {trend}
Google Trends: {google}
Social Presence: {social}
Momentum: {momentum}
Token: {token}

Tasks:
1. Explain the trend (2–3 sentences)
2. Status (accelerating / stable / declining)
3. One meme line
4. Is the token genuinely related?

Respond ONLY as JSON:
analysis, status, meme, token_relevant
"""
    text = call_claude(prompt)
    try:
        return json.loads(text)
    except:
        return {
            "analysis": "Analysis unavailable.",
            "status": "stable",
            "meme": "",
            "token_relevant": False
        }

# =====================================================
# MAIN
# =====================================================

def main():
    tracked = load_tracked_trends()
    all_trends = tracked.copy()

    if ENABLE_AUTO_DISCOVERY:
        discovered = discover_trends()
        for t in discovered:
            if t not in all_trends:
                all_trends.append(t)
                if len(all_trends) - len(tracked) >= MAX_NEW_TRENDS_PER_RUN:
                    break
        save_tracked_trends(all_trends)

    for trend in all_trends:
        file = f"{DATA_DIR}/{safe_name(trend)}.json"
        history = []

        if os.path.exists(file):
            with open(file) as f:
                history = json.load(f).get("history", [])

        google = get_google_trends(trend)
        social = get_social_presence(trend)
        signal = compute_signal_score(google, social)
        momentum = compute_momentum(history, signal)

        history.append({
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "signal_score": signal
        })
        history = history[-12:]

        token_candidate = search_meme_coin(trend)
        analysis = claude_analysis(trend, google, social, momentum, token_candidate)
        token = token_candidate if analysis.get("token_relevant") else None

        lifecycle = determine_lifecycle(history, signal, momentum)
        highlight = True if token else False

        data = {
            "trend": trend,
            "google_trends": google,
            "social_presence": social,
            "signal_score": signal,
            "momentum": momentum,
            "lifecycle": lifecycle,
            "highlight": highlight,
            "history": history,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "analysis": analysis,
            "token": token
        }

        with open(file, "w") as f:
            json.dump(data, f, indent=2)

        print("Updated:", trend)

if __name__ == "__main__":
    main()
