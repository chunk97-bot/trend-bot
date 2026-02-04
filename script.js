const container = document.getElementById("trends");

async function loadTrends() {
  container.innerHTML = "";

  try {
    // cache-busting so GitHub Pages always pulls latest data
    const res = await fetch("./data/npc_livestreams.json?ts=" + Date.now());
    const data = await res.json();
    renderTrend(data);
  } catch (err) {
    console.error(err);
    container.innerHTML = "<p>Failed to load trend data.</p>";
  }
}

function renderTrend(data) {
  const card = document.createElement("div");
  card.className = "card";

  const status = data.analysis?.status || "stable";
  const metrics = data.metrics || {};
  const google = data.google_trends || {};

  const tiktok = metrics.tiktok || 0;
  const youtube = metrics.youtube || 0;
  const x = metrics.x || 0;
  const googleScore = google.interest_score || 0;

  const totalInterest = tiktok + youtube + x + googleScore;

  // IMAGE HANDLING (SAFE)
  const imagePrompt = data.analysis?.image_prompt || data.trend;
  const imageUrl = `https://source.unsplash.com/900x500/?${encodeURIComponent(
    imagePrompt
  )}`;

  const img = document.createElement("img");
  img.className = "trend-image";
  img.style.display = "none"; // hide until loaded
  img.src = imageUrl;

  img.onload = () => {
    img.style.display = "block";
  };

  img.onerror = () => {
    img.remove();
  };

  card.appendChild(img);

  // MAIN CONTENT
  card.innerHTML += `
    <h2>${data.trend}</h2>

    <div class="status ${status}">
      ${status.toUpperCase()}
    </div>

    <p>${data.analysis?.analysis || "No analysis available."}</p>

    <div class="meme">
      😂 ${data.analysis?.meme || ""}
    </div>

    <div class="counters">
      <div class="total">
        👀 <strong>Total Interest:</strong> ${totalInterest}
      </div>

      <div class="counter-row">
        <span>🎵 TikTok: ${tiktok}</span>
        <span>▶️ YouTube: ${youtube}</span>
        <span>🐦 X: ${x}</span>
        <span>🔎 Google: ${googleScore}</span>
      </div>
    </div>
  `;

  // OPTIONAL TOKEN BLOCK (only if exists)
  if (data.token) {
    card.innerHTML += `
      <div class="token">
        <strong>🪙 Token Detected</strong><br/>
        ${data.token.ticker} (${data.token.chain})<br/>
        Liquidity: $${data.token.liquidity?.toLocaleString() || 0}<br/>
        1h Volume: $${data.token.volume_1h?.toLocaleString() || 0}<br/>
        5m Change: ${data.token.price_change_5m || 0}%
      </div>
    `;
  }

  container.appendChild(card);
}

// initial load
loadTrends();

// auto refresh every 2 minutes
setInterval(loadTrends, 120000);
