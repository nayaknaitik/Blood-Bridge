/**
 * Blood Bridge - All API calls go through this module.
 * All requests use credentials: "include" so the Flask session cookie is sent and stored.
 */

const API_BASE = '';

function request(method, path, body = null, headers = {}) {
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
    return fetch(API_BASE + path, opts)
        .then(res => res.json().then(data => ({ ok: res.ok, status: res.status, data })))
        .catch(err => ({ ok: false, status: 0, data: { success: false, message: 'Network error' } }));
}

const api = {
    auth: {
        register(payload) {
            return request('POST', '/api/auth/register', payload);
        },
        login(payload) {
            return request('POST', '/api/auth/login', {
                email: (payload && payload.email) != null ? String(payload.email).trim().toLowerCase() : '',
                password: (payload && payload.password) != null ? String(payload.password) : '',
            });
        },
        logout() {
            return request('POST', '/api/auth/logout');
        },
        session() {
            return request('GET', '/api/auth/session');
        },
        chooseRole(payload) {
            return request('POST', '/api/auth/choose-role', payload);
        },
        deleteUser(userId) {
            return request('POST', `/api/auth/users/${encodeURIComponent(userId)}/delete`);
        },
    },
    donors: {
        myDonations() {
            return request('GET', '/api/donors/my-donations');
        },
        schedule(payload) {
            return request('POST', '/api/donors/schedule', payload);
        },
    },
    requests: {
        create(payload) {
            return request('POST', '/api/requests', payload);
        },
        my() {
            return request('GET', '/api/requests/my');
        },
        pending() {
            return request('GET', '/api/requests/pending');
        },
        all() {
            return request('GET', '/api/requests/all');
        },
    },
    matching: {
        inventory() {
            return request('GET', '/api/matching/inventory');
        },
        dashboard() {
            return request('GET', '/api/matching/dashboard');
        },
    },
    health: {
        contact(payload) {
            return request('POST', '/api/contact', payload);
        },
    },
};

window.BloodBridgeAPI = api;
