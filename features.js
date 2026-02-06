// ===============================
// TREND RADAR - FEATURES MODULE
// ===============================

// === UTILITIES ===
const FeatureUtils = {
  // Generate unique ID
  generateId: () => Math.random().toString(36).substr(2, 9),
  
  // Debounce function
  debounce: (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },
  
  // Format numbers
  formatNumber: (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  },
  
  // Calculate read time
  calculateReadTime: (text) => {
    const wordsPerMinute = 200;
    const wordCount = text.split(/\s+/).length;
    const minutes = Math.ceil(wordCount / wordsPerMinute);
    return minutes < 1 ? 1 : minutes;
  },
  
  // Get random items from array
  getRandomItems: (arr, count) => {
    const shuffled = [...arr].sort(() => 0.5 - Math.random());
    return shuffled.slice(0, count);
  }
};

// === BOOKMARKS SYSTEM ===
const Bookmarks = {
  STORAGE_KEY: 'trend_radar_bookmarks',
  
  getAll() {
    const stored = localStorage.getItem(this.STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  },
  
  add(trend) {
    const bookmarks = this.getAll();
    if (!bookmarks.find(b => b.trend === trend.trend)) {
      bookmarks.push({
        ...trend,
        bookmarkedAt: new Date().toISOString()
      });
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(bookmarks));
      this.updateUI();
      this.showToast('Bookmark added! 🔖');
      return true;
    }
    return false;
  },
  
  remove(trendName) {
    let bookmarks = this.getAll();
    bookmarks = bookmarks.filter(b => b.trend !== trendName);
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(bookmarks));
    this.updateUI();
    this.showToast('Bookmark removed');
    return true;
  },
  
  isBookmarked(trendName) {
    return this.getAll().some(b => b.trend === trendName);
  },
  
  toggle(trend) {
    if (this.isBookmarked(trend.trend)) {
      this.remove(trend.trend);
      return false;
    }
    this.add(trend);
    return true;
  },
  
  updateUI() {
    const count = this.getAll().length;
    // Update all bookmark count badges
    const badges = document.querySelectorAll('#bookmark-count, #nav-bookmark-count');
    badges.forEach(badge => {
      badge.textContent = count;
      badge.style.display = count > 0 ? 'flex' : 'none';
    });
  },
  
  showToast(message) {
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
};

