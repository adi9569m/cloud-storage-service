import apiClient from './api';

export const storageService = {

  async getSummary() {
    const response = await apiClient.get('/storage/summary');
    return response.data;
  },

  async getBreakdown() {
    const response = await apiClient.get('/storage/breakdown');
    return response.data;
  },

  async recalculate() {
    const response = await apiClient.post('/storage/recalculate');
    return response.data;
  },
};

export default storageService;
