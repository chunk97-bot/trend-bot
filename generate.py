import os
import json
import datetime
import requests
from pytrends.request import TrendReq

# =========================
# CONFIG
# =========================

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

TRENDS = [
    "npc livestreams",
    "girl dinner",
    "skull emoji era",
    "ai yearbook photos"
]

CLAUDE_MODEL = "claude-3-haiku-20240307"

# =========================
# GOOGLE TRENDS
# =========================

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

        if latest > prev:
            direction = "rising"
        elif latest < prev:
            direction = "falling"
        else:
            direction = "flat"

        return {
            "interest_score": int(latest),
            "trend_direction": direction
        }

    except Exception as e:
        print("Google Trends error:", e)
        return {"interest_score": 0, "trend_direction": "flat"}

# =========================
# CLAUDE ANALYSIS
# =========================

def claude_analysis(trend, google_trends):
    if not CLAUDE_API_KEY:
        return {
            "analysis": "Claude API key not configured.",
            "status": "stable",
            "meme": "",
            "image_prompt": ""
        }

    prompt = f"""
You are an internet trend analyst.

Trend: {trend}

Google Trends:
- Interest score: {google_trends['interest_score']}
- Direction: {google_trends['trend_direction']}

Tasks:
1. Explain the trend in 2–3 sentences
2. Classify status as accelerating, stable, or declining
3. Write ONE funny meme-style sentence
4. Write ONE short visual image prompt (for AI image generation)

Respond ONLY in JSON with keys:
analysis, status, meme, image_prompt
"""

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": CLAUDE_MODEL,
                "max_tokens": 400,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )

        text = response.json()["content"][0]["text"]
        return json.loads(text)

    except Exception as e:
        print("Claude error:", e)
        return {
            "analysis": "AI analysis unavailable.",
            "status": "stable",
            "meme": "",
            "image_prompt": ""
        }

# =========================
# MAIN LOOP
# =========================

def main():
    for trend in TRENDS:
        safe_name = trend.replace(" ", "_").lower()
        output_file = f"{DATA_DIR}/{safe_name}.json"

        print("Processing:", trend)

        google_trends = get_google_trends(trend)
        analysis = claude_analysis(trend, google_trends)

        data = {
            "trend": trend,
            "metrics": {
                "tiktok": 0,
                "youtube": 0,
                "x": 0
            },
            "google_trends": google_trends,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "analysis": analysis,
            "token": None
        }

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        print("Saved:", output_file)

# =========================
# ENTRY
# =========================

if __name__ == "__main__":
    main()