// === SHARE SYSTEM ===
const Share = {
  copyLink(url = window.location.href) {
    navigator.clipboard.writeText(url).then(() => {
      Bookmarks.showToast('Link copied! 📋');
    });
  },
  
  twitter(text, url = window.location.href) {
    const tweetUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`;
    window.open(tweetUrl, '_blank', 'width=550,height=420');
  },
  
  whatsapp(text, url = window.location.href) {
    const waUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(text + ' ' + url)}`;
    window.open(waUrl, '_blank');
  },
  
  facebook(url = window.location.href) {
    const fbUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`;
    window.open(fbUrl, '_blank', 'width=550,height=420');
  },
  
  telegram(text, url = window.location.href) {
    const tgUrl = `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`;
    window.open(tgUrl, '_blank');
  },
  
  createShareButtons(trend) {
    const url = window.location.origin + `/posts/${trend.trend.toLowerCase().replace(/\s+/g, '-')}.html`;
    const text = `Check out this trend: ${trend.trend} 🔥`;
    
    return `
      <div class="share-buttons">
        <button class="share-btn" onclick="Share.copyLink('${url}')" title="Copy link">
          <span>📋</span>
        </button>
        <button class="share-btn twitter" onclick="Share.twitter('${text.replace(/'/g, "\\'")}', '${url}')" title="Share on X">
          <span>𝕏</span>
        </button>
        <button class="share-btn whatsapp" onclick="Share.whatsapp('${text.replace(/'/g, "\\'")}', '${url}')" title="Share on WhatsApp">
          <span>💬</span>
        </button>
        <button class="share-btn telegram" onclick="Share.telegram('${text.replace(/'/g, "\\'")}', '${url}')" title="Share on Telegram">
          <span>✈️</span>
        </button>
      </div>
    `;
  }
};

// === REACTIONS SYSTEM ===
const Reactions = {
  STORAGE_KEY: 'trend_radar_reactions',
  EMOJIS: ['🔥', '🤯', '😂', '👀', '💯', '🚀'],
  
  getAll() {
    const stored = localStorage.getItem(this.STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
  },
  
  getForTrend(trendName) {
    const all = this.getAll();
    return all[trendName] || { counts: {}, userReaction: null };
  },
  
  react(trendName, emoji) {
    const all = this.getAll();
    if (!all[trendName]) {
      all[trendName] = { counts: {}, userReaction: null };
    }
    
    // Remove previous reaction
    if (all[trendName].userReaction) {
      const prevEmoji = all[trendName].userReaction;
      all[trendName].counts[prevEmoji] = Math.max(0, (all[trendName].counts[prevEmoji] || 1) - 1);
    }
    
    // Add new reaction (or toggle off)
    if (all[trendName].userReaction === emoji) {
      all[trendName].userReaction = null;
    } else {
      all[trendName].userReaction = emoji;
      all[trendName].counts[emoji] = (all[trendName].counts[emoji] || 0) + 1;
    }
    
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(all));
    return all[trendName];
  },
  
  createReactionBar(trendName, simulatedCounts = {}) {
    const data = this.getForTrend(trendName);
    const counts = { ...simulatedCounts, ...data.counts };
    
    return `
      <div class="reaction-bar" data-trend="${trendName}">
        ${this.EMOJIS.map(emoji => `
          <button class="reaction-btn ${data.userReaction === emoji ? 'active' : ''}" 
                  onclick="Reactions.handleClick('${trendName}', '${emoji}')">
            <span class="reaction-emoji">${emoji}</span>
            <span class="reaction-count">${FeatureUtils.formatNumber(counts[emoji] || Math.floor(Math.random() * 50))}</span>
          </button>
        `).join('')}
      </div>
    `;
  },
  
  handleClick(trendName, emoji) {
    const data = this.react(trendName, emoji);
    const bar = document.querySelector(`.reaction-bar[data-trend="${trendName}"]`);
    if (bar) {
      bar.querySelectorAll('.reaction-btn').forEach(btn => {
        const btnEmoji = btn.querySelector('.reaction-emoji').textContent;
        btn.classList.toggle('active', data.userReaction === btnEmoji);
      });
    }
  }
};

// === COMMENTS SYSTEM ===
const Comments = {
  STORAGE_KEY: 'trend_radar_comments',
  
  getAll() {
    const stored = localStorage.getItem(this.STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
  },
  
  getForTrend(trendName) {
    const all = this.getAll();
    return all[trendName] || [];
  },
  
  add(trendName, text, author = 'Anonymous') {
    const all = this.getAll();
    if (!all[trendName]) all[trendName] = [];
    
    const comment = {
      id: FeatureUtils.generateId(),
      text: text.trim(),
      author,
      timestamp: new Date().toISOString(),
      likes: 0
    };
    
    all[trendName].unshift(comment);
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(all));
    return comment;
  },
  
  createSection(trendName) {
    const comments = this.getForTrend(trendName);
    
    return `
      <div class="comments-section" data-trend="${trendName}">
        <h4 class="comments-title">
          <span>💬 Discussion</span>
          <span class="comments-count">${comments.length}</span>
        </h4>
        
        <form class="comment-form" onsubmit="Comments.handleSubmit(event, '${trendName}')">
          <input type="text" class="comment-input" placeholder="Share your thoughts..." required />
          <button type="submit" class="comment-submit">Post</button>
        </form>
        
        <div class="comments-list">
          ${comments.length === 0 ? 
            '<p class="no-comments">Be the first to comment!</p>' :
            comments.slice(0, 5).map(c => this.renderComment(c)).join('')
          }
        </div>
        
        ${comments.length > 5 ? `<button class="load-more-comments" onclick="Comments.loadMore('${trendName}')">Load more comments</button>` : ''}
      </div>
    `;
  },
  
  renderComment(comment) {
    const date = new Date(comment.timestamp).toLocaleDateString();
    return `
      <div class="comment" data-id="${comment.id}">
        <div class="comment-header">
          <span class="comment-avatar">👤</span>
          <span class="comment-author">${comment.author}</span>
          <span class="comment-date">${date}</span>
        </div>
        <p class="comment-text">${comment.text}</p>
      </div>
    `;
  },
  
  handleSubmit(event, trendName) {
    event.preventDefault();
    const form = event.target;
    const input = form.querySelector('.comment-input');
    const text = input.value.trim();
    
    if (text) {
      const comment = this.add(trendName, text);
      const list = form.closest('.comments-section').querySelector('.comments-list');
      const noComments = list.querySelector('.no-comments');
      if (noComments) noComments.remove();
      
      list.insertAdjacentHTML('afterbegin', this.renderComment(comment));
      input.value = '';
      
      // Update count
      const countEl = form.closest('.comments-section').querySelector('.comments-count');
      countEl.textContent = parseInt(countEl.textContent) + 1;
      
      Bookmarks.showToast('Comment posted! 💬');
    }
  },
  
  loadMore(trendName) {
    // Implementation for loading more comments
  }
};

// === NOTIFICATIONS SYSTEM ===
const Notifications = {
  STORAGE_KEY: 'trend_radar_notifications',
  CATEGORIES_KEY: 'trend_radar_notify_categories',
  
  getCategories() {
    const stored = localStorage.getItem(this.CATEGORIES_KEY);
    return stored ? JSON.parse(stored) : [];
  },
  
  setCategories(categories) {
    localStorage.setItem(this.CATEGORIES_KEY, JSON.stringify(categories));
  },
  
  toggleCategory(category) {
    const cats = this.getCategories();
    const idx = cats.indexOf(category);
    if (idx > -1) {
      cats.splice(idx, 1);
    } else {
      cats.push(category);
    }
    this.setCategories(cats);
    this.updateBell();
    return cats.includes(category);
  },
  
  getNotifications() {
    const stored = localStorage.getItem(this.STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  },
  
  addNotification(message, category) {
    const notifs = this.getNotifications();
    notifs.unshift({
      id: FeatureUtils.generateId(),
      message,
      category,
      timestamp: new Date().toISOString(),
      read: false
    });
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(notifs.slice(0, 50)));
    this.updateBell();
  },
  
  markAllRead() {
    const notifs = this.getNotifications();
    notifs.forEach(n => n.read = true);
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(notifs));
    this.updateBell();
  },
  
  getUnreadCount() {
    return this.getNotifications().filter(n => !n.read).length;
  },
  
  updateBell() {
    const badge = document.getElementById('notification-count');
    const count = this.getUnreadCount();
    if (badge) {
      badge.textContent = count;
      badge.style.display = count > 0 ? 'flex' : 'none';
    }
  }
};

// === CUSTOM FEED PREFERENCES ===
const CustomFeed = {
  STORAGE_KEY: 'trend_radar_feed_prefs',
  
  getPreferences() {
    const stored = localStorage.getItem(this.STORAGE_KEY);
    return stored ? JSON.parse(stored) : {
      categories: [],
      sortBy: 'score',
      showHotOnly: false
    };
  },
  
  setPreferences(prefs) {
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(prefs));
  },
  
  toggleCategory(category) {
    const prefs = this.getPreferences();
    const idx = prefs.categories.indexOf(category);
    if (idx > -1) {
      prefs.categories.splice(idx, 1);
    } else {
      prefs.categories.push(category);
    }
    this.setPreferences(prefs);
    return prefs;
  }
};

// === SORT OPTIONS ===
const SortOptions = {
  STORAGE_KEY: 'trend_radar_sort',
  
  getCurrentSort() {
    return localStorage.getItem(this.STORAGE_KEY) || 'score';
  },
  
  setSort(sortBy) {
    localStorage.setItem(this.STORAGE_KEY, sortBy);
  },
  
  sortTrends(trends, sortBy) {
    const sorted = [...trends];
    switch (sortBy) {
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
};

// === HOT BADGE ===
const HotBadge = {
  isHot(trend) {
    // Consider hot if: high score, positive momentum, or lifecycle is "new"
    const momentum = parseFloat(trend.momentum || '0');
    return trend.signal_score >= 80 || momentum > 20 || trend.lifecycle === 'new';
  },
  
  createBadge() {
    return '<span class="hot-badge">🔥 HOT</span>';
  }
};

// === POPULARITY METER ===
const PopularityMeter = {
  create(score) {
    const percentage = Math.min(100, Math.max(0, score));
    const color = percentage >= 70 ? '#10b981' : percentage >= 40 ? '#f59e0b' : '#ef4444';
    
    return `
      <div class="popularity-meter" title="Popularity: ${percentage}%">
        <div class="meter-bar">
          <div class="meter-fill" style="width: ${percentage}%; background: ${color}"></div>
        </div>
        <span class="meter-value">${percentage}%</span>
      </div>
    `;
  }
};

// === READ TIME ===
const ReadTime = {
  create(text) {
    const minutes = FeatureUtils.calculateReadTime(text);
    return `<span class="read-time">📖 ${minutes} min read</span>`;
  }
};

// === LIVE ACTIVITY ===
const LiveActivity = {
  viewers: {},
  
  init() {
    // Simulate live viewers
    setInterval(() => this.updateViewers(), 5000);
  },
  
  updateViewers() {
    document.querySelectorAll('.live-viewers').forEach(el => {
      const base = parseInt(el.dataset.base || '10');
      const variation = Math.floor(Math.random() * 10) - 5;
      const viewers = Math.max(1, base + variation);
      el.querySelector('.viewer-count').textContent = viewers;
    });
  },
  
  createCounter(trendName) {
    const baseViewers = Math.floor(Math.random() * 50) + 10;
    return `
      <div class="live-viewers" data-trend="${trendName}" data-base="${baseViewers}">
        <span class="live-dot"></span>
        <span class="viewer-count">${baseViewers}</span>
        <span class="viewer-text">viewing now</span>
      </div>
    `;
  }
};

// === SKELETON LOADING ===
const SkeletonLoader = {
  createCard() {
    return `
      <div class="skeleton-card">
        <div class="skeleton-header">
          <div class="skeleton skeleton-tag"></div>
          <div class="skeleton skeleton-badge"></div>
        </div>
        <div class="skeleton skeleton-title"></div>
        <div class="skeleton skeleton-text"></div>
        <div class="skeleton skeleton-text short"></div>
        <div class="skeleton-metrics">
          <div class="skeleton skeleton-metric"></div>
          <div class="skeleton skeleton-metric"></div>
        </div>
      </div>
    `;
  },
  
  createMultiple(count = 6) {
    return Array(count).fill(this.createCard()).join('');
  },
  
  show(container) {
    if (container) {
      container.innerHTML = this.createMultiple(6);
    }
  }
};

// === INFINITE SCROLL ===
const InfiniteScroll = {
  loading: false,
  page: 1,
  hasMore: true,
  
  init(loadMoreFn) {
    this.loadMore = loadMoreFn;
    
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && !this.loading && this.hasMore) {
        this.load();
      }
    }, { threshold: 0.1 });
    
    const sentinel = document.getElementById('scroll-sentinel');
    if (sentinel) observer.observe(sentinel);
  },
  
  async load() {
    this.loading = true;
    document.getElementById('loading-more')?.classList.add('visible');
    
    // Simulate loading delay
    await new Promise(r => setTimeout(r, 500));
    
    if (this.loadMore) {
      this.hasMore = await this.loadMore(this.page);
      this.page++;
    }
    
    this.loading = false;
    document.getElementById('loading-more')?.classList.remove('visible');
  }
};

// === RANDOM TREND ===
const RandomTrend = {
  get(trends) {
    if (trends.length === 0) return null;
    return trends[Math.floor(Math.random() * trends.length)];
  },
  
  discover(trends, renderFn) {
    const trend = this.get(trends);
    if (trend) {
      Bookmarks.showToast(`Discovered: ${trend.trend} 🎲`);
      // Highlight the card
      renderFn(trend, true);
    }
  }
};

// === RELATED TRENDS ===
const RelatedTrends = {
  find(currentTrend, allTrends, limit = 4) {
    // Find trends in same category or with similar keywords
    const related = allTrends.filter(t => {
      if (t.trend === currentTrend.trend) return false;
      if (t.category === currentTrend.category) return true;
      
      // Check for keyword matches
      const currentWords = currentTrend.trend.toLowerCase().split(/\s+/);
      const otherWords = t.trend.toLowerCase().split(/\s+/);
      return currentWords.some(w => otherWords.includes(w));
    });
    
    return FeatureUtils.getRandomItems(related, limit);
  },
  
  createSection(related) {
    if (related.length === 0) return '';
    
    return `
      <div class="related-trends">
        <h4 class="related-title">🔗 Related Trends</h4>
        <div class="related-grid">
          ${related.map(t => `
            <a href="./posts/${t.trend.toLowerCase().replace(/\s+/g, '-')}.html" class="related-card">
              <span class="related-category">${t.category || 'other'}</span>
              <h5>${t.trend}</h5>
              <span class="related-score">📊 ${t.signal_score}</span>
            </a>
          `).join('')}
        </div>
      </div>
    `;
  }
};

// === SMART RECOMMENDATIONS ===
const SmartRecommendations = {
  HISTORY_KEY: 'trend_radar_view_history',
  
  addToHistory(trend) {
    const history = this.getHistory();
    history.unshift({
      trend: trend.trend,
      category: trend.category,
      timestamp: new Date().toISOString()
    });
    // Keep last 50
    localStorage.setItem(this.HISTORY_KEY, JSON.stringify(history.slice(0, 50)));
  },
  
  getHistory() {
    const stored = localStorage.getItem(this.HISTORY_KEY);
    return stored ? JSON.parse(stored) : [];
  },
  
  getPreferredCategories() {
    const history = this.getHistory();
    const categoryCounts = {};
    history.forEach(h => {
      categoryCounts[h.category] = (categoryCounts[h.category] || 0) + 1;
    });
    
    return Object.entries(categoryCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([cat]) => cat);
  },
  
  getRecommendations(allTrends, limit = 4) {
    const preferred = this.getPreferredCategories();
    if (preferred.length === 0) {
      return FeatureUtils.getRandomItems(allTrends, limit);
    }
    
    const recommended = allTrends.filter(t => preferred.includes(t.category));
    return FeatureUtils.getRandomItems(recommended, limit);
  },
  
  createSection(recommendations) {
    if (recommendations.length === 0) return '';
    
    return `
      <div class="recommendations-section">
        <h4 class="rec-title">✨ Recommended for You</h4>
        <div class="rec-grid">
          ${recommendations.map(t => `
            <div class="rec-card">
              <span class="rec-category">${t.category || 'other'}</span>
              <h5>${t.trend}</h5>
              <p>${(t.analysis?.analysis || '').substring(0, 80)}...</p>
              ${PopularityMeter.create(t.signal_score)}
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }
};

// === DIGEST ===
const Digest = {
  createWeeklyDigest(trends) {
    const topTrends = [...trends]
      .sort((a, b) => (b.signal_score || 0) - (a.signal_score || 0))
      .slice(0, 5);
    
    const categoryBreakdown = {};
    trends.forEach(t => {
      categoryBreakdown[t.category] = (categoryBreakdown[t.category] || 0) + 1;
    });
    
    return `
      <div class="digest-section">
        <div class="digest-header">
          <h3>📅 Weekly Digest</h3>
          <span class="digest-date">${new Date().toLocaleDateString()}</span>
        </div>
        
        <div class="digest-content">
          <div class="digest-top">
            <h4>🏆 Top 5 This Week</h4>
            <ol class="top-list">
              ${topTrends.map((t, i) => `
                <li>
                  <span class="rank">#${i + 1}</span>
                  <span class="trend-name">${t.trend}</span>
                  <span class="trend-score">${t.signal_score}</span>
                </li>
              `).join('')}
            </ol>
          </div>
          
          <div class="digest-breakdown">
            <h4>📊 By Category</h4>
            <div class="category-bars">
              ${Object.entries(categoryBreakdown).map(([cat, count]) => `
                <div class="category-bar-item">
                  <span class="cat-name">${cat}</span>
                  <div class="cat-bar">
                    <div class="cat-fill" style="width: ${(count / trends.length) * 100}%"></div>
                  </div>
                  <span class="cat-count">${count}</span>
                </div>
              `).join('')}
            </div>
          </div>
        </div>
      </div>
    `;
  }
};

// === 3D GLOBE WITH CONNECTIONS ===
const Globe3D = {
  create() {
    return `
      <div class="globe-3d-container" id="trend-globe">
        <div class="globe-3d">
          <div class="globe-sphere-3d">
            <div class="latitude lat-1"></div>
            <div class="latitude lat-2"></div>
            <div class="latitude lat-3"></div>
            <div class="longitude lon-1"></div>
            <div class="longitude lon-2"></div>
            <div class="longitude lon-3"></div>
            <div class="globe-surface"></div>
            <div class="globe-node node-1"></div>
            <div class="globe-node node-2"></div>
            <div class="globe-node node-3"></div>
            <div class="globe-node node-4"></div>
            <div class="globe-node node-5"></div>
          </div>
          <div class="globe-glow"></div>
        </div>
      </div>
    `;
  }
};

// === IMAGE GALLERY ===
const ImageGallery = {
  create(images = []) {
    if (images.length === 0) {
      // Generate placeholder images
      images = [
        `https://picsum.photos/seed/${Math.random()}/400/300`,
        `https://picsum.photos/seed/${Math.random()}/400/300`,
        `https://picsum.photos/seed/${Math.random()}/400/300`
      ];
    }
    
    return `
      <div class="image-gallery">
        <div class="gallery-main">
          <img src="${images[0]}" alt="Trend image" class="gallery-image active" />
        </div>
        ${images.length > 1 ? `
          <div class="gallery-thumbs">
            ${images.map((img, i) => `
              <button class="gallery-thumb ${i === 0 ? 'active' : ''}" data-index="${i}">
                <img src="${img}" alt="Thumbnail ${i + 1}" />
              </button>
            `).join('')}
          </div>
          <div class="gallery-controls">
            <button class="gallery-prev" onclick="ImageGallery.prev(this)">‹</button>
            <button class="gallery-next" onclick="ImageGallery.next(this)">›</button>
          </div>
        ` : ''}
      </div>
    `;
  },
  
  prev(btn) {
    const gallery = btn.closest('.image-gallery');
    const thumbs = gallery.querySelectorAll('.gallery-thumb');
    const currentIndex = [...thumbs].findIndex(t => t.classList.contains('active'));
    const newIndex = (currentIndex - 1 + thumbs.length) % thumbs.length;
    this.goTo(gallery, newIndex);
  },
  
  next(btn) {
    const gallery = btn.closest('.image-gallery');
    const thumbs = gallery.querySelectorAll('.gallery-thumb');
    const currentIndex = [...thumbs].findIndex(t => t.classList.contains('active'));
    const newIndex = (currentIndex + 1) % thumbs.length;
    this.goTo(gallery, newIndex);
  },
  
  goTo(gallery, index) {
    const thumbs = gallery.querySelectorAll('.gallery-thumb');
    const mainImg = gallery.querySelector('.gallery-image');
    
    thumbs.forEach((t, i) => t.classList.toggle('active', i === index));
    mainImg.src = thumbs[index].querySelector('img').src;
  }
};

