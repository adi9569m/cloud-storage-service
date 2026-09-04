import apiClient from './api';

export const linkShareService = {

  async createLink(payload) {
    const response = await apiClient.post('/links', payload);
    return response.data;
  },

  async listFileLinks(fileId) {
    const response = await apiClient.get(`/links/file/${fileId}`);
    return response.data;
  },

  async listFolderLinks(folderId) {
    const response = await apiClient.get(`/links/folder/${folderId}`);
    return response.data;
  },

  async updateLink(linkId, payload) {
    const response = await apiClient.put(`/links/${linkId}`, payload);
    return response.data;
  },

  async revokeLink(linkId) {
    const response = await apiClient.delete(`/links/${linkId}`);
    return response.data;
  },

  async inspectPublicLink(token, password = null) {
    const params = password ? { password } : {};
    const response = await apiClient.get(`/public/links/${token}`, { params });
    return response.data;
  },

  async accessWithPassword(token, password) {
    const response = await apiClient.post(`/public/links/${token}/access`, { password });
    return response.data;
  },

  async getPublicFolderContents(token, folderId = null, password = null) {
    const params = {};
    if (folderId) params.folder_id = folderId;
    if (password) params.password = password;

    const response = await apiClient.get(`/public/links/${token}/contents`, { params });
    return response.data;
  },

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
