/* AnwaltsAI App JavaScript - CSP Compliant with Mobile CTAs */

document.addEventListener('DOMContentLoaded', function() {
  // Initialize all functionality
  initRevealAnimations();
  initLoginModal();
  initMobileNavigation();
  initFormHandlers();
  
  console.log('✅ AnwaltsAI app initialized');
});

// Reveal animations on scroll with performance optimization
function initRevealAnimations() {
  const elements = document.querySelectorAll('.reveal');
  
  if (!elements.length) return;
  
  // Use single observer for performance
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        requestAnimationFrame(() => {
          entry.target.classList.add('is-visible');
        });
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.15,
    rootMargin: '0px 0px -20px 0px'
  });
  
  elements.forEach(el => {
    observer.observe(el);
  });
}

// Enhanced login modal functionality
function initLoginModal() {
  const modal = document.getElementById('loginModal');
  const loginBtns = document.querySelectorAll('.login-trigger, [href="/login"]');
  const closeBtn = document.querySelector('.login-close');
  const loginForm = document.getElementById('loginForm');
  const demoBtn = document.getElementById('demoLoginBtn');
  
  if (!modal) return;
  
  // Open modal for all login triggers
  loginBtns.forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      openLoginModal();
    });
  });
  
  // Close modal handlers
  if (closeBtn) {
    closeBtn.addEventListener('click', closeLoginModal);
  }
  
  // Close on outside click
  window.addEventListener('click', function(event) {
    if (event.target === modal) {
      closeLoginModal();
    }
  });
  
  // Close on Escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && modal.style.display === 'block') {
      closeLoginModal();
    }
  });
  
  // Handle login form submission
  if (loginForm) {
    loginForm.addEventListener('submit', handleLogin);
  }
  
  // Handle demo login
  if (demoBtn) {
    demoBtn.addEventListener('click', handleDemoLogin);
  }
}

function openLoginModal() {
  const modal = document.getElementById('loginModal');
  if (modal) {
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    
    // Focus first input for accessibility
    const firstInput = modal.querySelector('input[type="email"]');
    if (firstInput) {
      setTimeout(() => firstInput.focus(), 150);
    }
    
    // Clear previous errors
    clearLoginErrors();
  }
}

function closeLoginModal() {
  const modal = document.getElementById('loginModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    clearLoginErrors();
  }
}

function handleLogin(event) {
  event.preventDefault();
  
  const email = document.getElementById('loginEmail');
  const password = document.getElementById('loginPassword');
  
  if (!email || !password) return;
  
  const emailValue = email.value.trim();
  const passwordValue = password.value;
  
  // Clear previous errors
  clearLoginErrors();
  
  // Client-side validation
  if (!emailValue || !passwordValue) {
    showLoginError('Bitte füllen Sie alle Felder aus.');
    return;
  }
  
  if (!isValidEmail(emailValue)) {
    showLoginError('Bitte geben Sie eine gültige E-Mail-Adresse ein.');
    return;
  }
  
  // Demo credentials check
  if (emailValue === 'admin@anwalts-ai.com' && passwordValue === 'admin123') {
    performLogin({
      email: emailValue,
      name: 'Demo Administrator',
      role: 'admin',
      loginTime: Date.now()
    });
    return;
  }
  
  // Show error for other credentials
  showLoginError('Ungültige Anmeldedaten. Versuchen Sie: admin@anwalts-ai.com / admin123');
}

function handleDemoLogin() {
  performLogin({
    email: 'admin@anwalts-ai.com',
    name: 'Demo Administrator',
    role: 'admin',
    loginTime: Date.now()
  });
}

function performLogin(userData) {
  try {
    // Store user data
    localStorage.setItem('anwalts_ai_user', JSON.stringify(userData));
    
    // Close modal
    closeLoginModal();
    
    // Redirect to dashboard
    window.location.href = 'dashboard-content.html';
    
  } catch (error) {
    console.error('Login error:', error);
    showLoginError('Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.');
  }
}

function showLoginError(message) {
  clearLoginErrors();
  
  const errorEl = document.createElement('div');
  errorEl.className = 'login-error';
  errorEl.style.cssText = 'color: #ef4444; font-size: 14px; margin-top: 12px; text-align: center; padding: 8px; background: rgba(239, 68, 68, 0.1); border-radius: 6px;';
  errorEl.textContent = message;
  
  const form = document.getElementById('loginForm');
  if (form) {
    form.appendChild(errorEl);
    
    setTimeout(() => {
      if (errorEl.parentNode) {
        errorEl.remove();
      }
    }, 5000);
  }
}

function clearLoginErrors() {
  const existingErrors = document.querySelectorAll('.login-error');
  existingErrors.forEach(error => error.remove());
}

function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

// Mobile navigation enhancement
function initMobileNavigation() {
  const mobileNavBtn = document.getElementById('mobile-nav');
  const navLinks = document.getElementById('nav-links');
  
  if (!mobileNavBtn || !navLinks) return;
  
  mobileNavBtn.addEventListener('click', function(e) {
    e.preventDefault();
    const isVisible = navLinks.style.display === 'block';
    navLinks.style.display = isVisible ? 'none' : 'block';
    mobileNavBtn.setAttribute('aria-expanded', !isVisible);
  });
}

// Handle signup and form submissions
function initFormHandlers() {
  // Handle signup links
  const signupLinks = document.querySelectorAll('[href="/signup"], .signup-trigger');
  signupLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      // Scroll to contact section for signup
      const contactSection = document.querySelector('#kontakt');
      if (contactSection) {
        contactSection.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });
}