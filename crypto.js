// Crypto Page JavaScript - Telegram Feed & Market Data
let allPosts = [];
let filteredPosts = [];
let currentFilter = 'all';
let displayedCount = 0;
const POSTS_PER_PAGE = 10;

// Type labels and icons
const TYPE_CONFIG = {
  market_overview: { icon: '📊', label: 'Market Overview' },
  onchain_analysis: { icon: '🔗', label: 'On-Chain Analysis' },
  trade_signal: { icon: '💹', label: 'Trade Signal' },
  whale_tracking: { icon: '🐋', label: 'Whale Tracking' },
  alert: { icon: '🚨', label: 'Alert' },
  analysis: { icon: '📈', label: 'Analysis' },
  general: { icon: '📝', label: 'Update' }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
  // Load all data in parallel
  await Promise.all([
    loadTelegramFeed(),
    fetchCoinGeckoTrending()
  ]);
  
  // Set up filter tabs
  setupFilterTabs();
  
  // Set up load more button
  setupLoadMore();
});

// Load Telegram feed from JSON
async function loadTelegramFeed() {
  const feed = document.getElementById('telegram-feed');
  
  try {
    const response = await fetch('./data/telegram_posts.json');
    if (!response.ok) throw new Error('No posts yet');
    
    const data = await response.json();
    allPosts = data.posts || [];
    
    // Update stats
    updateStats(data);
    
    // Update last updated time
    if (data.last_updated) {
      const date = new Date(data.last_updated);
      document.getElementById('last-update').textContent = 
        `Last updated: ${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
    }
    
    // Update mentioned coins
    updateMentionedCoins(allPosts);
    
    // Apply initial filter
    applyFilter('all');
    
  } catch (error) {
    console.error('Failed to load Telegram feed:', error);
    feed.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📱</div>
        <h3>No Posts Yet</h3>
        <p>Run generate.py to fetch posts from Telegram.</p>
        <a href="https://t.me/tkresearch_tradingchannel" target="_blank" class="filter-tab" style="display: inline-block; margin-top: 1rem;">
          View on Telegram →
        </a>
      </div>
    `;
  }
}

// Update stats sidebar
function updateStats(data) {
  document.getElementById('total-posts').textContent = data.total_posts || 0;
  document.getElementById('signals-count').textContent = data.type_counts?.trade_signal || 0;
  
  const analysisCount = (data.type_counts?.market_overview || 0) + 
                        (data.type_counts?.onchain_analysis || 0) +
                        (data.type_counts?.analysis || 0);
  document.getElementById('analysis-count').textContent = analysisCount;
  
  // Count unique coins
  const coins = new Set();
  (data.posts || []).forEach(post => {
    (post.coins || []).forEach(coin => coins.add(coin));
  });
  document.getElementById('coins-mentioned').textContent = coins.size;
  
  // Update topic counts
  updateTopicCounts(data);
}

// Update topic navigation counts
function updateTopicCounts(data) {
  const posts = data.posts || [];
  const typeCounts = data.type_counts || {};
  
  // All posts count
  const allCount = document.getElementById('all-count');
  if (allCount) allCount.textContent = posts.length;
  
  // Market overview count
  const marketCount = document.getElementById('market-count');
  if (marketCount) marketCount.textContent = typeCounts.market_overview || 0;
  
  // On-chain analysis count
  const onchainCount = document.getElementById('onchain-count');
  if (onchainCount) onchainCount.textContent = (typeCounts.onchain_analysis || 0) + (typeCounts.analysis || 0);
  
  // Trade signals count
  const signalCount = document.getElementById('signal-count');
  if (signalCount) signalCount.textContent = typeCounts.trade_signal || 0;
  
  // Whale tracking count
  const whaleCount = document.getElementById('whale-count');
  if (whaleCount) whaleCount.textContent = typeCounts.whale_tracking || 0;
  
  // Alerts count
  const alertCount = document.getElementById('alert-count');
  if (alertCount) alertCount.textContent = typeCounts.alert || 0;
}

// Update mentioned coins sidebar
function updateMentionedCoins(posts) {
  const container = document.getElementById('mentioned-coins');
  
  // Count coin mentions
  const coinCounts = {};
  posts.forEach(post => {
    (post.coins || []).forEach(coin => {
      coinCounts[coin] = (coinCounts[coin] || 0) + 1;
    });
  });
  
  // Sort by count
  const sortedCoins = Object.entries(coinCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8);
  
  if (sortedCoins.length === 0) {
    container.innerHTML = '<div class="empty-state" style="padding: 1rem;">No coins mentioned yet</div>';
    return;
  }
  
  container.innerHTML = sortedCoins.map(([coin, count], i) => `
    <div class="trending-item">
      <span class="trending-rank">${i + 1}</span>
      <span class="trending-name">$${coin}</span>
      <span class="trending-change">${count} mentions</span>
    </div>
  `).join('');
}

// Apply filter to posts
function applyFilter(filter) {
  currentFilter = filter;
  displayedCount = 0;
  
  if (filter === 'all') {
    filteredPosts = [...allPosts];
  } else {
    filteredPosts = allPosts.filter(post => post.type === filter);
  }
  
  // Update badge
  document.getElementById('post-count').textContent = `${filteredPosts.length} posts`;
  
  // Render first batch
  renderPosts();
}

// Render posts
function renderPosts() {
  const feed = document.getElementById('telegram-feed');
  const loadMoreContainer = document.getElementById('load-more-container');
  
  const postsToShow = filteredPosts.slice(0, displayedCount + POSTS_PER_PAGE);
  displayedCount = postsToShow.length;
  
  if (postsToShow.length === 0) {
    feed.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📭</div>
        <h3>No Posts Found</h3>
        <p>No posts match the selected filter.</p>
      </div>
    `;
    loadMoreContainer.style.display = 'none';
    return;
  }
  
  feed.innerHTML = postsToShow.map(post => renderPost(post)).join('');
  
  // Show/hide load more button
  loadMoreContainer.style.display = displayedCount < filteredPosts.length ? 'block' : 'none';
}

// Render single post
function renderPost(post) {
  const typeConfig = TYPE_CONFIG[post.type] || TYPE_CONFIG.general;
  const timestamp = post.timestamp ? formatDate(post.timestamp) : '';
  const views = post.views || '';
  
  // Format content with highlights
  let content = escapeHtml(post.content || '');
  
  // Highlight coin mentions
  content = content.replace(/\$([A-Z]{2,10})/g, '<strong>$$$1</strong>');
  
  // Highlight important keywords
  const highlights = ['Entry', 'TP', 'SL', 'Insight', 'Scenario', 'Key support', 'Key resistance'];
  highlights.forEach(word => {
    content = content.replace(new RegExp(`(${word}[:\\s])`, 'gi'), '<strong>$1</strong>');
  });
  
  // Build trade signal box if applicable
  let signalBox = '';
  if (post.trade_signal && (post.trade_signal.entry || post.trade_signal.tp.length > 0)) {
    signalBox = `
      <div class="trade-signal-box">
        ${post.trade_signal.entry ? `
          <div class="signal-row">
            <span class="signal-label">Entry</span>
            <span class="signal-value entry">$${post.trade_signal.entry}</span>
          </div>
        ` : ''}
        ${post.trade_signal.tp.length > 0 ? `
          <div class="signal-row">
            <span class="signal-label">Take Profit</span>
            <span class="signal-value tp">${post.trade_signal.tp.map(t => '$' + t).join(' → ')}</span>
          </div>
        ` : ''}
        ${post.trade_signal.sl ? `
          <div class="signal-row">
            <span class="signal-label">Stop Loss</span>
            <span class="signal-value sl">$${post.trade_signal.sl}</span>
          </div>
        ` : ''}
      </div>
    `;
  }
  
  // Build coins tags
  const coinsHtml = (post.coins || []).length > 0 ? `
    <div class="post-coins">
      ${post.coins.map(coin => `<span class="coin-tag">$${coin}</span>`).join('')}
    </div>
  ` : '';
  
  return `
    <div class="telegram-post ${post.type}">
      <div class="post-header">
        <span class="post-type ${post.type}">
          ${typeConfig.icon} ${typeConfig.label}
        </span>
        <div class="post-meta">
          ${views ? `<span>👁 ${views}</span>` : ''}
          ${timestamp ? `<span>📅 ${timestamp}</span>` : ''}
          <a href="${post.url}" target="_blank" style="color: var(--accent);">🔗</a>
        </div>
      </div>
      <div class="post-content">${content}</div>
      ${signalBox}
      ${coinsHtml}
    </div>
  `;
}

// Setup filter tabs
function setupFilterTabs() {
  const tabs = document.querySelectorAll('.topic-item[data-filter]');
  
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      // Update active state
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      
      // Apply filter
      applyFilter(tab.dataset.filter);
    });
  });
}

// Setup load more button
function setupLoadMore() {
  const btn = document.getElementById('load-more-btn');
  if (btn) {
    btn.addEventListener('click', () => {
      renderPosts();
    });
  }
}

// Fetch CoinGecko trending coins for scrolling ticker
async function fetchCoinGeckoTrending() {
  const track = document.getElementById('ticker-track');
  const sidebarContainer = document.getElementById('coingecko-trending');
  
  try {
    const response = await fetch('https://api.coingecko.com/api/v3/search/trending');
    const data = await response.json();
    
    const coins = (data.coins || []).slice(0, 15);
    
    if (coins.length === 0) {
      track.innerHTML = '<div class="ticker-item"><span>No trending data available</span></div>';
      return;
    }
    
    // Build ticker items
    const tickerHTML = coins.map((coin, i) => {
      const item = coin.item;
      const priceChange = item.data?.price_change_percentage_24h?.usd || 0;
      const changeClass = priceChange >= 0 ? 'up' : 'down';
      const price = item.data?.price ? `$${parseFloat(item.data.price).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 6})}` : '--';
      const thumb = item.thumb || '';
      
      return `
        <div class="ticker-item" title="${item.name}">
          <span class="ticker-rank">${i + 1}</span>
          ${thumb ? `<img class="ticker-icon" src="${thumb}" alt="${item.symbol}" onerror="this.className='ticker-icon placeholder';this.innerHTML='${item.symbol.substring(0,2).toUpperCase()}';this.src=''">` : `<div class="ticker-icon placeholder">${item.symbol.substring(0,2).toUpperCase()}</div>`}
          <div class="ticker-info">
            <span class="ticker-symbol">${item.symbol.toUpperCase()}</span>
            <span class="ticker-name">${item.name}</span>
          </div>
          <span class="ticker-price">${price}</span>
          <span class="ticker-change ${changeClass}">${priceChange >= 0 ? '+' : ''}${priceChange.toFixed(1)}%</span>
        </div>
      `;
    }).join('');
    
    // Duplicate for seamless looping
    track.innerHTML = tickerHTML + tickerHTML;
    
    // Also update sidebar
    if (sidebarContainer) {
      sidebarContainer.innerHTML = coins.slice(0, 7).map((coin, i) => {
        const item = coin.item;
        const priceChange = item.data?.price_change_percentage_24h?.usd || 0;
        const changeClass = priceChange >= 0 ? 'up' : 'down';
        
        return `
          <div class="trending-item">
            <span class="trending-rank">${i + 1}</span>
            <span class="trending-name">${item.symbol.toUpperCase()}</span>
            <span class="trending-change ${changeClass}">${priceChange >= 0 ? '+' : ''}${priceChange.toFixed(1)}%</span>
          </div>
        `;
      }).join('');
    }
  } catch (error) {
    console.error('Failed to fetch CoinGecko trending:', error);
    track.innerHTML = '<div class="ticker-item"><span>Failed to load trending coins</span></div>';
    if (sidebarContainer) {
      sidebarContainer.innerHTML = '<div class="empty-state" style="padding: 1rem;">Failed to load</div>';
    }
  }
}

// Utility: Format date
function formatDate(dateStr) {
  try {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
  } catch {
    return '';
  }
}

// Utility: Escape HTML
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
