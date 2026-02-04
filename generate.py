import os
import json
import datetime
from pytrends.request import TrendReq
import requests

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

TREND = "npc livestreams"
SAFE_FILENAME = TREND.replace(" ", "_").lower()
OUTPUT_FILE = f"{DATA_DIR}/{SAFE_FILENAME}.json"


def get_google_trends(keyword):
    pytrends = TrendReq(hl="en-US", tz=360)
    pytrends.build_payload([keyword], timeframe="now 7-d")

    interest = pytrends.interest_over_time()
    if interest.empty:
        return {"interest_score": 0, "trend_direction": "flat"}

    values = interest[keyword].tolist()
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


def claude_analysis(trend, google_trends):
    if not CLAUDE_API_KEY:
        return {
            "analysis": "Claude API key not found.",
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
1. Explain why this trend exists (2–3 sentences)
2. Label status as accelerating / stable / declining
3. Write ONE funny meme-style line
4. Write ONE short visual image prompt (for AI image generation)

Respond in JSON with keys:
analysis, status, meme, image_prompt
"""

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "Content-Type": "application/json",
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01"
        },
        json={
            "model": "claude-3-haiku-20240307",
            "max_tokens": 400,
            "messages": [{"role": "user", "content": prompt}]
        },
        timeout=30
    )

    text = response.json()["content"][0]["text"]
    return json.loads(text)


def main():
    google_trends = get_google_trends(TREND)
    analysis = claude_analysis(TREND, google_trends)

    data = {
        "trend": TREND,
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

    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print("Trend updated:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
