/**
 * Authentication Page Logic (Login, Registration, Google Auth, Forgot/Reset Password)
 */

document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');
  const forgotForm = document.getElementById('forgot-form');
  const resetForm = document.getElementById('reset-form');

  const showForgotBtn = document.getElementById('show-forgot-btn');
  const backToLoginBtn = document.getElementById('back-to-login-btn');
  const backToLoginBtn2 = document.getElementById('back-to-login-btn-2');

  // --- View Toggle Helpers ---
  if (showForgotBtn) {
    showForgotBtn.addEventListener('click', (e) => {
      e.preventDefault();
      loginForm.style.display = 'none';
      forgotForm.style.display = 'block';
    });
  }

  if (backToLoginBtn) {
    backToLoginBtn.addEventListener('click', (e) => {
      e.preventDefault();
      forgotForm.style.display = 'none';
      loginForm.style.display = 'block';
    });
  }

  if (backToLoginBtn2) {
    backToLoginBtn2.addEventListener('click', (e) => {
      e.preventDefault();
      resetForm.style.display = 'none';
      loginForm.style.display = 'block';
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
        showToast('Account created successfully! Please check your email for the verification code.', 'success');
        setTimeout(() => {
          window.location.href = '/';
        }, 1500);
      } else {
        showToast(result.message || 'Registration failed.', 'error');
      }
    });
  }

  // --- Forgot Password Submission ---
  if (forgotForm) {
    forgotForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const emailInput = document.getElementById('forgot-email');
      const email = emailInput.value.trim();

      if (!email) {
        showToast('Please enter your email address.', 'warning');
        return;
      }

      const submitBtn = forgotForm.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<div class="spinner"></div> Processing...`;

      const result = await API.post('/auth/forgot-password', { email });

      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;

      if (result.success) {
        showToast('If the email exists, a 6-digit reset code has been sent.', 'success');
        // Pre-fill email in reset form and transition to reset form
        document.getElementById('reset-email').value = email;
        forgotForm.style.display = 'none';
        resetForm.style.display = 'block';
      } else {
        showToast(result.message || 'Failed to request reset.', 'error');
      }
    });
  }

  // --- Reset Password Submission ---
  if (resetForm) {
    resetForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('reset-email').value.trim();
      const code = document.getElementById('reset-code').value.trim();
      const newPassword = document.getElementById('reset-new-password').value;
      const confirmPassword = document.getElementById('reset-confirm-password').value;

      if (!code || !newPassword || !confirmPassword) {
        showToast('Please fill in all reset fields.', 'warning');
        return;
      }

      if (newPassword !== confirmPassword) {
        showToast('Passwords do not match.', 'error');
        return;
      }

      if (newPassword.length < 6) {
        showToast('Password must be at least 6 characters.', 'warning');
        return;
      }

      const submitBtn = resetForm.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<div class="spinner"></div> Resetting...`;

      const result = await API.post('/auth/reset-password', {
        email,
        code,
        new_password: newPassword
      });

      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;

      if (result.success) {
        showToast('Password reset successfully! You can now log in.', 'success');
        resetForm.reset();
        resetForm.style.display = 'none';
        loginForm.style.display = 'block';
      } else {
        showToast(result.message || 'Password reset failed.', 'error');
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

  // Wire up Google Button click to trigger simulation modal
  const googleBtn = document.getElementById('google-signin-btn');
  const googleSimModal = document.getElementById('google-sim-modal');
  const closeGoogleSimBtn = document.getElementById('close-google-sim-btn');
  const simCustomAccountBtn = document.getElementById('sim-custom-account-btn');
  const simCustomInputPanel = document.getElementById('sim-custom-input-panel');
  const simCustomEmail = document.getElementById('sim-custom-email');
  const simCustomSubmitBtn = document.getElementById('sim-custom-submit-btn');

  if (googleBtn && googleSimModal) {
    googleBtn.addEventListener('click', () => {
      // Reset modal state
      if (simCustomInputPanel) simCustomInputPanel.style.display = 'none';
      if (simCustomEmail) simCustomEmail.value = '';
      googleSimModal.style.display = 'flex';
      googleSimModal.classList.add('open');
    });
  }

  if (closeGoogleSimBtn && googleSimModal) {
    closeGoogleSimBtn.addEventListener('click', () => {
      googleSimModal.classList.remove('open');
      setTimeout(() => {
        googleSimModal.style.display = 'none';
      }, 300);
    });
  }

  // Handle Account Selection Clicks
  const accountButtons = document.querySelectorAll('.sim-account-btn[data-email]');
  accountButtons.forEach(btn => {
    btn.addEventListener('click', async () => {
      const email = btn.getAttribute('data-email');
      const username = btn.getAttribute('data-username') || email.split('@')[0];
      if (googleSimModal) {
        googleSimModal.classList.remove('open');
        googleSimModal.style.display = 'none';
      }
      await executeSimulatedGoogleLogin(email, username);
    });
  });

  // Toggle Custom Account Input
  if (simCustomAccountBtn && simCustomInputPanel) {
    simCustomAccountBtn.addEventListener('click', () => {
      simCustomInputPanel.style.display = 'block';
      if (simCustomEmail) simCustomEmail.focus();
    });
  }

  // Submit Custom Account
  if (simCustomSubmitBtn && simCustomEmail) {
    simCustomSubmitBtn.addEventListener('click', async () => {
      const email = simCustomEmail.value.trim();
      if (!email || !email.includes('@')) {
        showToast('Please enter a valid email address.', 'warning');
        return;
      }
      const username = email.split('@')[0];
      if (googleSimModal) {
        googleSimModal.classList.remove('open');
        googleSimModal.style.display = 'none';
      }
      await executeSimulatedGoogleLogin(email, username);
    });
  }

  async function executeSimulatedGoogleLogin(email, username) {
    showToast('Simulating Google Auth...', 'info');
    const result = await API.post('/auth/google', {
      credential: 'simulated_google_token',
      email: email,
      username: username
    });

    if (result.success && result.token) {
      AuthToken.set(result.token);
      showToast(result.message || 'Logged in with Google (Simulated)!', 'success');
      setTimeout(() => {
        window.location.href = '/';
      }, 800);
    } else {
      showToast(result.message || 'Google Sign-In failed.', 'error');
    }
  }
});
