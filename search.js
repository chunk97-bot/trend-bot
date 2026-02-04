const results = document.getElementById("results");
const input = document.getElementById("search");

let trends = [];

// Load all trend data
async function loadTrends() {
  try {
    const indexRes = await fetch("./data/index.json");
    const index = await indexRes.json();

    for (const file of index.files) {
      try {
        const res = await fetch(`./data/${file}`);
        const data = await res.json();
        trends.push(data);
      } catch (e) {
        console.error("Failed loading", file);
      }
    }

    render(trends);
  } catch (err) {
    results.innerHTML = "<p>Failed to load trend data.</p>";
  }
}

// Render list
function render(list) {
  results.innerHTML = "";

  if (list.length === 0) {
    results.innerHTML = "<p>No trends found.</p>";
    return;
  }

  list.forEach(t => {
    const card = document.createElement("div");
    card.className = "card";

    card.innerHTML = `
      <h3>${t.trend}</h3>

      <div class="lifecycle ${t.lifecycle}">
        ${t.lifecycle.toUpperCase()}
      </div>

      <p>${t.analysis?.analysis || ""}</p>
    `;

    results.appendChild(card);
  });
}

// Filter on input
input.addEventListener("input", e => {
  const q = e.target.value.toLowerCase().trim();

  if (!q) {
    render(trends);
    return;
  }

  const filtered = trends.filter(t =>
    t.trend.toLowerCase().includes(q)
  );

  render(filtered);
});

// Init
loadTrends();
