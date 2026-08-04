/**
 * Authentication Page Logic (Login, Registration, Google Auth, Forgot/Reset Password)
 */

// Global Google Sign-In Callback Handler
// Must be defined at global scope before Google Identity Services (GSI) parses data-callback
window.handleGoogleSignIn = async function(response) {
  if (!response || !response.credential) {
    showToast('No Google credential received. Please try again.', 'error');
    return;
  }

  try {
    showToast('Verifying Google Identity...', 'info', 4000);
    const result = await API.post('/auth/google', { credential: response.credential });

    if (result && result.success && result.token) {
      AuthToken.set(result.token);
      showToast(result.message || 'Google Login successful!', 'success', 3000);
      setTimeout(() => {
        window.location.replace('/');
      }, 500);
    } else {
      const errMsg = (result && result.message) ? result.message : 'Google Sign-In failed. Please try again.';
      showToast(errMsg, 'error', 6000);

      const notice = document.getElementById('auth-recovery-notice');
      const msgElem = document.getElementById('auth-recovery-msg');
      if (notice && errMsg.toLowerCase().includes('password')) {
        if (msgElem) msgElem.textContent = errMsg;
        notice.style.display = 'block';
      }
    }
  } catch (err) {
    console.error('Google Sign-In Exception:', err);
    showToast('Google Sign-In error: ' + (err.message || 'Server communication failed'), 'error', 6000);
  }
};

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
  const recoveryPasswordBtn = document.getElementById('recovery-password-btn');
  const recoveryForgotBtn = document.getElementById('recovery-forgot-btn');

  // --- Initialize Google Accounts SDK programmatically for mobile & desktop ---
  function initGoogleAuth() {
    const gIdOnload = document.getElementById('g_id_onload');
    if (!gIdOnload) return;
    const clientId = gIdOnload.getAttribute('data-client_id');
    if (clientId && window.google && window.google.accounts && window.google.accounts.id) {
      try {
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: window.handleGoogleSignIn,
          auto_select: false,
          itp_support: true
        });

        const gsiElement = document.querySelector('.g_id_signin');
        const customGoogleBtn = document.getElementById('google-signin-btn');
        if (gsiElement && customGoogleBtn) {
          try {
            window.google.accounts.id.renderButton(gsiElement, {
              type: 'standard',
              theme: 'filled_dark',
              size: 'large',
              width: '400',
              text: 'signin_with',
              logo_alignment: 'left'
            });
            customGoogleBtn.style.display = 'none';
          } catch (e) {
            console.log('GSI renderButton fallback notice:', e);
          }
        }
      } catch (e) {
        console.warn('Google GSI initialization notice:', e);
      }
    }
  }

  initGoogleAuth();
  if (!window.google || !window.google.accounts) {
    const interval = setInterval(() => {
      if (window.google && window.google.accounts && window.google.accounts.id) {
        clearInterval(interval);
        initGoogleAuth();
      }
    }, 300);
    setTimeout(() => clearInterval(interval), 5000);
  }

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
          window.location.replace('/');
        }, 500);
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
          window.location.replace('/');
        }, 800);
      } else {
        showToast(result.message || 'Registration failed.', 'error');
      }
    });
  }

  // Wire up Google Sign-In Button click fallback
  const googleBtn = document.getElementById('google-signin-btn');
  if (googleBtn) {
    googleBtn.addEventListener('click', () => {
      const gIdOnload = document.getElementById('g_id_onload');
      const clientId = gIdOnload ? gIdOnload.getAttribute('data-client_id') : null;

      if (!clientId) {
        showToast('Google Sign-In requires a valid Google Client ID configured on the server.', 'warning', 5000);
        return;
      }

      if (window.google && window.google.accounts && window.google.accounts.id) {
        try {
          window.google.accounts.id.initialize({
            client_id: clientId,
            callback: window.handleGoogleSignIn,
            auto_select: false,
            itp_support: true
          });
          window.google.accounts.id.prompt((notification) => {
            if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
              const reason = (notification.getNotDisplayedReason && notification.getNotDisplayedReason()) || 'prompt constraint';
              console.warn('Google prompt notice:', reason);
              showToast('Google Sign-In prompt was skipped or blocked (' + reason + '). Please check browser popups.', 'warning', 6000);
            }
          });
        } catch (err) {
          console.error('Google Sign-In initialization exception:', err);
          showToast('Failed to initialize Google Sign-In: ' + err.message, 'error', 5000);
        }
      } else {
        showToast('Google Sign-In service is initializing. Please try again in a moment.', 'info', 4000);
      }
    });
  }
});
