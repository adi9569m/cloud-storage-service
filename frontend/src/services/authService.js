/**
 * Authentication and User Profile API service client.
 */

import apiClient from './api';

export const authService = {
  /**
   * Log in user with email and password credentials.
   */
  async login(email, password) {
    const response = await apiClient.post('/auth/login', {
      email,
      password,
    });
    return response.data;
  },

  /**
   * Register a new user account.
   */
  async register(email, password, fullName = '') {
    const response = await apiClient.post('/auth/register', {
      email,
      password,
      full_name: fullName,
    });
    return response.data;
  },

  /**
   * Fetch current authenticated user profile.
   */
  async getMe() {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },

  /**
   * Update current user profile.
   */
  async updateProfile(profileData) {
    const response = await apiClient.put('/auth/me', profileData);
    return response.data;
  },

  /**
   * Change current user account password.
   */
  async changePassword(oldPassword, newPassword) {
    const response = await apiClient.post('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    });
    return response.data;
  },
};

export default authService;
