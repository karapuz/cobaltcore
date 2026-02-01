const API_URL = 'http://localhost:8000/api';

class AuthService {
  // ─────────────────────────────────────
  // Auth methods
  // ─────────────────────────────────────

  async signup(name, email, password) {
    const response = await fetch(`${API_URL}/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password }),
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Signup failed');

    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    return data;
  }

  async login(email, password) {
    const response = await fetch(`${API_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Login failed');

    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    return data;
  }

  async logout() {
    try {
      const token = this.getAccessToken();
      await fetch(`${API_URL}/logout`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
  }

  getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  }

  getAccessToken() {
    return localStorage.getItem('access_token');
  }

  getRefreshToken() {
    return localStorage.getItem('refresh_token');
  }

  isAuthenticated() {
    return !!this.getAccessToken();
  }

  async refreshToken() {
    const refresh_token = this.getRefreshToken();
    if (!refresh_token) throw new Error('No refresh token available');

    const response = await fetch(`${API_URL}/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token }),
    });

    const data = await response.json();
    if (!response.ok) {
      this.logout();
      throw new Error('Token refresh failed');
    }

    localStorage.setItem('access_token', data.access_token);
    return data.access_token;
  }

  async getUserProfile() {
    const token = this.getAccessToken();
    const response = await fetch(`${API_URL}/user`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (response.status === 401) {
      await this.refreshToken();
      return this.getUserProfile();
    }

    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to fetch user profile');
    return data;
  }

  async updateProfile(name) {
    const token = this.getAccessToken();
    const response = await fetch(`${API_URL}/user/profile`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name }),
    });

    if (response.status === 401) {
      await this.refreshToken();
      return this.updateProfile(name);
    }

    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to update profile');
    localStorage.setItem('user', JSON.stringify(data));
    return data;
  }

  // ─────────────────────────────────────
  // Generic authenticated fetch helper
  // Auto-refreshes token on 401, retries once
  // ─────────────────────────────────────
  async _authFetch(url, options = {}, retried = false) {
    const token = this.getAccessToken();
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...(options.headers || {}),
    };

    const response = await fetch(url, { ...options, headers });

    if (response.status === 401 && !retried) {
      await this.refreshToken();
      return this._authFetch(url, options, true);
    }

    return response;
  }

  // ─────────────────────────────────────
  // Portfolio methods (credit_ratings.json)
  // ─────────────────────────────────────

  async getPortfolio() {
    const response = await this._authFetch(`${API_URL}/portfolio`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to fetch portfolio');
    return data;
  }

  async getCreditRating(computationId) {
    const response = await this._authFetch(`${API_URL}/portfolio/${computationId}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Credit rating not found');
    return data;
  }

  async addCreditRating(rating) {
    const response = await this._authFetch(`${API_URL}/portfolio`, {
      method: 'POST',
      body: JSON.stringify(rating),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to add credit rating');
    return data;
  }

  async updateCreditRating(computationId, updatedFields) {
    const response = await this._authFetch(`${API_URL}/portfolio/${computationId}`, {
      method: 'PUT',
      body: JSON.stringify(updatedFields),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to update credit rating');
    return data;
  }

  async deleteCreditRating(computationId) {
    const response = await this._authFetch(`${API_URL}/portfolio/${computationId}`, {
      method: 'DELETE',
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to delete credit rating');
    return data;
  }

  // ─────────────────────────────────────
  // Scenarios methods (scenarios.json)
  // ─────────────────────────────────────

  async getScenarios() {
    const response = await this._authFetch(`${API_URL}/scenarios`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to fetch scenarios');
    return data;
  }

  async getScenario(computationId) {
    const response = await this._authFetch(`${API_URL}/scenarios/${computationId}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Scenario not found');
    return data;
  }

  async updateScenario(computationId, updatedFields) {
    const response = await this._authFetch(`${API_URL}/scenarios/${computationId}`, {
      method: 'PUT',
      body: JSON.stringify(updatedFields),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to update scenario');
    return data;
  }
}

export default new AuthService();