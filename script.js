const container = document.getElementById("trends");
const filterButtons = document.getElementById("filter-buttons");
const trendsCount = document.getElementById("trends-count");

let allTrends = [];
let currentFilter = "all";
let currentSort = "score";
let currentPage = 1;
const TRENDS_PER_PAGE = 10;

// Live update tracking
let lastUpdateTime = null;

// Check URL for category and page parameters
function getCategoryFromURL() {
  const params = new URLSearchParams(window.location.search);
  return params.get('category') || 'all';
}

function getPageFromURL() {
  const params = new URLSearchParams(window.location.search);
  return parseInt(params.get('page')) || 1;
}

function getHighlightFromURL() {
  const params = new URLSearchParams(window.location.search);
  return params.get('highlight') || null;
}

// Category detection keywords
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

// Detect category from trend name and analysis
function detectCategory(trend) {
  const text = `${trend.trend} ${trend.analysis?.analysis || ""}`.toLowerCase();
  
  for (const [category, keywords] of Object.entries(categoryKeywords)) {
    for (const keyword of keywords) {
      if (text.includes(keyword)) {
        return category;
      }
    }
  }
  return "other";
}

// === NEW FEATURE FUNCTIONS ===

// SEEN TRENDS TRACKING
const SEEN_TRENDS_KEY = 'trend_radar_seen_trends';

function getSeenTrends() {
  const stored = localStorage.getItem(SEEN_TRENDS_KEY);
  return stored ? JSON.parse(stored) : {};
}

function markTrendAsSeen(trendName) {
  const seen = getSeenTrends();
  seen[trendName] = Date.now();
  // Keep only last 100 trends
  const entries = Object.entries(seen).sort((a, b) => b[1] - a[1]).slice(0, 100);
  localStorage.setItem(SEEN_TRENDS_KEY, JSON.stringify(Object.fromEntries(entries)));
}

function getMissedTrends(trends) {
  const seen = getSeenTrends();
  const now = Date.now();
  const hours48 = 48 * 60 * 60 * 1000;
  
  return trends.filter(t => {
    const seenTime = seen[t.trend];
    // Not seen OR seen more than 48 hours ago
    return !seenTime || (now - seenTime > hours48);
  });
}

// SPEED INDICATOR
function getSpeedIndicator(momentum, direction) {
  if (momentum > 20 || direction === 'rising') {
    return { icon: '🚀', label: 'Exploding', class: 'speed-exploding' };
  } else if (momentum > 5) {
    return { icon: '📈', label: 'Growing', class: 'speed-growing' };
  } else if (momentum < -10 || direction === 'falling') {
    return { icon: '📉', label: 'Fading', class: 'speed-fading' };
  } else {
    return { icon: '➡️', label: 'Stable', class: 'speed-stable' };
  }
}

// AUTHENTICITY SCORE
function calculateAuthenticityScore(trend) {
  let score = 50; // Base score
  
  // Multi-platform presence increases authenticity
  const platforms = trend.social_presence || {};
  if (platforms.x === 'high') score += 15;
  if (platforms.tiktok === 'high') score += 15;
  if (platforms.instagram === 'high') score += 10;
  
  // Google Trends data increases authenticity
  if (trend.google_trends?.interest_score > 50) score += 10;
  
  // History data increases authenticity
  if (trend.history && trend.history.length > 1) score += 10;
  
  // Very sudden spikes might indicate bots
  const momentum = parseFloat(trend.momentum?.replace('%', '') || '0');
  if (momentum > 50) score -= 15;
  
  // Cap at 100
  score = Math.min(100, Math.max(0, score));
  
  let label, icon;
  if (score >= 80) {
    label = 'Highly Organic';
    icon = '✅';
  } else if (score >= 60) {
    label = 'Likely Organic';
    icon = '👍';
  } else if (score >= 40) {
    label = 'Mixed Signals';
    icon = '⚠️';
  } else {
    label = 'Possibly Artificial';
    icon = '🤖';
  }
  
  return { score, label, icon };
}

// ORIGIN STORY GENERATOR
function generateOriginStory(trend) {
  const category = trend.category || 'other';
  const platforms = trend.social_presence || {};
  const direction = trend.google_trends?.trend_direction || 'stable';
  
  const platformList = [];
  if (platforms.tiktok === 'high') platformList.push('TikTok');
  if (platforms.x === 'high') platformList.push('X (Twitter)');
  if (platforms.instagram === 'high') platformList.push('Instagram');
  
  const platformText = platformList.length > 0 
    ? `gaining traction on ${platformList.join(' and ')}`
    : 'emerging across social media';
  
  const categoryStories = {
    memes: `This meme started ${platformText}. It quickly spread as users created their own variations, turning it into a viral sensation.`,
    crypto: `This crypto trend began in trading communities before ${platformText}. Traders and enthusiasts are actively discussing its potential.`,
    technology: `Tech enthusiasts first noticed this trend, which is now ${platformText}. It reflects growing interest in emerging technologies.`,
    gaming: `Gamers discovered this trend which is now ${platformText}. The gaming community is actively engaging with related content.`,
    entertainment: `Entertainment fans picked up on this trend, ${platformText}. It's generating buzz across pop culture discussions.`,
    politics: `This political trend emerged from current events, now ${platformText}. It reflects ongoing public discourse.`,
    sports: `Sports fans started discussing this, now ${platformText}. Athletes and teams may be involved in the conversation.`,
    music: `Music lovers discovered this trend, ${platformText}. Artists and fans are driving the conversation.`,
    news: `Breaking developments led to this trend, ${platformText}. It's connected to recent news events.`,
    culture: `Cultural observers noted this trend, ${platformText}. It reflects shifting cultural conversations.`,
    other: `This trend emerged organically, ${platformText}. It's capturing attention across multiple communities.`
  };
  
  return categoryStories[category] || categoryStories.other;
}

