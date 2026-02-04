const container = document.getElementById("trends");

async function loadTrends() {
  container.innerHTML = "";

  let index;
  try {
    const res = await fetch(`./data/index.json?ts=${Date.now()}`);
    index = await res.json();
  } catch {
    container.innerHTML = "<p>Failed to load trends.</p>";
    return;
  }

  const trends = [];

  for (const file of index.files) {
    try {
      const res = await fetch(`./data/${file}?ts=${Date.now()}`);
      trends.push(await res.json());
    } catch {}
  }

  trends.sort((a, b) => (b.signal_score || 0) - (a.signal_score || 0));
  trends.forEach(renderTrend);
}

function renderTrend(t) {
  const card = document.createElement("div");
  card.className = "card";
  if (t.highlight) card.classList.add("highlight");

  card.innerHTML = `
    <h2>${t.trend}</h2>

    <div class="lifecycle ${t.lifecycle}">
      ${t.lifecycle.toUpperCase()}
    </div>

    <p>${t.analysis.analysis}</p>

    <div class="meme">😂 ${t.analysis.meme}</div>

    <div class="metrics">
      🚀 Momentum: <strong>${t.momentum}</strong><br/>
      📊 Signal Score: ${t.signal_score}
    </div>

    <div class="social">
      🐦 X: ${t.social_presence.x} |
      🎵 TikTok: ${t.social_presence.tiktok} |
      📸 Instagram: ${t.social_presence.instagram}
    </div>
  `;

  if (t.token) {
    card.innerHTML += `
      <div class="token">
        🪙 <strong>${t.token.symbol}</strong> (${t.token.chain})<br/>
        Liquidity: $${t.token.liquidity_usd || "N/A"}<br/>
        <a href="${t.token.url}" target="_blank">View on DexScreener</a>
      </div>
    `;
  }

  container.appendChild(card);
}

loadTrends();
setInterval(loadTrends, 120000);
