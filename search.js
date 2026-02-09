const results = document.getElementById("results");
const input = document.getElementById("search");

let trends = [];

// Category detection keywords (same as script.js)
const categoryKeywords = {
  politics: ["election", "president", "congress", "senate", "vote", "political", "government", "biden", "trump", "democrat", "republican", "law", "policy"],
  technology: ["ai", "tech", "software", "app", "google", "apple", "microsoft", "coding", "robot", "computer", "digital", "cyber", "data", "cloud"],
  crypto: ["bitcoin", "crypto", "token", "coin", "nft", "blockchain", "defi", "eth", "solana", "meme coin", "dex", "trading"],
  gaming: ["game", "gaming", "xbox", "playstation", "nintendo", "esports", "twitch", "streamer", "fortnite", "minecraft", "gta", "cod"],
  entertainment: ["movie", "film", "tv", "show", "netflix", "disney", "celebrity", "actor", "actress", "hollywood", "series", "streaming"],
  memes: ["meme", "viral", "funny", "lol", "npc", "trend", "challenge", "tiktoker", "influencer"],
  sports: ["football", "basketball", "soccer", "nfl", "nba", "sports", "game", "player", "team", "world cup", "super bowl"],
  news: ["breaking", "news", "report", "update", "happening", "crisis", "event", "announcement"],
  music: ["music", "song", "album", "artist", "concert", "spotify", "rapper", "singer", "billboard", "grammy"],
  culture: ["fashion", "style", "beauty", "lifestyle", "food", "travel", "art", "design", "aesthetic"]
};

function detectCategory(trend) {
  const text = `${trend.trend} ${trend.analysis?.analysis || ""}`.toLowerCase();
  for (const [category, keywords] of Object.entries(categoryKeywords)) {
    for (const keyword of keywords) {
      if (text.includes(keyword)) return category;
    }
  }
  return "other";
}

function getCategoryIcon(category) {
  const icons = {
    politics: "🏛️", technology: "💻", crypto: "🪙", gaming: "🎮",
    entertainment: "🎬", memes: "😂", sports: "🏈", news: "📰",
    music: "🎵", culture: "🛍️", other: "🌐"
  };
  return icons[category] || "🌐";
}

// Load all trend data
async function loadTrends() {
  try {
    const indexRes = await fetch("./data/index.json");
    const index = await indexRes.json();

    for (const file of index.files) {
      try {
        const res = await fetch(`./data/${file}`);
        const data = await res.json();
        data.category = data.category || detectCategory(data);
        trends.push(data);
      } catch (e) {
        console.error("Failed loading", file);
      }
    }

    trends.sort((a, b) => new Date(b.timestamp || 0) - new Date(a.timestamp || 0));
    render(trends);
  } catch (err) {
    results.innerHTML = "<p class='error-message'>Failed to load trend data.</p>";
  }
}

// Generate safe filename from trend name (matches post URLs)
function safeFilename(name) {
  return name.toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .substring(0, 50);
}

// Render list
function render(list) {
  results.innerHTML = "";

  if (list.length === 0) {
    results.innerHTML = "<p class='no-results'>No trends found. Try a different search term.</p>";
    return;
  }

  list.forEach(t => {
    const card = document.createElement("a");
    card.className = "card search-result-card";
    card.href = `./posts/${safeFilename(t.trend)}.html`;
    card.style.textDecoration = 'none';
    card.style.color = 'inherit';
    card.style.display = 'block';
    card.style.cursor = 'pointer';
    const icon = getCategoryIcon(t.category);

    card.innerHTML = `
      <div class="card-header">
        <span class="category-tag">${icon} ${t.category || 'other'}</span>
        <div class="lifecycle ${t.lifecycle || 'new'}">
          ${t.lifecycle?.toUpperCase() || 'NEW'}
        </div>
      </div>

      <h3>${t.analysis?.headline || t.trend}</h3>
      <div class="trend-topic-small">📌 ${t.trend}</div>

      ${t.analysis?.summary ? `<p class="search-summary">${t.analysis.summary}</p>` : ''}

      <div class="metrics">
        🚀 Momentum: <strong>${t.momentum || 'stable'}</strong> · 
        📊 Signal: <strong>${t.signal_score || 0}</strong>
        ${t.platform_count ? ` · 🌐 ${t.platform_count} platforms` : ''}
      </div>
      
      <div class="view-details">
        View Full Details →
      </div>
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
    t.trend.toLowerCase().includes(q) ||
    (t.analysis?.analysis || "").toLowerCase().includes(q) ||
    (t.category || "").toLowerCase().includes(q)
  );

  render(filtered);
});

// Init
loadTrends();
