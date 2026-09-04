import apiClient from './api';

export const shareService = {

  async listSharedWithMe() {
    const response = await apiClient.get('/shares/shared-with-me');
    return response.data;
  },

  async listSharedByMe() {
    const response = await apiClient.get('/shares/shared-by-me');
    return response.data;
  },

  async listFileShares(fileId) {
    const response = await apiClient.get(`/shares/file/${fileId}`);
    return response.data;
  },

  async listFolderShares(folderId) {
    const response = await apiClient.get(`/shares/folder/${folderId}`);
    return response.data;
  },

  async createShare(payload) {
    const response = await apiClient.post('/shares', payload);
    return response.data;
  },

  async updateShareRole(shareId, role) {
    const response = await apiClient.put(`/shares/${shareId}`, { role });
    return response.data;
  },

  async revokeShare(shareId) {
    const response = await apiClient.delete(`/shares/${shareId}`);
    return response.data;
  },
};

export default shareService;
