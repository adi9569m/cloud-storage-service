/**
 * Custom color tags and item labeling API service client.
 */

import apiClient from './api';

export const tagService = {
  /**
   * List all custom tags created by current user.
   */
  async listTags() {
    const response = await apiClient.get('/tags');
    return response.data;
  },

  /**
   * Create a new custom tag.
   */
  async createTag({ name, color = '#3B82F6' }) {
    const response = await apiClient.post('/tags', { name, color });
    return response.data;
  },

  /**
   * Update an existing tag.
   */
  async updateTag(tagId, { name = null, color = null }) {
    const response = await apiClient.put(`/tags/${tagId}`, { name, color });
    return response.data;
  },

  /**
   * Delete tag and unbind from all items.
   */
  async deleteTag(tagId) {
    const response = await apiClient.delete(`/tags/${tagId}`);
    return response.data;
  },

  /**
   * Attach a tag to a file or folder.
   */
  async attachTag({ tag_id, file_id = null, folder_id = null }) {
    const response = await apiClient.post('/tags/attach', {
      tag_id,
      file_id,
      folder_id,
    });
    return response.data;
  },

  /**
   * Detach a tag from a file or folder.
   */
  async detachTag({ tag_id, file_id = null, folder_id = null }) {
    const response = await apiClient.post('/tags/detach', {
      tag_id,
      file_id,
      folder_id,
    });
    return response.data;
  },

  /**
   * Get all files and folders attached to a tag.
   */
  async getTaggedItems(tagId) {
    const response = await apiClient.get(`/tags/${tagId}/items`);
    return response.data;
  },

  /**
   * Get all tags attached to a file.
   */
  async getFileTags(fileId) {
    const response = await apiClient.get(`/tags/items/file/${fileId}`);
    return response.data;
  },

  /**
   * Get all tags attached to a folder.
   */
  async getFolderTags(folderId) {
    const response = await apiClient.get(`/tags/items/folder/${folderId}`);
    return response.data;
  },
};

export default tagService;