// FORMAT TIMESTAMP
function formatTimestamp(timestamp) {
  if (!timestamp) return 'Unknown';
  const date = new Date(timestamp);
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// FORMAT POST DATE (with relative time for recent posts)
function formatPostDate(timestamp) {
  if (!timestamp) return 'Unknown';
  
  // Handle relative timestamps like "2 hours ago"
  if (typeof timestamp === 'string' && timestamp.includes('ago')) {
    return timestamp;
  }
  
  const now = new Date();
  const date = parseTrendDate(timestamp);
  
  if (!date || isNaN(date.getTime())) {
    return timestamp; // Return as-is if can't parse
  }
  
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  // Show relative time for recent posts
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  // Show full date for older posts
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
  }) + ' · ' + date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit'
  });
}

// GET ORIGIN PLATFORM
function getOriginPlatform(trend) {
  const platforms = trend.social_presence || {};
  if (platforms.tiktok === 'high') return 'TikTok';
  if (platforms.x === 'high') return 'X (Twitter)';
  if (platforms.instagram === 'high') return 'Instagram';
  return 'Multiple platforms';
}

// RELATED TRENDS
function getRelatedTrends(currentTrend, allTrends) {
  const category = currentTrend.category;
  return allTrends
    .filter(t => t.trend !== currentTrend.trend && t.category === category)
    .slice(0, 3);
}

// TOGGLE ORIGIN STORY
function toggleOriginStory(element) {
  const content = element.nextElementSibling;
  const toggle = element.querySelector('.origin-toggle');
  if (content.style.display === 'none') {
    content.style.display = 'block';
    toggle.textContent = '▲';
  } else {
    content.style.display = 'none';
    toggle.textContent = '▼';
  }
}

// SCROLL TO TREND BY NAME
function scrollToTrendByName(trendName) {
  const cards = document.querySelectorAll('.card');
  for (const card of cards) {
    const title = card.querySelector('h2');
    if (title && title.textContent === trendName) {
      card.scrollIntoView({ behavior: 'smooth', block: 'center' });
      card.style.animation = 'none';
      card.offsetHeight;
      card.style.animation = 'highlight-pulse 2s ease';
      break;
    }
  }
}

// TOPIC ALERTS
const TOPIC_ALERTS_KEY = 'trend_radar_topic_alerts';

function getTopicAlerts() {
  const stored = localStorage.getItem(TOPIC_ALERTS_KEY);
  return stored ? JSON.parse(stored) : [];
}

function isTopicAlertEnabled(trendName) {
  return getTopicAlerts().includes(trendName);
}

function toggleTopicAlert(event, trendName) {
  event.stopPropagation();
  const alerts = getTopicAlerts();
  const idx = alerts.indexOf(trendName);
  
  if (idx > -1) {
    alerts.splice(idx, 1);
    showToast(`🔕 Alerts disabled for "${trendName}"`);
  } else {
    alerts.push(trendName);
    showToast(`🔔 You'll be alerted when "${trendName}" updates`);
  }
  
  localStorage.setItem(TOPIC_ALERTS_KEY, JSON.stringify(alerts));
  
  // Update button
  const btn = event.target.closest('.alert-btn');
  if (btn) {
    btn.classList.toggle('active');
    btn.textContent = alerts.includes(trendName) ? '🔔' : '🔕';
  }
}

// Update live status display
function updateLiveStatus() {
  const lastUpdatedEl = document.getElementById('last-updated-time');
  
  if (lastUpdatedEl && lastUpdateTime) {
    const now = new Date();
    const diff = Math.floor((now - lastUpdateTime) / 1000);
    if (diff < 60) {
      lastUpdatedEl.textContent = 'Just now';
    } else if (diff < 3600) {
      lastUpdatedEl.textContent = `${Math.floor(diff / 60)}m ago`;
    } else {
      lastUpdatedEl.textContent = lastUpdateTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
  }
}

async function loadTrends() {
  // Show skeleton loading
  if (typeof SkeletonLoader !== 'undefined') {
    SkeletonLoader.show(container);
  }
  
  let index;
  try {
    const res = await fetch(`./data/index.json?ts=${Date.now()}`);
    index = await res.json();
  } catch {
    container.innerHTML = "<p class='error-message'>Failed to load trends. Please try again.</p>";
    return;
  }

  // Track previous trend count for new trend detection
  const previousTrendCount = allTrends.length;
  allTrends = [];

  for (const file of index.files) {
    try {
      const res = await fetch(`./data/${file}?ts=${Date.now()}`);
      const data = await res.json();
      data.category = data.category || detectCategory(data);
      allTrends.push(data);
    } catch {}
  }

  // Update last update time
  lastUpdateTime = new Date();
  updateLiveStatus();
  
  // Show notification if new trends were added
  if (previousTrendCount > 0 && allTrends.length > previousTrendCount) {
    const newCount = allTrends.length - previousTrendCount;
    showNewTrendsNotification(newCount);
  }

  // Apply sort
  allTrends = sortTrends(allTrends);
  displayedCount = 0;
  renderTrends();
}

// Show notification for new trends
function showNewTrendsNotification(count) {
  const notification = document.createElement('div');
  notification.className = 'new-trends-notification';
  notification.innerHTML = `
    <span class="notification-pulse"></span>
    🆕 ${count} new trend${count > 1 ? 's' : ''} detected!
  `;
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.classList.add('fade-out');
    setTimeout(() => notification.remove(), 500);
  }, 4000);
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
  
  const filtered = currentFilter === "all" 
    ? allTrends 
    : allTrends.filter(t => t.category === currentFilter);

  const totalPages = Math.ceil(filtered.length / TRENDS_PER_PAGE);
  
  // Validate current page
  if (currentPage > totalPages) currentPage = totalPages;
  if (currentPage < 1) currentPage = 1;

  // Calculate start and end indices
  const startIndex = (currentPage - 1) * TRENDS_PER_PAGE;
  const endIndex = Math.min(startIndex + TRENDS_PER_PAGE, filtered.length);
  const trendsToRender = filtered.slice(startIndex, endIndex);

  // Update count display
  if (trendsCount) {
    trendsCount.textContent = `Showing ${startIndex + 1}-${endIndex} of ${filtered.length} trends`;
  }

  if (filtered.length === 0) {
    container.innerHTML = `<p class='no-results'>No trends found in this category. Try selecting "All" to see all trends.</p>`;
    renderPagination(0, 0);
    return;
  }

  // Render trends
  trendsToRender.forEach((trend, index) => {
    renderTrend(trend, index);
  });
  
  // Render pagination controls
  renderPagination(totalPages, filtered.length);
  
  // Update URL
  updateURL();
}

