const container = document.getElementById("featured-trend");

async function loadTopTrend() {
  try {
    const indexRes = await fetch("./data/index.json");
    const index = await indexRes.json();

    let trends = [];

    for (const file of index.files) {
      const res = await fetch(`./data/${file}`);
      const data = await res.json();
      trends.push(data);
    }

    // Prefer rising trends, then highest signal score
    trends.sort((a, b) => {
      if (a.lifecycle === "rising" && b.lifecycle !== "rising") return -1;
      if (b.lifecycle === "rising" && a.lifecycle !== "rising") return 1;
      return (b.signal_score || 0) - (a.signal_score || 0);
    });

    const top = trends[0];
    renderTop(top);
  } catch (e) {
    container.innerHTML = "<p>Failed to load top trend.</p>";
  }
}

function renderTop(t) {
  container.innerHTML = `
    <h4>${t.trend}</h4>

    <div class="lifecycle ${t.lifecycle}">
      ${t.lifecycle.toUpperCase()}
    </div>

    <p>${t.analysis?.analysis || ""}</p>

    <div class="metrics">
      🚀 Momentum: <strong>${t.momentum}</strong><br/>
      📊 Signal Score: ${t.signal_score}
    </div>

    ${
      t.token
        ? `<div class="token">
            🪙 <strong>${t.token.symbol}</strong>
            (${t.token.chain})
          </div>`
        : ""
    }
  `;
}

// Init
loadTopTrend();
