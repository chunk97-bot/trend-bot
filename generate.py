import os
import json
import urllib.request
from datetime import datetime

# =========================================
# CONFIG
# =========================================
TREND = "npc livestreams"
DATA_DIR = "data"

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_MODEL = "claude-3-haiku-20240307"

os.makedirs(DATA_DIR, exist_ok=True)

print("=== GENERATE.PY START ===")
print("Claude key exists:", bool(CLAUDE_API_KEY))

# =========================================
# METRICS (PLACEHOLDER – WILL IMPROVE LATER)
# =========================================
def get_metrics():
    return {
        "tiktok": 0,
        "youtube": 0,
        "x": 0
    }

# =========================================
# DEXSCREENER LOOKUP (CONDITIONAL)
# =========================================
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

# =========================================
# CLAUDE CALL
# =========================================
def call_claude(trend, metrics):
    prompt = f"""
You are an internet trend analyst.

Trend: {trend}

Metrics:
{json.dumps(metrics, indent=2)}

Tasks:
1. Explain what is happening with this trend
2. Classify it as accelerating, stable, or fading
3. Write a short meme-style line (1–2 lines)
4. Determine if THIS trend explicitly involves a crypto or meme coin

Rules for token detection:
- Only return a token if it is clearly part of the trend narrative
- Token must be relevant to the trend itself
- If unsure, return null

Return ONLY valid JSON in one of these formats:

{{
  "analysis": "...",
  "status": "accelerating | stable | fading",
  "meme": "...",
  "token": null
}}

OR (only if clearly relevant):

{{
  "analysis": "...",
  "status": "accelerating | stable | fading",
  "meme": "...",
  "token": {{
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

# =========================================
# MAIN
# =========================================
file_path = os.path.join(DATA_DIR, f"{TREND}.json")

metrics = get_metrics()

data = {
    "trend": TREND,
    "metrics": metrics,
    "timestamp": datetime.utcnow().isoformat()
}

# Run Claude
if CLAUDE_API_KEY:
    try:
        print("Calling Claude...")
        analysis = call_claude(TREND, metrics)
        data["analysis"] = analysis
        print("Claude analysis saved")

        # Attach token data ONLY if relevant and not already attached
        if analysis.get("token"):
            print("Claude detected token:", analysis["token"]["ticker"])

            if "token" not in data:
                token_data = fetch_token_from_dexscreener(
                    analysis["token"]["ticker"]
                )
                if token_data:
                    data["token"] = token_data
                    print("Token attached:", token_data["ticker"])

    except Exception as e:
        print("Claude error:", e)

# Persist data
with open(file_path, "w") as f:
    json.dump(data, f, indent=2)

print("=== RUN COMPLETE ===")
