/**
 * Multi-faceted search and filter API service client.
 */

import apiClient from './api';

export const searchService = {
  /**
   * Search files and folders with faceted filtering.
   * @param {Object} params - { q, type, mime_type, extension, min_size, max_size, folder_id, is_starred, sort_by, sort_order, page, page_size }
   */
  async search(params = {}) {
    const cleanParams = {};
    Object.keys(params).forEach((key) => {
      if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
        cleanParams[key] = params[key];
      }
    });

    const response = await apiClient.get('/search', { params: cleanParams });
    return response.data;
  },
};

export default searchService;