function renderPagination(totalPages, totalItems) {
  const paginationContainer = document.getElementById('pagination');
  if (!paginationContainer) return;
  
  if (totalPages <= 1) {
    paginationContainer.innerHTML = '';
    return;
  }
  
  let paginationHTML = '<div class="pagination-controls">';
  
  // Previous button
  paginationHTML += `
    <button class="page-btn prev-btn" ${currentPage === 1 ? 'disabled' : ''} onclick="goToPage(${currentPage - 1})">
      ← Previous
    </button>
  `;
  
  // Page numbers
  paginationHTML += '<div class="page-numbers">';
  
  // Always show first page
  if (currentPage > 3) {
    paginationHTML += `<button class="page-btn" onclick="goToPage(1)">1</button>`;
    if (currentPage > 4) {
      paginationHTML += `<span class="page-ellipsis">...</span>`;
    }
  }
  
  // Show pages around current page
  for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
    paginationHTML += `
      <button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">
        ${i}
      </button>
    `;
  }
  
  // Always show last page
  if (currentPage < totalPages - 2) {
    if (currentPage < totalPages - 3) {
      paginationHTML += `<span class="page-ellipsis">...</span>`;
    }
    paginationHTML += `<button class="page-btn" onclick="goToPage(${totalPages})">${totalPages}</button>`;
  }
  
  paginationHTML += '</div>';
  
  // Next button
  paginationHTML += `
    <button class="page-btn next-btn" ${currentPage === totalPages ? 'disabled' : ''} onclick="goToPage(${currentPage + 1})">
      Next →
    </button>
  `;
  
  paginationHTML += '</div>';
  
  // Page info
  paginationHTML += `
    <div class="pagination-info">
      Page ${currentPage} of ${totalPages} · ${totalItems} total trends
    </div>
  `;
  
  paginationContainer.innerHTML = paginationHTML;
}

