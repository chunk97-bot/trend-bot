const container = document.getElementById("featured-trend");

async function loadTopTrend() {
  try {
    const indexRes = await fetch(`./data/index.json?ts=${Date.now()}`);
    const index = await indexRes.json();

    let trends = [];

    for (const file of index.files) {
      try {
        const res = await fetch(`./data/${file}?ts=${Date.now()}`);
        const data = await res.json();
        trends.push(data);
      } catch {}
    }

    // Prefer rising trends, then highest signal score
    trends.sort((a, b) => {
      if (a.lifecycle === "rising" && b.lifecycle !== "rising") return -1;
      if (b.lifecycle === "rising" && a.lifecycle !== "rising") return 1;
      return (b.signal_score || 0) - (a.signal_score || 0);
    });

    if (trends.length > 0) {
      renderTop(trends[0]);
    }
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
      📊 Signal Score: <strong>${t.signal_score}</strong>
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

// Initial load
loadTopTrend();

// === BROWSER PUSH NOTIFICATIONS ===
const NOTIF_ENABLED_KEY = 'trend_radar_notifications_enabled';
const LAST_NOTIF_TREND_KEY = 'trend_radar_last_notified_trend';

// Check if browser supports notifications
function notificationsSupported() {
  return 'Notification' in window;
}

// Get current permission status
function getNotificationPermission() {
  if (!notificationsSupported()) return 'unsupported';
  return Notification.permission; // 'granted', 'denied', or 'default'
}

// Check if user enabled notifications in our app
function isNotificationsEnabled() {
  return localStorage.getItem(NOTIF_ENABLED_KEY) === 'true';
}

// Request browser permission and enable notifications
async function requestNotificationPermission() {
  if (!notificationsSupported()) {
    showNotificationToast('Your browser does not support notifications', 'error');
    return false;
  }
  
  const permission = await Notification.requestPermission();
  
  if (permission === 'granted') {
    localStorage.setItem(NOTIF_ENABLED_KEY, 'true');
    updateNotificationUI();
    showNotificationToast('Notifications enabled! You\'ll be notified of new trends.', 'success');
    
    // Send a test notification
    sendBrowserNotification('Trend Radar', 'Notifications are now enabled! 🔔', './assets/logo.png');
    return true;
  } else if (permission === 'denied') {
    localStorage.setItem(NOTIF_ENABLED_KEY, 'false');
    updateNotificationUI();
    showNotificationToast('Notifications blocked. Enable them in browser settings.', 'error');
    return false;
  }
  
  return false;
}

// Disable notifications
function disableNotifications() {
  localStorage.setItem(NOTIF_ENABLED_KEY, 'false');
  updateNotificationUI();
  showNotificationToast('Notifications muted', 'info');
}

// Send actual browser notification
function sendBrowserNotification(title, body, icon = './assets/logo.png') {
  if (!notificationsSupported() || !isNotificationsEnabled()) return;
  if (Notification.permission !== 'granted') return;
  
  const notification = new Notification(title, {
    body: body,
    icon: icon,
    badge: icon,
    tag: 'trend-radar-notification',
    renotify: true,
    requireInteraction: false,
    silent: false
  });
  
  notification.onclick = function(event) {
    event.preventDefault();
    window.focus();
    window.location.href = './trending.html';
    notification.close();
  };
  
  // Auto close after 5 seconds
  setTimeout(() => notification.close(), 5000);
}

// Check for new trends and notify
async function checkAndNotifyNewTrends() {
  if (!isNotificationsEnabled() || Notification.permission !== 'granted') return;
  
  try {
    const res = await fetch('./data/index.json?ts=' + Date.now());
    const index = await res.json();
    
    if (index.files && index.files.length > 0) {
      const latestFile = index.files[0];
      const trendRes = await fetch('./data/' + latestFile + '?ts=' + Date.now());
      const trend = await trendRes.json();
      
      const lastNotified = localStorage.getItem(LAST_NOTIF_TREND_KEY);
      
      if (trend.trend && trend.trend !== lastNotified) {
        localStorage.setItem(LAST_NOTIF_TREND_KEY, trend.trend);
        
        sendBrowserNotification(
          '🔥 New Trend: ' + trend.trend,
          (trend.analysis?.analysis || '').substring(0, 100) + '...',
          './assets/logo.png'
        );
      }
    }
  } catch (e) {
    console.log('Failed to check for new trends:', e);
  }
}

// Show toast message
function showNotificationToast(message, type = 'info') {
  const existing = document.querySelector('.notif-toast');
  if (existing) existing.remove();
  
  const toast = document.createElement('div');
  toast.className = 'notif-toast ' + type;
  toast.innerHTML = '<span>' + message + '</span>';
  document.body.appendChild(toast);
  
  setTimeout(() => toast.classList.add('visible'), 10);
  setTimeout(() => {
    toast.classList.remove('visible');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Update UI based on notification state
function updateNotificationUI() {
  const permission = getNotificationPermission();
  const enabled = isNotificationsEnabled();
  const bellIcon = document.querySelector('.bell-icon');
  const toggleSwitch = document.getElementById('notification-switch');
  const statusEl = document.getElementById('notification-status');
  const bellBtn = document.getElementById('notification-bell');
  
  const isActive = enabled && permission === 'granted';
  
  if (bellIcon) {
    bellIcon.textContent = isActive ? '🔔' : '🔕';
  }
  
  if (toggleSwitch) {
    toggleSwitch.checked = isActive;
    toggleSwitch.disabled = permission === 'denied';
  }
  
  if (statusEl) {
    if (permission === 'unsupported') {
      statusEl.innerHTML = '<span style="color: #ef4444;">Browser not supported</span>';
    } else if (permission === 'denied') {
      statusEl.innerHTML = '<span style="color: #ef4444;">Blocked in browser settings</span>';
    } else if (isActive) {
      statusEl.innerHTML = 'Notifications are <strong style="color: #10b981;">enabled</strong>';
    } else {
      statusEl.innerHTML = 'Notifications are <strong>disabled</strong>';
    }
  }
  
  if (bellBtn) {
    bellBtn.classList.toggle('muted', !isActive);
  }
}

// Initialize notification system
document.addEventListener('DOMContentLoaded', () => {
  updateNotificationUI();
  
  const bellBtn = document.getElementById('notification-bell');
  const dropdown = document.getElementById('notification-dropdown');
  const toggleSwitch = document.getElementById('notification-switch');
  
  if (bellBtn && dropdown) {
    bellBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      dropdown.classList.toggle('visible');
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.notification-wrapper')) {
        dropdown.classList.remove('visible');
      }
    });
  }
  
  if (toggleSwitch) {
    toggleSwitch.addEventListener('change', async (e) => {
      if (e.target.checked) {
        await requestNotificationPermission();
      } else {
        disableNotifications();
      }
    });
  }
});
