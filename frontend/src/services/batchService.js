/**
 * Batch operations API service client for bulk moves, copies, deletions,
 * starring, and ZIP downloads.
 */

import apiClient from './api';

export const batchService = {
  /**
   * Bulk soft-delete items to trash.
   */
  async batchDelete({ file_ids = [], folder_ids = [] }) {
    const response = await apiClient.post('/batch/delete', {
      file_ids,
      folder_ids,
    });
    return response.data;
  },

  /**
   * Bulk restore items from trash.
   */
  async batchRestore({ file_ids = [], folder_ids = [] }) {
    const response = await apiClient.post('/batch/restore', {
      file_ids,
      folder_ids,
    });
    return response.data;
  },

  /**
   * Bulk permanently purge items.
   */
  async batchPurge({ file_ids = [], folder_ids = [] }) {
    const response = await apiClient.post('/batch/purge', {
      file_ids,
      folder_ids,
    });
    return response.data;
  },

  /**
   * Bulk move items to target destination folder.
   */
  async batchMove({ file_ids = [], folder_ids = [], destination_folder_id = null }) {
    const response = await apiClient.post('/batch/move', {
      file_ids,
      folder_ids,
      destination_folder_id,
    });
    return response.data;
  },

  /**
   * Bulk duplicate files to target destination folder.
   */
  async batchCopy({ file_ids = [], destination_folder_id = null }) {
    const response = await apiClient.post('/batch/copy', {
      file_ids,
      destination_folder_id,
    });
    return response.data;
  },

  /**
   * Bulk star or unstar files and folders.
   */
  async batchStar({ file_ids = [], folder_ids = [], is_starred = true }) {
    const response = await apiClient.post('/batch/star', {
      file_ids,
      folder_ids,
      is_starred,
    });
    return response.data;
  },

  /**
   * Download multiple files and folders packed into a ZIP archive.
   */
  async batchDownloadZip({ file_ids = [], folder_ids = [] }, archiveName = 'archive.zip') {
    const response = await apiClient.post(
      '/batch/download',
      {
        file_ids,
        folder_ids,
      },
      {
        responseType: 'blob',
      }
    );

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', archiveName);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};

export default batchService;
