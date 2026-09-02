/**
 * Storage analytics and quota API service client.
 */

import apiClient from './api';

export const storageService = {
  /**
   * Fetch comprehensive storage summary, metrics, and largest files.
   */
  async getSummary() {
    const response = await apiClient.get('/storage/summary');
    return response.data;
  },

  /**
   * Fetch category breakdown metrics.
   */
  async getBreakdown() {
    const response = await apiClient.get('/storage/breakdown');
    return response.data;
  },

  /**
   * Recalculate and re-synchronize user storage usage.
   */
  async recalculate() {
    const response = await apiClient.post('/storage/recalculate');
    return response.data;
  },
};

export default storageService;
