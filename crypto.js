// Crypto Page JavaScript
const container = document.getElementById("trends");
const filterButtons = document.getElementById("crypto-filter-buttons");
const trendsCount = document.getElementById("trends-count");

let allTrends = [];
let cryptoTrends = [];
let currentFilter = "all";
let currentSort = "score";
let currentPage = 1;
const TRENDS_PER_PAGE = 10;

// Crypto-specific keywords for filtering
const cryptoKeywords = {
  bitcoin: ["bitcoin", "btc", "satoshi", "lightning network", "btc etf"],
  ethereum: ["ethereum", "eth", "vitalik", "layer 2", "erc-20", "solidity"],
  altcoins: ["solana", "cardano", "polkadot", "avalanche", "chainlink", "polygon", "matic", "xrp", "ripple", "litecoin"],
  defi: ["defi", "uniswap", "aave", "compound", "yield", "liquidity", "staking", "lending", "dex"],
  nft: ["nft", "opensea", "blur", "pfp", "digital art", "collectible", "tokenized"],
  memecoins: ["dogecoin", "doge", "shiba", "pepe", "memecoin", "meme coin", "bonk", "wif"],
  regulations: ["sec", "regulation", "compliance", "legal", "lawsuit", "ban", "cbdc", "etf approval"]
};

// Skeleton loader for better UX
const SkeletonLoader = {
  show(container) {
    container.innerHTML = Array(6).fill().map(() => `
      <div class="card skeleton-card">
        <div class="skeleton skeleton-header"></div>
        <div class="skeleton skeleton-title"></div>
        <div class="skeleton skeleton-text"></div>
        <div class="skeleton skeleton-text short"></div>
      </div>
    `).join('');
  }
};

// Check if a trend is crypto-related
function isCryptoTrend(trend) {
  const text = `${trend.trend} ${trend.analysis?.summary || ''} ${trend.analysis?.headline || ''}`.toLowerCase();
  
  // Check if category is crypto
  if (trend.category === 'crypto') return true;
  
  // Check for crypto keywords
  const allCryptoKeywords = [
    "crypto", "bitcoin", "btc", "ethereum", "eth", "blockchain", "token", "coin",
    "nft", "defi", "wallet", "mining", "staking", "altcoin", "exchange", "binance",
    "coinbase", "trading", "hodl", "bull", "bear", "market cap", "satoshi"
  ];
  
  for (const keyword of allCryptoKeywords) {
    if (text.includes(keyword)) return true;
  }
  
  return false;
}

// Filter crypto trends by subcategory
function filterCryptoByCategory(trends, filter) {
  if (filter === 'all') return trends;
  
  const keywords = cryptoKeywords[filter] || [];
  return trends.filter(trend => {
    const text = `${trend.trend} ${trend.analysis?.summary || ''}`.toLowerCase();
    return keywords.some(kw => text.includes(kw));
  });
}

// Fetch crypto prices (simulated - replace with real API)
async function fetchCryptoPrices() {
  try {
    // Using CoinGecko free API
    const response = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true');
    const data = await response.json();
    
    if (data.bitcoin) {
      const btcChange = data.bitcoin.usd_24h_change?.toFixed(2) || 0;
      const btcClass = btcChange >= 0 ? 'price-up' : 'price-down';
      document.getElementById('btc-price').innerHTML = `$${data.bitcoin.usd.toLocaleString()} <span class="${btcClass}">(${btcChange >= 0 ? '+' : ''}${btcChange}%)</span>`;
    }
    
    if (data.ethereum) {
      const ethChange = data.ethereum.usd_24h_change?.toFixed(2) || 0;
      const ethClass = ethChange >= 0 ? 'price-up' : 'price-down';
      document.getElementById('eth-price').innerHTML = `$${data.ethereum.usd.toLocaleString()} <span class="${ethClass}">(${ethChange >= 0 ? '+' : ''}${ethChange}%)</span>`;
    }
  } catch (error) {
    document.getElementById('btc-price').textContent = '--';
    document.getElementById('eth-price').textContent = '--';
  }
}

