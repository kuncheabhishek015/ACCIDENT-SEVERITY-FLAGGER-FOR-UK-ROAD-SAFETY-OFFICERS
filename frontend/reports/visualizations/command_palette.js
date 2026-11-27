/* Spotlight Command Palette (Ctrl+K / Cmd+K)
 * Quick actions, tab navigation, preset loading, theme switcher, and settings.
 */

const CommandPalette = (() => {
  let modal = null;
  let input = null;
  let resultsList = null;
  let activeIndex = 0;
  let filteredCommands = [];

  const COMMANDS = [
    // Navigation
    { id: 'tab-risk', category: 'Navigation', icon: '🎯', title: 'Go to Risk Evaluator & Road Simulator', action: () => switchTab('risk-evaluator') },
    { id: 'tab-shortlist', category: 'Navigation', icon: '📋', title: 'Go to Council Shortlist (Top K Interventions)', action: () => switchTab('priority-shortlist') },
    { id: 'tab-eda', category: 'Navigation', icon: '📈', title: 'Go to EDA & Publication Plots', action: () => switchTab('eda-gallery') },
    { id: 'tab-chi', category: 'Navigation', icon: '📊', title: 'Go to Chi-Square Statistics & Contingency Tables', action: () => switchTab('statistical-insights') },
    { id: 'tab-benchmarks', category: 'Navigation', icon: '🧠', title: 'Go to ML Model Benchmarks (Precision@25)', action: () => switchTab('model-benchmarks') },
    { id: 'tab-audit', category: 'Navigation', icon: '📜', title: 'Go to SQL Query Audit Logs', action: () => switchTab('audit-logs') },

    // Scenario Presets
    { id: 'preset-rural', category: 'Preset', icon: '🌧️', title: 'Load Scenario: Rural High-Speed Wet Carriageway (60 mph)', action: () => loadPreset('rural_wet') },
    { id: 'preset-night', category: 'Preset', icon: '🌃', title: 'Load Scenario: Night City T-Junction (30 mph)', action: () => loadPreset('night_city') },
    { id: 'preset-fog', category: 'Preset', icon: '🌫️', title: 'Load Scenario: Foggy Dawn Motorway (70 mph)', action: () => loadPreset('fog_motorway') },
    { id: 'preset-ice', category: 'Preset', icon: '❄️', title: 'Load Scenario: Icy Suburban Roundabout (20 mph)', action: () => loadPreset('ice_roundabout') },
    { id: 'preset-clear', category: 'Preset', icon: '☀️', title: 'Load Scenario: Clear Dual Carriageway (50 mph)', action: () => loadPreset('clear_dual') },

    // Themes
    { id: 'theme-titanium', category: 'Theme', icon: '✨', title: 'Switch Theme: Ultra-Sleek Titanium Glass (Apple / Linear)', action: () => setTheme('titanium') },
    { id: 'theme-cyber', category: 'Theme', icon: '⚡', title: 'Switch Theme: Cyber Command HUD (Neon Cyan & Amber)', action: () => setTheme('cyber') },
    { id: 'theme-emerald', category: 'Theme', icon: '🛡️', title: 'Switch Theme: Emerald Safety (GovTech Road Safety)', action: () => setTheme('emerald') },

    // Actions
    { id: 'act-eval', category: 'Action', icon: '⚡', title: 'Calculate Collision Risk Immediately', action: () => { switchTab('risk-evaluator'); if (window.evaluateRisk) window.evaluateRisk(); } },
    { id: 'act-sound', category: 'Action', icon: '🔊', title: 'Toggle Sound Effects (Mute / Unmute)', action: () => { if (window.SoundFX) window.SoundFX.toggleMute(); } },
    { id: 'act-export', category: 'Action', icon: '📥', title: 'Export Council Shortlist to CSV File', action: () => { const btn = document.getElementById('export-csv-btn'); if (btn) btn.click(); } },
    { id: 'act-refresh', category: 'Action', icon: '🔄', title: 'Refresh SQL Audit Logs', action: () => { const btn = document.getElementById('refresh-logs-btn'); if (btn) btn.click(); } },
    { id: 'act-api', category: 'Action', icon: '⚙️', title: 'Configure Flask Backend API Endpoint', action: () => { if (window.openApiConfigModal) window.openApiConfigModal(); } }
  ];

  function init() {
    createPaletteDOM();
    bindEvents();
  }

  function createPaletteDOM() {
    const existing = document.getElementById('command-palette-modal');
    if (existing) existing.remove();

    const dom = `
      <div id="command-palette-modal" class="palette-overlay" style="display:none;">
        <div class="palette-card">
          <div class="palette-search-box">
            <span class="palette-icon">🔍</span>
            <input type="text" id="palette-input" placeholder="Type a command, scenario preset, or tab..." autocomplete="off">
            <kbd class="palette-esc-kbd">ESC</kbd>
          </div>
          <div class="palette-results" id="palette-results"></div>
          <div class="palette-footer">
            <span><kbd>↑</kbd> <kbd>↓</kbd> to navigate</span>
            <span><kbd>↵</kbd> to select</span>
            <span><kbd>esc</kbd> to close</span>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', dom);
    modal = document.getElementById('command-palette-modal');
    input = document.getElementById('palette-input');
    resultsList = document.getElementById('palette-results');
  }

  function bindEvents() {
    // Keyboard shortcut (Ctrl+K or Cmd+K)
    window.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
        e.preventDefault();
        toggle();
      } else if (e.key === 'Escape' && isOpen()) {
        close();
      }
    });

    // Header search button click
    const triggerBtn = document.getElementById('command-palette-btn');
    if (triggerBtn) {
      triggerBtn.addEventListener('click', open);
    }

    // Modal background click
    modal.addEventListener('click', (e) => {
      if (e.target === modal) close();
    });

    // Input search typing
    input.addEventListener('input', () => {
      renderResults(input.value);
    });

    // Arrow keys & Enter inside input
    input.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        navigate(1);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        navigate(-1);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        executeActive();
      }
    });
  }

  function isOpen() {
    return modal && modal.style.display !== 'none';
  }

  function toggle() {
    if (isOpen()) close();
    else open();
  }

  function open() {
    if (!modal) return;
    if (window.SoundFX) window.SoundFX.playClick();
    modal.style.display = 'flex';
    input.value = '';
    renderResults('');
    input.focus();
  }

  function close() {
    if (!modal) return;
    modal.style.display = 'none';
  }

  function renderResults(query) {
    const q = query.toLowerCase().trim();
    filteredCommands = COMMANDS.filter(c => 
      c.title.toLowerCase().includes(q) || c.category.toLowerCase().includes(q)
    );

    activeIndex = 0;

    if (filteredCommands.length === 0) {
      resultsList.innerHTML = `<div class="palette-empty">No matching commands found for "${query}"</div>`;
      return;
    }

    let currentCat = '';
    let html = '';

    filteredCommands.forEach((cmd, idx) => {
      if (cmd.category !== currentCat) {
        currentCat = cmd.category;
        html += `<div class="palette-category-label">${currentCat}</div>`;
      }

      html += `
        <div class="palette-item ${idx === activeIndex ? 'active' : ''}" data-index="${idx}">
          <span class="palette-item-icon">${cmd.icon}</span>
          <span class="palette-item-title">${cmd.title}</span>
          <span class="palette-item-badge">${cmd.category}</span>
        </div>
      `;
    });

    resultsList.innerHTML = html;

    // Attach click handlers to items
    resultsList.querySelectorAll('.palette-item').forEach(el => {
      el.addEventListener('click', () => {
        const idx = parseInt(el.getAttribute('data-index'));
        activeIndex = idx;
        executeActive();
      });
      el.addEventListener('mouseenter', () => {
        const idx = parseInt(el.getAttribute('data-index'));
        updateActiveIndex(idx);
      });
    });
  }

  function navigate(delta) {
    if (filteredCommands.length === 0) return;
    activeIndex = (activeIndex + delta + filteredCommands.length) % filteredCommands.length;
    updateActiveIndex(activeIndex);
  }

  function updateActiveIndex(idx) {
    activeIndex = idx;
    const items = resultsList.querySelectorAll('.palette-item');
    items.forEach((item, i) => {
      if (i === activeIndex) {
        item.classList.add('active');
        item.scrollIntoView({ block: 'nearest' });
      } else {
        item.classList.remove('active');
      }
    });
  }

  function executeActive() {
    if (filteredCommands.length > 0 && filteredCommands[activeIndex]) {
      const cmd = filteredCommands[activeIndex];
      close();
      if (window.SoundFX) window.SoundFX.playClick();
      cmd.action();
    }
  }

  function switchTab(tabId) {
    const tabBtn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
    if (tabBtn) tabBtn.click();
  }

  function loadPreset(key) {
    switchTab('risk-evaluator');
    if (window.applyScenarioPreset) {
      window.applyScenarioPreset(key);
    }
  }

  function setTheme(theme) {
    if (window.setAppTheme) {
      window.setAppTheme(theme);
    }
  }

  return {
    init,
    open,
    close,
    toggle
  };
})();