function goToPage(page) {
  const filtered = currentFilter === "all" 
    ? allTrends 
    : allTrends.filter(t => t.category === currentFilter);
  const totalPages = Math.ceil(filtered.length / TRENDS_PER_PAGE);
  
  if (page < 1 || page > totalPages) return;
  
  currentPage = page;
  renderTrends();
  
  // Scroll to top of trends
  container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function updateURL() {
  const url = new URL(window.location);
  
  if (currentFilter === 'all') {
    url.searchParams.delete('category');
  } else {
    url.searchParams.set('category', currentFilter);
  }
  
  if (currentPage === 1) {
    url.searchParams.delete('page');
  } else {
    url.searchParams.set('page', currentPage);
  }
  
  window.history.replaceState({}, '', url);
}

function renderTrend(t, index = 0) {
  const card = document.createElement("div");
  card.className = "card flip-reveal";
  card.style.animationDelay = `${index * 0.05}s`;
  if (t.highlight) card.classList.add("highlight");

  // Ensure lifecycle exists with fallback
  if (!t.lifecycle) {
    t.lifecycle = t.signal_score >= 80 ? 'new' : (t.signal_score >= 60 ? 'rising' : (t.signal_score >= 40 ? 'peak' : 'declining'));
  }

  const categoryIcon = getCategoryIcon(t.category);
  
  // Check if hot
  const isHot = t.signal_score >= 80 || parseFloat(t.momentum || '0') > 20 || t.lifecycle === 'new';
  const hotBadge = isHot ? '<span class="hot-badge">🔥 HOT</span>' : '';
  
  // Check if bookmarked
  const isBookmarked = typeof Bookmarks !== 'undefined' && Bookmarks.isBookmarked(t.trend);
  
  // Get timestamp (from root or history)
  const trendTimestamp = t.timestamp || t.history?.[0]?.timestamp || null;
  
  // Analysis text
  const analysisText = t.analysis?.insight || t.google_trends?.description || '';
  
  // === NEW FEATURES ===
  
  // Trend Speed Indicator
  const momentum = parseFloat(t.momentum?.replace('%', '') || '0');
  const speedIndicator = getSpeedIndicator(momentum, t.google_trends?.trend_direction);
  
  // Authenticity Score (based on social presence patterns)
  const authenticityScore = calculateAuthenticityScore(t);
  
  // Origin Story
  const originStory = generateOriginStory(t);
  
  // Related Trends
  const relatedTrends = getRelatedTrends(t, allTrends);
  
  // Mark as seen
  markTrendAsSeen(t.trend);

  card.innerHTML = `
    <div class="card-header">
      <span class="category-tag">${categoryIcon} ${t.category || 'other'}</span>
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
    <div class="trend-topic">📌 Topic: <strong>${t.trend}</strong></div>
    
    <!-- News Summary -->
    ${t.analysis?.summary ? `
    <div class="news-summary">
      <p>${t.analysis.summary}</p>
    </div>
    ` : ''}
    
    <!-- Expert Analysis -->
    ${t.analysis?.expert_analysis ? `
    <div class="expert-analysis">
      <div class="analysis-header">💡 Analysis</div>
      <p>${t.analysis.expert_analysis}</p>
    </div>
    ` : ''}
    
    <!-- Origin Story -->
    <div class="origin-story origin-story-open">
      <div class="origin-header">
        <span>📜 Origin Story</span>
      </div>
      <div class="origin-content">
        <p>${t.analysis?.origin_story || originStory}</p>
        <div class="origin-meta">
          <span>📅 First seen: ${formatTimestamp(t.timestamp)}</span>
          <span>📍 Started on: ${getOriginPlatform(t)}</span>
        </div>
      </div>
    </div>

    <div class="metrics">
      🚀 Momentum: <strong>${t.momentum}</strong><br/>
      📊 Signal Score: <strong>${t.signal_score}</strong>
      ${t.platform_count ? `<br/>🌐 Trending on: <strong>${t.platform_count} platforms</strong>` : ''}
    </div>

    <div class="social platform-metrics">
      ${t.metrics?.x?.posts ? `<span class="platform-badge x">🐦 X: ${t.metrics.x.posts} posts · ${t.metrics.x.reposts} reposts</span>` : 
        (t.social_presence?.x ? `<span>🐦 X: ${t.social_presence.x}</span>` : '')}
      ${t.metrics?.tiktok?.views ? `<span class="platform-badge tiktok">🎵 TikTok: ${t.metrics.tiktok.views} views · ${t.metrics.tiktok.videos} videos</span>` : 
        (t.social_presence?.tiktok ? `<span>🎵 TikTok: ${t.social_presence.tiktok}</span>` : '')}
      ${t.metrics?.instagram?.posts ? `<span class="platform-badge instagram">📸 IG: ${t.metrics.instagram.posts} posts · ${t.metrics.instagram.reach} reach</span>` : 
        (t.social_presence?.instagram ? `<span>📸 IG: ${t.social_presence.instagram}</span>` : '')}
      ${t.metrics?.google?.searches ? `<span class="platform-badge google">🔍 Google: ${t.metrics.google.searches} searches</span>` : ''}
    </div>
    
    <!-- Related Trends -->
    ${relatedTrends.length > 0 ? `
    <div class="related-trends">
      <div class="related-header">🔗 Related Trends</div>
      <div class="related-list">
        ${relatedTrends.map(rt => `
          <a href="#" class="related-tag" onclick="scrollToTrendByName('${rt.trend.replace(/'/g, "\\'")}'); return false;">
            ${rt.trend}
          </a>
        `).join('')}
      </div>
    </div>
    ` : ''}

    <div class="card-actions">
      <button class="bookmark-btn ${isBookmarked ? 'active' : ''}" onclick="toggleBookmark(event, '${t.trend.replace(/'/g, "\\'")}')">
        ${isBookmarked ? '🔖' : '📑'}
      </button>
      <button class="comment-toggle-btn" onclick="toggleComments(event, '${t.trend.replace(/'/g, "\\'")}')">
        💬 <span class="comment-count">${getCommentCount(t.trend)}</span>
      </button>
      <button class="alert-btn ${isTopicAlertEnabled(t.trend) ? 'active' : ''}" onclick="toggleTopicAlert(event, '${t.trend.replace(/'/g, "\\'")}')" title="Get alerts for this topic">
        ${isTopicAlertEnabled(t.trend) ? '🔔' : '🔕'}
      </button>
      <div class="share-buttons">
        <button class="share-btn" onclick="copyTrendLink('${t.trend.replace(/'/g, "\\'")}')" title="Copy link">📋</button>
        <button class="share-btn twitter" onclick="shareTwitter('${t.trend.replace(/'/g, "\\'")}')" title="Share on X">𝕏</button>
        <button class="share-btn whatsapp" onclick="shareWhatsApp('${t.trend.replace(/'/g, "\\'")}')" title="Share on WhatsApp">💬</button>
      </div>
    </div>

    <div class="reaction-bar" data-trend="${t.trend}">
      ${['🔥', '🤯', '😂', '👀', '💯', '🚀'].map(emoji => {
        const count = getReactionCount(t.trend, emoji);
        const isActive = isUserReacted(t.trend, emoji);
        return `
          <button class="reaction-btn ${isActive ? 'active' : ''}" onclick="handleReaction(event, '${t.trend.replace(/'/g, "\\'")}', '${emoji}')">
            <span class="reaction-emoji">${emoji}</span>
            <span class="reaction-count">${count}</span>
          </button>
        `;
      }).join('')}
    </div>

    <!-- Comments Dropdown -->
    <div class="comments-dropdown" id="comments-${t.trend.replace(/\s+/g, '-').replace(/'/g, '')}" style="display: none;">
      <div class="comments-header">
        <span>💬 Comments</span>
        <button class="close-comments" onclick="closeComments('${t.trend.replace(/'/g, "\\'")}')">&times;</button>
      </div>
      <form class="comment-form" onsubmit="submitComment(event, '${t.trend.replace(/'/g, "\\'")}')">
        <input type="text" class="comment-input" placeholder="Write a comment..." required />
        <button type="submit" class="comment-submit">Post</button>
      </form>
      <div class="comments-list" id="comments-list-${t.trend.replace(/\s+/g, '-').replace(/'/g, '')}">
        ${renderComments(t.trend)}
      </div>
    </div>
  `;

  if (t.token) {
    const tokenDiv = document.createElement('div');
    tokenDiv.className = 'token';
    tokenDiv.innerHTML = `
      🪙 <strong>${t.token.symbol}</strong> (${t.token.chain})<br/>
      Liquidity: $${t.token.liquidity_usd?.toLocaleString() || "N/A"}<br/>
      <a href="${t.token.url}" target="_blank" rel="noopener">View on DexScreener →</a>
    `;
    card.appendChild(tokenDiv);
  }

  container.appendChild(card);
}

// Bookmark functions
function toggleBookmark(event, trendName) {
  event.stopPropagation();
  const trend = allTrends.find(t => t.trend === trendName);
  if (!trend || typeof Bookmarks === 'undefined') return;
  
  const isNowBookmarked = Bookmarks.toggle(trend);
  const btn = event.currentTarget;
  btn.classList.toggle('active', isNowBookmarked);
  btn.textContent = isNowBookmarked ? '🔖' : '📑';
}

// Share functions
function copyTrendLink(trendName) {
  const url = `${window.location.origin}/trending.html?highlight=${encodeURIComponent(trendName)}`;
  navigator.clipboard.writeText(url).then(() => {
    showToast('Link copied! 📋');
  });
}

function shareTwitter(trendName) {
  const url = `${window.location.origin}/trending.html?highlight=${encodeURIComponent(trendName)}`;
  const text = `Check out this trending topic: ${trendName} 🔥 via @TrendRadar`;
  window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`, '_blank');
}

function shareWhatsApp(trendName) {
  const url = `${window.location.origin}/trending.html?highlight=${encodeURIComponent(trendName)}`;
  const text = `Check out this trending topic: ${trendName} 🔥 ${url}`;
  window.open(`https://api.whatsapp.com/send?text=${encodeURIComponent(text)}`, '_blank');
}

