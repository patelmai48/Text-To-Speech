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

  // Wire up Google Sign-In Button click
  const googleBtn = document.getElementById('google-signin-btn');
  if (googleBtn) {
    googleBtn.addEventListener('click', () => {
      if (window.google && window.google.accounts && window.google.accounts.id) {
        window.google.accounts.id.prompt((notification) => {
          if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
            showToast('Please enable popup or configure GOOGLE_CLIENT_ID for Google Sign-In.', 'warning');
          }
        });
      } else {
        showToast('Google Sign-In requires configuring GOOGLE_CLIENT_ID in environment settings.', 'error');
      }
    });
  }
});

