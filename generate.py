import os
import json
import urllib.request
from datetime import datetime

# ================================
# CONFIG
# ================================
TREND = "npc livestreams"
DATA_DIR = "data"

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_MODEL = "claude-3-haiku-20240307"

os.makedirs(DATA_DIR, exist_ok=True)

print("=== GENERATE.PY START ===")
print("Claude key exists:", bool(CLAUDE_API_KEY))

# ================================
# METRICS (PLACEHOLDER FOR NOW)
# ================================
def get_metrics():
    return {
        "tiktok": 0,
        "youtube": 0,
        "x": 0
    }

# ================================
# CLAUDE CALL
# ================================
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

Return ONLY valid JSON:

{{
  "analysis": "...",
  "status": "accelerating | stable | fading",
  "meme": "..."
}}
"""

    body = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": 300,
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

# ================================
# MAIN
# ================================
file_path = os.path.join(DATA_DIR, f"{TREND}.json")

metrics = get_metrics()

data = {
    "trend": TREND,
    "metrics": metrics,
    "timestamp": datetime.utcnow().isoformat()
}

if CLAUDE_API_KEY:
    try:
        print("Calling Claude...")
        analysis = call_claude(TREND, metrics)
        data["analysis"] = analysis
        print("Claude analysis saved")
    except Exception as e:
        print("Claude error:", e)

with open(file_path, "w") as f:
    json.dump(data, f, indent=2)

print("=== RUN COMPLETE ===")