// Reaction handler
function handleReaction(event, trendName, emoji) {
  event.stopPropagation();
  
  const REACTIONS_KEY = 'trend_radar_reactions';
  let reactions = JSON.parse(localStorage.getItem(REACTIONS_KEY) || '{}');
  
  if (!reactions[trendName]) {
    reactions[trendName] = { counts: {}, userReactions: [] };
  }
  
  const userReacted = reactions[trendName].userReactions.includes(emoji);
  
  if (userReacted) {
    // Remove reaction
    reactions[trendName].userReactions = reactions[trendName].userReactions.filter(e => e !== emoji);
    reactions[trendName].counts[emoji] = Math.max(0, (reactions[trendName].counts[emoji] || 1) - 1);
  } else {
    // Add reaction
    reactions[trendName].userReactions.push(emoji);
    reactions[trendName].counts[emoji] = (reactions[trendName].counts[emoji] || 0) + 1;
  }
  
  localStorage.setItem(REACTIONS_KEY, JSON.stringify(reactions));
  
  // Update UI
  const btn = event.currentTarget;
  btn.classList.toggle('active', !userReacted);
  const countEl = btn.querySelector('.reaction-count');
  countEl.textContent = reactions[trendName].counts[emoji] || 0;
  
  // Animate
  btn.style.transform = 'scale(1.2)';
  setTimeout(() => btn.style.transform = '', 200);
}

// Get reaction count
function getReactionCount(trendName, emoji) {
  const REACTIONS_KEY = 'trend_radar_reactions';
  const reactions = JSON.parse(localStorage.getItem(REACTIONS_KEY) || '{}');
  // Start with some base counts for visual appeal
  const baseCount = Math.floor(Math.random() * 30) + 5;
  return (reactions[trendName]?.counts?.[emoji] || 0) + baseCount;
}

// Check if user reacted
function isUserReacted(trendName, emoji) {
  const REACTIONS_KEY = 'trend_radar_reactions';
  const reactions = JSON.parse(localStorage.getItem(REACTIONS_KEY) || '{}');
  return reactions[trendName]?.userReactions?.includes(emoji) || false;
}

// Comments functions
const COMMENTS_KEY = 'trend_radar_comments';

function getComments(trendName) {
  const comments = JSON.parse(localStorage.getItem(COMMENTS_KEY) || '{}');
  return comments[trendName] || [];
}

function getCommentCount(trendName) {
  return getComments(trendName).length;
}

function renderComments(trendName) {
  const comments = getComments(trendName);
  if (comments.length === 0) {
    return '<p class="no-comments">No comments yet. Be the first to comment!</p>';
  }
  return comments.map(c => `
    <div class="comment">
      <div class="comment-header">
        <span class="comment-avatar">👤</span>
        <span class="comment-author">${c.author}</span>
        <span class="comment-date">${new Date(c.timestamp).toLocaleDateString()}</span>
      </div>
      <p class="comment-text">${c.text}</p>
    </div>
  `).join('');
}

