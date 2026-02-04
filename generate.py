import os
import json
import datetime
import requests
from pytrends.request import TrendReq

# ================= CONFIG =================

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_MODEL = "claude-3-haiku-20240307"

DATA_DIR = "data"
TRACK_FILE = "tracked_trends.json"

ENABLE_AUTO_DISCOVERY = True
MAX_NEW_TRENDS_PER_RUN = 2
DISCOVERY_SCORE_THRESHOLD = 30

SEED_KEYWORDS = [
    "npc", "ai", "meme", "viral",
    "trend", "internet", "stream",
    "photo", "live"
]

HEADERS = {"User-Agent": "Mozilla/5.0"}
os.makedirs(DATA_DIR, exist_ok=True)

# ================= UTILS =================

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

def update_index_file(trends):
    files = [f"{safe_name(t)}.json" for t in trends]
    with open(f"{DATA_DIR}/index.json", "w") as f:
        json.dump({"files": files}, f, indent=2)

def check_url(url):
    try:
        return requests.get(url, headers=HEADERS, timeout=8).status_code == 200
    except:
        return False

# ================= SOCIAL PRESENCE =================

def get_social_presence(trend):
    tag = trend.replace(" ", "")
    return {
        "x": "high" if check_url(f"https://x.com/search?q={trend}") else "low",
        "tiktok": "high" if check_url(f"https://www.tiktok.com/tag/{tag}") else "low",
        "instagram": "high" if check_url(
            f"https://www.instagram.com/explore/tags/{tag}/"
        ) else "low"
    }

# ================= GOOGLE DISCOVERY =================

def google_autocomplete(seed):
    try:
        r = requests.get(
            "https://suggestqueries.google.com/complete/search",
            params={"client": "firefox", "q": seed},
            headers=HEADERS,
            timeout=8
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

def score_trend(t):
    score = 0
    if len(t.split()) >= 2:
        score += 10
    if any(w in t for w in ["npc", "ai", "meme", "viral", "stream", "photo"]):
        score += 20
    if len(t) < 35:
        score += 10
    return score

def discover_trends():
    c = set()
    for seed in SEED_KEYWORDS:
        for term in google_autocomplete(seed):
            if score_trend(term.lower()) >= DISCOVERY_SCORE_THRESHOLD:
                c.add(term.lower())
    for term in trending_searches():
        if score_trend(term.lower()) >= DISCOVERY_SCORE_THRESHOLD:
            c.add(term.lower())
    return list(c)

# ================= GOOGLE TRENDS =================

def get_google_trends(keyword):
    try:
        pytrends = TrendReq(hl="en-US", tz=360)
        pytrends.build_payload([keyword], timeframe="now 7-d")
        df = pytrends.interest_over_time()
        if df.empty:
            return {"interest_score": 0, "trend_direction": "flat"}

        v = df[keyword].tolist()
        latest, prev = v[-1], v[-2] if len(v) > 1 else v[-1]
        return {
            "interest_score": int(latest),
            "trend_direction": "rising" if latest > prev else "falling" if latest < prev else "flat"
        }
    except:
        return {"interest_score": 0, "trend_direction": "flat"}

# ================= SIGNAL & LIFECYCLE =================

def social_weight(v):
    return {"low": 5, "medium": 15, "high": 30}.get(v, 0)

def compute_signal(google, social):
    s = google.get("interest_score", 0)
    for v in social.values():
        s += social_weight(v)
    return min(s, 100)

def compute_momentum(history, current):
    if not history:
        return "0%"
    prev = history[-1]["signal_score"]
    if prev == 0:
        return "0%"
    return f"{((current - prev) / prev * 100):+.0f}%"

def determine_lifecycle(history, signal, momentum):
    if len(history) < 3:
        return "new"
    d = int(momentum.replace("%", ""))
    if signal < 20:
        return "dead"
    if d >= 10:
        return "rising"
    if -5 <= d <= 5:
        return "peak"
    if d <= -10:
        return "fading"
    return "stable"

# ================= MEME COIN =================

def search_meme_coin(trend):
    try:
        q = trend.split()[0]
        r = requests.get(
            f"https://api.dexscreener.com/latest/dex/search/?q={q}",
            timeout=8
        )
        p = r.json().get("pairs", [])
        if not p:
            return None
        t = p[0]
        return {
            "name": t["baseToken"]["name"],
            "symbol": t["baseToken"]["symbol"],
            "chain": t["chainId"],
            "liquidity_usd": t.get("liquidity", {}).get("usd"),
            "url": t.get("url")
        }
    except:
        return None

# ================= CLAUDE =================

def call_claude(prompt, max_tokens=350):
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
            timeout=25
        )
        return r.json()["content"][0]["text"]
    except:
        return None

def claude_analysis(trend, google, social, momentum, token):
    prompt = f"""
Trend: {trend}
Google: {google}
Social: {social}
Momentum: {momentum}
Token: {token}

Return JSON:
analysis, status, meme, token_relevant
"""
    try:
        return json.loads(call_claude(prompt))
    except:
        return {"analysis": "", "status": "stable", "meme": "", "token_relevant": False}

# ================= MAIN =================

def main():
    tracked = load_tracked_trends()
    all_trends = tracked.copy()

    if ENABLE_AUTO_DISCOVERY:
        for t in discover_trends():
            if t not in all_trends:
                all_trends.append(t)
                if len(all_trends) - len(tracked) >= MAX_NEW_TRENDS_PER_RUN:
                    break
        save_tracked_trends(all_trends)

    for trend in all_trends:
        path = f"{DATA_DIR}/{safe_name(trend)}.json"
        history = []

        if os.path.exists(path):
            with open(path) as f:
                history = json.load(f).get("history", [])

        google = get_google_trends(trend)
        social = get_social_presence(trend)
        signal = compute_signal(google, social)
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

        data = {
            "trend": trend,
            "google_trends": google,
            "social_presence": social,
            "signal_score": signal,
            "momentum": momentum,
            "lifecycle": lifecycle,
            "highlight": bool(token),
            "history": history,
            "analysis": analysis,
            "token": token,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    update_index_file(all_trends)

if __name__ == "__main__":
    main()
