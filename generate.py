import os
print("Claude key exists:", bool(os.getenv("CLAUDE_API_KEY")))

import os
import json
import re
import urllib.request
from datetime import datetime

# ======================================================
# CONFIG
# ======================================================
TREND = "npc livestreams"   # later this becomes dynamic
DATA_DIR = "data"
POSTS_DIR = "posts"

CLAUDE_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_MODEL = "claude-3-haiku-20240307"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(POSTS_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ======================================================
# HELPERS
# ======================================================
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

def pct_change(new, old):
    if old == 0:
        return 100 if new > 0 else 0
    return ((new - old) / old) * 100

# ======================================================
# METRIC FETCHERS (SAFE + FREE)
# ======================================================
def tiktok_views(tag):
    try:
        html = fetch_url(f"https://www.tiktok.com/tag/{tag}")
        match = re.search(r'([\d\.]+[KMB]) views', html)
        return extract_number(match.group(1)) if match else 0
    except:
        return 0

def youtube_views(keyword):
    try:
        html = fetch_url("https://www.youtube.com/feed/trending")
        views = re.findall(r'([\d,]+) views', html)
        return sum(int(v.replace(",", "")) for v in views[:10])
    except:
        return 0

def x_visibility(keyword):
    try:
        html = fetch_url(f"https://x.com/search?q={keyword}")
        hits = html.lower().count(keyword.split()[0])
        return hits * 50
    except:
        return 0

# ======================================================
# UPDATE METRICS + HISTORY
# ======================================================
def update_metrics(trend):
    filename = os.path.join(DATA_DIR, f"{trend}.json")
    now = datetime.utcnow().isoformat()

    tag = trend.replace(" ", "")
    new_metrics = {
        "tiktok": tiktok_views(tag),
        "youtube": youtube_views(trend),
        "x": x_visibility(trend),
        "instagram": 0,
        "facebook": 0
    }

    if os.path.exists(filename):
        with open(filename, "r") as f:
            old = json.load(f)
    else:
        old = {"history": [], "platforms": {}}

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

# ======================================================
# SHOULD WE CALL CLAUDE?
# ======================================================
def should_analyze(history):
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
# CLAUDE ANALYSIS
# ======================================================
def call_claude(old_metrics, new_metrics, trend):
    prompt = f"""
You are a viral internet trend analyst.

Trend: {trend}

Old metrics:
{json.dumps(old_metrics, indent=2)}

New metrics:
{json.dumps(new_metrics, indent=2)}

Tasks:
1. Explain which platform is driving growth
2. Say if trend is accelerating, stable, or fading
3. Write a meme-style summary (1–2 lines, human, no hashtags)

Return ONLY JSON:
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
            "x-api-key": CLAUDE_KEY,
            "anthropic-version": "2023-06-01"
        }
    )

    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read().decode("utf-8"))
        return json.loads(res["content"][0]["text"])

# ======================================================
# IMAGE + UI HELPERS
# ======================================================
def image_url(trend):
    return f"https://source.unsplash.com/1600x900/?{trend.replace(' ', ',')},internet"

def badge_color(status):
    return {
        "accelerating": "#16a34a",
        "stable": "#f59e0b",
        "fading": "#dc2626"
    }.get(status.lower(), "#6b7280")

# ======================================================
# MAIN FLOW
# ======================================================
data = update_metrics(TREND)
history = data["history"]

analysis = {
    "analysis": "Tracking live engagement across platforms.",
    "status": "stable",
    "meme": "everyone knows it's dumb\nnobody stopped watching"
}

if CLAUDE_KEY and should_analyze(history):
    try:
        old = history[-2]["metrics"] if len(history) >= 2 else {}
        new = history[-1]["metrics"]
        analysis = call_claude(old, new, TREND)
    except Exception as e:
        print("Claude error:", e)

# ======================================================
# BUILD UI
# ======================================================
metrics = data["platforms"]
cards = ""

for p in metrics:
    v = metrics[p]["value"]
    d = metrics[p]["delta"]
    arrow = "▲" if d >= 0 else "▼"
    color = "#16a34a" if d >= 0 else "#dc2626"
    cards += f"""
    <div class="card">
      <div class="label">{p.title()}</div>
      <div class="value">{v:,}</div>
      <div class="delta" style="color:{color}">{arrow} {abs(d):,}</div>
    </div>
    """

status_color = badge_color(analysis["status"])

html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" />
<title>{TREND}</title>
<style>
body {{
  margin: 0;
  font-family: system-ui, sans-serif;
  background: #0f172a;
  color: #e5e7eb;
}}
.hero {{
  height: 320px;
  background: url('{image_url(TREND)}') center/cover;
}}
.container {{
  max-width: 960px;
  margin: -80px auto 40px;
  padding: 20px;
}}
.main {{
  background: #020617;
  border-radius: 16px;
  padding: 24px;
}}
.badge {{
  display: inline-block;
  margin-top: 10px;
  padding: 6px 14px;
  border-radius: 999px;
  background: {status_color};
}}
.metrics {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px,1fr));
  gap: 14px;
  margin-top: 24px;
}}
.card {{
  background: #020617;
  border: 1px solid #1e293b;
  border-radius: 12px;
  padding: 14px;
  text-align: center;
}}
.label {{ color:#94a3b8; font-size:.8rem }}
.value {{ font-size:1.2rem }}
pre {{
  background:#020617;
  padding:14px;
  border-left:4px solid #38bdf8;
}}
</style>
</head>
<body>
<div class="hero"></div>
<div class="container">
<div class="main">
<h1>{TREND}</h1>
<span class="badge">{analysis["status"].upper()}</span>

<div class="metrics">{cards}</div>

<h3>AI Insight</h3>
<p>{analysis["analysis"]}</p>

<h3>Meme take</h3>
<pre>{analysis["meme"]}</pre>

<p><em>Last updated {datetime.utcnow()} UTC</em></p>
<a href="./index.html">← Back</a>
</div>
</div>
</body>
</html>
"""

slug = TREND.replace(" ", "-")
with open(os.path.join(POSTS_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
    f.write(html)

print("Post updated with full UI")