function toggleComments(event, trendName) {
  event.stopPropagation();
  const id = 'comments-' + trendName.replace(/\s+/g, '-').replace(/'/g, '');
  const dropdown = document.getElementById(id);
  
  // Close all other dropdowns first
  document.querySelectorAll('.comments-dropdown').forEach(d => {
    if (d.id !== id) d.style.display = 'none';
  });
  
  if (dropdown) {
    const isVisible = dropdown.style.display === 'block';
    dropdown.style.display = isVisible ? 'none' : 'block';
    
    if (!isVisible) {
      // Refresh comments list
      const listId = 'comments-list-' + trendName.replace(/\s+/g, '-').replace(/'/g, '');
      const list = document.getElementById(listId);
      if (list) list.innerHTML = renderComments(trendName);
    }
  }
}

function closeComments(trendName) {
  const id = 'comments-' + trendName.replace(/\s+/g, '-').replace(/'/g, '');
  const dropdown = document.getElementById(id);
  if (dropdown) dropdown.style.display = 'none';
}

function submitComment(event, trendName) {
  event.preventDefault();
  event.stopPropagation();
  
  const form = event.target;
  const input = form.querySelector('.comment-input');
  const text = input.value.trim();
  
  if (!text) return;
  
  // Save comment
  const comments = JSON.parse(localStorage.getItem(COMMENTS_KEY) || '{}');
  if (!comments[trendName]) comments[trendName] = [];
  
  comments[trendName].unshift({
    id: Date.now(),
    text: text,
    author: 'You',
    timestamp: new Date().toISOString()
  });
  
  localStorage.setItem(COMMENTS_KEY, JSON.stringify(comments));
  
  // Update UI
  const listId = 'comments-list-' + trendName.replace(/\s+/g, '-').replace(/'/g, '');
  const list = document.getElementById(listId);
  if (list) list.innerHTML = renderComments(trendName);
  
  // Update count on button
  const card = form.closest('.card');
  const countEl = card.querySelector('.comment-count');
  if (countEl) countEl.textContent = getCommentCount(trendName);
  
  // Clear input
  input.value = '';
  showToast('Comment posted! 💬');
}

// Toast notification
function showToast(message) {
  const existing = document.querySelector('.toast-notification');
  if (existing) existing.remove();
  
  const toast = document.createElement('div');
  toast.className = 'toast-notification';
  toast.textContent = message;
  document.body.appendChild(toast);
  
  setTimeout(() => toast.classList.add('show'), 10);
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 2000);
}

// Random trend discovery
function discoverRandomTrend() {
  if (allTrends.length === 0) return;
  const randomTrend = allTrends[Math.floor(Math.random() * allTrends.length)];
  showToast(`Discovered: ${randomTrend.trend} 🎲`);
  
  // Scroll to and highlight the card
  const cards = document.querySelectorAll('.card');
  cards.forEach(card => {
    if (card.querySelector('h2').textContent === randomTrend.trend) {
      card.scrollIntoView({ behavior: 'smooth', block: 'center' });
      card.style.animation = 'none';
      card.offsetHeight; // Trigger reflow
      card.style.animation = 'highlight-pulse 2s ease';
    }
  });
}

// Sort handler
function handleSort(sortBy) {
  currentSort = sortBy;
  currentPage = 1;
  allTrends = sortTrends(allTrends);
  renderTrends();
  updateURL();
}

function getCategoryIcon(category) {
  const icons = {
    politics: "🏛️",
    technology: "💻",
    crypto: "🪙",
    gaming: "🎮",
    entertainment: "🎬",
    memes: "😂",
    sports: "🏈",
    news: "📰",
    music: "🎵",
    culture: "🛍️",
    other: "🌐"
  };
  return icons[category] || "🌐";
}

// Filter button handlers
if (filterButtons) {
  filterButtons.addEventListener("click", (e) => {
    if (e.target.classList.contains("filter-btn")) {
      // Update active state
      document.querySelectorAll(".filter-btn").forEach(btn => btn.classList.remove("active"));
      e.target.classList.add("active");
      
      // Apply filter and reset to page 1
      currentFilter = e.target.dataset.category;
      currentPage = 1;
      renderTrends();
      updateURL();
      
      // Update URL category without page reload
      const url = new URL(window.location);
      if (currentFilter === 'all') {
        url.searchParams.delete('category');
      } else {
        url.searchParams.set('category', currentFilter);
      }
      window.history.replaceState({}, '', url);
    }
  });
}

// Sort select handler
const sortSelect = document.getElementById('sort-select');
if (sortSelect) {
  sortSelect.addEventListener('change', (e) => {
    handleSort(e.target.value);
  });
}

// Random trend button
const randomBtn = document.getElementById('random-trend-btn');
if (randomBtn) {
  randomBtn.addEventListener('click', discoverRandomTrend);
}

// Apply category from URL on page load
function applyURLCategory() {
  currentFilter = getCategoryFromURL();
  
  // Update active button state
  if (filterButtons) {
    document.querySelectorAll(".filter-btn").forEach(btn => {
      btn.classList.remove("active");
      if (btn.dataset.category === currentFilter) {
        btn.classList.add("active");
      }
    });
  }
}

// Live viewer count updater
function updateLiveViewers() {
  document.querySelectorAll('.live-viewers').forEach(el => {
    const base = parseInt(el.dataset.base || '10');
    const variation = Math.floor(Math.random() * 10) - 5;
    const viewers = Math.max(1, base + variation);
    const countEl = el.querySelector('.viewer-count');
    if (countEl) countEl.textContent = viewers;
  });
}

// Initialize
applyURLCategory();
currentPage = getPageFromURL();
loadTrends().then(() => {
  // Initialize missed trends after loading
  initMissedTrends();
  // Initialize topic alerts panel
  initTopicAlerts();
  
  // Check for highlight parameter from search
  const highlightTrend = getHighlightFromURL();
  if (highlightTrend) {
    // Find the trend and scroll to it
    setTimeout(() => {
      const cards = document.querySelectorAll('.card');
      for (const card of cards) {
        const titleEl = card.querySelector('h2.trend-headline') || card.querySelector('h2');
        const topicEl = card.querySelector('.trend-topic');
        if (titleEl || topicEl) {
          const cardText = (titleEl?.textContent || '') + ' ' + (topicEl?.textContent || '');
          if (cardText.toLowerCase().includes(highlightTrend.toLowerCase())) {
            card.classList.add('highlight', 'search-highlight');
            card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            // Add pulse animation
            card.style.animation = 'highlight-pulse 1s ease-in-out 3';
            break;
          }
        }
      }
    }, 500);
  }
});

// Update live viewers every 5 seconds
setInterval(updateLiveViewers, 5000);

// Auto-refresh trends every 15 minutes to check for new data
setInterval(async () => {
  console.log('Auto-refreshing trends...');
  await loadTrends();
  showToast('Trends refreshed');
}, 15 * 60 * 1000);

// Add highlight pulse animation
const style = document.createElement('style');
style.textContent = `
  @keyframes highlight-pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0); }
    50% { box-shadow: 0 0 0 20px rgba(99, 102, 241, 0.3); }
  }
`;
document.head.appendChild(style);

// === MISSED TRENDS INITIALIZATION ===
function initMissedTrends() {
  const section = document.getElementById('missed-trends-section');
  const container = document.getElementById('missed-trends-container');
  if (!section || !container || allTrends.length === 0) return;
  
  const missed = getMissedTrends(allTrends);
  
  if (missed.length === 0) {
    section.style.display = 'none';
    return;
  }
  
  section.style.display = 'block';
  container.innerHTML = missed.slice(0, 10).map(t => `
    <div class="missed-trend-card" onclick="goToTrend('${t.trend.replace(/'/g, "\\'")}')">
      <div class="missed-trend-meta">
        <span class="category-tag">${getCategoryIcon(t.category)} ${t.category || 'other'}</span>
        <span class="speed-indicator ${getSpeedIndicator(parseFloat(t.momentum?.replace('%', '') || '0'), t.google_trends?.trend_direction).class}">
          ${getSpeedIndicator(parseFloat(t.momentum?.replace('%', '') || '0'), t.google_trends?.trend_direction).icon}
        </span>
      </div>
      <h4>${t.trend}</h4>
      <p>${(t.analysis?.analysis || '').substring(0, 80)}...</p>
      <div class="missed-trend-meta">
        <span>📊 ${t.signal_score}</span>
        <span>🚀 ${t.momentum}</span>
      </div>
    </div>
  `).join('');
}

function goToTrend(trendName) {
  // Mark as seen
  markTrendAsSeen(trendName);
  // Find the page this trend is on
  const filtered = allTrends.filter(t => currentFilter === 'all' || t.category === currentFilter);
  const idx = filtered.findIndex(t => t.trend === trendName);
  if (idx !== -1) {
    currentPage = Math.floor(idx / TRENDS_PER_PAGE) + 1;
    renderTrends();
    updateURL();
    setTimeout(() => scrollToTrendByName(trendName), 300);
  }
}

function dismissMissedTrends() {
  // Mark all current trends as seen
  allTrends.forEach(t => markTrendAsSeen(t.trend));
  const section = document.getElementById('missed-trends-section');
  if (section) section.style.display = 'none';
}

// === TOPIC ALERTS INITIALIZATION ===
function initTopicAlerts() {
  const section = document.getElementById('topic-alerts-section');
  const list = document.getElementById('alerts-list');
  const count = document.getElementById('alerts-count');
  
  if (!section || !list) return;
  
  const alerts = getTopicAlerts();
  
  if (alerts.length === 0) {
    section.classList.remove('visible');
    return;
  }
  
  section.classList.add('visible');
  count.textContent = alerts.length;
  
  list.innerHTML = alerts.map(topic => `
    <div class="alert-tag">
      <span>🔔 ${topic}</span>
      <button class="remove-alert" onclick="removeTopicAlert('${topic.replace(/'/g, "\\'")}')">✕</button>
    </div>
  `).join('');
}

function removeTopicAlert(topic) {
  const alerts = getTopicAlerts();
  const idx = alerts.indexOf(topic);
  if (idx > -1) {
    alerts.splice(idx, 1);
    localStorage.setItem(TOPIC_ALERTS_KEY, JSON.stringify(alerts));
    initTopicAlerts();
    showToast(`Removed alert for "${topic}"`);
    
    // Update button in card if visible
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
      const title = card.querySelector('h2');
      if (title && title.textContent === topic) {
        const btn = card.querySelector('.alert-btn');
        if (btn) {
          btn.classList.remove('active');
          btn.textContent = '🔕';
        }
      }
    });
  }
}

// ========== DATE FILTER ==========
let currentDateFilter = null; // null = all time, or { start: Date, end: Date }

function initDateFilter() {
  const filterBtn = document.getElementById('date-filter-btn');
  const dropdown = document.getElementById('date-filter-dropdown');
  const dateOptions = document.querySelectorAll('.date-option');
  const customPicker = document.getElementById('custom-date-picker');
  const customDateInput = document.getElementById('custom-date-input');
  const applyBtn = document.getElementById('apply-custom-date');
  const filterLabel = document.getElementById('date-filter-label');
  
  if (!filterBtn || !dropdown) return;
  
  // Toggle dropdown
  filterBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdown.classList.toggle('show');
  });
  
  // Close dropdown when clicking outside
  document.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target) && !filterBtn.contains(e.target)) {
      dropdown.classList.remove('show');
    }
  });
  
  // Handle date option clicks
  dateOptions.forEach(option => {
    option.addEventListener('click', () => {
      dateOptions.forEach(o => o.classList.remove('active'));
      option.classList.add('active');
      
      const range = option.dataset.range;
      
      if (range === 'custom') {
        if (customPicker) customPicker.style.display = 'flex';
      } else {
        if (customPicker) customPicker.style.display = 'none';
        applyDateRange(range);
        dropdown.classList.remove('show');
      }
    });
  });
  
  // Apply custom date
  if (applyBtn) {
    applyBtn.addEventListener('click', () => {
      if (customDateInput && customDateInput.value) {
        const selectedDate = new Date(customDateInput.value);
        const startOfDay = new Date(selectedDate);
        startOfDay.setHours(0, 0, 0, 0);
        const endOfDay = new Date(selectedDate);
        endOfDay.setHours(23, 59, 59, 999);
        
        currentDateFilter = { start: startOfDay, end: endOfDay };
        filterLabel.textContent = formatDateLabel(selectedDate);
        dropdown.classList.remove('show');
        applyDateFilterToTrends();
      }
    });
  }
}

