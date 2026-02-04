import os
import json
import re
import urllib.request
from datetime import datetime

# ======================================================
# CONFIG
# ======================================================
TREND = "npc livestreams"     # static for now
DATA_DIR = "data"

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_MODEL = "claude-3-haiku-20240307"

os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ======================================================
# BASIC HELPERS
# ======================================================
def fetch_url(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode("utf-8", errors="ignore")

def extract_number(text):
    text = text.replace(",", "")
    m = re.search(r"(\d+(\.\d+)?)([KMB]?)", text)
    if not m:
        return 0
    num = float(m.group(1))
    mult = {"":1, "K":1e3, "M":1e6, "B":1e9}[m.group(3)]
    return int(num * mult)

def pct_change(new, old):
    if old == 0:
        return 100 if new > 0 else 0
    return ((new - old) / old) * 100

# ======================================================
# METRIC FETCHERS (FREE / HEURISTIC)
# ======================================================
def tiktok_views(tag):
    try:
        html = fetch_url(f"https://www.tiktok.com/tag/{tag}")
        m = re.search(r'([\d\.]+[KMB]) views', html)
        return extract_number(m.group(1)) if m else 0
    except:
        return 0

def youtube_views():
    try:
        html = fetch_url("https://www.youtube.com/feed/trending")
        views = re.findall(r'([\d,]+) views', html)
        return sum(int(v.replace(",", "")) for v in views[:10])
    except:
        return 0

def x_visibility(keyword):
    try:
        html = fetch_url(f"https://x.com/search?q={keyword}")
        return html.lower().count(keyword.split()[0]) * 50
    except:
        return 0

# ======================================================
# UPDATE METRICS + HISTORY
# ======================================================
def update_metrics(trend):
    file_path = os.path.join(DATA_DIR, f"{trend}.json")
    now = datetime.utcnow().isoformat()

    tag = trend.replace(" ", "")
    new_metrics = {
        "tiktok": tiktok_views(tag),
        "youtube": youtube_views(),
        "x": x_visibility(trend)
    }

    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            old = json.load(f)
    else:
        old = {"history": [], "platforms": {}, "analysis": {}}

    deltas = {}
    for p, v in new_metrics.items():
        old_v = old.get("platforms", {}).get(p, {}).get("value", 0)
        deltas[p] = v - old_v

    snapshot = {
        "timestamp": now,
        "metrics": new_metrics
    }

    updated = {
        "trend": trend,
        "platforms": {
            p: {"value": new_metrics[p], "delta": deltas[p]}
            for p in new_metrics
        },
        "history": old.get("history", []) + [snapshot],
        "analysis": old.get("analysis", {}),
        "last_updated": now
    }

    with open(file_path, "w") as f:
        json.dump(updated, f, indent=2)

    return updated

# ======================================================
# SHOULD WE CALL CLAUDE?
# ======================================================
def should_call_claude(history):
    if len(history) < 2:
        return True

    old = history[-2]["metrics"]
    new = history[-1]["metrics"]

    for p in new:
        if pct_change(new[p], old.get(p, 0)) >= 20:
            return True
        if old.get(p, 0) == 0 and new[p] > 0:
            return True

    return False

# ======================================================
# CLAUDE CALL
# ======================================================
def call_claude(trend, old_metrics, new_metrics):
    prompt = f"""
You are an internet trend analyst.

Trend: {trend}

Old metrics:
{json.dumps(old_metrics, indent=2)}

New metrics:
{json.dumps(new_metrics, indent=2)}

Tasks:
1. Explain what changed and why
2. Say if the trend is accelerating, stable, or fading
3. Write a short meme-style summary (1–2 lines, no hashtags)

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
        "messages": [{"role": "user", "content": prompt}]
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

    with urllib.request.urlopen(req, timeout=20) as r:
        res = json.loads(r.read().decode("utf-8"))
        return json.loads(res["content"][0]["text"])

# ======================================================
# MAIN FLOW
# ======================================================
print("Claude key exists:", bool(CLAUDE_API_KEY))

data = update_metrics(TREND)
history = data["history"]

# Default analysis (fallback)
analysis_block = {
    "analysis": "Tracking live engagement across platforms.",
    "status": "stable",
    "meme": "people are watching\nnobody knows why but it works"
}

if CLAUDE_API_KEY:
    try:
        old = history[-2]["metrics"] if len(history) >= 2 else {}
        new = history[-1]["metrics"]
        analysis_block = call_claude(TREND, old, new)
        print("Claude analysis updated")
    except Exception as e:
        print("Claude error:", e)

# Save Claude output into data file
data["analysis"] = analysis_block

with open(os.path.join(DATA_DIR, f"{TREND}.json"), "w") as f:
    json.dump(data, f, indent=2)

print("Run complete")
