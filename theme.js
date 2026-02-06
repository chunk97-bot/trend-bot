// Theme Toggle Functionality
(function() {
  const THEME_KEY = 'trend-radar-theme';
  
  // Get saved theme or default to light
  function getSavedTheme() {
    return localStorage.getItem(THEME_KEY) || 'light';
  }
  
  // Apply theme to document
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    updateToggleIcon(theme);
  }
  
  // Update toggle button icon (CSS handles visibility via data-theme attribute)
  function updateToggleIcon(theme) {
    // Icons are controlled by CSS based on data-theme attribute
    // No need to update DOM here
  }
  
  // Toggle between themes
  function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
    localStorage.setItem(THEME_KEY, newTheme);
  }
  
  // Initialize theme on page load
  function init() {
    const savedTheme = getSavedTheme();
    applyTheme(savedTheme);
    
    // Set up toggle button
    const toggle = document.getElementById('theme-toggle');
    if (toggle) {
      toggle.addEventListener('click', toggleTheme);
    }
  }
  
  // Apply theme immediately to prevent flash
  applyTheme(getSavedTheme());
  
  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