function applyDateRange(range) {
  const filterLabel = document.getElementById('date-filter-label');
  const now = new Date();
  
  switch (range) {
    case 'all':
      currentDateFilter = null;
      filterLabel.textContent = 'All Time';
      break;
    case 'today':
      const todayStart = new Date(now);
      todayStart.setHours(0, 0, 0, 0);
      currentDateFilter = { start: todayStart, end: now };
      filterLabel.textContent = 'Today';
      break;
    case 'yesterday':
      const yesterdayStart = new Date(now);
      yesterdayStart.setDate(yesterdayStart.getDate() - 1);
      yesterdayStart.setHours(0, 0, 0, 0);
      const yesterdayEnd = new Date(now);
      yesterdayEnd.setDate(yesterdayEnd.getDate() - 1);
      yesterdayEnd.setHours(23, 59, 59, 999);
      currentDateFilter = { start: yesterdayStart, end: yesterdayEnd };
      filterLabel.textContent = 'Yesterday';
      break;
    case 'week':
      const weekStart = new Date(now);
      weekStart.setDate(weekStart.getDate() - 7);
      weekStart.setHours(0, 0, 0, 0);
      currentDateFilter = { start: weekStart, end: now };
      filterLabel.textContent = 'Last 7 Days';
      break;
  }
  
  applyDateFilterToTrends();
}

function formatDateLabel(date) {
  const options = { month: 'short', day: 'numeric', year: 'numeric' };
  return date.toLocaleDateString('en-US', options);
}

function applyDateFilterToTrends() {
  if (!allTrends || allTrends.length === 0) return;
  
  let filteredTrends;
  
  if (!currentDateFilter) {
    filteredTrends = [...allTrends];
  } else {
    filteredTrends = allTrends.filter(trend => {
      // Parse the trend's timestamp
      const trendDate = parseTrendDate(trend.timestamp);
      if (!trendDate) return true; // If no valid date, include it
      
      return trendDate >= currentDateFilter.start && trendDate <= currentDateFilter.end;
    });
  }
  
  // Update the result info
  updateDateResultInfo(filteredTrends.length);
  
  // Re-render with filtered trends
  currentPage = 1;
  renderFilteredTrends(filteredTrends);
}

