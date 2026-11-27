/* Sound FX Synthesizer using Web Audio API (Zero external audio files needed) */

var SoundFX = (() => {
  let audioCtx = null;
  let isMuted = localStorage.getItem('ROAD_SAFETY_MUTED') === 'true';

  function getContext() {
    if (!audioCtx && (window.AudioContext || window.webkitAudioContext)) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    return audioCtx;
  }

  function isAudioEnabled() {
    return !isMuted;
  }

  function toggleMute() {
    isMuted = !isMuted;
    localStorage.setItem('ROAD_SAFETY_MUTED', isMuted);
    updateSoundButtonUI();
    if (!isMuted) {
      playClick();
    }
    return isMuted;
  }

  function updateSoundButtonUI() {
    const btn = document.getElementById('sound-toggle-btn');
    if (!btn) return;
    if (isMuted) {
      btn.innerHTML = `<span class="sound-icon">🔇</span> <span class="sound-text">Muted</span>`;
      btn.classList.add('muted');
      btn.setAttribute('title', 'Sound Effects Muted. Click to Unmute.');
    } else {
      btn.innerHTML = `<span class="sound-icon">🔊</span> <span class="sound-text">Sound FX</span>`;
      btn.classList.remove('muted');
      btn.setAttribute('title', 'Sound Effects Active. Click to Mute.');
    }
  }

  // Soft high-tech UI click
  function playClick() {
    if (!isAudioEnabled()) return;
    try {
      const ctx = getContext();
      if (!ctx) return;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(1400, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(700, ctx.currentTime + 0.04);

      gain.gain.setValueAtTime(0.08, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.04);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      osc.stop(ctx.currentTime + 0.04);
    } catch (e) {
      // AudioContext policy catch
    }
  }

  // Pleasant tab switch swoosh
  function playTabSwitch() {
    if (!isAudioEnabled()) return;
    try {
      const ctx = getContext();
      if (!ctx) return;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(440, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.07);

      gain.gain.setValueAtTime(0.06, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.07);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      osc.stop(ctx.currentTime + 0.07);
    } catch (e) { }
  }

  // Preset selected notification
  function playPresetChime() {
    if (!isAudioEnabled()) return;
    try {
      const ctx = getContext();
      if (!ctx) return;

      [523.25, 659.25, 783.99].forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        const startTime = ctx.currentTime + idx * 0.05;

        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, startTime);

        gain.gain.setValueAtTime(0.07, startTime);
        gain.gain.exponentialRampToValueAtTime(0.001, startTime + 0.12);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start(startTime);
        osc.stop(startTime + 0.12);
      });
    } catch (e) { }
  }

  // Evaluation outcome sound based on risk category
  function playRiskResult(category) {
    if (!isAudioEnabled()) return;
    try {
      const ctx = getContext();
      if (!ctx) return;

      if (category === 'Low Risk') {
        // Soft harmonic major chord (C5 - G5 - C6)
        [523.25, 659.25, 783.99, 1046.50].forEach((freq, i) => {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          const t = ctx.currentTime + (i * 0.05);

          osc.type = 'sine';
          osc.frequency.setValueAtTime(freq, t);

          gain.gain.setValueAtTime(0.09, t);
          gain.gain.exponentialRampToValueAtTime(0.001, t + 0.25);

          osc.connect(gain);
          gain.connect(ctx.destination);

          osc.start(t);
          osc.stop(t + 0.25);
        });
      } else if (category === 'Moderate Risk') {
        // Caution dual-tone chime
        [440, 554.37].forEach((freq, i) => {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          const t = ctx.currentTime + (i * 0.08);

          osc.type = 'triangle';
          osc.frequency.setValueAtTime(freq, t);

          gain.gain.setValueAtTime(0.1, t);
          gain.gain.exponentialRampToValueAtTime(0.001, t + 0.22);

          osc.connect(gain);
          gain.connect(ctx.destination);

          osc.start(t);
          osc.stop(t + 0.22);
        });
      } else {
        // High or Critical Risk: Tactical warning pulse chord
        [349.23, 277.18, 220.00].forEach((freq, i) => {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          const t = ctx.currentTime + (i * 0.06);

          osc.type = 'sawtooth';
          osc.frequency.setValueAtTime(freq, t);

          gain.gain.setValueAtTime(0.12, t);
          gain.gain.exponentialRampToValueAtTime(0.001, t + 0.35);

          osc.connect(gain);
          gain.connect(ctx.destination);

          osc.start(t);
          osc.stop(t + 0.35);
        });
      }
    } catch (e) { }
  }

  return {
    toggleMute,
    updateSoundButtonUI,
    playClick,
    playTabSwitch,
    playPresetChime,
    playRiskResult,
    isMuted: () => isMuted
  };
})();

window.SoundFX = SoundFX;
