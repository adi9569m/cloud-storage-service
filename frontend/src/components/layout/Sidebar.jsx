/**
 * Collapsible Google Drive-style navigation sidebar with "+ New" action button
 * and dynamic storage meter widget.
 */

import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import useAuth from '../../hooks/useAuth';
import {
  HardDrive,
  Users,
  Star,
  Trash2,
  Tag,
  Cloud,
  Plus,
  FolderPlus,
  Upload,
} from 'lucide-react';

export const Sidebar = ({ isOpen, onClose, onNewFolder, onUploadFile }) => {
  const { user } = useAuth();

  const navItems = [
    { name: 'My Drive', path: '/', icon: HardDrive },
    { name: 'Shared with me', path: '/shared', icon: Users },
    { name: 'Starred', path: '/starred', icon: Star },
    { name: 'Trash', path: '/trash', icon: Trash2 },
    { name: 'Tags & Labels', path: '/tags', icon: Tag },
    { name: 'Storage', path: '/storage', icon: Cloud },
  ];

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const usedBytes = user?.storage_used_bytes || 0;
  const quotaBytes = 5 * 1024 * 1024 * 1024; // 5 GB
  const usedPercentage = Math.min(100, Math.round((usedBytes / quotaBytes) * 100));

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-sm md:hidden"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col justify-between border-r border-surface-border bg-white pt-16 transition-transform duration-300 md:static md:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col gap-6 p-4">
          {/* "+ New" Action Button */}
          <div className="relative group">
            <button
              className="flex items-center gap-3 rounded-2xl bg-white px-5 py-3.5 text-sm font-semibold text-slate-700 shadow-soft hover:bg-slate-50 hover:shadow-md transition-all focus:outline-none"
              onClick={onUploadFile}
            >
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-drive-600 text-white">
                <Plus className="h-4 w-4" />
              </div>
              <span>New</span>
            </button>
          </div>

          {/* Navigation Items */}
          <nav className="flex flex-col gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.name}
                  to={item.path}
                  onClick={onClose}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-full px-4 py-2.5 text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-drive-50 text-drive-700 font-semibold'
                        : 'text-slate-600 hover:bg-slate-100'
                    }`
                  }
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.name}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Bottom Storage Meter Widget */}
        <div className="p-4 border-t border-slate-100">
          <div className="rounded-2xl bg-slate-50 p-4">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-700 mb-2">
              <Cloud className="h-4 w-4 text-drive-600" />
              <span>Storage</span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200 mb-2">
              <div
                className="h-full bg-drive-600 rounded-full transition-all duration-300"
                style={{ width: `${Math.max(2, usedPercentage)}%` }}
              />
            </div>
            <p className="text-xs text-slate-500 mb-3">
              {formatBytes(usedBytes)} of {formatBytes(quotaBytes)} ({usedPercentage}%) used
            </p>
            <Link
              to="/storage"
              className="block w-full rounded-lg border border-slate-300 bg-white py-1.5 text-center text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors"
            >
              Storage details
            </Link>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
