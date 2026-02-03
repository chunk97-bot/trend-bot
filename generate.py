import os
import json
from datetime import datetime

# =========================
# CONFIG
# =========================
POSTS_DIR = "posts"
DATA_DIR = "data"

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# =========================
# SIMULATED METRIC FETCHERS
# (real fetchers come next step)
# =========================
def fetch_metrics(trend):
    """
    Returns approximate platform metrics.
    These numbers intentionally fluctuate to simulate growth.
    """
    base = hash(trend) % 100000

    return {
        "tiktok": base * 1200,
        "youtube": base * 15,
        "x": base * 2,
        "instagram": base,
        "facebook": base // 10
    }

# =========================
# LOAD / UPDATE METRICS
# =========================
def update_trend_metrics(trend):
    filename = os.path.join(DATA_DIR, f"{trend}.json")

    new_metrics = fetch_metrics(trend)
    now = datetime.utcnow().isoformat()

    if os.path.exists(filename):
        with open(filename, "r") as f:
            old = json.load(f)
    else:
        old = {
            "trend": trend,
            "platforms": {},
            "history": []
        }

    deltas = {}
    for platform, value in new_metrics.items():
        old_value = old["platforms"].get(platform, {}).get("value", 0)
        deltas[platform] = value - old_value

    snapshot = {
        "timestamp": now,
        "metrics": new_metrics
    }

    updated = {
        "trend": trend,
        "platforms": {
            p: {
                "value": new_metrics[p],
                "delta": deltas[p]
            } for p in new_metrics
        },
        "history": old.get("history", []) + [snapshot],
        "last_updated": now
    }

    with open(filename, "w") as f:
        json.dump(updated, f, indent=2)

    return updated

# =========================
# MAIN (TEMP TREND)
# =========================
trend_name = "npc-livestreams"

data = update_trend_metrics(trend_name)

print("Updated metrics for:", trend_name)
print(json.dumps(data["platforms"], indent=2))
