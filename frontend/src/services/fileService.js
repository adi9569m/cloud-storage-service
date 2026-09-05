import apiClient from './api';

export const fileService = {

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

  async getDetail(fileId) {
    const response = await apiClient.get(`/files/${fileId}`);
    return response.data;
  },

  async getDownloadUrl(fileId, versionNumber = null) {
    const endpoint = versionNumber
      ? `/files/${fileId}/versions/${versionNumber}/download-url`
      : `/files/${fileId}/download-url`;
    const response = await apiClient.get(endpoint);
    return response.data;
  },

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

  getPreviewUrl(fileId) {
    const token = localStorage.getItem('access_token');
    return `/api/v1/files/${fileId}/preview${token ? `?token=${encodeURIComponent(token)}` : ''}`;
  },

  async getTextContent(fileId) {
    const response = await apiClient.get(`/files/${fileId}/text-content`);
    return response.data;
  },

  async rename(fileId, name) {
    const response = await apiClient.put(`/files/${fileId}`, { name });
    return response.data;
  },

  async move(fileId, destinationFolderId) {
    const response = await apiClient.post(`/files/${fileId}/move`, {
      destination_folder_id: destinationFolderId,
    });
    return response.data;
  },

  async copy(fileId, destinationFolderId = null, newName = null) {
    const response = await apiClient.post(`/files/${fileId}/copy`, {
      destination_folder_id: destinationFolderId,
      new_name: newName,
    });
    return response.data;
  },

  async toggleStar(fileId) {
    const response = await apiClient.post(`/files/${fileId}/star`);
    return response.data;
  },

  async softDelete(fileId) {
    const response = await apiClient.delete(`/files/${fileId}`);
    return response.data;
  },

  async restore(fileId) {
    const response = await apiClient.post(`/files/${fileId}/restore`);
    return response.data;
  },

  async permanentDelete(fileId) {
    const response = await apiClient.delete(`/files/${fileId}/permanent`);
    return response.data;
  },

  async listVersions(fileId) {
    const response = await apiClient.get(`/files/${fileId}/versions`);
    return response.data;
  },

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

  async listComments(fileId) {
    const response = await apiClient.get(`/files/${fileId}/comments`);
    return response.data;
  },

  async addComment(fileId, content) {
    const response = await apiClient.post(`/files/${fileId}/comments`, { content });
    return response.data;
  },

  async deleteComment(commentId) {
    const response = await apiClient.delete(`/files/comments/${commentId}`);
    return response.data;
  },

  async extractArchive(fileId, payload = {}) {
    const response = await apiClient.post(`/files/${fileId}/extract`, payload);
    return response.data;
  },

  async verifyChecksum(fileId) {
    const response = await apiClient.post(`/files/${fileId}/verify-checksum`);
    return response.data;
  },

  async searchFiles(query = '', params = {}) {
    const response = await apiClient.get('/files/search/query', {
      params: {
        query: query || undefined,
        ...params,
      },
    });
    return response.data?.items || [];
  },
};

export default fileService;

