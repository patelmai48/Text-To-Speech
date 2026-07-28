/**
 * API Service & Toast Notification Manager
 */

// --- Toast Notification Manager ---
function showToast(message, type = 'info', duration = 4000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const icons = {
    success: 'bi-check-circle-fill',
    error: 'bi-exclamation-triangle-fill',
    warning: 'bi-exclamation-circle-fill',
    info: 'bi-info-circle-fill'
  };

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <i class="bi ${icons[type] || icons.info} toast-icon"></i>
    <span style="flex:1;">${message}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(50px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// --- LocalStorage Auth Token Helpers ---
const AuthToken = {
  get: () => localStorage.getItem('tts_jwt_token'),
  set: (token) => localStorage.setItem('tts_jwt_token', token),
  remove: () => localStorage.removeItem('tts_jwt_token'),
  exists: () => !!localStorage.getItem('tts_jwt_token')
};

// --- REST API Fetch Wrapper ---
const API = {
  async request(endpoint, method = 'GET', data = null, isBlob = false) {
    const token = AuthToken.get();
    const headers = {};

    if (data && !(data instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
      method,
      headers
    };

    if (data) {
      config.body = data instanceof FormData ? data : JSON.stringify(data);
    }

    try {
      const response = await fetch(`/api${endpoint}`, config);

      if (response.status === 401) {
        // Token expired or invalid
        AuthToken.remove();
        if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
          showToast('Session expired. Please log in again.', 'warning');
          setTimeout(() => {
            window.location.href = '/login';
          }, 1200);
        }
        return { success: false, message: 'Unauthorized' };
      }

      if (isBlob) {
        return await response.blob();
      }

      const json = await response.json();

      if (!response.ok && !json.message) {
        json.message = `HTTP error status: ${response.status}`;
      }

      return json;
    } catch (error) {
      console.error('API Client Error:', error);
      showToast('Network error or server unavailable.', 'error');
      return { success: false, message: error.message || 'Network error' };
    }
  },

  get(endpoint) {
    return this.request(endpoint, 'GET');
  },

  post(endpoint, data) {
    return this.request(endpoint, 'POST', data);
  },

  put(endpoint, data) {
    return this.request(endpoint, 'PUT', data);
  },

  delete(endpoint) {
    return this.request(endpoint, 'DELETE');
  },

  getBlob(endpoint) {
    return this.request(endpoint, 'GET', null, true);
  }
};
