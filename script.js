const container = document.getElementById("trends");

async function loadTrends() {
  container.innerHTML = "";

  try {
    const res = await fetch("./data/npc_livestreams.json?ts=" + Date.now());
    const data = await res.json();
    renderTrend(data);
  } catch (err) {
    container.innerHTML = "<p>Failed to load trend.</p>";
    console.error(err);
  }
}

function renderTrend(data) {
  const card = document.createElement("div");
  card.className = "card";

  const status = data.analysis?.status || "stable";
  const metrics = data.metrics || {};
  const gt = data.google_trends || {};

  const imagePrompt = data.analysis?.image_prompt || data.trend;
  const imageUrl = `https://source.unsplash.com/900x500/?${encodeURIComponent(imagePrompt)}`;

  const total =
    (metrics.tiktok || 0) +
    (metrics.youtube || 0) +
    (metrics.x || 0) +
    (gt.interest_score || 0);

const img = document.createElement("img");
img.className = "trend-image";
img.style.display = "none";
img.src = imageUrl;

img.onload = () => {
  img.style.display = "block";
};

img.onerror = () => {
  img.remove();
};
  card.appendChild(img);

  card.innerHTML += `
    <h2>${data.trend}</h2>

    <div class="status ${status}">
      ${status.toUpperCase()}
    </div>

    <p>${data.analysis?.analysis || ""}</p>

    <div class="meme">😂 ${data.analysis?.meme || ""}</div>

    <div class="counters">
      <div class="total">👀 <strong>Total Interest:</strong> ${total}</div>
      <div class="counter-row">
        <span>🎵 TikTok: ${metrics.tiktok || 0}</span>
        <span>▶️ YouTube: ${metrics.youtube || 0}</span>
        <span>🐦 X: ${metrics.x || 0}</span>
        <span>🔎 Google: ${gt.interest_score || 0}</span>
      </div>
    </div>
  `;

  container.appendChild(card);
}

loadTrends();
setInterval(loadTrends, 120000);
