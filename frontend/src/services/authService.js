import apiClient from './api';

export const authService = {

  async login(email, password) {
    const response = await apiClient.post('/auth/login', {
      email,
      password,
    });
    return response.data;
  },

  async register(email, password, fullName = '') {
    const response = await apiClient.post('/auth/register', {
      email,
      password,
      full_name: fullName,
    });
    return response.data;
  },

  async getMe() {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },

  async updateProfile(profileData) {
    const response = await apiClient.put('/auth/me', profileData);
    return response.data;
  },

  async changePassword(currentPassword, newPassword) {
    const response = await apiClient.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response.data;
  },
};

export default authService;
