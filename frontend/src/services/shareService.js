/**
 * Direct user-to-user sharing API service client.
 */

import apiClient from './api';

export const shareService = {
  /**
   * List files and folders shared with the current authenticated user.
   */
  async listSharedWithMe() {
    const response = await apiClient.get('/shares/shared-with-me');
    return response.data;
  },

  /**
   * List active shares granted by current user.
   */
  async listSharedByMe() {
    const response = await apiClient.get('/shares/shared-by-me');
    return response.data;
  },

  /**
   * List shares on a specific file.
   */
  async listFileShares(fileId) {
    const response = await apiClient.get(`/shares/file/${fileId}`);
    return response.data;
  },

  /**
   * List shares on a specific folder.
   */
  async listFolderShares(folderId) {
    const response = await apiClient.get(`/shares/folder/${folderId}`);
    return response.data;
  },

  /**
   * Grant direct share access to a user by email.
   * @param {Object} payload - { grantee_email, role ('VIEWER'|'EDITOR'), file_id?, folder_id? }
   */
  async createShare(payload) {
    const response = await apiClient.post('/shares', payload);
    return response.data;
  },

  /**
   * Update role for an existing share.
   */
  async updateShareRole(shareId, role) {
    const response = await apiClient.put(`/shares/${shareId}`, { role });
    return response.data;
  },

  /**
   * Revoke a direct share.
   */
  async revokeShare(shareId) {
    const response = await apiClient.delete(`/shares/${shareId}`);
    return response.data;
  },
};

export default shareService;
