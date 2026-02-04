const container = document.getElementById("trends");

async function loadTrends() {
  container.innerHTML = "";

  const files = await fetch("./data")
    .then(() => [])
    .catch(() => []);

  const trendFiles = [
    "npc_livestreams.json",
    "girl_dinner.json",
    "ai_yearbook_photos.json",
    "skull_emoji_era.json"
  ];

  const trends = [];

  for (const file of trendFiles) {
    try {
      const res = await fetch(`./data/${file}?t=${Date.now()}`);
      const data = await res.json();
      trends.push(data);
    } catch {}
  }

  trends.sort((a, b) => b.signal_score - a.signal_score);
  trends.forEach(renderTrend);
}

function renderTrend(trend) {
  const card = document.createElement("div");
  card.className = "card";
  if (trend.highlight) card.classList.add("highlight");

  card.innerHTML = `
    <h2>${trend.trend}</h2>

    <div class="lifecycle ${trend.lifecycle}">
      ${trend.lifecycle.toUpperCase()}
    </div>

    <p>${trend.analysis.analysis}</p>

    <div class="meme">😂 ${trend.analysis.meme}</div>

    <div class="metrics">
      🚀 Momentum: <strong>${trend.momentum}</strong><br/>
      📊 Signal Score: ${trend.signal_score}
    </div>

    <div class="social">
      🐦 X: ${trend.social_presence.x} |
      🎵 TikTok: ${trend.social_presence.tiktok} |
      📸 Instagram: ${trend.social_presence.instagram}
    </div>
  `;

  if (trend.token) {
    card.innerHTML += `
      <div class="token">
        🪙 <strong>${trend.token.symbol}</strong>
        (${trend.token.chain})<br/>
        Liquidity: $${trend.token.liquidity_usd || "N/A"}<br/>
        <a href="${trend.token.url}" target="_blank">View on DexScreener</a>
      </div>
    `;
  }

  container.appendChild(card);
}

loadTrends();
setInterval(loadTrends, 120000);
