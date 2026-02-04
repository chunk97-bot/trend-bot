import os
import json
import urllib.request
from datetime import datetime
from pytrends.request import TrendReq

# =====================================================
# CONFIG
# =====================================================
TREND = "npc livestreams"
DATA_DIR = "data"
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_MODEL = "claude-3-haiku-20240307"

os.makedirs(DATA_DIR, exist_ok=True)

print("=== GENERATE.PY START ===")
print("Claude key exists:", bool(CLAUDE_API_KEY))

# =====================================================
# SOCIAL METRICS (PLACEHOLDER FOR NOW)
# =====================================================
def get_metrics():
    return {
        "tiktok": 0,
        "youtube": 0,
        "x": 0
    }

# =====================================================
# GOOGLE TRENDS (NO API KEY)
# =====================================================
def fetch_google_trends(trend):
    try:
        pytrends = TrendReq(hl="en-US", tz=360)
        pytrends.build_payload([trend], timeframe="now 7-d")
        interest = pytrends.interest_over_time()

        if interest.empty:
            return {
                "interest_score": 0,
                "trend_direction": "flat"
            }

        values = interest[trend].tolist()
        latest = values[-1]
        previous = values[-2] if len(values) > 1 else latest

        direction = (
            "rising" if latest > previous else
            "falling" if latest < previous else
            "flat"
        )

        return {
            "interest_score": int(latest),
            "trend_direction": direction
        }

    except Exception as e:
        print("Google Trends error:", e)
        return {
            "interest_score": 0,
            "trend_direction": "unknown"
        }

# =====================================================
# DEXSCREENER (ONLY IF TOKEN IS RELEVANT)
# =====================================================
def fetch_token_from_dexscreener(ticker):
    try:
        symbol = ticker.replace("$", "")
        url = f"https://api.dexscreener.com/latest/dex/search?q={symbol}"

        with urllib.request.urlopen(url, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))

        if not data.get("pairs"):
            return None

        pair = data["pairs"][0]

        return {
            "name": symbol,
            "ticker": ticker,
            "chain": pair.get("chainId"),
            "liquidity": int(pair.get("liquidity", {}).get("usd", 0)),
            "volume_1h": int(pair.get("volume", {}).get("h1", 0)),
            "price_change_5m": pair.get("priceChange", {}).get("m5", 0),
            "first_detected": datetime.utcnow().isoformat()
        }

    except Exception as e:
        print("DexScreener error:", e)
        return None

# =====================================================
# CLAUDE AI
# =====================================================
def call_claude(trend, metrics, google_trends):
    prompt = f"""
You are an internet trend analyst.

Trend:
{trend}

Social Metrics:
{json.dumps(metrics, indent=2)}

Google Trends:
{json.dumps(google_trends, indent=2)}

Tasks:
1. Explain what is happening with this trend
2. Classify it as accelerating, stable, or fading
3. Write a short meme-style line (1–2 lines)
4. Decide if this trend explicitly involves a crypto or meme coin

Rules:
- Only return a token if it is clearly part of the trend
- If unsure, return null
- Do NOT hallucinate tokens

Return ONLY valid JSON:

{{
  "analysis": "...",
  "status": "accelerating | stable | fading",
  "meme": "...",
  "token": null OR {{
    "name": "TokenName",
    "ticker": "$TICKER"
  }}
}}
"""

    body = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": 400,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01"
        }
    )

    with urllib.request.urlopen(req, timeout=30) as r:
        response = json.loads(r.read().decode("utf-8"))
        return json.loads(response["content"][0]["text"])

# =====================================================
# MAIN
# =====================================================
file_path = os.path.join(DATA_DIR, f"{TREND}.json")

metrics = get_metrics()
google_trends = fetch_google_trends(TREND)

data = {
    "trend": TREND,
    "metrics": metrics,
    "google_trends": google_trends,
    "timestamp": datetime.utcnow().isoformat()
}

if CLAUDE_API_KEY:
    try:
        print("Calling Claude...")
        analysis = call_claude(TREND, metrics, google_trends)
        data["analysis"] = analysis
        print("Claude analysis saved")

        # Attach token ONLY if Claude says so
        if analysis.get("token"):
            print("Claude detected token:", analysis["token"]["ticker"])
            token_data = fetch_token_from_dexscreener(
                analysis["token"]["ticker"]
            )
            if token_data:
                data["token"] = token_data
                print("Token attached:", token_data["ticker"])

    except Exception as e:
        print("Claude error:", e)

with open(file_path, "w") as f:
    json.dump(data, f, indent=2)

print("=== RUN COMPLETE ===")
