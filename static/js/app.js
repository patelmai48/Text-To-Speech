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
    setupQuickConvert();
    setupDeleteAccountModal();
    setupVerificationHandlers();

    await loadUserData();
    await loadVoices();
    await loadHistory();
    await loadFavorites();
    await loadSummaries();

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
            'summaries': 'Saved Summaries',
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

      // Check verification status
      const verifyBanner = document.getElementById('email-verify-banner');
      if (verifyBanner) {
        verifyBanner.style.display = 'none';
      }

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
        if (!checkVerificationState()) return;
        const text = textEditor.value.trim();
        if (!text) {
          showToast('Please enter text or a topic to summarize.', 'warning');
          return;
        }

        summarizeBtn.disabled = true;
        summarizeBtn.innerHTML = '<div class="spinner" style="width: 14px; height: 14px; border-width: 2px; border-top-color: #fff; margin-right: 4px;"></div> Summarizing...';

        const res = await API.post('/tts/summarize', { text });

        summarizeBtn.disabled = false;
        summarizeBtn.innerHTML = '<i class="bi bi-magic"></i> Summarize';

        if (res.success && res.summary) {
          textEditor.value = res.summary;
          updateCharCount();
          showToast('Summary & ideas generated and saved to Summaries tab!', 'success');
          await loadSummaries();
        } else {
          showToast(res.message || 'Summarization failed.', 'error');
        }
      });
    }

    // Favorite Voice Toggle Button
    if (favVoiceBtn) {
      favVoiceBtn.addEventListener('click', async () => {
        if (!checkVerificationState()) return;
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
    charCounter.textContent = `${len.toLocaleString()} characters`;
    charCounter.className = 'char-counter';
  }

  // --- Speech Conversion API Handler with Progress Bar & Estimated Time ---
  async function handleSpeechConversion(customText = null) {
    if (!checkVerificationState()) return;
    let text = '';
    if (typeof customText === 'string' && customText.trim()) {
      text = customText.trim();
    } else if (textEditor && textEditor.value.trim()) {
      text = textEditor.value.trim();
    }

    if (!text) {
      showToast('Please enter text into the TTS Studio editor to synthesize.', 'warning');
      return;
    }

    const voice = voiceSelect ? voiceSelect.value : 'en-us';
    const speed = speedSlider ? parseFloat(speedSlider.value) : 1.0;
    const pitch = pitchSlider ? parseFloat(pitchSlider.value) : 1.0;
    const volume = volumeSlider ? parseFloat(volumeSlider.value) : 1.0;

    if (convertBtn) {
      convertBtn.disabled = true;
      convertBtn.innerHTML = `<div class="spinner"></div> Synthesizing Audio...`;
    }

    // Show conversion progress modal
    const progressModal = document.getElementById('conversion-progress-modal');
    const progressFill = document.getElementById('conversion-progress-fill');
    const progressPercent = document.getElementById('progress-percent-text');
    const progressTime = document.getElementById('progress-time-text');
    const progressStatus = document.getElementById('progress-status-text');

    let progressInterval = null;
    let currentPercent = 0;
    const estTotalSeconds = Math.max(2, Math.ceil(text.length / 70));

    if (progressModal && progressFill) {
      progressFill.style.width = '0%';
      if (progressPercent) progressPercent.textContent = '0%';
      if (progressTime) progressTime.textContent = `Estimated time: ~${estTotalSeconds}s`;
      if (progressStatus) progressStatus.textContent = 'Processing text with neural AI voice engine...';
      progressModal.style.display = 'flex';

      const updateStepMs = 100;
      const totalSteps = (estTotalSeconds * 1000) / updateStepMs;
      const stepPercent = 90 / totalSteps;

      progressInterval = setInterval(() => {
        if (currentPercent < 90) {
          currentPercent = Math.min(90, currentPercent + stepPercent);
          progressFill.style.width = `${Math.round(currentPercent)}%`;
          if (progressPercent) progressPercent.textContent = `${Math.round(currentPercent)}%`;
          const remainingSecs = Math.max(1, Math.ceil(estTotalSeconds * (1 - currentPercent / 100)));
          if (progressTime) progressTime.textContent = `Estimated remaining: ~${remainingSecs}s`;
        }
      }, updateStepMs);
    }

    const res = await API.post('/tts', { text, voice, speed, pitch, volume });

    if (progressInterval) clearInterval(progressInterval);

    if (progressModal && progressFill) {
      progressFill.style.width = '100%';
      if (progressPercent) progressPercent.textContent = '100%';
      if (progressTime) progressTime.textContent = 'Completed!';
      setTimeout(() => {
        progressModal.style.display = 'none';
      }, 400);
    }

    if (convertBtn) {
      convertBtn.disabled = false;
      convertBtn.innerHTML = `<i class="bi bi-soundwave"></i> Convert to Speech`;
    }

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
      updateHistoryButtonsState();
    });

    currentAudio.addEventListener('play', updateHistoryButtonsState);
    currentAudio.addEventListener('pause', updateHistoryButtonsState);
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

    if (res.success) {
      // 1. Populate Desktop Table
      if (historyTableBody) {
        if (res.history.length === 0) {
          historyTableBody.innerHTML = `
            <tr>
              <td colspan="6" style="padding:0;">
                <div class="empty-state-card">
                  <div class="empty-state-icon">
                    <i class="bi bi-mic"></i>
                  </div>
                  <h3 style="font-size: 1.25rem; margin-bottom: 8px;">No Conversions Yet</h3>
                  <p style="color: var(--text-secondary); max-width: 400px; margin-bottom: 20px; font-size: 0.9rem;">
                    You haven't converted any text to speech yet. Start synthesizing speech now using high-quality AI voices.
                  </p>
                  <button class="btn btn-primary btn-sm" onclick="document.querySelector('.nav-item[data-view=\\'studio\\']').click()">
                    <i class="bi bi-soundwave"></i> Generate your first speech
                  </button>
                </div>
              </td>
            </tr>
          `;
        } else {
          historyTableBody.innerHTML = res.history.map(item => `
            <tr>
              <td><span class="badge">#${item.id}</span></td>
              <td class="history-text-cell" title="${escapeHTML(item.text)}">${escapeHTML(item.text)}</td>
              <td><span class="badge">${item.voice}</span></td>
              <td>${item.character_count} chars</td>
              <td>${new Date(item.created_at).toLocaleDateString()}</td>
              <td>
                <div style="display:flex; gap:6px; flex-wrap: wrap;">
                  <button class="btn btn-primary btn-sm play-history-btn" data-url="${item.audio_url}" title="Play Audio">
                    <i class="bi bi-play-fill"></i> Play
                  </button>
                  <button class="btn btn-secondary btn-sm download-history-btn" data-url="${item.audio_url}" data-filename="speech_${item.id}.mp3" title="Download MP3">
                    <i class="bi bi-download"></i>
                  </button>
                  <button class="btn btn-secondary btn-sm duplicate-history-btn" data-text="${encodeURIComponent(item.text)}" data-voice="${item.voice}" data-speed="${item.speed}" data-pitch="${item.pitch}" data-volume="${item.volume}" title="Duplicate / Copy Settings">
                    <i class="bi bi-copy"></i>
                  </button>
                  <button class="btn btn-secondary btn-sm edit-history-btn" data-text="${encodeURIComponent(item.text)}" data-voice="${item.voice}" data-speed="${item.speed}" data-pitch="${item.pitch}" data-volume="${item.volume}" title="Edit in Studio">
                    <i class="bi bi-pencil-square"></i>
                  </button>
                  <button class="btn btn-danger btn-sm delete-history-btn" data-id="${item.id}" title="Delete Record">
                    <i class="bi bi-trash-fill"></i>
                  </button>
                </div>
              </td>
            </tr>
          `).join('');
        }
      }

      // 2. Populate Mobile Cards
      const historyCardsContainer = document.getElementById('history-cards-container');
      if (historyCardsContainer) {
        if (res.history.length === 0) {
          historyCardsContainer.innerHTML = `
            <div class="empty-state-card glass-card" style="margin-bottom:0;">
              <div class="empty-state-icon">
                <i class="bi bi-mic"></i>
              </div>
              <h3 style="font-size: 1.25rem; margin-bottom: 8px;">No Conversions Yet</h3>
              <p style="color: var(--text-secondary); max-width: 400px; margin-bottom: 20px; font-size: 0.9rem;">
                You haven't converted any text to speech yet. Start synthesizing speech now using high-quality AI voices.
              </p>
              <button class="btn btn-primary btn-sm" onclick="document.querySelector('.nav-item[data-view=\\'studio\\']').click()">
                <i class="bi bi-soundwave"></i> Generate your first speech
              </button>
            </div>
          `;
        } else {
          historyCardsContainer.innerHTML = res.history.map(item => {
            const voiceMeta = availableVoices.find(v => v.voice_id === item.voice) || {
              voice_id: item.voice,
              name: item.voice.toUpperCase(),
              flag: '🌐',
              gender: 'Female',
              code: 'en'
            };
            const estDuration = Math.max(1, Math.ceil(item.character_count / 15));
            const formattedDate = new Date(item.created_at).toLocaleDateString();
            
            return `
              <div class="history-card">
                <div class="history-card-header">
                  <div class="voice-info">
                    <span class="voice-flag">${voiceMeta.flag}</span>
                    <div class="voice-meta-details">
                      <span class="voice-name">${voiceMeta.name}</span>
                      <span class="voice-id-badge">${item.voice}</span>
                    </div>
                  </div>
                  <span class="status-badge success-badge">
                    <i class="bi bi-check-circle-fill"></i> Success
                  </span>
                </div>
                
                <div class="history-card-body">
                  <p class="history-card-text" title="${escapeHTML(item.text)}">${escapeHTML(item.text)}</p>
                  <div class="history-card-metadata">
                    <div class="meta-row">
                      <span class="meta-label">Language</span>
                      <span class="meta-value">${voiceMeta.name.split(' (')[0]}</span>
                    </div>
                    <div class="meta-row">
                      <span class="meta-label">Date</span>
                      <span class="meta-value">${formattedDate}</span>
                    </div>
                    <div class="meta-row">
                      <span class="meta-label">Duration</span>
                      <span class="meta-value">${estDuration}s</span>
                    </div>
                  </div>
                </div>
                
                <div class="history-card-actions" style="display:flex; gap:6px; flex-wrap:wrap;">
                  <button class="btn btn-primary btn-sm play-history-btn" data-url="${item.audio_url}">
                    <i class="bi bi-play-fill"></i> Play
                  </button>
                  <button class="btn btn-secondary btn-sm download-history-btn" data-url="${item.audio_url}" data-filename="speech_${item.id}.mp3">
                    <i class="bi bi-download"></i> Download
                  </button>
                  <button class="btn btn-secondary btn-sm duplicate-history-btn" data-text="${encodeURIComponent(item.text)}" data-voice="${item.voice}" data-speed="${item.speed}" data-pitch="${item.pitch}" data-volume="${item.volume}">
                    <i class="bi bi-copy"></i> Duplicate
                  </button>
                  <button class="btn btn-secondary btn-sm edit-history-btn" data-text="${encodeURIComponent(item.text)}" data-voice="${item.voice}" data-speed="${item.speed}" data-pitch="${item.pitch}" data-volume="${item.volume}">
                    <i class="bi bi-pencil-square"></i> Edit
                  </button>
                  <button class="btn btn-danger btn-sm delete-history-btn" data-id="${item.id}">
                    <i class="bi bi-trash-fill"></i>
                  </button>
                </div>
              </div>
            `;
          }).join('');
        }
      }

      // 3. Update Dashboard Recent Table Preview
      const dashboardHistoryBody = document.getElementById('dashboard-recent-body');
      if (dashboardHistoryBody) {
        if (res.history.length === 0) {
          dashboardHistoryBody.innerHTML = `
            <tr>
              <td colspan="4" style="text-align:center; padding: 20px; color: var(--text-muted);">No recent conversions.</td>
            </tr>
          `;
        } else {
          dashboardHistoryBody.innerHTML = res.history.slice(0, 5).map(item => `
            <tr>
              <td class="history-text-cell" title="${escapeHTML(item.text)}">${escapeHTML(item.text)}</td>
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
      }

      // 4. Attach Event Listeners to rendered elements
      document.querySelectorAll('.play-history-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const url = btn.getAttribute('data-url');
          if (!url) return;

          let btnPath = '';
          try {
            btnPath = new URL(url, window.location.origin).pathname;
          } catch (e) {
            btnPath = url;
          }
          const currentSrc = currentAudio.src ? new URL(currentAudio.src).pathname : '';

          if (btnPath === currentSrc) {
            if (currentAudio.paused || currentAudio.ended) {
              currentAudio.play();
              showToast('Resuming audio snippet...', 'info');
            } else {
              currentAudio.pause();
              showToast('Pausing audio snippet...', 'info');
            }
          } else {
            playGeneratedAudio(url);
            showToast('Playing audio snippet...', 'info');
          }
        });
      });

      document.querySelectorAll('.download-history-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const url = btn.getAttribute('data-url');
          const filename = btn.getAttribute('data-filename') || `speech_${Date.now()}.mp3`;
          const a = document.createElement('a');
          a.href = url;
          a.download = filename;
          a.click();
          showToast('Downloading audio file...', 'success');
        });
      });

      document.querySelectorAll('.duplicate-history-btn, .edit-history-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const text = decodeURIComponent(btn.getAttribute('data-text') || '');
          const voice = btn.getAttribute('data-voice');
          const speed = btn.getAttribute('data-speed');
          const pitch = btn.getAttribute('data-pitch');
          const volume = btn.getAttribute('data-volume');

          if (textEditor) textEditor.value = text;
          if (voiceSelect && voice) voiceSelect.value = voice;
          if (speedSlider && speed) {
            speedSlider.value = speed;
            if (speedVal) speedVal.textContent = `${parseFloat(speed).toFixed(1)}x`;
          }
          if (pitchSlider && pitch) {
            pitchSlider.value = pitch;
            if (pitchVal) pitchVal.textContent = `${parseFloat(pitch).toFixed(1)}x`;
          }
          if (volumeSlider && volume) {
            volumeSlider.value = volume;
            if (volumeVal) volumeVal.textContent = `${Math.round(parseFloat(volume) * 100)}%`;
          }
          updateCharCount();

          const isEdit = btn.classList.contains('edit-history-btn');
          showToast(isEdit ? 'Loaded conversion into Studio for editing.' : 'Duplicated conversion settings into Studio.', 'success');

          const studioNavItem = document.querySelector('.nav-item[data-view="studio"]');
          if (studioNavItem) studioNavItem.click();
        });
      });

      document.querySelectorAll('.delete-history-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = btn.getAttribute('data-id');
          if (confirm('Are you sure you want to delete this conversion record?')) {
            const delRes = await API.delete(`/history/${id}`);
            if (delRes.success) {
              showToast('History item deleted.', 'success');
              await loadHistory();
              await loadUserData();
            }
          }
        });
      });

      updateHistoryButtonsState();
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

  const downloadHistoryFile = async (endpoint, extension) => {
    try {
      const username = currentUser ? currentUser.username : 'user';
      const filename = `tts_history_${username}.${extension}`;
      
      const token = AuthToken.get();
      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to export history file.');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      showToast('Failed to export history. Please try again.', 'error');
      console.error(err);
    }
  };

  if (exportCsvBtn) {
    exportCsvBtn.addEventListener('click', () => {
      downloadHistoryFile('/api/history/export/csv', 'csv');
    });
  }

  if (exportPdfBtn) {
    exportPdfBtn.addEventListener('click', () => {
      downloadHistoryFile('/api/history/export/pdf', 'pdf');
    });
  }

  // --- Favorites Manager ---
  async function loadFavorites() {
    const res = await API.get('/favorites');
    if (res.success && favoritesContainer) {
      if (res.favorites.length === 0) {
        favoritesContainer.innerHTML = `
          <div class="empty-state-card glass-card" style="grid-column: 1/-1; margin-bottom: 0;">
            <div class="empty-state-icon" style="background: rgba(245, 158, 11, 0.12); color: var(--accent-amber);">
              <i class="bi bi-star"></i>
            </div>
            <h3 style="font-size: 1.25rem; margin-bottom: 8px;">No Favorite Voices Saved</h3>
            <p style="color: var(--text-secondary); max-width: 400px; margin-bottom: 20px; font-size: 0.9rem;">
              Save your favorite neural voice presets for instant access and one-click speech synthesis.
            </p>
            <button class="btn btn-primary btn-sm" onclick="document.querySelector('.nav-item[data-view=\\'studio\\']').click()">
              <i class="bi bi-sliders"></i> Explore & Favorite Voices
            </button>
          </div>
        `;
        return;
      }

      // Fetch history for statistics computation
      const historyRes = await API.get('/history');
      const history = historyRes.success ? historyRes.history : [];

      favoritesContainer.innerHTML = res.favorites.map(fav => {
        // Find matching voice metadata from availableVoices
        const voiceMeta = availableVoices.find(v => v.voice_id === fav.item_value) || {
          voice_id: fav.item_value,
          name: fav.item_value.toUpperCase(),
          flag: '🌐',
          gender: 'Unknown',
          code: 'en'
        };

        // Calculate statistics
        const voiceHistory = history.filter(h => h.voice === fav.item_value);
        const timesUsed = voiceHistory.length;
        let lastUsedStr = 'Never';
        if (timesUsed > 0) {
          const lastDate = new Date(voiceHistory[0].created_at);
          lastUsedStr = lastDate.toLocaleDateString() + ' ' + lastDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }

        return `
          <div class="voice-card glass-card" style="margin-bottom:0;">
            <div class="voice-card-header">
              <div class="voice-card-title">
                <span class="voice-flag">${voiceMeta.flag}</span>
                <div class="voice-lang-info">
                  <span class="voice-lang-name">${voiceMeta.name}</span>
                  <span class="voice-provider-badge"><i class="bi bi-cloud-check-fill"></i> Google TTS</span>
                </div>
              </div>
            </div>

            <div class="voice-card-details">
              <div class="detail-row">
                <span class="detail-label"><i class="bi bi-translate"></i> Language</span>
                <span class="detail-value">${voiceMeta.name.split(' (')[0]}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label"><i class="bi bi-gender-ambiguous"></i> Gender</span>
                <span class="detail-value voice-gender-text gender-${voiceMeta.gender.toLowerCase()}">${voiceMeta.gender}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label"><i class="bi bi-cpu"></i> Voice Type</span>
                <span class="detail-value voice-type-badge">Standard</span>
              </div>
              <div class="detail-row">
                <span class="detail-label"><i class="bi bi-clock"></i> Last Used</span>
                <span class="detail-value">${lastUsedStr}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label"><i class="bi bi-graph-up-arrow"></i> Times Used</span>
                <span class="detail-value usage-badge">${timesUsed}</span>
              </div>
            </div>

            <div class="voice-card-actions">
              <button class="btn btn-secondary btn-sm preview-voice-btn" data-voice="${voiceMeta.voice_id}" data-lang="${voiceMeta.code}" data-name="${voiceMeta.name}">
                <i class="bi bi-play-circle-fill"></i> Preview
              </button>
              <button class="btn btn-primary btn-sm use-voice-btn" data-voice="${voiceMeta.voice_id}">
                <i class="bi bi-mic-fill"></i> Use Voice
              </button>
              <button class="btn btn-danger btn-sm remove-fav-btn" data-id="${fav.id}">
                <i class="bi bi-trash-fill"></i> Remove
              </button>
            </div>
          </div>
        `;
      }).join('');

      // Add event listeners for buttons
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

      document.querySelectorAll('.use-voice-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const voiceId = btn.getAttribute('data-voice');
          if (voiceSelect) {
            voiceSelect.value = voiceId;
            voiceSelect.dispatchEvent(new Event('change'));
          }
          const studioNavItem = document.querySelector('.nav-item[data-view="studio"]');
          if (studioNavItem) {
            studioNavItem.click();
            showToast(`Selected voice: ${voiceId}`, 'success');
          }
        });
      });

      document.querySelectorAll('.preview-voice-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          const voiceId = btn.getAttribute('data-voice');
          const langCode = btn.getAttribute('data-lang');
          const voiceName = btn.getAttribute('data-name');

          // Localized preview text
          const previews = {
            'en': `Hello! This is a preview of the ${voiceName} voice.`,
            'es': `¡Hola! Esta es una vista previa de la voz en español.`,
            'fr': `Bonjour! Ceci est un aperçu de la voix française.`,
            'de': `Hallo! Dies ist eine Vorschau der deutschen Stimme.`,
            'hi': `नमस्ते! यह हिंदी आवाज़ का पूर्वावलोकन है।`,
            'ja': `こんにちは！これは日本語の音声プレビューです。`,
            'zh': `你好！这是中文普通话声音的预览。`,
            'it': `Ciao! Questa è un'anteprima della voce italiana.`,
            'pt': `Olá! Esta é uma prévia da voz em português.`,
            'ru': `Привет! Это пример звучания русского голоса.`,
            'ar': `مرحباً! هذا معاينة للصوت العربي.`,
            'ko': `안녕하세요! 한국어 목소리 미리듣기입니다.`
          };

          const text = previews[langCode] || previews[langCode.split('-')[0]] || 'Hello! This is a voice preview.';

          btn.disabled = true;
          const originalHTML = btn.innerHTML;
          btn.innerHTML = '<div class="spinner" style="width: 14px; height: 14px; border-width: 2px; border-top-color: #fff; margin-right: 4px;"></div> Playing...';

          try {
            const res = await API.post('/tts', { text, voice: voiceId, speed: 1.0, pitch: 1.0, volume: 1.0 });
            if (res.success && res.history) {
              playGeneratedAudio(res.history.audio_url);
              showToast(`Playing preview for ${voiceName}...`, 'info');
              await loadHistory();
            } else {
              showToast(res.message || 'Failed to synthesize preview.', 'error');
            }
          } catch (e) {
            showToast('Preview error occurred.', 'error');
          } finally {
            btn.disabled = false;
            btn.innerHTML = originalHTML;
          }
        });
      });
    }
  }

  // --- Summaries Manager ---
  async function loadSummaries(searchQuery = '') {
    const summariesContainer = document.getElementById('summaries-container');
    const summariesSearchInput = document.getElementById('summaries-search');

    if (!summariesContainer) return;

    const res = await API.get('/summaries');
    if (!res.success) return;

    let items = res.summaries || [];
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      items = items.filter(s => s.original_topic.toLowerCase().includes(q) || s.summary_content.toLowerCase().includes(q));
    }

    if (items.length === 0) {
      summariesContainer.innerHTML = `
        <div class="empty-state-card glass-card" style="grid-column: 1/-1; margin-bottom: 0;">
          <div class="empty-state-icon" style="background: rgba(99, 102, 241, 0.12); color: var(--accent-primary);">
            <i class="bi bi-magic"></i>
          </div>
          <h3 style="font-size: 1.25rem; margin-bottom: 8px;">No Saved Summaries Yet</h3>
          <p style="color: var(--text-secondary); max-width: 420px; margin-bottom: 20px; font-size: 0.9rem;">
            Click <strong>Summarize</strong> in the TTS Studio to generate structured summaries, ideas, and guides. They will automatically save here.
          </p>
          <button class="btn btn-primary btn-sm" onclick="document.querySelector('.nav-item[data-view=\\'studio\\']').click()">
            <i class="bi bi-pencil-square"></i> Go to TTS Studio
          </button>
        </div>
      `;
      return;
    }

    summariesContainer.innerHTML = items.map(item => {
      const dateStr = new Date(item.created_at).toLocaleDateString();
      const timeStr = new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      return `
        <div class="summary-card glass-card" style="margin-bottom:0;">
          <div class="summary-card-header">
            <div>
              <div class="summary-topic-title">${escapeHTML(item.original_topic)}</div>
              <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 4px;">
                <i class="bi bi-clock"></i> ${dateStr} ${timeStr}
              </div>
            </div>
            <span class="badge" style="background: rgba(99, 102, 241, 0.15); color: var(--accent-primary);"><i class="bi bi-magic"></i> AI Summary</span>
          </div>

          <div class="summary-card-body">${escapeHTML(item.summary_content)}</div>

          <div style="display:flex; gap:8px; flex-wrap:wrap; margin-top: 10px;">
            <button class="btn btn-primary btn-sm use-summary-btn" data-text="${encodeURIComponent(item.summary_content)}">
              <i class="bi bi-soundwave"></i> Convert in Studio
            </button>
            <button class="btn btn-secondary btn-sm copy-summary-btn" data-text="${encodeURIComponent(item.summary_content)}">
              <i class="bi bi-copy"></i> Copy
            </button>
            <button class="btn btn-danger btn-sm delete-summary-btn" data-id="${item.id}">
              <i class="bi bi-trash-fill"></i>
            </button>
          </div>
        </div>
      `;
    }).join('');

    // Attach event listeners for summary card buttons
    document.querySelectorAll('.use-summary-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const text = decodeURIComponent(btn.getAttribute('data-text') || '');
        if (textEditor) {
          textEditor.value = text;
          updateCharCount();
        }
        const studioNavItem = document.querySelector('.nav-item[data-view="studio"]');
        if (studioNavItem) studioNavItem.click();
        showToast('Synthesizing speech from summary...', 'info');
        await handleSpeechConversion(text);
      });
    });

    document.querySelectorAll('.copy-summary-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const text = decodeURIComponent(btn.getAttribute('data-text') || '');
        navigator.clipboard.writeText(text);
        showToast('Summary copied to clipboard!', 'success');
      });
    });

    document.querySelectorAll('.delete-summary-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.getAttribute('data-id');
        if (confirm('Are you sure you want to delete this saved summary?')) {
          const res = await API.delete(`/summaries/${id}`);
          if (res.success) {
            showToast('Summary deleted.', 'info');
            await loadSummaries();
          }
        }
      });
    });

    if (summariesSearchInput && !summariesSearchInput.hasAttribute('data-bound')) {
      summariesSearchInput.setAttribute('data-bound', 'true');
      summariesSearchInput.addEventListener('input', (e) => {
        loadSummaries(e.target.value.trim());
      });
    }
  }

  function escapeHTML(str) {
    if (!str) return '';
    return str.replace(/[&<>'"]/g, 
      tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
    );
  }

  // --- Profile Settings Handlers ---
  if (profileForm) {
    profileForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!checkVerificationState()) return;
      const username = document.getElementById('profile-username').value.trim();
      const email = document.getElementById('profile-email').value.trim();

      const submitBtn = profileForm.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<div class="spinner" style="width: 14px; height: 14px; border-width: 2px; border-top-color: #fff; margin-right: 4px;"></div> Updating...`;

      const res = await API.put('/profile', { username, email });
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;

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
      if (!checkVerificationState()) return;
      const current_password = document.getElementById('current-password').value;
      const new_password = document.getElementById('new-password').value;

      const submitBtn = passwordForm.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<div class="spinner" style="width: 14px; height: 14px; border-width: 2px; border-top-color: #fff; margin-right: 4px;"></div> Updating...`;

      const res = await API.put('/profile/password', { current_password, new_password });
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;

      if (res.success) {
        showToast('Password updated successfully!', 'success');
        passwordForm.reset();
      } else {
        showToast(res.message || 'Password update failed.', 'error');
      }
    });
  }

  // --- Dashboard Quick Convert Handler ---
  function setupQuickConvert() {
    const quickTextarea = document.getElementById('dashboard-quick-text');
    const fileInput = document.getElementById('dashboard-file-upload');
    const fileNameSpan = document.getElementById('dashboard-file-name');
    const quickConvertBtn = document.getElementById('dashboard-quick-convert-btn');
    const openStudioBtn = document.getElementById('dashboard-open-studio-btn');

    if (fileInput) {
      fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
        if (!file.name.endsWith('.txt')) {
          showToast('Please select a valid .txt file.', 'warning');
          return;
        }
        if (fileNameSpan) fileNameSpan.textContent = file.name;
        const reader = new FileReader();
        reader.onload = (evt) => {
          if (quickTextarea) quickTextarea.value = evt.target.result;
          showToast('Loaded text file into Quick Convert', 'info');
        };
        reader.readAsText(file);
      });
    }

    if (quickConvertBtn) {
      quickConvertBtn.addEventListener('click', async () => {
        const text = quickTextarea ? quickTextarea.value.trim() : '';
        if (!text) {
          showToast('Please enter or upload text to convert.', 'warning');
          return;
        }
        if (textEditor) {
          textEditor.value = text;
          updateCharCount();
        }
        await handleSpeechConversion(text);
      });
    }

    if (openStudioBtn) {
      openStudioBtn.addEventListener('click', () => {
        const text = quickTextarea ? quickTextarea.value.trim() : '';
        if (text && textEditor) {
          textEditor.value = text;
          updateCharCount();
        }
        const studioItem = document.querySelector('.nav-item[data-view="studio"]');
        if (studioItem) studioItem.click();
      });
    }
  }

  // --- Delete Account Safety Confirmation Handler ---
  function setupDeleteAccountModal() {
    const deleteModal = document.getElementById('delete-confirm-modal');
    const closeDeleteModalBtn = document.getElementById('close-delete-modal-btn');
    const deleteInput = document.getElementById('delete-confirm-username');
    const deleteSubmitBtn = document.getElementById('delete-confirm-submit-btn');
    const deleteForm = document.getElementById('delete-account-confirm-form');

    if (deleteAccountBtn && deleteModal) {
      deleteAccountBtn.addEventListener('click', () => {
        if (!checkVerificationState()) return;
        if (deleteInput) deleteInput.value = '';
        if (deleteSubmitBtn) deleteSubmitBtn.disabled = true;
        deleteModal.style.display = 'flex';
        deleteModal.classList.add('open');
      });
    }

    if (closeDeleteModalBtn && deleteModal) {
      closeDeleteModalBtn.addEventListener('click', () => {
        deleteModal.classList.remove('open');
        setTimeout(() => deleteModal.style.display = 'none', 300);
      });
    }

    if (deleteInput && deleteSubmitBtn) {
      deleteInput.addEventListener('input', () => {
        const val = deleteInput.value.trim();
        deleteSubmitBtn.disabled = (val.toUpperCase() !== 'DELETE');
      });
    }

    if (deleteForm) {
      deleteForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const val = deleteInput ? deleteInput.value.trim() : '';
        if (val.toUpperCase() !== 'DELETE') {
          showToast('Please type DELETE to confirm account deletion.', 'warning');
          return;
        }

        const submitBtn = deleteForm.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<div class="spinner"></div> Deleting Account...`;

        const res = await API.delete('/profile');
        if (res.success) {
          AuthToken.remove();
          showToast('Account permanently deleted.', 'info');
          setTimeout(() => window.location.href = '/login', 800);
        } else {
          submitBtn.disabled = false;
          submitBtn.innerHTML = 'Permanently Delete';
          showToast(res.message || 'Account deletion failed.', 'error');
        }
      });
    }
  }

  // --- Verification Checks & Playback Sync Helpers ---
  function checkVerificationState() {
    return true;
  }

  function updateHistoryButtonsState() {
    if (!currentAudio) return;
    const currentSrc = currentAudio.src ? new URL(currentAudio.src).pathname : '';
    const isPlaying = !currentAudio.paused && !currentAudio.ended;

    document.querySelectorAll('.play-history-btn').forEach(btn => {
      const btnUrl = btn.getAttribute('data-url');
      if (!btnUrl) return;

      let btnPath = '';
      try {
        btnPath = new URL(btnUrl, window.location.origin).pathname;
      } catch (e) {
        btnPath = btnUrl;
      }

      const hasText = btn.textContent.includes('Play') || btn.textContent.includes('Pause');

      if (btnPath === currentSrc && isPlaying) {
        if (hasText) {
          btn.innerHTML = '<i class="bi bi-pause-fill"></i> Pause';
        } else {
          btn.innerHTML = '<i class="bi bi-pause-fill"></i>';
        }
        btn.classList.add('playing');
      } else {
        if (hasText) {
          btn.innerHTML = '<i class="bi bi-play-fill"></i> Play';
        } else {
          btn.innerHTML = '<i class="bi bi-play-fill"></i>';
        }
        btn.classList.remove('playing');
      }
    });
  }

  // --- Verification Banner & Modal Handlers ---
  function setupVerificationHandlers() {
    const verifyBanner = document.getElementById('email-verify-banner');
    const triggerBtn = document.getElementById('trigger-verify-modal-btn');
    const resendBtn = document.getElementById('resend-verify-email-btn');
    const modalResendBtn = document.getElementById('modal-resend-verify-email-btn');
    const modal = document.getElementById('verify-modal');
    const closeBtn = document.getElementById('close-verify-modal-btn');
    const form = document.getElementById('verify-email-form');

    if (triggerBtn && modal) {
      triggerBtn.addEventListener('click', () => modal.classList.add('open'));
    }

    if (closeBtn && modal) {
      closeBtn.addEventListener('click', () => modal.classList.remove('open'));
    }

    const handleResend = async (btn) => {
      btn.disabled = true;
      const originalText = btn.innerHTML;
      btn.innerHTML = 'Resending...';

      const res = await API.post('/auth/resend-verification');
      btn.disabled = false;
      btn.innerHTML = originalText;

      if (res.success) {
        showToast('Verification code resent successfully.', 'success');
      } else {
        showToast(res.message || 'Failed to resend code.', 'error');
      }
    };

    if (resendBtn) {
      resendBtn.addEventListener('click', () => handleResend(resendBtn));
    }

    if (modalResendBtn) {
      modalResendBtn.addEventListener('click', (e) => {
        e.preventDefault();
        handleResend(modalResendBtn);
      });
    }

    if (form && modal) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const codeInput = document.getElementById('verification-input-code');
        const code = codeInput.value.trim();

        if (!code) {
          showToast('Please enter the verification code.', 'warning');
          return;
        }

        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = 'Verifying...';

        const res = await API.post('/auth/verify-email', { code });
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;

        if (res.success) {
          showToast('Email verified successfully!', 'success');
          modal.classList.remove('open');
          form.reset();
          if (currentUser) currentUser.email_verified = true;
          if (verifyBanner) verifyBanner.style.display = 'none';
        } else {
          showToast(res.message || 'Invalid code. Verification failed.', 'error');
        }
      });
    }
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
