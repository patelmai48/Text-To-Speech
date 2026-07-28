/**
 * Main Application Controller (Dashboard, Studio, Audio Player, Canvas Visualizer, History, Profile)
 */

document.addEventListener('DOMContentLoaded', () => {
  // Check auth
  if (!AuthToken.exists() && !window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
    window.location.href = '/login';
    return;
  }

  // --- State Variables ---
  let currentUser = null;
  let availableVoices = [];
  let currentAudio = new Audio();
  let audioContext = null;
  let analyserNode = null;
  let audioSourceNode = null;
  let isVisualizerSetup = false;
  let animationFrameId = null;

  // --- DOM Elements ---
  const navItems = document.querySelectorAll('.nav-item');
  const viewPanels = document.querySelectorAll('.view-panel');
  const pageTitle = document.getElementById('page-title');
  const themeToggleBtn = document.getElementById('theme-toggle');
  const logoutBtn = document.getElementById('logout-btn');
  const mobileNavToggle = document.getElementById('mobile-nav-toggle');
  const sidebar = document.querySelector('.sidebar');

  // Studio Elements
  const textEditor = document.getElementById('text-editor');
  const charCounter = document.getElementById('char-counter');
  const voiceSelect = document.getElementById('voice-select');
  const speedSlider = document.getElementById('speed-slider');
  const speedVal = document.getElementById('speed-val');
  const pitchSlider = document.getElementById('pitch-slider');
  const pitchVal = document.getElementById('pitch-val');
  const volumeSlider = document.getElementById('volume-slider');
  const volumeVal = document.getElementById('volume-val');
  const convertBtn = document.getElementById('convert-btn');
  const clearTextBtn = document.getElementById('clear-text-btn');
  const copyTextBtn = document.getElementById('copy-text-btn');
  const summarizeBtn = document.getElementById('summarize-btn');

  // Player Elements
  const playerCard = document.getElementById('player-card');
  const playPauseBtn = document.getElementById('play-pause-btn');
  const stopBtn = document.getElementById('stop-btn');
  const downloadAudioBtn = document.getElementById('download-audio-btn');
  const playerTimeDisplay = document.getElementById('player-time-display');
  const visualizerCanvas = document.getElementById('waveform-canvas');

  // History & Favorites Elements
  const historySearchInput = document.getElementById('history-search');
  const historyTableBody = document.getElementById('history-table-body');
  const clearHistoryBtn = document.getElementById('clear-history-btn');
  const exportCsvBtn = document.getElementById('export-csv-btn');
  const exportPdfBtn = document.getElementById('export-pdf-btn');
  const favoritesContainer = document.getElementById('favorites-container');
  const favVoiceBtn = document.getElementById('fav-voice-btn');

  // Profile Elements
  const profileForm = document.getElementById('profile-form');
  const passwordForm = document.getElementById('password-form');
  const deleteAccountBtn = document.getElementById('delete-account-btn');

  // --- Initializer ---
  initApp();

  async function initApp() {
    setupTheme();
    setupNavigation();
    setupMobileSidebar();
    setupShortcuts();
    setupEditorAutoSave();
    setupAudioPlayer();

    await loadUserData();
    await loadVoices();
    await loadHistory();
    await loadFavorites();

    // Hide player initially
    if (playerCard) playerCard.style.display = 'none';
  }

  // --- Theme Management ---
  function setupTheme() {
    const savedTheme = localStorage.getItem('tts_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    if (themeToggleBtn) {
      themeToggleBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('tts_theme', newTheme);
        updateThemeIcon(newTheme);
        showToast(`Switched to ${newTheme} mode`, 'info');
      });
    }
  }

  function updateThemeIcon(theme) {
    if (themeToggleBtn) {
      const icon = themeToggleBtn.querySelector('i');
      if (icon) {
        icon.className = theme === 'light' ? 'bi bi-moon-stars-fill' : 'bi bi-sun-fill';
      }
    }
  }

  // --- Navigation & Views ---
  function setupNavigation() {
    navItems.forEach(item => {
      item.addEventListener('click', () => {
        const targetView = item.getAttribute('data-view');

        navItems.forEach(n => n.classList.remove('active'));
        item.classList.add('active');

        viewPanels.forEach(panel => {
          if (panel.id === `${targetView}-view`) {
            panel.classList.add('active');
          } else {
            panel.classList.remove('active');
          }
        });

        if (pageTitle) {
          const titles = {
            'dashboard': 'Dashboard',
            'studio': 'TTS Studio',
            'history': 'Conversion History',
            'favorites': 'Favorite Voices',
            'profile': 'Account Profile'
          };
          pageTitle.textContent = titles[targetView] || 'TTS Application';
        }

        if (window.innerWidth <= 768 && sidebar) {
          sidebar.classList.remove('open');
        }
      });
    });

    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => {
        AuthToken.remove();
        showToast('Logged out successfully.', 'info');
        setTimeout(() => window.location.href = '/login', 600);
      });
    }
  }

  function setupMobileSidebar() {
    if (mobileNavToggle && sidebar) {
      mobileNavToggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
      });
    }
  }

  // --- Load User Profile Data & Stats ---
  async function loadUserData() {
    const res = await API.get('/profile');
    if (res.success) {
      currentUser = res.user;

      // Update Header & Sidebar UI
      const userNames = document.querySelectorAll('.user-name-display');
      const userEmails = document.querySelectorAll('.user-email-display');
      const userAvatars = document.querySelectorAll('.avatar-circle');

      userNames.forEach(el => el.textContent = currentUser.username);
      userEmails.forEach(el => el.textContent = currentUser.email);
      userAvatars.forEach(el => el.textContent = currentUser.username.charAt(0).toUpperCase());

      // Update Dashboard Stats Cards
      if (res.stats) {
        document.getElementById('stat-total-conversions').textContent = res.stats.total_conversions || 0;
        document.getElementById('stat-total-characters').textContent = (res.stats.total_characters || 0).toLocaleString();
        document.getElementById('stat-favorite-voices').textContent = res.stats.favorite_voices_count || 0;

        if (res.stats.last_login) {
          const lastDate = new Date(res.stats.last_login);
          document.getElementById('stat-last-login').textContent = lastDate.toLocaleDateString() + ' ' + lastDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
      }

      // Populate Profile form inputs
      if (document.getElementById('profile-username')) {
        document.getElementById('profile-username').value = currentUser.username;
        document.getElementById('profile-email').value = currentUser.email;
      }
    }
  }

  // --- Voice Selection Engine ---
  async function loadVoices() {
    const res = await API.get('/voices');
    if (res.success && res.voices) {
      availableVoices = res.voices;
      if (voiceSelect) {
        voiceSelect.innerHTML = availableVoices.map(v => `
          <option value="${v.voice_id}">${v.flag} ${v.name} (${v.gender})</option>
        `).join('');
      }
    }
  }

  // --- Editor & Controls Handlers ---
  function setupEditorAutoSave() {
    // Draft autosave in local storage
    const savedDraft = localStorage.getItem('tts_draft_text');
    if (savedDraft && textEditor) {
      textEditor.value = savedDraft;
      updateCharCount();
    }

    if (textEditor) {
      textEditor.addEventListener('input', () => {
        updateCharCount();
        localStorage.setItem('tts_draft_text', textEditor.value);
      });
    }

    // Slider value synchronization
    if (speedSlider && speedVal) {
      speedSlider.addEventListener('input', () => speedVal.textContent = `${parseFloat(speedSlider.value).toFixed(1)}x`);
    }
    if (pitchSlider && pitchVal) {
      pitchSlider.addEventListener('input', () => pitchVal.textContent = `${parseFloat(pitchSlider.value).toFixed(1)}x`);
    }
    if (volumeSlider && volumeVal) {
      volumeSlider.addEventListener('input', () => {
        const val = parseFloat(volumeSlider.value);
        volumeVal.textContent = `${Math.round(val * 100)}%`;
        if (currentAudio) currentAudio.volume = val;
      });
    }

    // Action buttons
    if (clearTextBtn) {
      clearTextBtn.addEventListener('click', () => {
        textEditor.value = '';
        updateCharCount();
        localStorage.removeItem('tts_draft_text');
        showToast('Text cleared', 'info');
      });
    }

    if (copyTextBtn) {
      copyTextBtn.addEventListener('click', () => {
        if (!textEditor.value.trim()) return;
        navigator.clipboard.writeText(textEditor.value);
        showToast('Text copied to clipboard!', 'success');
      });
    }

    if (summarizeBtn) {
      summarizeBtn.addEventListener('click', async () => {
        const text = textEditor.value.trim();
        if (!text) {
          showToast('Please enter text to summarize.', 'warning');
          return;
        }

        summarizeBtn.disabled = true;
        summarizeBtn.innerHTML = '<div class="spinner"></div> Summarizing...';

        const res = await API.post('/tts/summarize', { text });

        summarizeBtn.disabled = false;
        summarizeBtn.innerHTML = '<i class="bi bi-magic"></i> Summarize';

        if (res.success && res.summary) {
          textEditor.value = res.summary;
          updateCharCount();
          showToast('Text summarized successfully!', 'success');
        } else {
          showToast(res.message || 'Summarization failed.', 'error');
        }
      });
    }

    // Favorite Voice Toggle Button
    if (favVoiceBtn) {
      favVoiceBtn.addEventListener('click', async () => {
        const selectedVoice = voiceSelect.value;
        const res = await API.post('/favorites', { item_type: 'voice', item_value: selectedVoice });
        if (res.success) {
          showToast('Added voice to favorites!', 'success');
          await loadFavorites();
          await loadUserData();
        }
      });
    }

    // Convert Button
    if (convertBtn) {
      convertBtn.addEventListener('click', handleSpeechConversion);
    }
  }

  function updateCharCount() {
    if (!textEditor || !charCounter) return;
    const len = textEditor.value.length;
    const max = 3000;
    charCounter.textContent = `${len} / ${max}`;

    if (len > max) {
      charCounter.className = 'char-counter limit';
    } else if (len > 2500) {
      charCounter.className = 'char-counter warning';
    } else {
      charCounter.className = 'char-counter';
    }
  }

  // --- Speech Conversion API Handler ---
  async function handleSpeechConversion() {
    const text = textEditor.value.trim();
    if (!text) {
      showToast('Please enter text to synthesize.', 'warning');
      return;
    }

    const voice = voiceSelect.value;
    const speed = parseFloat(speedSlider.value);
    const pitch = parseFloat(pitchSlider.value);
    const volume = parseFloat(volumeSlider.value);

    convertBtn.disabled = true;
    convertBtn.innerHTML = `<div class="spinner"></div> Synthesizing Audio...`;

    const res = await API.post('/tts', { text, voice, speed, pitch, volume });

    convertBtn.disabled = false;
    convertBtn.innerHTML = `<i class="bi bi-soundwave"></i> Convert to Speech`;

    if (res.success && res.history) {
      showToast('Audio synthesized successfully!', 'success');
      playGeneratedAudio(res.history.audio_url);
      await loadHistory();
      await loadUserData();
    } else {
      showToast(res.message || 'Audio synthesis failed.', 'error');
    }
  }

  // --- Audio Player & Canvas Waveform Visualizer ---
  function setupAudioPlayer() {
    if (playPauseBtn) {
      playPauseBtn.addEventListener('click', () => {
        if (currentAudio.paused) {
          currentAudio.play();
          playPauseBtn.innerHTML = '<i class="bi bi-pause-fill"></i>';
        } else {
          currentAudio.pause();
          playPauseBtn.innerHTML = '<i class="bi bi-play-fill"></i>';
        }
      });
    }

    if (stopBtn) {
      stopBtn.addEventListener('click', () => {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        playPauseBtn.innerHTML = '<i class="bi bi-play-fill"></i>';
        if (playerTimeDisplay) playerTimeDisplay.textContent = '00:00 / 00:00';
      });
    }

    currentAudio.addEventListener('timeupdate', () => {
      if (playerTimeDisplay && currentAudio.duration) {
        const cur = formatTime(currentAudio.currentTime);
        const dur = formatTime(currentAudio.duration);
        playerTimeDisplay.textContent = `${cur} / ${dur}`;
      }
    });

    currentAudio.addEventListener('ended', () => {
      if (playPauseBtn) playPauseBtn.innerHTML = '<i class="bi bi-play-fill"></i>';
    });
  }

  function playGeneratedAudio(audioUrl) {
    if (!audioUrl) return;

    if (playerCard) playerCard.style.display = 'block';

    currentAudio.src = audioUrl;
    currentAudio.volume = parseFloat(volumeSlider.value);
    currentAudio.playbackRate = parseFloat(speedSlider.value);

    currentAudio.play().then(() => {
      if (playPauseBtn) playPauseBtn.innerHTML = '<i class="bi bi-pause-fill"></i>';
      initCanvasVisualizer();
    }).catch(err => {
      console.warn("Autoplay deferred:", err);
    });

    if (downloadAudioBtn) {
      downloadAudioBtn.onclick = () => {
        const a = document.createElement('a');
        a.href = audioUrl;
        a.download = `speech_${Date.now()}.mp3`;
        a.click();
      };
    }
  }

  function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  // --- Real-time Canvas Waveform Animation ---
  function initCanvasVisualizer() {
    if (!visualizerCanvas) return;

    if (!audioContext) {
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }

    if (audioContext.state === 'suspended') {
      audioContext.resume();
    }

    if (!isVisualizerSetup) {
      try {
        analyserNode = audioContext.createAnalyser();
        analyserNode.fftSize = 64;
        audioSourceNode = audioContext.createMediaElementSource(currentAudio);
        audioSourceNode.connect(analyserNode);
        analyserNode.connect(audioContext.destination);
        isVisualizerSetup = true;
      } catch (e) {
        // Fallback for re-attaching
      }
    }

    renderWaveform();
  }

  function renderWaveform() {
    if (!visualizerCanvas || !analyserNode) return;

    const ctx = visualizerCanvas.getContext('2d');
    const width = visualizerCanvas.width = visualizerCanvas.offsetWidth;
    const height = visualizerCanvas.height = visualizerCanvas.offsetHeight;
    const bufferLength = analyserNode.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    function draw() {
      animationFrameId = requestAnimationFrame(draw);
      analyserNode.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, width, height);

      const barWidth = (width / bufferLength) * 2;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * height * 0.8;

        const gradient = ctx.createLinearGradient(0, height, 0, height - barHeight);
        gradient.addColorStop(0, '#6366f1');
        gradient.addColorStop(0.5, '#a855f7');
        gradient.addColorStop(1, '#ec4899');

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.roundRect(x, height - barHeight, barWidth - 4, barHeight, 4);
        ctx.fill();

        x += barWidth;
      }
    }

    if (animationFrameId) cancelAnimationFrame(animationFrameId);
    draw();
  }

  // --- History Management & Searching ---
  async function loadHistory(searchQuery = '') {
    const endpoint = searchQuery ? `/history?search=${encodeURIComponent(searchQuery)}` : '/history';
    const res = await API.get(endpoint);

    if (res.success && historyTableBody) {
      if (res.history.length === 0) {
        historyTableBody.innerHTML = `
          <tr>
            <td colspan="6" style="text-align:center; padding:30px; color:var(--text-muted);">
              No conversion history found.
            </td>
          </tr>
        `;
        return;
      }

      historyTableBody.innerHTML = res.history.map(item => `
        <tr>
          <td><span class="badge">#${item.id}</span></td>
          <td class="history-text-cell" title="${item.text}">${item.text}</td>
          <td><span class="badge">${item.voice}</span></td>
          <td>${item.character_count} chars</td>
          <td>${new Date(item.created_at).toLocaleDateString()}</td>
          <td>
            <div style="display:flex; gap:6px;">
              <button class="btn btn-primary btn-sm play-history-btn" data-url="${item.audio_url}">
                <i class="bi bi-play-fill"></i> Play
              </button>
              <button class="btn btn-danger btn-sm delete-history-btn" data-id="${item.id}">
                <i class="bi bi-trash-fill"></i>
              </button>
            </div>
          </td>
        </tr>
      `).join('');

      // Also update dashboard recent table preview
      const dashboardHistoryBody = document.getElementById('dashboard-recent-body');
      if (dashboardHistoryBody) {
        dashboardHistoryBody.innerHTML = res.history.slice(0, 5).map(item => `
          <tr>
            <td class="history-text-cell">${item.text}</td>
            <td><span class="badge">${item.voice}</span></td>
            <td>${item.character_count}</td>
            <td>
              <button class="btn btn-primary btn-sm play-history-btn" data-url="${item.audio_url}">
                <i class="bi bi-play-fill"></i>
              </button>
            </td>
          </tr>
        `).join('');
      }

      // Add event listeners for table buttons
      document.querySelectorAll('.play-history-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const url = btn.getAttribute('data-url');
          playGeneratedAudio(url);
          showToast('Playing audio snippet...', 'info');
        });
      });

      document.querySelectorAll('.delete-history-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = btn.getAttribute('data-id');
          const delRes = await API.delete(`/history/${id}`);
          if (delRes.success) {
            showToast('History item deleted.', 'success');
            await loadHistory();
            await loadUserData();
          }
        });
      });
    }
  }

  // Setup History Search Listener
  if (historySearchInput) {
    historySearchInput.addEventListener('input', (e) => {
      loadHistory(e.target.value.trim());
    });
  }

  if (clearHistoryBtn) {
    clearHistoryBtn.addEventListener('click', async () => {
      if (confirm('Are you sure you want to clear all conversion history?')) {
        const res = await API.delete('/history');
        if (res.success) {
          showToast('All history cleared.', 'success');
          await loadHistory();
          await loadUserData();
        }
      }
    });
  }

  if (exportCsvBtn) {
    exportCsvBtn.addEventListener('click', () => {
      window.open('/api/history/export/csv', '_blank');
    });
  }

  if (exportPdfBtn) {
    exportPdfBtn.addEventListener('click', () => {
      window.open('/api/history/export/pdf', '_blank');
    });
  }

  // --- Favorites Manager ---
  async function loadFavorites() {
    const res = await API.get('/favorites');
    if (res.success && favoritesContainer) {
      if (res.favorites.length === 0) {
        favoritesContainer.innerHTML = `
          <div style="grid-column: 1/-1; text-align:center; padding: 40px; color: var(--text-muted);">
            No favorite voices added yet. Add voices from the TTS Studio!
          </div>
        `;
        return;
      }

      favoritesContainer.innerHTML = res.favorites.map(fav => `
        <div class="glass-card" style="display:flex; align-items:center; justify-content:space-between; margin-bottom:0;">
          <div style="display:flex; align-items:center; gap:12px;">
            <i class="bi bi-star-fill" style="color:var(--accent-amber); font-size:1.4rem;"></i>
            <div>
              <div style="font-weight:700;">${fav.item_value}</div>
              <div style="font-size:0.8rem; color:var(--text-muted);">${fav.item_type.toUpperCase()}</div>
            </div>
          </div>
          <button class="btn btn-danger btn-sm remove-fav-btn" data-id="${fav.id}">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      `).join('');

      document.querySelectorAll('.remove-fav-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = btn.getAttribute('data-id');
          const delRes = await API.delete(`/favorites/${id}`);
          if (delRes.success) {
            showToast('Favorite removed.', 'info');
            await loadFavorites();
            await loadUserData();
          }
        });
      });
    }
  }

  // --- Profile Settings Handlers ---
  if (profileForm) {
    profileForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const username = document.getElementById('profile-username').value.trim();
      const email = document.getElementById('profile-email').value.trim();

      const res = await API.put('/profile', { username, email });
      if (res.success) {
        showToast('Profile updated successfully!', 'success');
        await loadUserData();
      } else {
        showToast(res.message || 'Profile update failed.', 'error');
      }
    });
  }

  if (passwordForm) {
    passwordForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const current_password = document.getElementById('current-password').value;
      const new_password = document.getElementById('new-password').value;

      const res = await API.put('/profile/password', { current_password, new_password });
      if (res.success) {
        showToast('Password updated successfully!', 'success');
        passwordForm.reset();
      } else {
        showToast(res.message || 'Password update failed.', 'error');
      }
    });
  }

  if (deleteAccountBtn) {
    deleteAccountBtn.addEventListener('click', async () => {
      if (confirm('CAUTION: Are you sure you want to permanently delete your account? This action cannot be undone.')) {
        const res = await API.delete('/profile');
        if (res.success) {
          AuthToken.remove();
          showToast('Account deleted.', 'info');
          setTimeout(() => window.location.href = '/login', 800);
        }
      }
    });
  }

  // --- Keyboard Shortcuts Listener ---
  function setupShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Ctrl + Enter: Convert text to speech
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        handleSpeechConversion();
      }
      // Ctrl + K: Focus editor
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        if (textEditor) textEditor.focus();
      }
      // Space (when not typing in an input/textarea): Toggle play/pause
      if (e.code === 'Space' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
        e.preventDefault();
        if (playPauseBtn) playPauseBtn.click();
      }
      // Esc: Clear editor focus or clear editor text
      if (e.key === 'Escape' && document.activeElement === textEditor) {
        textEditor.blur();
      }
    });
  }
});
