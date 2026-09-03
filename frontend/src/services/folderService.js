/**
 * Folder management API service client for hierarchical navigation,
 * creation, moving, star toggling, and directory ZIP downloading.
 */

import apiClient from './api';

export const folderService = {
  /**
   * List contents of the Root storage directory.
   */
  async getRootContents(sortBy = 'name', sortOrder = 'asc') {
    const response = await apiClient.get('/folders', {
      params: { sort_by: sortBy, sort_order: sortOrder },
    });
    return response.data;
  },

  /**
   * List child subfolders and files inside a specific folder.
   */
  async getFolderContents(folderId, sortBy = 'name', sortOrder = 'asc') {
    const response = await apiClient.get(`/folders/${folderId}/contents`, {
      params: { sort_by: sortBy, sort_order: sortOrder },
    });
    return response.data;
  },

  /**
   * Get single folder detail with breadcrumbs.
   */
  async getFolderDetail(folderId) {
    const response = await apiClient.get(`/folders/${folderId}`);
    return response.data;
  },

  /**
   * Get recursive folder directory tree for destination pickers.
   */
  async getFolderTree() {
    const response = await apiClient.get('/folders/tree');
    return response.data;
  },

  /**
   * Create a new folder.
   */
  async createFolder({ name, parent_id = null, color = null }) {
    const response = await apiClient.post('/folders', {
      name,
      parent_id,
      color,
    });
    return response.data;
  },

  /**
   * Update folder name or UI color tag.
   */
  async updateFolder(folderId, { name = null, color = null }) {
    const response = await apiClient.put(`/folders/${folderId}`, {
      name,
      color,
    });
    return response.data;
  },

  /**
   * Move folder to a new destination folder.
   */
  async moveFolder(folderId, destinationParentId) {
    const response = await apiClient.post(`/folders/${folderId}/move`, {
      destination_parent_id: destinationParentId,
    });
    return response.data;
  },

  /**
   * Toggle star favorite status for folder.
   */
  async toggleStar(folderId) {
    const response = await apiClient.post(`/folders/${folderId}/star`);
    return response.data;
  },

  /**
   * Soft delete folder to trash bin.
   */
  async softDelete(folderId) {
    const response = await apiClient.delete(`/folders/${folderId}`);
    return response.data;
  },

  /**
   * Restore folder from trash bin.
   */
  async restore(folderId) {
    const response = await apiClient.post(`/folders/${folderId}/restore`);
    return response.data;
  },

  /**
   * Permanently delete folder.
   */
  async permanentDelete(folderId) {
    const response = await apiClient.delete(`/folders/${folderId}/permanent`);
    return response.data;
  },

  /**
   * Download entire folder recursively as a ZIP archive.
   */
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
