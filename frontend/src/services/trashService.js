/**
 * Trash bin listing, restoration, and purge API service client.
 */

import apiClient from './api';

export const trashService = {
  /**
   * List all soft-deleted items currently in the trash bin.
   */
  async listTrash() {
    const response = await apiClient.get('/trash');
    return response.data;
  },

  /**
   * Restore all trash items in a single batch operation.
   */
  async restoreAll() {
    const response = await apiClient.post('/trash/restore-all');
    return response.data;
  },

  /**
   * Permanently empty trash bin.
   */
  async emptyTrash() {
    const response = await apiClient.delete('/trash/empty');
    return response.data;
  },
};

export default trashService;
