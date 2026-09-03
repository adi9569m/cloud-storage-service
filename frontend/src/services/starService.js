/**
 * Starred favorite items API service client.
 */

import apiClient from './api';

export const starService = {
  /**
   * List all starred files and folders.
   */
  async listStarred() {
    const response = await apiClient.get('/stars');
    return response.data;
  },

  /**
   * Toggle star status for a file or folder.
   * @param {Object} payload - { file_id?, folder_id? }
   */
  async toggleStar({ file_id = null, folder_id = null }) {
    const response = await apiClient.post('/stars/toggle', {
      file_id,
      folder_id,
    });
    return response.data;
  },
};

export default starService;
