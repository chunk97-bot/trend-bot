import os
import json
import re
import urllib.request
from datetime import datetime

# =========================
# CONFIG
# =========================
POSTS_DIR = "posts"
DATA_DIR = "data"

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# =========================
# HELPERS
# =========================
def fetch_url(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode("utf-8", errors="ignore")

def extract_number(text):
    text = text.replace(",", "")
    match = re.search(r"(\d+(\.\d+)?)([KMB]?)", text)
    if not match:
        return 0
    num = float(match.group(1))
    mult = match.group(3)
    return int(num * {"":1, "K":1e3, "M":1e6, "B":1e9}[mult])

# =========================
# REAL METRIC FETCHERS
# =========================
def tiktok_hashtag_views(tag):
    try:
        html = fetch_url(f"https://www.tiktok.com/tag/{tag}")
        match = re.search(r'([\d\.]+[KMB]) views', html)
        return extract_number(match.group(1)) if match else 0
    except:
        return 0

def youtube_trending_views(keyword):
    try:
        html = fetch_url("https://www.youtube.com/feed/trending")
        views = re.findall(r'([\d,]+) views', html)
        total = sum(int(v.replace(",", "")) for v in views[:10])
        return total
    except:
        return 0

def x_visibility_score(keyword):
    try:
        html = fetch_url(f"https://x.com/search?q={keyword}&src=trend_click")
        hits = len(re.findall(keyword.split()[0], html.lower()))
        return hits * 50
    except:
        return 0

# =========================
# METRIC UPDATE
# =========================
def update_trend_metrics(trend):
    filename = os.path.join(DATA_DIR, f"{trend}.json")
    now = datetime.utcnow().isoformat()

    tag = trend.replace(" ", "")
    new_metrics = {
        "tiktok": tiktok_hashtag_views(tag),
        "youtube": youtube_trending_views(trend),
        "x": x_visibility_score(trend),
        "instagram": 0,   # next step
        "facebook": 0     # next step
    }

    if os.path.exists(filename):
        with open(filename, "r") as f:
            old = json.load(f)
    else:
        old = {"platforms": {}, "history": []}

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
        "last_updated": now
    }

    with open(filename, "w") as f:
        json.dump(updated, f, indent=2)

    return updated

# =========================
# MAIN (TEST TREND)
# =========================
trend_name = "npc livestreams"

data = update_trend_metrics(trend_name)

print("Updated REAL metrics:")
print(json.dumps(data["platforms"], indent=2))
