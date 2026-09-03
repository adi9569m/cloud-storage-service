/**
 * File management API service client for uploads, downloads, versioning,
 * inline previews, comments, moves, and metadata management.
 */

import apiClient from './api';

export const fileService = {
  /**
   * Direct multipart file upload.
   * @param {File} file - Browser File object
   * @param {string|null} folderId - Destination folder UUID or null for root
   * @param {Function} [onProgress] - Optional upload progress callback (percent 0-100)
   */
  async directUpload(file, folderId = null, onProgress = null) {
    const formData = new FormData();
    formData.append('file', file);
    if (folderId) {
      formData.append('folder_id', folderId);
    }

    const response = await apiClient.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percent);
        }
      },
    });
    return response.data;
  },

  /**
   * Get detailed metadata for a file including breadcrumbs and versions.
   */
  async getDetail(fileId) {
    const response = await apiClient.get(`/files/${fileId}`);
    return response.data;
  },

  /**
   * Get presigned or direct download URL for active or historical version.
   */
  async getDownloadUrl(fileId, versionNumber = null) {
    const endpoint = versionNumber
      ? `/files/${fileId}/versions/${versionNumber}/download-url`
      : `/files/${fileId}/download-url`;
    const response = await apiClient.get(endpoint);
    return response.data;
  },

  /**
   * Stream and trigger browser binary file download.
   */
  async downloadFile(fileId, filename = 'download', versionNumber = null) {
    const endpoint = versionNumber
      ? `/files/${fileId}/versions/${versionNumber}/download`
      : `/files/${fileId}/download`;

    const response = await apiClient.get(endpoint, {
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

  /**
   * Get preview stream URL with auth token query if needed.
   */
  getPreviewUrl(fileId) {
    const token = localStorage.getItem('access_token');
    return `/api/v1/files/${fileId}/preview${token ? `?token=${encodeURIComponent(token)}` : ''}`;
  },

  /**
   * Retrieve text or code content for syntax inspection.
   */
  async getTextContent(fileId) {
    const response = await apiClient.get(`/files/${fileId}/text-content`);
    return response.data;
  },

  /**
   * Rename file.
   */
  async rename(fileId, name) {
    const response = await apiClient.put(`/files/${fileId}`, { name });
    return response.data;
  },

  /**
   * Move file to destination folder.
   */
  async move(fileId, destinationFolderId) {
    const response = await apiClient.post(`/files/${fileId}/move`, {
      destination_folder_id: destinationFolderId,
    });
    return response.data;
  },

  /**
   * Duplicate file to destination folder.
   */
  async copy(fileId, destinationFolderId = null, newName = null) {
    const response = await apiClient.post(`/files/${fileId}/copy`, {
      destination_folder_id: destinationFolderId,
      new_name: newName,
    });
    return response.data;
  },

  /**
   * Toggle star status for a file.
   */
  async toggleStar(fileId) {
    const response = await apiClient.post(`/files/${fileId}/star`);
    return response.data;
  },

  /**
   * Move file to trash bin (soft delete).
   */
  async softDelete(fileId) {
    const response = await apiClient.delete(`/files/${fileId}`);
    return response.data;
  },

  /**
   * Restore file from trash bin.
   */
  async restore(fileId) {
    const response = await apiClient.post(`/files/${fileId}/restore`);
    return response.data;
  },

  /**
   * Hard delete file permanently.
   */
  async permanentDelete(fileId) {
    const response = await apiClient.delete(`/files/${fileId}/permanent`);
    return response.data;
  },

  /**
   * List version history snapshots for a file.
   */
  async listVersions(fileId) {
    const response = await apiClient.get(`/files/${fileId}/versions`);
    return response.data;
  },

  /**
   * Direct multipart upload for a new version of an existing file.
   */
  async uploadNewVersion(fileId, file, onProgress = null) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post(`/files/${fileId}/versions/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percent);
        }
      },
    });
    return response.data;
  },

  /**
   * List all comments on a file.
   */
  async listComments(fileId) {
    const response = await apiClient.get(`/files/${fileId}/comments`);
    return response.data;
  },

  /**
   * Post a new collaboration comment on a file.
   */
  async addComment(fileId, content) {
    const response = await apiClient.post(`/files/${fileId}/comments`, { content });
    return response.data;
  },

  /**
   * Delete a comment.
   */
  async deleteComment(commentId) {
    const response = await apiClient.delete(`/files/comments/${commentId}`);
    return response.data;
  },
};

export default fileService;