// Update market sentiment based on trends
function updateMarketSentiment() {
  if (cryptoTrends.length === 0) {
    document.getElementById('market-sentiment').textContent = 'Neutral';
    return;
  }
  
  let positiveCount = 0;
  let negativeCount = 0;
  
  cryptoTrends.forEach(trend => {
    const text = `${trend.analysis?.summary || ''} ${trend.analysis?.headline || ''}`.toLowerCase();
    
    // Positive keywords
    if (text.match(/bull|rally|surge|soar|record|breakout|gains|pump|moon/)) {
      positiveCount++;
    }
    // Negative keywords
    if (text.match(/bear|crash|dump|fall|decline|fear|correction|drop|plunge/)) {
      negativeCount++;
    }
  });
  
  const sentimentEl = document.getElementById('market-sentiment');
  if (positiveCount > negativeCount) {
    sentimentEl.textContent = '📈 Bullish';
    sentimentEl.className = 'stat-value sentiment bullish';
  } else if (negativeCount > positiveCount) {
    sentimentEl.textContent = '📉 Bearish';
    sentimentEl.className = 'stat-value sentiment bearish';
  } else {
    sentimentEl.textContent = '➡️ Neutral';
    sentimentEl.className = 'stat-value sentiment neutral';
  }
}

// Format timestamp
function formatPostDate(timestamp) {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

function formatTimestamp(ts) {
  if (!ts) return 'Unknown';
  return new Date(ts).toLocaleString();
}

function getCategoryIcon(category) {
  const icons = {
    crypto: '🪙',
    technology: '💻',
    politics: '🏛️',
    entertainment: '🎬',
    gaming: '🎮',
    memes: '😂',
    sports: '🏈',
    news: '📰',
    music: '🎵',
    culture: '🛍️'
  };
  return icons[category] || '📌';
}

function getOriginPlatform(t) {
  if (t.platforms?.x) return 'X/Twitter';
  if (t.platforms?.tiktok) return 'TikTok';
  if (t.platforms?.google) return 'Google';
  if (t.platforms?.instagram) return 'Instagram';
  return 'Multiple platforms';
}

// Load and filter crypto trends
async function loadCryptoTrends() {
  SkeletonLoader.show(container);
  
  let index;
  try {
    const res = await fetch(`./data/index.json?ts=${Date.now()}`);
    index = await res.json();
  } catch {
    container.innerHTML = "<p class='error-message'>Failed to load trends. Please try again.</p>";
    return;
  }

  allTrends = [];

  for (const file of index.files) {
    try {
      const res = await fetch(`./data/${file}?ts=${Date.now()}`);
      const data = await res.json();
      allTrends.push(data);
    } catch {}
  }

  // Filter to only crypto trends
  cryptoTrends = allTrends.filter(isCryptoTrend);
  
  // Update stats
  document.getElementById('trending-coins-count').textContent = cryptoTrends.length;
  document.getElementById('last-updated-time').textContent = new Date().toLocaleTimeString();
  
  // Update market sentiment
  updateMarketSentiment();

  // Apply sort and render
  cryptoTrends = sortTrends(cryptoTrends);
  renderTrends();
  
  // Show/hide no crypto message
  const noMessage = document.getElementById('no-crypto-message');
  if (cryptoTrends.length === 0) {
    container.style.display = 'none';
    noMessage.style.display = 'flex';
  } else {
    container.style.display = 'grid';
    noMessage.style.display = 'none';
  }
}

function sortTrends(trends) {
  const sorted = [...trends];
  switch (currentSort) {
    case 'score':
      return sorted.sort((a, b) => (b.signal_score || 0) - (a.signal_score || 0));
    case 'date':
      return sorted.sort((a, b) => new Date(b.timestamp || 0) - new Date(a.timestamp || 0));
    case 'name':
      return sorted.sort((a, b) => a.trend.localeCompare(b.trend));
    case 'momentum':
      return sorted.sort((a, b) => parseFloat(b.momentum || '0') - parseFloat(a.momentum || '0'));
    default:
      return sorted;
  }
}

function renderTrends() {
  container.innerHTML = "";
  
  const filtered = filterCryptoByCategory(cryptoTrends, currentFilter);
  const totalPages = Math.ceil(filtered.length / TRENDS_PER_PAGE);
  
  if (currentPage > totalPages) currentPage = totalPages;
  if (currentPage < 1) currentPage = 1;

  const startIndex = (currentPage - 1) * TRENDS_PER_PAGE;
  const endIndex = Math.min(startIndex + TRENDS_PER_PAGE, filtered.length);
  const trendsToRender = filtered.slice(startIndex, endIndex);

  if (trendsCount) {
    trendsCount.textContent = `Showing ${filtered.length} crypto trends`;
  }

  if (filtered.length === 0) {
    container.innerHTML = `<p class='no-results'>No crypto trends found in this category.</p>`;
    return;
  }

  trendsToRender.forEach((trend, index) => {
    renderTrend(trend, index);
  });
  
  renderPagination(totalPages, filtered.length);
}

function renderTrend(t, index = 0) {
  const card = document.createElement("div");
  card.className = "card flip-reveal";
  card.style.animationDelay = `${index * 0.05}s`;
  
  // Ensure lifecycle exists
  if (!t.lifecycle) {
    t.lifecycle = t.signal_score >= 80 ? 'new' : (t.signal_score >= 60 ? 'rising' : (t.signal_score >= 40 ? 'peak' : 'declining'));
  }

  const categoryIcon = getCategoryIcon(t.category);
  const isHot = t.signal_score >= 80 || t.lifecycle === 'new';
  const hotBadge = isHot ? '<span class="hot-badge">🔥 HOT</span>' : '';
  const trendTimestamp = t.timestamp || t.history?.[0]?.timestamp || null;

  card.innerHTML = `
    <div class="card-header">
      <span class="category-tag">${categoryIcon} ${t.category || 'crypto'}</span>
      <div class="card-header-right">
        ${hotBadge}
        <div class="lifecycle ${t.lifecycle}">
          ${t.lifecycle.toUpperCase()}
        </div>
      </div>
    </div>

    <div class="card-meta">
      ${trendTimestamp ? `<span class="post-timestamp">🕐 ${formatPostDate(trendTimestamp)}</span>` : ''}
    </div>

    <!-- News Headline -->
    <h2 class="trend-headline">${t.analysis?.headline || t.trend}</h2>
    <div class="trend-topic">🪙 Topic: <strong>${t.trend}</strong></div>
    
    <!-- News Summary -->
    ${t.analysis?.summary ? `
    <div class="news-summary crypto-summary">
      <p>${t.analysis.summary}</p>
    </div>
    ` : ''}
    
    <!-- Expert Analysis -->
    ${t.analysis?.expert_analysis ? `
    <div class="expert-analysis">
      <div class="analysis-header">💡 Market Analysis</div>
      <p>${t.analysis.expert_analysis}</p>
    </div>
    ` : ''}
    
    <!-- Origin Story -->
    <div class="origin-story origin-story-open">
      <div class="origin-header">
        <span>📜 Origin Story</span>
      </div>
      <div class="origin-content">
        <p>${t.analysis?.origin_story || 'This trend emerged from crypto community discussions.'}</p>
        <div class="origin-meta">
          <span>📅 First seen: ${formatTimestamp(t.timestamp)}</span>
          <span>📍 Started on: ${getOriginPlatform(t)}</span>
        </div>
      </div>
    </div>

    <div class="popularity-meter" title="Popularity: ${t.signal_score}%">
      <div class="meter-bar">
        <div class="meter-fill" style="width: ${Math.min(100, t.signal_score)}%; background: ${t.signal_score >= 70 ? '#10b981' : t.signal_score >= 40 ? '#f59e0b' : '#ef4444'}"></div>
      </div>
      <span class="meter-value">${t.signal_score}%</span>
    </div>

    <div class="metrics">
      🚀 Momentum: <strong>${t.momentum}</strong><br/>
      📊 Signal Score: <strong>${t.signal_score}</strong>
      ${t.platform_count ? `<br/>🌐 Trending on: <strong>${t.platform_count} platforms</strong>` : ''}
    </div>

    <div class="social platform-metrics">
      ${t.metrics?.x?.posts ? `<span class="platform-badge x">🐦 X: ${t.metrics.x.posts} posts · ${t.metrics.x.reposts} reposts</span>` : ''}
      ${t.metrics?.tiktok?.views ? `<span class="platform-badge tiktok">🎵 TikTok: ${t.metrics.tiktok.views} views</span>` : ''}
      ${t.metrics?.google?.searches ? `<span class="platform-badge google">🔍 Google: ${t.metrics.google.searches} searches</span>` : ''}
    </div>
  `;

  container.appendChild(card);
}

function renderPagination(totalPages, totalItems) {
  const paginationContainer = document.getElementById('pagination');
  if (!paginationContainer) return;
  
  if (totalPages <= 1) {
    paginationContainer.innerHTML = '';
    return;
  }
  
  let paginationHTML = '<div class="pagination-controls">';
  
  paginationHTML += `
    <button class="page-btn prev-btn" ${currentPage === 1 ? 'disabled' : ''} onclick="goToPage(${currentPage - 1})">
      ← Previous
    </button>
  `;
  
  paginationHTML += '<div class="page-numbers">';
  
  for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
    paginationHTML += `
      <button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">
        ${i}
      </button>
    `;
  }
  
  paginationHTML += '</div>';
  
  paginationHTML += `
    <button class="page-btn next-btn" ${currentPage === totalPages ? 'disabled' : ''} onclick="goToPage(${currentPage + 1})">
      Next →
    </button>
  `;
  
  paginationHTML += '</div>';
  paginationHTML += `<div class="pagination-info">Page ${currentPage} of ${totalPages} · ${totalItems} crypto trends</div>`;
  
  paginationContainer.innerHTML = paginationHTML;
}