// === TREND HISTORY CHART ===
const TrendChart = {
  create(history = []) {
    // Generate sample history if none provided
    if (history.length < 2) {
      history = Array.from({ length: 7 }, (_, i) => ({
        timestamp: new Date(Date.now() - (6 - i) * 24 * 60 * 60 * 1000).toISOString(),
        signal_score: Math.floor(Math.random() * 40) + 60
      }));
    }
    
    const maxScore = Math.max(...history.map(h => h.signal_score));
    const minScore = Math.min(...history.map(h => h.signal_score));
    const range = maxScore - minScore || 1;
    
    const points = history.map((h, i) => {
      const x = (i / (history.length - 1)) * 100;
      const y = 100 - ((h.signal_score - minScore) / range) * 80 - 10;
      return `${x},${y}`;
    }).join(' ');
    
    return `
      <div class="trend-chart">
        <h4 class="chart-title">📈 Trend History</h4>
        <div class="chart-container">
          <svg viewBox="0 0 100 100" class="chart-svg">
            <defs>
              <linearGradient id="chartGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="rgba(99, 102, 241, 0.3)" />
                <stop offset="100%" stop-color="rgba(99, 102, 241, 0)" />
              </linearGradient>
            </defs>
            <polyline
              class="chart-area"
              points="${points} 100,100 0,100"
              fill="url(#chartGradient)"
            />
            <polyline
              class="chart-line"
              points="${points}"
              fill="none"
              stroke="#6366f1"
              stroke-width="2"
            />
            ${history.map((h, i) => {
              const x = (i / (history.length - 1)) * 100;
              const y = 100 - ((h.signal_score - minScore) / range) * 80 - 10;
              return `<circle cx="${x}" cy="${y}" r="3" fill="#6366f1" class="chart-point" data-value="${h.signal_score}" />`;
            }).join('')}
          </svg>
          <div class="chart-labels">
            <span>${new Date(history[0]?.timestamp).toLocaleDateString()}</span>
            <span>${new Date(history[history.length - 1]?.timestamp).toLocaleDateString()}</span>
          </div>
        </div>
      </div>
    `;
  }
};

// === INITIALIZE ALL FEATURES ===
function initFeatures() {
  // Update bookmark count
  Bookmarks.updateUI();
  
  // Update notification count
  Notifications.updateBell();
  
  // Initialize live activity updates
  LiveActivity.init();
  
  console.log('✅ Trend Radar Features initialized');
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initFeatures);
} else {
  initFeatures();
}
