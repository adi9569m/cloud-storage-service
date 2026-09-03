/**
 * Activity audit logging API service client.
 */

import apiClient from './api';

export const activityService = {
  /**
   * List recent user activities with optional filters.
   */
  async listActivities({ resource_type = null, action = null, limit = 50, offset = 0 } = {}) {
    const params = { limit, offset };
    if (resource_type) params.resource_type = resource_type;
    if (action) params.action = action;

    const response = await apiClient.get('/activities', { params });
    return response.data;
  },

  /**
   * Get audit log history for a specific resource.
   */
  async getResourceActivities(resourceType, resourceId, { limit = 50, offset = 0 } = {}) {
    const response = await apiClient.get(`/activities/resource/${resourceType}/${resourceId}`, {
      params: { limit, offset },
    });
    return response.data;
  },
};

export default activityService;