function goToPage(page) {
  const filtered = filterCryptoByCategory(cryptoTrends, currentFilter);
  const totalPages = Math.ceil(filtered.length / TRENDS_PER_PAGE);
  
  if (page < 1 || page > totalPages) return;
  
  currentPage = page;
  renderTrends();
  container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Event Listeners
if (filterButtons) {
  filterButtons.addEventListener('click', (e) => {
    const btn = e.target.closest('.filter-btn');
    if (!btn) return;
    
    filterButtons.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    
    currentFilter = btn.dataset.filter;
    currentPage = 1;
    renderTrends();
  });
}

const sortSelect = document.getElementById('sort-select');
if (sortSelect) {
  sortSelect.addEventListener('change', (e) => {
    currentSort = e.target.value;
    cryptoTrends = sortTrends(cryptoTrends);
    renderTrends();
  });
}

const randomBtn = document.getElementById('random-trend-btn');
if (randomBtn) {
  randomBtn.addEventListener('click', () => {
    if (cryptoTrends.length === 0) return;
    const randomIndex = Math.floor(Math.random() * cryptoTrends.length);
    const randomTrend = cryptoTrends[randomIndex];
    
    // Find and highlight the trend
    container.innerHTML = '';
    renderTrend(randomTrend, 0);
    
    // Add random highlight animation
    const card = container.querySelector('.card');
    if (card) {
      card.classList.add('highlight', 'random-pick');
      setTimeout(() => card.classList.remove('random-pick'), 2000);
    }
  });
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  loadCryptoTrends();
  fetchCryptoPrices();
  
  // Refresh prices every 30 seconds
  setInterval(fetchCryptoPrices, 30000);
});