function parseTrendDate(timestamp) {
  if (!timestamp) return null;
  
  // Handle relative timestamps like "2 hours ago", "3 days ago"
  const now = new Date();
  
  if (timestamp.includes('hour')) {
    const hours = parseInt(timestamp) || 1;
    return new Date(now.getTime() - hours * 60 * 60 * 1000);
  }
  if (timestamp.includes('day')) {
    const days = parseInt(timestamp) || 1;
    return new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
  }
  if (timestamp.includes('week')) {
    const weeks = parseInt(timestamp) || 1;
    return new Date(now.getTime() - weeks * 7 * 24 * 60 * 60 * 1000);
  }
  if (timestamp.includes('month')) {
    const months = parseInt(timestamp) || 1;
    const date = new Date(now);
    date.setMonth(date.getMonth() - months);
    return date;
  }
  if (timestamp.includes('minute')) {
    const minutes = parseInt(timestamp) || 1;
    return new Date(now.getTime() - minutes * 60 * 1000);
  }
  if (timestamp.includes('second')) {
    return now;
  }
  
  // Try to parse as a date string
  const parsed = new Date(timestamp);
  if (!isNaN(parsed.getTime())) {
    return parsed;
  }
  
  return now; // Default to now if can't parse
}

function updateDateResultInfo(count) {
  const resultInfo = document.getElementById('date-result-info');
  if (resultInfo) {
    if (currentDateFilter) {
      resultInfo.innerHTML = `Showing <span>${count}</span> trend${count !== 1 ? 's' : ''} for selected date`;
      resultInfo.style.display = 'block';
    } else {
      resultInfo.style.display = 'none';
    }
  }
}

function renderFilteredTrends(filteredTrends) {
  if (!container) return;
  
  if (filteredTrends.length === 0) {
    container.innerHTML = `
      <div class="no-results" style="grid-column: 1/-1; text-align: center; padding: 60px 20px;">
        <div style="font-size: 60px; margin-bottom: 20px;">📅</div>
        <h3 style="margin-bottom: 10px; color: var(--text-color);">No trends for this date</h3>
        <p style="color: var(--text-muted);">Try selecting a different date range</p>
      </div>
    `;
    renderPagination(0, 0);
    return;
  }
  
  // Temporarily replace allTrends for rendering
  const originalTrends = allTrends;
  allTrends = filteredTrends;
  renderTrends();
  allTrends = originalTrends;
}

// Initialize date filter when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  initDateFilter();
  initRegionFilter();
});

// ========== REGIONAL FILTER ==========
let currentRegion = 'global';

// Region keywords to detect region from trend content
const regionKeywords = {
  us: ['america', 'american', 'usa', 'united states', 'biden', 'trump', 'congress', 'senate', 'nfl', 'nba', 'super bowl', 'washington', 'new york', 'california', 'texas', 'hollywood', 'silicon valley', 'wall street'],
  uk: ['britain', 'british', 'uk', 'united kingdom', 'england', 'london', 'parliament', 'premier league', 'bbc', 'royal', 'king charles', 'westminster'],
  eu: ['europe', 'european', 'eu', 'germany', 'france', 'spain', 'italy', 'berlin', 'paris', 'brussels', 'euro', 'bundesliga', 'la liga', 'serie a'],
  asia: ['asia', 'asian', 'china', 'chinese', 'japan', 'japanese', 'korea', 'korean', 'india', 'indian', 'beijing', 'tokyo', 'anime', 'k-pop', 'bollywood', 'samsung', 'sony', 'huawei'],
  latam: ['latin america', 'brazil', 'brazilian', 'mexico', 'mexican', 'argentina', 'colombian', 'latin', 'south america', 'caribbean'],
  africa: ['africa', 'african', 'nigeria', 'south africa', 'kenya', 'egypt', 'morocco'],
  oceania: ['australia', 'australian', 'new zealand', 'oceania', 'sydney', 'melbourne', 'afl']
};

function detectTrendRegion(trend) {
  const text = `${trend.trend} ${trend.analysis?.analysis || ''} ${trend.analysis?.summary || ''}`.toLowerCase();
  
  for (const [region, keywords] of Object.entries(regionKeywords)) {
    for (const keyword of keywords) {
      if (text.includes(keyword)) {
        return region;
      }
    }
  }
  return 'global'; // Default to global if no region detected
}

function initRegionFilter() {
  const filterBtn = document.getElementById('region-filter-btn');
  const dropdown = document.getElementById('region-filter-dropdown');
  const regionOptions = document.querySelectorAll('.region-option');
  const filterLabel = document.getElementById('region-filter-label');
  
  if (!filterBtn || !dropdown) return;
  
  // Load saved region preference
  const savedRegion = localStorage.getItem('trendRadar_region');
  if (savedRegion) {
    currentRegion = savedRegion;
    const activeOption = document.querySelector(`.region-option[data-region="${savedRegion}"]`);
    if (activeOption) {
      regionOptions.forEach(o => o.classList.remove('active'));
      activeOption.classList.add('active');
      filterLabel.textContent = activeOption.textContent.split(' ').slice(1).join(' ');
    }
  }
  
  // Toggle dropdown
  filterBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    // Close date dropdown if open
    const dateDropdown = document.getElementById('date-filter-dropdown');
    if (dateDropdown) dateDropdown.classList.remove('show');
    dropdown.classList.toggle('show');
  });
  
  // Close dropdown when clicking outside
  document.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target) && !filterBtn.contains(e.target)) {
      dropdown.classList.remove('show');
    }
  });
  
  // Handle region option clicks
  regionOptions.forEach(option => {
    option.addEventListener('click', () => {
      regionOptions.forEach(o => o.classList.remove('active'));
      option.classList.add('active');
      
      const region = option.dataset.region;
      currentRegion = region;
      localStorage.setItem('trendRadar_region', region);
      
      // Update button label (remove emoji)
      filterLabel.textContent = option.textContent.split(' ').slice(1).join(' ');
      
      dropdown.classList.remove('show');
      applyRegionFilterToTrends();
    });
  });
}

function applyRegionFilterToTrends() {
  if (!allTrends || allTrends.length === 0) return;
  
  let filteredTrends;
  
  if (currentRegion === 'global') {
    filteredTrends = [...allTrends];
  } else {
    filteredTrends = allTrends.filter(trend => {
      const trendRegion = detectTrendRegion(trend);
      return trendRegion === currentRegion || trendRegion === 'global';
    });
  }
  
  // Re-render with filtered trends
  currentPage = 1;
  renderFilteredTrends(filteredTrends);
  
  // Update count
  if (trendsCount) {
    trendsCount.textContent = `Showing ${filteredTrends.length} trends from ${currentRegion.toUpperCase()}`;
  }
}
