const container = document.getElementById("trends");

async function loadTrends() {
  container.innerHTML = "";

  try {
    const res = await fetch("./data/npc livestreams.json?ts=" + Date.now());
    const data = await res.json();
    renderTrend(data);
  } catch (err) {
    container.innerHTML = "<p>Failed to load trend data.</p>";
    console.error(err);
  }
}

function renderTrend(data) {
  const card = document.createElement("div");
  card.className = "card";

  const status = data.analysis?.status || "stable";
  const gt = data.google_trends || { interest_score: 0 };
  const metrics = data.metrics || {};

  const tiktok = metrics.tiktok || 0;
  const youtube = metrics.youtube || 0;
  const x = metrics.x || 0;
  const google = gt.interest_score || 0;
  const totalInterest = tiktok + youtube + x + google;

  const imageQuery = encodeURIComponent(data.trend);
  const imageUrl = `https://source.unsplash.com/900x500/?${imageQuery}`;

  card.innerHTML = `
    <img class="trend-image" src="${imageUrl}" alt="${data.trend}" />

    <h2>${data.trend}</h2>

    <div class="status ${status}">
      ${status.toUpperCase()}
    </div>

    <p>${data.analysis?.analysis || "No analysis yet."}</p>

    <div class="meme">😂 ${data.analysis?.meme || ""}</div>

    <div class="counters">
      <div class="total">
        👀 <strong>Total Interest:</strong> ${totalInterest}
      </div>
      <div class="counter-row">
        <span>🎵 TikTok: ${tiktok}</span>
        <span>▶️ YouTube: ${youtube}</span>
        <span>🐦 X: ${x}</span>
        <span>🔎 Google: ${google}</span>
      </div>
    </div>
  `;

  if (data.token) {
    card.innerHTML += `
      <div class="token">
        <strong>🪙 Token Detected</strong><br/>
        ${data.token.ticker} (${data.token.chain})<br/>
        Liquidity: $${data.token.liquidity.toLocaleString()}<br/>
        1h Volume: $${data.token.volume_1h.toLocaleString()}<br/>
        5m Change: ${data.token.price_change_5m}%
      </div>
    `;
  }

  container.appendChild(card);
}

loadTrends();
setInterval(loadTrends, 120000);
