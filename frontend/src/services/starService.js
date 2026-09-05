import apiClient from './api';

export const starService = {

  async listStarred() {
    const response = await apiClient.get('/stars');
    return response.data;
  },

  async toggleStar({ file_id = null, folder_id = null }) {
    const response = await apiClient.post('/stars/toggle', {
      file_id,
      folder_id,
    });
    return response.data;
  },

  async starItem({ file_id = null, folder_id = null }) {
    return this.toggleStar({ file_id, folder_id });
  },

  async unstarItem({ file_id = null, folder_id = null }) {
    return this.toggleStar({ file_id, folder_id });
  },
};

export default starService;

