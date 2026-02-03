# ---------- UI HELPERS ----------
def image_url_from_trend(trend):
    keywords = trend.replace(" ", ",")
    return f"https://source.unsplash.com/1600x900/?{keywords},internet"

def badge_color(status):
    return {
        "accelerating": "#16a34a",
        "stable": "#f59e0b",
        "fading": "#dc2626"
    }.get(status.lower(), "#6b7280")

metrics = data["platforms"]

image_url = image_url_from_trend(trend)
status = result["status"]
status_color = badge_color(status)

def metric_card(name, value, delta):
    arrow = "▲" if delta >= 0 else "▼"
    color = "#16a34a" if delta >= 0 else "#dc2626"
    return f"""
    <div class="card">
      <div class="label">{name}</div>
      <div class="value">{value:,}</div>
      <div class="delta" style="color:{color}">{arrow} {abs(delta):,}</div>
    </div>
    """

cards_html = (
    metric_card("TikTok", metrics["tiktok"]["value"], metrics["tiktok"]["delta"]) +
    metric_card("YouTube", metrics["youtube"]["value"], metrics["youtube"]["delta"]) +
    metric_card("X", metrics["x"]["value"], metrics["x"]["delta"]) +
    metric_card("Instagram", metrics["instagram"]["value"], metrics["instagram"]["delta"]) +
    metric_card("Facebook", metrics["facebook"]["value"], metrics["facebook"]["delta"])
)

html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" />
<title>{trend}</title>
<style>
  body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;
    background: #0f172a;
    color: #e5e7eb;
  }}
  .hero {{
    width: 100%;
    height: 320px;
    background-image: url('{image_url}');
    background-size: cover;
    background-position: center;
  }}
  .container {{
    max-width: 960px;
    margin: -80px auto 40px;
    padding: 20px;
  }}
  .card-main {{
    background: #020617;
    border-radius: 14px;
    padding: 24px;
    box-shadow: 0 20px 40px rgba(0,0,0,0.4);
  }}
  h1 {{
    margin: 0;
    font-size: 2rem;
  }}
  .badge {{
    display: inline-block;
    margin-top: 10px;
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    background: {status_color};
    color: white;
  }}
  .metrics {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
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
  .label {{
    font-size: 0.8rem;
    color: #94a3b8;
  }}
  .value {{
    font-size: 1.2rem;
    margin-top: 6px;
  }}
  .delta {{
    font-size: 0.8rem;
    margin-top: 4px;
  }}
  .section {{
    margin-top: 28px;
  }}
  .section h3 {{
    margin-bottom: 8px;
  }}
  pre {{
    background: #020617;
    border-left: 4px solid #38bdf8;
    padding: 14px;
    border-radius: 10px;
    white-space: pre-wrap;
  }}
  .footer {{
    margin-top: 24px;
    font-size: 0.75rem;
    color: #94a3b8;
  }}
  a {{
    color: #38bdf8;
    text-decoration: none;
  }}
</style>
</head>

<body>
  <div class="hero"></div>

  <div class="container">
    <div class="card-main">
      <h1>{trend}</h1>
      <span class="badge">{status.upper()}</span>

      <div class="metrics">
        {cards_html}
      </div>

      <div class="section">
        <h3>AI Insight</h3>
        <p>{result["analysis"]}</p>
      </div>

      <div class="section">
        <h3>Meme take</h3>
        <pre>{result["meme"]}</pre>
      </div>

      <div class="footer">
        Last updated {datetime.utcnow()} UTC ·
        <a href="./index.html">Back to posts</a>
      </div>
    </div>
  </div>
</body>
</html>
"""
