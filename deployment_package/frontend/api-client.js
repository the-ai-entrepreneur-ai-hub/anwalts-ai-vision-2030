/**
 * AnwaltsAIApiClient - minimal browser client for Enhanced Flask API (port 5001)
 * Endpoints implemented:
 *  - POST /auth/login
 *  - GET  /templates
 *  - POST /generate-document
 *
 * Base URL is taken from window.API_BASE (see Client/config.js) with fallback to http://localhost:5001
 */
(function (global) {
  const DEFAULT_BASE = 'http://localhost:5001';
  const BASE_URL = (global.API_BASE || DEFAULT_BASE).replace(/\/+$/g, '');

  class AnwaltsAIApiClient {
    constructor(baseUrl = BASE_URL) {
      this.baseUrl = baseUrl.replace(/\/+$/g, '');
      this.token = null;
    }

    setToken(token) {
      this.token = token;
    }

    get headers() {
      const headers = {
        'Content-Type': 'application/json'
      };
      if (this.token) {
        headers['Authorization'] = `Bearer ${this.token}`;
      }
      return headers;
    }

    async login(email, password) {
      const res = await fetch(`${this.baseUrl}/auth/login`, {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({ email, password })
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.success || !data.token) {
        return {
          success: false,
          message: data.error || 'Login failed'
        };
      }

      // persist token in memory; caller can also persist in storage if desired
      this.setToken(data.token);

      return {
        success: true,
        token: data.token,
        user: data.user
      };
    }

    async validateToken() {
      const res = await fetch(`${this.baseUrl}/auth/validate`, {
        method: 'GET',
        headers: this.headers
      });
      const data = await res.json().catch(() => ({}));
      return res.ok ? data : { valid: false };
    }

    async getTemplates(params = {}) {
      const qs = new URLSearchParams(params);
      const url = `${this.baseUrl}/templates${qs.toString() ? `?${qs.toString()}` : ''}`;
      const res = await fetch(url, {
        method: 'GET',
        headers: this.headers
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.success === false) {
        throw new Error(data.error || 'Failed to load templates');
      }
      return data.templates || [];
    }

    /**
     * Generate a document
     * payload: { prompt: string, template_id?: string }
     * Note: The server accepts both JSON and multipart; we use JSON here.
     */
    async generateDocument(payload) {
      const res = await fetch(`${this.baseUrl}/generate-document`, {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify(payload)
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.success === false) {
        throw new Error(data.error || 'Dokumentenerstellung fehlgeschlagen');
      }
      return data.document;
    }
  }

  // Attach to window
  global.AnwaltsAIApiClient = AnwaltsAIApiClient;

  // Auto-instantiate for the landing page usage (if not already created)
  if (!global.apiClient) {
    try {
      global.apiClient = new AnwaltsAIApiClient(BASE_URL);

      // Attempt to restore token from localStorage if present
      const storedUser = localStorage.getItem('anwalts_user');
      const storedToken = storedUser ? (JSON.parse(storedUser).token || null) : null;
      if (storedToken) {
        global.apiClient.setToken(storedToken);
      }
    } catch (e) {
      console.error('Failed to initialize AnwaltsAIApiClient:', e);
    }
  }
})(window);
