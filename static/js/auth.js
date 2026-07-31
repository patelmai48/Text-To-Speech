/**
 * Authentication Page Logic (Login, Registration, Google Auth, Forgot/Reset Password)
 */

document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');
  const showForgotBtn = document.getElementById('show-forgot-btn');
  const loginView = document.getElementById('login-view');
  const forgotForm = document.getElementById('forgot-form');
  const resetForm = document.getElementById('reset-form');
  const backToLoginBtn = document.getElementById('back-to-login-btn');
  const backToLoginBtn2 = document.getElementById('back-to-login-btn-2');

  const recoveryNotice = document.getElementById('auth-recovery-notice');
  const recoveryMsg = document.getElementById('auth-recovery-msg');
  const recoveryPasswordBtn = document.getElementById('recovery-password-btn');
  const recoveryForgotBtn = document.getElementById('recovery-forgot-btn');

  // --- Password Visibility Toggle Handler ---
  document.querySelectorAll('.password-toggle-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const wrapper = btn.closest('.password-input-wrapper');
      if (!wrapper) return;
      const input = wrapper.querySelector('input');
      const icon = btn.querySelector('i');

      if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'bi bi-eye-slash';
      } else {
        input.type = 'password';
        icon.className = 'bi bi-eye';
      }
    });
  });

  // --- View Toggle Helpers ---
  if (showForgotBtn) {
    showForgotBtn.addEventListener('click', (e) => {
      e.preventDefault();
      if (loginView) loginView.style.display = 'none';
      if (forgotForm) forgotForm.style.display = 'block';
      if (resetForm) resetForm.style.display = 'none';
    });
  }

  [backToLoginBtn, backToLoginBtn2].forEach(btn => {
    if (btn) {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        if (loginView) loginView.style.display = 'block';
        if (forgotForm) forgotForm.style.display = 'none';
        if (resetForm) resetForm.style.display = 'none';
      });
    }
  });

  // --- Recovery Action Buttons ---
  if (recoveryPasswordBtn) {
    recoveryPasswordBtn.addEventListener('click', () => {
      const emailInput = document.getElementById('email_or_username');
      const passInput = document.getElementById('password');
      if (emailInput && recoveryNotice && recoveryNotice.getAttribute('data-email')) {
        emailInput.value = recoveryNotice.getAttribute('data-email');
      }
      if (passInput) passInput.focus();
      if (recoveryNotice) recoveryNotice.style.display = 'none';
    });
  }

  if (recoveryForgotBtn) {
    recoveryForgotBtn.addEventListener('click', () => {
      const forgotEmail = document.getElementById('forgot-email');
      if (forgotEmail && recoveryNotice && recoveryNotice.getAttribute('data-email')) {
        forgotEmail.value = recoveryNotice.getAttribute('data-email');
      }
      if (showForgotBtn) showForgotBtn.click();
      if (recoveryNotice) recoveryNotice.style.display = 'none';
    });
  }

  // --- Forgot & Reset Password Handlers ---
  if (forgotForm) {
    forgotForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('forgot-email').value.trim();
      if (!email) return;
      const submitBtn = forgotForm.querySelector('button[type="submit"]');
      const origText = submitBtn.innerHTML;

      submitBtn.disabled = true;
      submitBtn.innerHTML = `<div class="spinner"></div> Sending code...`;

      const res = await API.post('/auth/forgot-password', { email });

      submitBtn.disabled = false;
      submitBtn.innerHTML = origText;

      if (res.success) {
        showToast(res.message || 'Reset code sent!', 'success');
        document.getElementById('reset-email').value = email;
        forgotForm.style.display = 'none';
        if (resetForm) resetForm.style.display = 'block';
        if (res.dev_code) {
          showToast(`Development reset code: ${res.dev_code}`, 'info', 8000);
          document.getElementById('reset-code').value = res.dev_code;
        }
      } else {
        showToast(res.message || 'Failed to request reset code.', 'error');
      }
    });
  }

  if (resetForm) {
    resetForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('reset-email').value.trim();
      const code = document.getElementById('reset-code').value.trim();
      const new_password = document.getElementById('reset-new-password').value;
      const confirm_password = document.getElementById('reset-confirm-password').value;

      if (new_password !== confirm_password) {
        showToast('Passwords do not match.', 'error');
        return;
      }

      const submitBtn = resetForm.querySelector('button[type="submit"]');
      const origText = submitBtn.innerHTML;

      submitBtn.disabled = true;
      submitBtn.innerHTML = `<div class="spinner"></div> Updating password...`;

      const res = await API.post('/auth/reset-password', { email, code, new_password });

      submitBtn.disabled = false;
      submitBtn.innerHTML = origText;

      if (res.success) {
        showToast('Password updated! Please log in.', 'success');
        resetForm.style.display = 'none';
        if (loginView) loginView.style.display = 'block';
      } else {
        showToast(res.message || 'Password reset failed.', 'error');
      }
    });
  }

  // --- Login Form Submission ---
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = loginForm.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;

      const email_or_username = document.getElementById('email_or_username').value.trim();
      const password = document.getElementById('password').value;

      if (!email_or_username || !password) {
        showToast('Please enter your email/username and password.', 'warning');
        return;
      }

      submitBtn.disabled = true;
      submitBtn.innerHTML = `<div class="spinner"></div> Authenticating...`;

      const result = await API.post('/login', { email_or_username, password });

      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;

      if (result.success && result.token) {
        AuthToken.set(result.token);
        showToast(result.message || 'Login successful!', 'success');
        setTimeout(() => {
          window.location.href = '/';
        }, 800);
      } else {
        showToast(result.message || 'Login failed. Please check your credentials.', 'error');
      }
    });
  }

  // --- Registration Form Submission ---
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = registerForm.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;

      const username = document.getElementById('username').value.trim();
      const email = document.getElementById('email').value.trim();
      const password = document.getElementById('password').value;
      const confirmPassword = document.getElementById('confirm_password').value;

      if (!username || !email || !password) {
        showToast('Please fill out all required fields.', 'warning');
        return;
      }

      if (password !== confirmPassword) {
        showToast('Passwords do not match.', 'error');
        return;
      }

      if (password.length < 6) {
        showToast('Password must be at least 6 characters long.', 'warning');
        return;
      }

      submitBtn.disabled = true;
      submitBtn.innerHTML = `<div class="spinner"></div> Creating Account...`;

      const result = await API.post('/register', { username, email, password });

      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;

      if (result.success && result.token) {
        AuthToken.set(result.token);
        showToast('Account created successfully! Welcome to VoxAI Studio.', 'success');
        setTimeout(() => {
          window.location.href = '/';
        }, 1200);
      } else {
        showToast(result.message || 'Registration failed.', 'error');
      }
    });
  }

  // --- Google Sign-In Callbacks & Fallback handlers ---
  window.handleGoogleSignIn = async (response) => {
    if (!response || !response.credential) return;

    showToast('Verifying Google Identity...', 'info');
    const result = await API.post('/auth/google', { credential: response.credential });
    if (result.success && result.token) {
      AuthToken.set(result.token);
      showToast(result.message || 'Google Login successful!', 'success');
      setTimeout(() => {
        window.location.href = '/';
      }, 800);
    } else {
      showToast(result.message || 'Google Sign-In failed.', 'error');
    }
  };

  // --- Dynamic Google Sign-In Account Storage & View Controller ---
  function getSavedGoogleAccounts() {
    try {
      return JSON.parse(localStorage.getItem('voxai_google_accounts') || '[]');
    } catch (e) {
      return [];
    }
  }

  function saveGoogleAccount(email, username) {
    let accounts = getSavedGoogleAccounts();
    const cleanEmail = email.toLowerCase().trim();
    const idx = accounts.findIndex(a => a.email.toLowerCase() === cleanEmail);
    if (idx >= 0) {
      accounts[idx].username = username || accounts[idx].username;
      accounts[idx].lastUsed = Date.now();
    } else {
      accounts.push({ email: cleanEmail, username: username || cleanEmail.split('@')[0], lastUsed: Date.now() });
    }
    accounts.sort((a, b) => b.lastUsed - a.lastUsed);
    accounts = accounts.slice(0, 4);
    localStorage.setItem('voxai_google_accounts', JSON.stringify(accounts));
  }

  function renderGoogleModalView() {
    const savedContainer = document.getElementById('google-saved-accounts-container');
    const inputPanel = document.getElementById('sim-custom-input-panel');
    const backLink = document.getElementById('sim-back-to-accounts-link');
    const customEmail = document.getElementById('sim-custom-email');
    const modalTitle = document.getElementById('google-oauth-title-text');

    const accounts = getSavedGoogleAccounts();

    if (accounts.length > 0 && savedContainer && inputPanel) {
      if (modalTitle) modalTitle.textContent = 'Choose an account';
      inputPanel.style.display = 'none';
      if (backLink) backLink.style.display = 'none';
      savedContainer.style.display = 'flex';

      const avatarColors = ['#22c55e', '#ec4899', '#3b82f6', '#8b5cf6', '#f59e0b'];

      savedContainer.innerHTML = accounts.map((acc, i) => {
        const color = avatarColors[i % avatarColors.length];
        const displayName = acc.username || acc.email.split('@')[0];
        const initial = displayName.charAt(0).toUpperCase();
        return `
          <button type="button" class="sim-account-btn dynamic-acc-btn" data-email="${acc.email}" data-username="${displayName}">
            <div class="sim-avatar" style="background: ${color};">${initial}</div>
            <div class="sim-account-details">
              <span class="sim-name">${escapeHTML(displayName)}</span>
              <span class="sim-email">${escapeHTML(acc.email)}</span>
            </div>
          </button>
        `;
      }).join('') + `
        <button type="button" class="sim-account-btn" id="sim-use-different-btn">
          <div class="sim-avatar sim-another-avatar"><i class="bi bi-person-circle"></i></div>
          <div class="sim-account-details">
            <span class="sim-name" style="font-weight: 500;">Use another account</span>
          </div>
        </button>
      `;

      // Event listener for clicking a saved account card
      savedContainer.querySelectorAll('.dynamic-acc-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          const email = btn.getAttribute('data-email');
          const username = btn.getAttribute('data-username') || email.split('@')[0];
          closeGoogleSimModal();
          await executeSimulatedGoogleLogin(email, username);
        });
      });

      // Event listener for "Use another account"
      const useDiffBtn = document.getElementById('sim-use-different-btn');
      if (useDiffBtn) {
        useDiffBtn.addEventListener('click', () => {
          if (modalTitle) modalTitle.textContent = 'Sign in';
          savedContainer.style.display = 'none';
          inputPanel.style.display = 'block';
          if (backLink) backLink.style.display = 'inline-block';
          if (customEmail) {
            customEmail.value = '';
            customEmail.focus();
          }
        });
      }
    } else if (inputPanel && savedContainer) {
      if (modalTitle) modalTitle.textContent = 'Sign in';
      savedContainer.style.display = 'none';
      inputPanel.style.display = 'block';
      if (backLink) backLink.style.display = 'none';
      if (customEmail) setTimeout(() => customEmail.focus(), 150);
    }

    if (backLink) {
      backLink.onclick = (e) => {
        e.preventDefault();
        renderGoogleModalView();
      };
    }
  }

  function closeGoogleSimModal() {
    if (googleSimModal) {
      googleSimModal.classList.remove('open');
      setTimeout(() => {
        googleSimModal.style.display = 'none';
      }, 250);
    }
  }

  function escapeHTML(str) {
    if (!str) return '';
    return str.replace(/[&<>'"]/g, 
      tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
    );
  }

  // Wire up Google Button click to trigger simulation modal
  const googleBtn = document.getElementById('google-signin-btn');
  const googleSimModal = document.getElementById('google-sim-modal');
  const closeGoogleSimBtn = document.getElementById('close-google-sim-btn');
  const simCustomEmail = document.getElementById('sim-custom-email');
  const simCustomSubmitBtn = document.getElementById('sim-custom-submit-btn');

  if (googleBtn && googleSimModal) {
    googleBtn.addEventListener('click', async () => {
      // Test if server supports simulated mode or Google Auth
      const testRes = await API.post('/auth/google', { credential: 'simulated_google_token' });
      if (testRes.status === 501 || (testRes.message && testRes.message.includes('not configured'))) {
        showToast('Google Sign-In not configured', 'error');
        return;
      }
      renderGoogleModalView();
      googleSimModal.style.display = 'flex';
      googleSimModal.classList.add('open');
    });
  }

  if (closeGoogleSimBtn) {
    closeGoogleSimBtn.addEventListener('click', closeGoogleSimModal);
  }

  // Submit Custom Account Email
  if (simCustomSubmitBtn && simCustomEmail) {
    simCustomSubmitBtn.addEventListener('click', async () => {
      const email = simCustomEmail.value.trim();
      if (!email || !email.includes('@')) {
        showToast('Please enter a valid email address.', 'warning');
        return;
      }
      const username = email.split('@')[0];
      closeGoogleSimModal();
      await executeSimulatedGoogleLogin(email, username);
    });

    simCustomEmail.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        simCustomSubmitBtn.click();
      }
    });
  }

  async function executeSimulatedGoogleLogin(email, username) {
    showToast('Verifying Google Identity...', 'info');
    const result = await API.post('/auth/google', {
      credential: 'simulated_google_token',
      email: email,
      username: username
    });

    if (result.success && result.token) {
      saveGoogleAccount(email, username);
      AuthToken.set(result.token);
      showToast(result.message || 'Logged in with Google!', 'success');
      setTimeout(() => {
        window.location.href = '/';
      }, 800);
    } else {
      showToast(result.message || 'Google Sign-In not configured', 'error');
    }
  }
});

