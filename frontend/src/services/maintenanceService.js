/**
 * System maintenance and diagnostics API service client.
 */

import api from './api';

export const maintenanceService = {
  /**
   * Purge soft-deleted items older than retention days threshold.
   * @param {number} olderThanDays - Threshold in days (default: 30)
   * @param {boolean} dryRun - Preview without permanently deleting (default: false)
   */
  async cleanupOldTrash(olderThanDays = 30, dryRun = false) {
    const response = await api.post('/maintenance/cleanup-trash', {
      older_than_days: olderThanDays,
      dry_run: dryRun,
    });
    return response.data;
  },

  /**
   * Deactivate public link shares that have passed their expiration timestamp.
   */
  async cleanupExpiredLinks() {
    const response = await api.post('/maintenance/cleanup-expired-links');
    return response.data;
  },

  /**
   * Recalculate storage metrics across all registered accounts.
   */
  async syncStorageQuotas() {
    const response = await api.post('/maintenance/sync-storage');
    return response.data;
  },

  /**
   * Retrieve system health diagnostics, telemetry, and platform stats.
   */
  async getSystemStatus() {
    const response = await api.get('/maintenance/system-status');
    return response.data;
  },
};

export default maintenanceService;
