import api from './api';

export const maintenanceService = {

  async cleanupOldTrash(olderThanDays = 30, dryRun = false) {
    const response = await api.post('/maintenance/cleanup-trash', {
      older_than_days: olderThanDays,
      dry_run: dryRun,
    });
    return response.data;
  },

  async cleanupExpiredLinks() {
    const response = await api.post('/maintenance/cleanup-expired-links');
    return response.data;
  },

  async syncStorageQuotas() {
    const response = await api.post('/maintenance/sync-storage');
    return response.data;
  },

  async getSystemStatus() {
    const response = await api.get('/maintenance/system-status');
    return response.data;
  },
};

export default maintenanceService;
