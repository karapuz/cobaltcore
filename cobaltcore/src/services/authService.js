const API_URL = 'http://localhost:8000/api';

class AuthService {
  async signup(name, email, password) {
    try {
      const response = await fetch(`${API_URL}/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Signup failed');
      }

      // Store tokens
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('user', JSON.stringify(data.user));

      return data;
    } catch (error) {
      throw error;
    }
  }

  async login(email, password) {
    try {
      const response = await fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Login failed');
      }

      // Store tokens
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('user', JSON.stringify(data.user));

      return data;
    } catch (error) {
      throw error;
    }
  }

  async logout() {
    try {
      const token = this.getAccessToken();
      
      await fetch(`${API_URL}/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage regardless of API call success
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
    try {
      const refresh_token = this.getRefreshToken();
      
      if (!refresh_token) {
        throw new Error('No refresh token available');
      }

      const response = await fetch(`${API_URL}/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      localStorage.setItem('access_token', data.access_token);
      
      return data.access_token;
    } catch (error) {
      this.logout();
      throw error;
    }
  }

  async getUserProfile() {
    try {
      const token = this.getAccessToken();
      
      const response = await fetch(`${API_URL}/user`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.status === 401) {
        // Try to refresh token
        await this.refreshToken();
        return this.getUserProfile(); // Retry
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to fetch user profile');
      }

      return data;
    } catch (error) {
      throw error;
    }
  }

  async updateProfile(name) {
    try {
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

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to update profile');
      }

      // Update local storage
      localStorage.setItem('user', JSON.stringify(data));

      return data;
    } catch (error) {
      throw error;
    }
  }
}

export default new AuthService();