const container = document.getElementById("trends");

// Add more JSON files here later
const trends = [
  "data/npc livestreams.json"
];

trends.forEach(url => {
  fetch(url)
    .then(res => res.json())
    .then(data => renderTrend(data))
    .catch(err => console.error("Failed to load", url, err));
});

function renderTrend(data) {
  const card = document.createElement("div");
  card.className = "card";

  const status = data.analysis?.status || "stable";
  const gt = data.google_trends || null;

  card.innerHTML = `
    <h2>${data.trend}</h2>

    <div class="status ${status}">
      ${status.toUpperCase()}
    </div>

    <p>${data.analysis?.analysis || "No analysis yet."}</p>

    <div class="meme">😂 ${data.analysis?.meme || ""}</div>
  `;

  // GOOGLE TRENDS (only if exists)
  if (gt) {
    const directionClass =
      gt.trend_direction === "rising" ? "gt-rising" :
      gt.trend_direction === "falling" ? "gt-falling" :
      "gt-flat";

    card.innerHTML += `
      <div class="google-trends">
        🔎 Google Trends:
        <strong>${gt.interest_score}/100</strong>
        <span class="gt-badge ${directionClass}">
          ${gt.trend_direction.toUpperCase()}
        </span>
      </div>
    `;
  }

  // TOKEN (only if exists)
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
