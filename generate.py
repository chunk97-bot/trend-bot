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
    "trend", "internet", "new",
    "stream", "live"
]

os.makedirs(DATA_DIR, exist_ok=True)

# =====================================================
# UTIL: LOAD / SAVE TRACKED TRENDS
# =====================================================

def load_tracked_trends():
    if not os.path.exists(TRACK_FILE):
        return []
    with open(TRACK_FILE, "r") as f:
        return json.load(f).get("trends", [])

def save_tracked_trends(trends):
    with open(TRACK_FILE, "w") as f:
        json.dump({"trends": sorted(list(set(trends)))}, f, indent=2)

# =====================================================
# GOOGLE AUTOCOMPLETE (FREE)
# =====================================================

def google_autocomplete(seed):
    try:
        r = requests.get(
            "https://suggestqueries.google.com/complete/search",
            params={"client": "firefox", "q": seed},
            timeout=10
        )
        return r.json()[1][:10]
    except:
        return []

# =====================================================
# GOOGLE TRENDS DISCOVERY (FREE)
# =====================================================

def google_trends_discovery():
    try:
        pytrends = TrendReq(hl="en-US", tz=360)
        df = pytrends.trending_searches(pn="united_states")
        return df[0].tolist()[:10]
    except:
        return []

# =====================================================
# DISCOVER RAW CANDIDATES
# =====================================================

def discover_candidates():
    candidates = set()

    for seed in SEED_KEYWORDS:
        for term in google_autocomplete(seed):
            candidates.add(term.lower())

    for term in google_trends_discovery():
        candidates.add(term.lower())

    return list(candidates)

# =====================================================
# SCORE TREND (NO APIS)
# =====================================================

def score_trend(keyword):
    score = 0

    if len(keyword.split()) >= 2:
        score += 10

    if any(w in keyword for w in ["npc", "ai", "meme", "stream", "viral"]):
        score += 20

    if len(keyword) < 35:
        score += 10

    return score

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

        direction = (
            "rising" if latest > prev else
            "falling" if latest < prev else
            "flat"
        )

        return {
            "interest_score": int(latest),
            "trend_direction": direction
        }

    except:
        return {"interest_score": 0, "trend_direction": "flat"}

# =====================================================
# CLAUDE CALL (GENERIC)
# =====================================================

def call_claude(prompt, max_tokens=300):
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

# =====================================================
# CLAUDE VALIDATION (NOISE FILTER)
# =====================================================

def claude_validate_trend(trend):
    prompt = f"""
You are validating internet trends.

Trend: "{trend}"

Is this a real emerging internet or meme trend, or just noise?

Respond ONLY as JSON:
{{
  "verdict": "approve" or "reject",
  "confidence": "low|medium|high",
  "reason": "short explanation"
}}
"""
    text = call_claude(prompt, 200)
    try:
        return json.loads(text)
    except:
        return {"verdict": "reject"}

# =====================================================
# CLAUDE ANALYSIS
# =====================================================

def claude_analysis(trend, google_trends):
    prompt = f"""
Trend: {trend}

Google Trends:
{google_trends}

Tasks:
1. Explain the trend in 2–3 sentences
2. Classify as accelerating, stable, or declining
3. Write ONE meme-style sentence
4. Write ONE short image prompt

Respond ONLY as JSON with keys:
analysis, status, meme, image_prompt
"""
    text = call_claude(prompt, 400)
    try:
        return json.loads(text)
    except:
        return {
            "analysis": "Analysis unavailable.",
            "status": "stable",
            "meme": "",
            "image_prompt": ""
        }

# =====================================================
# MAIN
# =====================================================

def main():
    tracked = load_tracked_trends()
    all_trends = tracked.copy()

    # -------- AUTO DISCOVERY --------
    if ENABLE_AUTO_DISCOVERY:
        candidates = discover_candidates()
        new_trends = []

        for term in candidates:
            if term in tracked:
                continue
            if score_trend(term) < DISCOVERY_SCORE_THRESHOLD:
                continue

            verdict = claude_validate_trend(term)
            if verdict.get("verdict") == "approve":
                new_trends.append(term)

            if len(new_trends) >= MAX_NEW_TRENDS_PER_RUN:
                break

        if new_trends:
            all_trends.extend(new_trends)
            save_tracked_trends(all_trends)

    # -------- GENERATE DATA --------
    for trend in all_trends:
        safe = trend.replace(" ", "_").lower()
        outfile = f"{DATA_DIR}/{safe}.json"

        google = get_google_trends(trend)
        analysis = claude_analysis(trend, google)

        data = {
            "trend": trend,
            "metrics": {
                "tiktok": 0,
                "youtube": 0,
                "x": 0
            },
            "google_trends": google,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "analysis": analysis,
            "token": None
        }

        with open(outfile, "w") as f:
            json.dump(data, f, indent=2)

        print("Updated:", trend)

# =====================================================
# ENTRY
# =====================================================

if __name__ == "__main__":
    main()
