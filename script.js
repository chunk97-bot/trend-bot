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

  card.innerHTML = `
    <h2>${data.trend}</h2>

    <div class="status ${status}">
      ${status.toUpperCase()}
    </div>

    <p>${data.analysis?.analysis || "No analysis yet."}</p>

    <div class="meme">😂 ${data.analysis?.meme || ""}</div>
  `;

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
