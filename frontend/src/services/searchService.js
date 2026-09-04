import apiClient from './api';

export const searchService = {

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
