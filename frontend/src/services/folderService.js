import apiClient from './api';

export const folderService = {

  async getRootContents(sortBy = 'name', sortOrder = 'asc') {
    const response = await apiClient.get('/folders', {
      params: { sort_by: sortBy, sort_order: sortOrder },
    });
    return response.data;
  },

  async getFolderContents(folderId, sortBy = 'name', sortOrder = 'asc') {
    const response = await apiClient.get(`/folders/${folderId}/contents`, {
      params: { sort_by: sortBy, sort_order: sortOrder },
    });
    return response.data;
  },

  async getFolderDetail(folderId) {
    const response = await apiClient.get(`/folders/${folderId}`);
    return response.data;
  },

  async getFolderTree() {
    const response = await apiClient.get('/folders/tree');
    return response.data;
  },

  async createFolder({ name, parent_id = null, color = null }) {
    const response = await apiClient.post('/folders', {
      name,
      parent_id,
      color,
    });
    return response.data;
  },

  async updateFolder(folderId, { name = null, color = null }) {
    const response = await apiClient.put(`/folders/${folderId}`, {
      name,
      color,
    });
    return response.data;
  },

  async moveFolder(folderId, destinationParentId) {
    const response = await apiClient.post(`/folders/${folderId}/move`, {
      destination_parent_id: destinationParentId,
    });
    return response.data;
  },

  async toggleStar(folderId) {
    const response = await apiClient.post(`/folders/${folderId}/star`);
    return response.data;
  },

  async softDelete(folderId) {
    const response = await apiClient.delete(`/folders/${folderId}`);
    return response.data;
  },

  async restore(folderId) {
    const response = await apiClient.post(`/folders/${folderId}/restore`);
    return response.data;
  },

  async permanentDelete(folderId) {
    const response = await apiClient.delete(`/folders/${folderId}/permanent`);
    return response.data;
  },

  async downloadZip(folderId, folderName = 'folder') {
    const response = await apiClient.get(`/folders/${folderId}/download-zip`, {
      responseType: 'blob',
    });

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${folderName}.zip`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};

export default folderService;
