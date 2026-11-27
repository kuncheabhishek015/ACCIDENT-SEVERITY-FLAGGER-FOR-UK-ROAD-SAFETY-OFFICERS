/* ==========================================================================
   Officer Authentication & View State Router
   Handles login credentials, demo account quick-fill, session state,
   and seamless transitions between Cinematic Landing Page and Main Portal.
   ========================================================================== */

const AuthPortal = (() => {
  // Preconfigured Demo Credentials for Evaluators & Safety Officers
  const DEMO_ACCOUNTS = {
    officer: {
      email: 'officer@dft.gov.uk',
      pass: 'safety2026',
      name: 'Kunche Abhishek',
      role: 'Senior Road Safety Officer',
      badge: 'DfT STATS19 Specialist',
      warrantId: 'DFT-8492-UK',
      authority: 'UK Department for Transport (DfT)',
      clearance: 'Level 3 Statutory Road Safety & Engineering Access',
      jurisdiction: 'National Highway Network & Strategic Road Network (SRN)',
      verified: true
    },
    planner: {
      email: 'planner@council.gov.uk',
      pass: 'council2026',
      name: 'Sarah Jenkins',
      role: 'Council Transport Director',
      badge: 'Intervention Allocator',
      warrantId: 'CPA-3011-LHA',
      authority: 'Local Highway Authority (LHA) Planning Directorate',
      clearance: 'Council Capital Safety Works Sign-off Authority',
      jurisdiction: 'Metropolitan & County Borough Carriageways',
      verified: true
    },
    scientist: {
      email: 'scientist@stats19.uk',
      pass: 'audit2026',
      name: 'Dr. David Evans',
      role: 'Lead ML Data Scientist',
      badge: 'Statistical Model Auditor',
      warrantId: 'SAB-9924-STATS',
      authority: 'DfT STATS19 Statistical Audit Review Board',
      clearance: 'ML Benchmark & Probabilistic Inference Evaluator',
      jurisdiction: 'National Casualty Empirical Database',
      verified: true
    },
    guest: {
      email: 'guest@roadsafety.org',
      pass: 'guest2026',
      name: 'Citizen Road Safety Auditor',
      role: 'Public Safety Observer',
      badge: 'Public Read-Only',
      warrantId: 'PUB-1004-OBS',
      authority: 'Vision Zero UK Public Transparency Portal',
      clearance: 'Public Open-Data Inquiry Access',
      jurisdiction: 'UK Public Road Safety Open Evidence',
      verified: true
    }
  };

  let currentUser = JSON.parse(localStorage.getItem('ROAD_SAFETY_USER')) || DEMO_ACCOUNTS.officer;

  function init() {
    bindEvents();
    checkInitialView();
  }

  function bindEvents() {
    // Open login modal triggers
    document.querySelectorAll('.open-login-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        openLoginModal();
      });
    });

    // Close modal
    const closeBtn = document.getElementById('login-modal-close');
    const modal = document.getElementById('login-modal-overlay');
    if (closeBtn) closeBtn.addEventListener('click', closeLoginModal);
    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) closeLoginModal();
      });
    }

    // Quick-fill credentials buttons
    document.querySelectorAll('.demo-account-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const key = chip.getAttribute('data-account');
        fillDemoAccount(key);
      });
    });

    // Form submit
    const form = document.getElementById('officer-login-form');
    if (form) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        handleLogin();
      });
    }

    // View switcher buttons (Back to Landing / Go to Dashboard)
    const btnToLanding = document.getElementById('nav-to-landing');
    if (btnToLanding) {
      btnToLanding.addEventListener('click', () => {
        showView('landing');
      });
    }

    const btnToDashboard = document.getElementById('nav-to-dashboard');
    if (btnToDashboard) {
      btnToDashboard.addEventListener('click', () => {
        showView('dashboard');
      });
    }

    // Logout button
    const logoutBtn = document.getElementById('officer-logout-btn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => {
        logout();
      });
    }
  }

  function openLoginModal() {
    const modal = document.getElementById('login-modal-overlay');
    if (!modal) return;
    if (window.SoundFX && window.SoundFX.playClick) window.SoundFX.playClick();
    modal.style.display = 'flex';

    // Auto-focus email
    const emailInput = document.getElementById('login-email');
    if (emailInput) setTimeout(() => emailInput.focus(), 100);
  }

  function closeLoginModal() {
    const modal = document.getElementById('login-modal-overlay');
    if (modal) modal.style.display = 'none';
  }

  function fillDemoAccount(accountKey) {
    const acc = DEMO_ACCOUNTS[accountKey];
    if (!acc) return;

    const emailInput = document.getElementById('login-email');
    const passInput = document.getElementById('login-password');
    if (emailInput) emailInput.value = acc.email;
    if (passInput) passInput.value = acc.pass;

    if (window.SoundFX && window.SoundFX.playClick) window.SoundFX.playClick();

    // Visual highlight on form
    const formCard = document.querySelector('.login-modal-card');
    if (formCard) {
      formCard.style.borderColor = 'var(--accent-primary)';
      setTimeout(() => formCard.style.borderColor = '', 600);
    }
  }

  function handleLogin() {
    const email = document.getElementById('login-email')?.value.trim();
    const pass = document.getElementById('login-password')?.value;
    const statusMsg = document.getElementById('login-status-msg');
    const submitBtn = document.getElementById('login-submit-btn');

    if (!email || !pass) {
      if (statusMsg) statusMsg.innerHTML = '<span style="color:#ef4444">Please enter email and password.</span>';
      return;
    }

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerText = 'Verifying Credentials...';
    }

    // Match against demo or authenticate
    let matchedUser = Object.values(DEMO_ACCOUNTS).find(a => a.email.toLowerCase() === email.toLowerCase());
    if (!matchedUser) {
      matchedUser = {
        email: email,
        name: email.split('@')[0].toUpperCase(),
        role: 'Authenticated Officer',
        badge: 'UK Road Safety Portal'
      };
    }

    setTimeout(() => {
      currentUser = matchedUser;
      localStorage.setItem('ROAD_SAFETY_USER', JSON.stringify(currentUser));

      if (statusMsg) {
        statusMsg.innerHTML = `<span style="color:#10b981">✓ Welcome, ${currentUser.name}! Entering Intelligence Portal...</span>`;
      }

      if (window.SoundFX && window.SoundFX.playPresetChime) window.SoundFX.playPresetChime();

      setTimeout(() => {
        closeLoginModal();
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerText = 'Authenticate & Enter Portal ➔';
        }
        updateUserUI();
        showView('dashboard');
      }, 250);
    }, 150);
  }

  function logout() {
    currentUser = DEMO_ACCOUNTS.officer;
    localStorage.removeItem('ROAD_SAFETY_USER');
    if (window.SoundFX && window.SoundFX.playClick) window.SoundFX.playClick();
    updateUserUI();
    showView('landing');
  }

  function updateUserUI() {
    const nameEl = document.getElementById('logged-officer-name');
    const roleEl = document.getElementById('logged-officer-role');
    const authBadge = document.getElementById('auth-status-indicator');
    const avatarBadge = document.getElementById('officer-avatar-badge');

    const activeUser = currentUser || DEMO_ACCOUNTS.officer;
    const parts = (activeUser && activeUser.name) ? activeUser.name.split(' ').filter(Boolean) : [];
    const initials = parts.length > 1 ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase() : 'KA';

    if (nameEl) nameEl.innerText = activeUser.name;
    if (roleEl) roleEl.innerText = `${activeUser.role}`;
    if (avatarBadge) avatarBadge.innerText = initials;
    if (authBadge) authBadge.style.display = 'inline-flex';
  }

  function showView(viewName) {
    const landingView = document.getElementById('view-landing-page');
    const dashboardView = document.getElementById('view-dashboard-page');

    if (viewName === 'landing') {
      if (landingView) landingView.style.display = 'block';
      if (dashboardView) dashboardView.style.display = 'none';
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      if (landingView) landingView.style.display = 'none';
      if (dashboardView) dashboardView.style.display = 'block';
      window.scrollTo({ top: 0, behavior: 'instant' });
      // Update conditions summary; keep risk at zero until user evaluates
      if (window.updateConditionsSummary) window.updateConditionsSummary();
      if (window.hasEvaluatedRisk && window.evaluateRisk) {
        window.evaluateRisk();
      } else if (window.renderZeroRiskState) {
        window.renderZeroRiskState();
      }
      setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
        if (typeof Plotly !== 'undefined') {
          Plotly.Plots.resize('gauge-chart');
          Plotly.Plots.resize('weather-chart');
          Plotly.Plots.resize('light-chart');
          Plotly.Plots.resize('benchmark-chart');
        }
      }, 70);
    }
  }

  function checkInitialView() {
    updateUserUI();
    // Default to Landing view if not explicitly in dashboard mode
    showView('landing');
  }

  return {
    init,
    openLoginModal,
    closeLoginModal,
    showView,
    logout,
    getCurrentUser: () => currentUser
  };
})();

window.openLoginModal = AuthPortal.openLoginModal;
window.showView = AuthPortal.showView;
