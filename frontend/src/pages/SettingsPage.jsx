/**
 * Account Settings, Profile Management, Security, and System Maintenance Hub.
 */

import React, { useState, useEffect } from 'react';
import useAuth from '../hooks/useAuth';
import authService from '../services/authService';
import storageService from '../services/storageService';
import maintenanceService from '../services/maintenanceService';
import { useToast } from '../context/ToastContext';
import { formatBytes, formatDate } from '../utils/formatters';

import {
  User,
  Shield,
  HardDrive,
  Wrench,
  KeyRound,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Server,
  Cloud,
  Trash2,
  Link,
  Activity,
  Calendar,
  Mail,
  Loader2,
  Sparkles,
} from 'lucide-react';

export const SettingsPage = () => {
  const { user, updateUser, refreshSession } = useAuth();
  const toast = useToast();

  const [activeTab, setActiveTab] = useState('profile');

  // Profile form state
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url || '');
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);

  // Password change state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  // Storage summary state
  const [storageData, setStorageData] = useState(null);
  const [isLoadingStorage, setIsLoadingStorage] = useState(false);
  const [isSyncingStorage, setIsSyncingStorage] = useState(false);

  // System maintenance state
  const [systemStatus, setSystemStatus] = useState(null);
  const [isLoadingStatus, setIsLoadingStatus] = useState(false);
  const [retentionDays, setRetentionDays] = useState(30);
  const [dryRun, setDryRun] = useState(false);
  const [isExecutingTask, setIsExecutingTask] = useState(false);
  const [taskResult, setTaskResult] = useState(null);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || '');
      setAvatarUrl(user.avatar_url || '');
    }
  }, [user]);

  // Load storage details when storage tab is clicked
  useEffect(() => {
    if (activeTab === 'storage' && !storageData) {
      loadStorageSummary();
    }
  }, [activeTab]);

  // Load system status when maintenance tab is clicked
  useEffect(() => {
    if (activeTab === 'maintenance' && !systemStatus) {
      loadSystemStatus();
    }
  }, [activeTab]);

  const loadStorageSummary = async () => {
    setIsLoadingStorage(true);
    try {
      const data = await storageService.getSummary();
      setStorageData(data);
    } catch (err) {
      console.error(err);
      toast.error('Failed to load storage details');
    } finally {
      setIsLoadingStorage(false);
    }
  };

  const loadSystemStatus = async () => {
    setIsLoadingStatus(true);
    try {
      const data = await maintenanceService.getSystemStatus();
      setSystemStatus(data);
    } catch (err) {
      console.error(err);
      toast.error('Failed to load system diagnostics');
    } finally {
      setIsLoadingStatus(false);
    }
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setIsUpdatingProfile(true);
    try {
      const updated = await authService.updateProfile({
        full_name: fullName.trim() || null,
        avatar_url: avatarUrl.trim() || null,
      });
      updateUser(updated);
      toast.success('Profile updated successfully');
    } catch (err) {
      console.error(err);
      toast.error('Failed to update profile');
    } finally {
      setIsUpdatingProfile(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }
    if (newPassword.length < 8) {
      toast.error('Password must be at least 8 characters long');
      return;
    }

    setIsChangingPassword(true);
    try {
      await authService.changePassword(currentPassword, newPassword);
      toast.success('Password changed successfully');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      console.error(err);
      toast.error(err.response?.data?.detail || 'Failed to change password');
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleRecalculateStorage = async () => {
    setIsSyncingStorage(true);
    try {
      await storageService.recalculate();
      toast.success('Storage recalculated and synchronized');
      await loadStorageSummary();
      await refreshSession();
    } catch (err) {
      console.error(err);
      toast.error('Failed to recalculate storage');
    } finally {
      setIsSyncingStorage(false);
    }
  };

  const handleCleanupTrash = async () => {
    setIsExecutingTask(true);
    setTaskResult(null);
    try {
      const res = await maintenanceService.cleanupOldTrash(retentionDays, dryRun);
      setTaskResult({
        title: dryRun ? 'Trash Purge Simulation Result' : 'Trash Cleanup Result',
        details: `${res.files_deleted} files and ${res.folders_deleted} folders purged. Reclaimed ${formatBytes(res.bytes_reclaimed || 0)}.`,
      });
      toast.success(dryRun ? 'Simulation complete' : 'Trash cleaned successfully');
      loadSystemStatus();
    } catch (err) {
      console.error(err);
      toast.error('Failed to run trash cleanup');
    } finally {
      setIsExecutingTask(false);
    }
  };

  const handleCleanupExpiredLinks = async () => {
    setIsExecutingTask(true);
    setTaskResult(null);
    try {
      const res = await maintenanceService.cleanupExpiredLinks();
      setTaskResult({
        title: 'Expired Links Cleanup Result',
        details: `Deactivated ${res.expired_links_deactivated} expired public share links.`,
      });
      toast.success(`Deactivated ${res.expired_links_deactivated} expired links`);
      loadSystemStatus();
    } catch (err) {
      console.error(err);
      toast.error('Failed to clean expired links');
    } finally {
      setIsExecutingTask(false);
    }
  };

  const handleSyncAllStorage = async () => {
    setIsExecutingTask(true);
    setTaskResult(null);
    try {
      const res = await maintenanceService.syncStorageQuotas();
      setTaskResult({
        title: 'System Storage Sync Result',
        details: `Synchronized storage quotas across ${res.users_processed} user accounts.`,
      });
      toast.success('System storage synced');
      loadSystemStatus();
    } catch (err) {
      console.error(err);
      toast.error('Failed to sync system storage');
    } finally {
      setIsExecutingTask(false);
    }
  };

  const tabs = [
    { id: 'profile', label: 'Profile & Account', icon: User },
    { id: 'security', label: 'Security & Password', icon: Shield },
    { id: 'storage', label: 'Storage & Usage', icon: HardDrive },
    { id: 'maintenance', label: 'System Diagnostics', icon: Wrench },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-slate-200 pb-4">
        <h1 className="text-2xl font-bold tracking-tight text-slate-800">Settings & Preferences</h1>
        <p className="text-xs text-slate-500 mt-1">
          Manage your personal account, login security, storage quota, and system diagnostics.
        </p>
      </div>

      {/* Settings Navigation Tabs */}
      <div className="flex border-b border-slate-200 gap-2 overflow-x-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 border-b-2 px-4 py-3 text-xs font-semibold whitespace-nowrap transition-colors ${
                isActive
                  ? 'border-drive-600 text-drive-700 bg-drive-50/50 rounded-t-xl'
                  : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded-t-xl'
              }`}
            >
              <Icon className="h-4 w-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* TAB CONTENT: Profile */}
      {activeTab === 'profile' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
            <h3 className="text-base font-bold text-slate-800 mb-4">Personal Details</h3>
            <form onSubmit={handleUpdateProfile} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Email Address
                </label>
                <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-500">
                  <Mail className="h-4 w-4 text-slate-400" />
                  <span>{user?.email}</span>
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  Email address is permanently associated with your authentication credentials.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Full Name / Display Name
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Jane Doe"
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 placeholder-slate-400 focus:border-drive-500 focus:outline-none focus:ring-2 focus:ring-drive-100"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Avatar Image URL (Optional)
                </label>
                <input
                  type="url"
                  value={avatarUrl}
                  onChange={(e) => setAvatarUrl(e.target.value)}
                  placeholder="https://example.com/avatar.png"
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 placeholder-slate-400 focus:border-drive-500 focus:outline-none focus:ring-2 focus:ring-drive-100"
                />
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isUpdatingProfile}
                  className="flex items-center gap-2 rounded-xl bg-drive-600 px-5 py-2.5 text-xs font-semibold text-white hover:bg-drive-700 transition-colors shadow-sm disabled:opacity-50"
                >
                  {isUpdatingProfile && <Loader2 className="h-4 w-4 animate-spin" />}
                  <span>Save Changes</span>
                </button>
              </div>
            </form>
          </div>

          {/* Account Summary Card */}
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft space-y-4">
            <h3 className="text-base font-bold text-slate-800">Account Overview</h3>
            <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-drive-600 text-white font-bold text-lg shadow-sm">
                {user?.full_name ? user.full_name.charAt(0).toUpperCase() : user?.email?.charAt(0).toUpperCase() || 'U'}
              </div>
              <div className="overflow-hidden">
                <p className="truncate text-sm font-bold text-slate-800">
                  {user?.full_name || 'Drive User'}
                </p>
                <p className="truncate text-xs text-slate-400">{user?.email}</p>
              </div>
            </div>

            <div className="space-y-2.5 text-xs text-slate-600">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-slate-500">
                  <Calendar className="h-3.5 w-3.5" /> Member Since
                </span>
                <span className="font-semibold text-slate-800">
                  {formatDate(user?.created_at)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-slate-500">
                  <Shield className="h-3.5 w-3.5" /> Account Status
                </span>
                <span className="inline-flex items-center gap-1 font-semibold text-emerald-600">
                  <CheckCircle2 className="h-3.5 w-3.5" /> Active
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-slate-500">
                  <HardDrive className="h-3.5 w-3.5" /> Quota Limit
                </span>
                <span className="font-semibold text-slate-800">5.00 GB</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT: Security */}
      {activeTab === 'security' && (
        <div className="max-w-2xl rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <h3 className="text-base font-bold text-slate-800 mb-2">Change Password</h3>
          <p className="text-xs text-slate-500 mb-6">
            Ensure your account uses a strong, unique password with at least 8 characters.
          </p>

          <form onSubmit={handleChangePassword} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Current Password
              </label>
              <input
                type="password"
                required
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="Enter current password"
                className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 placeholder-slate-400 focus:border-drive-500 focus:outline-none focus:ring-2 focus:ring-drive-100"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                New Password
              </label>
              <input
                type="password"
                required
                minLength={8}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new password (min. 8 characters)"
                className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 placeholder-slate-400 focus:border-drive-500 focus:outline-none focus:ring-2 focus:ring-drive-100"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Confirm New Password
              </label>
              <input
                type="password"
                required
                minLength={8}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter new password"
                className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 placeholder-slate-400 focus:border-drive-500 focus:outline-none focus:ring-2 focus:ring-drive-100"
              />
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={isChangingPassword}
                className="flex items-center gap-2 rounded-xl bg-drive-600 px-5 py-2.5 text-xs font-semibold text-white hover:bg-drive-700 transition-colors shadow-sm disabled:opacity-50"
              >
                {isChangingPassword && <Loader2 className="h-4 w-4 animate-spin" />}
                <span>Update Password</span>
              </button>
            </div>
          </form>
        </div>
      )}

      {/* TAB CONTENT: Storage */}
      {activeTab === 'storage' && (
        <div className="space-y-6">
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
            <div className="flex items-center justify-between gap-4 mb-6">
              <div>
                <h3 className="text-base font-bold text-slate-800">Storage Allocation</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  {formatBytes(user?.storage_used_bytes || 0)} used of 5 GB available quota
                </p>
              </div>

              <button
                onClick={handleRecalculateStorage}
                disabled={isSyncingStorage}
                className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 text-drive-600 ${isSyncingStorage ? 'animate-spin' : ''}`} />
                <span>{isSyncingStorage ? 'Syncing...' : 'Recalculate'}</span>
              </button>
            </div>

            <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full bg-drive-600 rounded-full transition-all duration-300"
                style={{
                  width: `${Math.min(100, Math.max(2, ((user?.storage_used_bytes || 0) / (5 * 1024 * 1024 * 1024)) * 100))}%`,
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT: System Maintenance */}
      {activeTab === 'maintenance' && (
        <div className="space-y-6">
          {/* Diagnostics Telemetry Card */}
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2.5">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-drive-50 text-drive-600">
                  <Server className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-800">System Telemetry & Health</h3>
                  <p className="text-xs text-slate-500">Live operational status and platform metrics</p>
                </div>
              </div>

              <button
                onClick={loadSystemStatus}
                disabled={isLoadingStatus}
                className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm disabled:opacity-50"
              >
                <RefreshCw className={`h-3.5 w-3.5 text-drive-600 ${isLoadingStatus ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </button>
            </div>

            {isLoadingStatus ? (
              <div className="flex h-32 items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-drive-600" />
              </div>
            ) : systemStatus ? (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4">
                <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
                  <span className="text-xs font-medium text-slate-500">Service Status</span>
                  <p className="text-sm font-bold text-emerald-600 mt-1 flex items-center gap-1.5">
                    <CheckCircle2 className="h-4 w-4" /> Healthy
                  </p>
                </div>
                <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
                  <span className="text-xs font-medium text-slate-500">Registered Users</span>
                  <p className="text-sm font-bold text-slate-800 mt-1">
                    {systemStatus.total_users || 0}
                  </p>
                </div>
                <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
                  <span className="text-xs font-medium text-slate-500">Total Files</span>
                  <p className="text-sm font-bold text-slate-800 mt-1">
                    {systemStatus.total_files || 0}
                  </p>
                </div>
                <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
                  <span className="text-xs font-medium text-slate-500">Total Storage</span>
                  <p className="text-sm font-bold text-slate-800 mt-1">
                    {formatBytes(systemStatus.total_bytes_stored || 0)}
                  </p>
                </div>
              </div>
            ) : null}
          </div>

          {/* Maintenance Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Trash Cleanup */}
            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2.5 mb-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-rose-50 text-rose-600">
                    <Trash2 className="h-4 w-4" />
                  </div>
                  <h4 className="text-sm font-bold text-slate-800">Automated Trash Purge</h4>
                </div>
                <p className="text-xs text-slate-500 mb-4">
                  Permanently purge soft-deleted files and folders older than the specified retention threshold.
                </p>

                <div className="space-y-3 mb-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Retention Threshold: {retentionDays} days
                    </label>
                    <input
                      type="range"
                      min={1}
                      max={90}
                      value={retentionDays}
                      onChange={(e) => setRetentionDays(parseInt(e.target.value, 10))}
                      className="w-full accent-drive-600 cursor-pointer"
                    />
                  </div>

                  <label className="flex items-center gap-2 text-xs font-medium text-slate-700 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={dryRun}
                      onChange={(e) => setDryRun(e.target.checked)}
                      className="rounded border-slate-300 text-drive-600 focus:ring-drive-500"
                    />
                    <span>Dry run simulation only (no permanent deletions)</span>
                  </label>
                </div>
              </div>

              <button
                onClick={handleCleanupTrash}
                disabled={isExecutingTask}
                className="flex items-center justify-center gap-2 rounded-xl border border-rose-200 bg-rose-50 py-2.5 text-xs font-semibold text-rose-700 hover:bg-rose-100 transition-colors disabled:opacity-50"
              >
                {isExecutingTask && <Loader2 className="h-4 w-4 animate-spin" />}
                <span>Execute Trash Purge</span>
              </button>
            </div>

            {/* Expired Links & Global Sync */}
            <div className="space-y-4">
              <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
                <div className="flex items-center gap-2.5 mb-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-cyan-50 text-cyan-600">
                    <Link className="h-4 w-4" />
                  </div>
                  <h4 className="text-sm font-bold text-slate-800">Deactivate Expired Links</h4>
                </div>
                <p className="text-xs text-slate-500 mb-4">
                  Scan and deactivate public link shares that have passed their expiration timestamp.
                </p>
                <button
                  onClick={handleCleanupExpiredLinks}
                  disabled={isExecutingTask}
                  className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-slate-50 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-colors disabled:opacity-50"
                >
                  {isExecutingTask && <Loader2 className="h-4 w-4 animate-spin" />}
                  <span>Cleanup Expired Share Links</span>
                </button>
              </div>

              <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
                <div className="flex items-center gap-2.5 mb-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-purple-50 text-purple-600">
                    <HardDrive className="h-4 w-4" />
                  </div>
                  <h4 className="text-sm font-bold text-slate-800">Sync All User Quotas</h4>
                </div>
                <p className="text-xs text-slate-500 mb-4">
                  Recalculate cumulative storage allocations for all registered accounts.
                </p>
                <button
                  onClick={handleSyncAllStorage}
                  disabled={isExecutingTask}
                  className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-slate-50 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-colors disabled:opacity-50"
                >
                  {isExecutingTask && <Loader2 className="h-4 w-4 animate-spin" />}
                  <span>Global Storage Quota Sync</span>
                </button>
              </div>
            </div>
          </div>

          {/* Task Result Summary */}
          {taskResult && (
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-xs text-emerald-800 animate-in fade-in duration-200">
              <p className="font-bold mb-0.5">{taskResult.title}</p>
              <p className="opacity-90">{taskResult.details}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SettingsPage;
