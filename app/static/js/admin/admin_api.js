/**
 * Admin API client - all admin endpoints, JSON + credentials.
 */

const ADMIN_API_BASE = '';

function adminRequest(method, path, body = null, headers = {}) {
  const opts = {
    method,
    credentials: 'include',
    headers: {
      'Accept': 'application/json',
      ...headers,
    },
  };
  if (body != null && method !== 'GET') {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = typeof body === 'string' ? body : JSON.stringify(body);
  }
  return fetch(ADMIN_API_BASE + path, opts)
    .then(res => res.json().then(data => ({ ok: res.ok, status: res.status, data })))
    .catch(() => ({ ok: false, status: 0, data: { success: false, message: 'Network error' } }));
}

const AdminAPI = {
  auth: {
    login(payload) {
      return adminRequest('POST', '/api/admin/login', {
        email: (payload && payload.email) ? String(payload.email).trim().toLowerCase() : '',
        password: (payload && payload.password) ? String(payload.password) : '',
      });
    },
    logout() {
      return adminRequest('POST', '/api/admin/logout');
    },
    session() {
      return adminRequest('GET', '/api/admin/session');
    },
  },
  dashboard: {
    stats() {
      return adminRequest('GET', '/api/admin/dashboard');
    },
  },
  users: {
    list() {
      return adminRequest('GET', '/api/admin/users');
    },
    delete(id) {
      return adminRequest('POST', `/api/admin/users/${encodeURIComponent(id)}/delete`);
    },
  },
  requests: {
    list() {
      return adminRequest('GET', '/api/admin/requests');
    },
  },
  donations: {
    list() {
      return adminRequest('GET', '/api/admin/donations');
    },
  },
  inventory: {
    list() {
      return adminRequest('GET', '/api/admin/inventory');
    },
  },
};

window.BloodBridgeAdminAPI = AdminAPI;

