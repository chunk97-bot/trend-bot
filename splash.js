// Splash Screen Controller
(function() {
  const splash = document.getElementById('splash');
  const mainContent = document.getElementById('main-content');
  const enterBtn = document.getElementById('enter-btn');
  const progressBar = document.getElementById('progress-bar');
  const typingText = document.getElementById('typing-text');
  const canvas = document.getElementById('neural-canvas');
  const ctx = canvas ? canvas.getContext('2d') : null;

  // Skip splash if already seen in this session
  if (sessionStorage.getItem('splash-seen')) {
    if (splash) splash.style.display = 'none';
    if (mainContent) mainContent.classList.add('visible');
    document.body.classList.remove('has-splash');
    return;
  }

  // Typing effect messages
  const messages = [
    "Initializing AI systems...",
    "Scanning trending topics...",
    "Analyzing social signals...",
    "Processing viral content...",
    "Ready to explore trends."
  ];

  let messageIndex = 0;
  let charIndex = 0;
  let isDeleting = false;
  let typingSpeed = 50;

  function typeEffect() {
    if (!typingText) return;
    
    const currentMessage = messages[messageIndex];
    
    if (isDeleting) {
      typingText.textContent = currentMessage.substring(0, charIndex - 1);
      charIndex--;
      typingSpeed = 30;
    } else {
      typingText.textContent = currentMessage.substring(0, charIndex + 1);
      charIndex++;
      typingSpeed = 50;
    }

    if (!isDeleting && charIndex === currentMessage.length) {
      isDeleting = true;
      typingSpeed = 1500; // Pause at end
    } else if (isDeleting && charIndex === 0) {
      isDeleting = false;
      messageIndex = (messageIndex + 1) % messages.length;
      typingSpeed = 300;
    }

    setTimeout(typeEffect, typingSpeed);
  }

  // Neural network animation
  let nodes = [];
  let connections = [];
  let animationId;

  function initCanvas() {
    if (!canvas || !ctx) return;
    
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    // Create nodes
    nodes = [];
    const nodeCount = Math.min(50, Math.floor((canvas.width * canvas.height) / 20000));
    
    for (let i = 0; i < nodeCount; i++) {
      nodes.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        radius: Math.random() * 3 + 2,
        pulse: Math.random() * Math.PI * 2
      });
    }
  }

  function drawNetwork() {
    if (!ctx || !canvas) return;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Get theme colors
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const nodeColor = isDark ? 'rgba(129, 140, 248, 0.8)' : 'rgba(99, 102, 241, 0.8)';
    const lineColor = isDark ? 'rgba(129, 140, 248, 0.15)' : 'rgba(99, 102, 241, 0.1)';
    const glowColor = isDark ? 'rgba(129, 140, 248, 0.4)' : 'rgba(99, 102, 241, 0.3)';
    
    // Update and draw connections
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        
        if (dist < 150) {
          ctx.beginPath();
          ctx.moveTo(nodes[i].x, nodes[i].y);
          ctx.lineTo(nodes[j].x, nodes[j].y);
          ctx.strokeStyle = lineColor;
          ctx.lineWidth = 1 - dist / 150;
          ctx.stroke();
        }
      }
    }
    
    // Update and draw nodes
    nodes.forEach(node => {
      // Move node
      node.x += node.vx;
      node.y += node.vy;
      node.pulse += 0.05;
      
      // Bounce off edges
      if (node.x < 0 || node.x > canvas.width) node.vx *= -1;
      if (node.y < 0 || node.y > canvas.height) node.vy *= -1;
      
      // Draw glow
      const pulseSize = Math.sin(node.pulse) * 0.3 + 1;
      const gradient = ctx.createRadialGradient(
        node.x, node.y, 0,
        node.x, node.y, node.radius * 3 * pulseSize
      );
      gradient.addColorStop(0, glowColor);
      gradient.addColorStop(1, 'transparent');
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius * 3 * pulseSize, 0, Math.PI * 2);
      ctx.fill();
      
      // Draw node
      ctx.fillStyle = nodeColor;
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius * pulseSize, 0, Math.PI * 2);
      ctx.fill();
    });
    
    animationId = requestAnimationFrame(drawNetwork);
  }

  // Progress bar animation
  function animateProgress() {
    if (!progressBar) return;
    
    let progress = 0;
    const interval = setInterval(() => {
      progress += 1;
      progressBar.style.width = progress + '%';
      
      if (progress >= 100) {
        clearInterval(interval);
      }
    }, 30);
  }

  // Enter site function
  function enterSite() {
    if (!splash || !mainContent) return;
    
    sessionStorage.setItem('splash-seen', 'true');
    
    splash.classList.add('fade-out');
    
    setTimeout(() => {
      splash.style.display = 'none';
      mainContent.classList.add('visible');
      document.body.classList.remove('has-splash');
      cancelAnimationFrame(animationId);
    }, 800);
  }

  // Click handler
  if (enterBtn) {
    enterBtn.addEventListener('click', enterSite);
  }

  // Keyboard handler
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      enterSite();
    }
  });

  // Touch/Swipe handler for mobile
  let touchStartY = 0;
  let touchEndY = 0;

  if (splash) {
    splash.addEventListener('touchstart', (e) => {
      touchStartY = e.changedTouches[0].screenY;
    }, { passive: true });

    splash.addEventListener('touchend', (e) => {
      touchEndY = e.changedTouches[0].screenY;
      handleSwipe();
    }, { passive: true });
  }

  function handleSwipe() {
    const swipeThreshold = 50;
    if (touchStartY - touchEndY > swipeThreshold) {
      // Swiped up
      enterSite();
    }
  }

  // Initialize
  function init() {
    initCanvas();
    drawNetwork();
    typeEffect();
    animateProgress();
    
    // Handle resize
    window.addEventListener('resize', () => {
      initCanvas();
    });
  }

  // Start when DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
