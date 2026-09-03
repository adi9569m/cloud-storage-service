/**
 * Public link sharing API service client for authenticated management
 * and unauthenticated public consumption.
 */

import apiClient from './api';

export const linkShareService = {
  // =========================================================================
  // Authenticated Management Endpoints
  // =========================================================================

  /**
   * Create a public shareable link.
   * @param {Object} payload - { file_id?, folder_id?, role, password?, expires_at? }
   */
  async createLink(payload) {
    const response = await apiClient.post('/links', payload);
    return response.data;
  },

  /**
   * List public links for a specific file.
   */
  async listFileLinks(fileId) {
    const response = await apiClient.get(`/links/file/${fileId}`);
    return response.data;
  },

  /**
   * List public links for a specific folder.
   */
  async listFolderLinks(folderId) {
    const response = await apiClient.get(`/links/folder/${folderId}`);
    return response.data;
  },

  /**
   * Update public link settings (role, password, expiration, is_active).
   */
  async updateLink(linkId, payload) {
    const response = await apiClient.put(`/links/${linkId}`, payload);
    return response.data;
  },

  /**
   * Revoke/delete a public link.
   */
  async revokeLink(linkId) {
    const response = await apiClient.delete(`/links/${linkId}`);
    return response.data;
  },

  // =========================================================================
  // Unauthenticated Public Consumer Endpoints
  // =========================================================================

  /**
   * Inspect a public link token.
   */
  async inspectPublicLink(token, password = null) {
    const params = password ? { password } : {};
    const response = await apiClient.get(`/public/links/${token}`, { params });
    return response.data;
  },

  /**
   * Access password-protected public link with payload.
   */
  async accessWithPassword(token, password) {
    const response = await apiClient.post(`/public/links/${token}/access`, { password });
    return response.data;
  },

  /**
   * Browse contents of a publicly shared folder.
   */
  async getPublicFolderContents(token, folderId = null, password = null) {
    const params = {};
    if (folderId) params.folder_id = folderId;
    if (password) params.password = password;

    const response = await apiClient.get(`/public/links/${token}/contents`, { params });
    return response.data;
  },

  /**
   * Trigger download of a publicly shared file.
   */
  async downloadPublicFile(token, filename = 'shared_file', password = null) {
    const params = password ? { password } : {};
    const response = await apiClient.get(`/public/links/${token}/download`, {
      params,
      responseType: 'blob',
    });

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};

export default linkShareService;
