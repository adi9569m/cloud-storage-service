import apiClient from './api';

export const tagService = {

  async listTags() {
    const response = await apiClient.get('/tags');
    return response.data;
  },

  async createTag({ name, color = '#3B82F6' }) {
    const response = await apiClient.post('/tags', { name, color });
    return response.data;
  },

  async updateTag(tagId, { name = null, color = null }) {
    const response = await apiClient.put(`/tags/${tagId}`, { name, color });
    return response.data;
  },

  async deleteTag(tagId) {
    const response = await apiClient.delete(`/tags/${tagId}`);
    return response.data;
  },

  async attachTag({ tag_id, file_id = null, folder_id = null }) {
    const response = await apiClient.post('/tags/attach', {
      tag_id,
      file_id,
      folder_id,
    });
    return response.data;
  },

  async detachTag({ tag_id, file_id = null, folder_id = null }) {
    const response = await apiClient.post('/tags/detach', {
      tag_id,
      file_id,
      folder_id,
    });
    return response.data;
  },

  async getTaggedItems(tagId) {
    const response = await apiClient.get(`/tags/${tagId}/items`);
    return response.data;
  },

  async getFileTags(fileId) {
    const response = await apiClient.get(`/tags/items/file/${fileId}`);
    return response.data;
  },

  async getFolderTags(folderId) {
    const response = await apiClient.get(`/tags/items/folder/${folderId}`);
    return response.data;
  },
};

export default tagService;
