import apiClient from './api';

export const trashService = {

  async listTrash() {
    const response = await apiClient.get('/trash');
    return response.data;
  },

  async restoreAll() {
    const response = await apiClient.post('/trash/restore-all');
    return response.data;
  },

  async emptyTrash() {
    const response = await apiClient.delete('/trash/empty');
    return response.data;
  },
};

export default trashService;
