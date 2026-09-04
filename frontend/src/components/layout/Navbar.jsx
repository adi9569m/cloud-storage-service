/**
 * Top application navigation header with global search and user avatar profile menu.
 */

import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import useAuth from '../../hooks/useAuth';
import {
  Search,
  Cloud,
  User as UserIcon,
  LogOut,
  Settings,
  HardDrive,
  Menu,
  SlidersHorizontal,
  Activity,
} from 'lucide-react';

export const Navbar = ({ onToggleSidebar }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const profileRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (profileRef.current && !profileRef.current.contains(event.target)) {
        setIsProfileOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-surface-border bg-white px-4">
      {/* Left branding and mobile menu toggle */}
      <div className="flex items-center gap-3 md:w-64">
        <button
          onClick={onToggleSidebar}
          className="rounded-full p-2 text-slate-600 hover:bg-slate-100 md:hidden focus:outline-none"
          title="Toggle Navigation"
        >
          <Menu className="h-5 w-5" />
        </button>
        <Link to="/" className="flex items-center gap-2.5 text-slate-800 hover:opacity-90 transition-opacity">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-drive-600 text-white shadow-sm">
            <Cloud className="h-5 w-5" />
          </div>
          <span className="text-lg font-semibold tracking-tight text-slate-800">Cloud Drive</span>
        </Link>
      </div>

      {/* Center search input */}
      <div className="flex-1 max-w-2xl px-2 md:px-6">
        <form onSubmit={handleSearchSubmit} className="relative w-full">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400">
            <Search className="h-4 w-4" />
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search in Drive..."
            className="w-full rounded-full border border-transparent bg-slate-100 py-2.5 pl-10 pr-10 text-sm text-slate-800 placeholder-slate-500 transition-all focus:border-drive-300 focus:bg-white focus:outline-none focus:ring-4 focus:ring-drive-100"
          />
          <button
            type="button"
            onClick={() => navigate('/search')}
            className="absolute inset-y-0 right-0 flex items-center pr-3.5 text-slate-400 hover:text-drive-600 transition-colors"
            title="Advanced Search & Filters"
          >
            <SlidersHorizontal className="h-4 w-4" />
          </button>
        </form>
      </div>

      {/* Right profile avatar and menu */}
      <div className="flex items-center gap-3">
        <div className="relative" ref={profileRef}>
          <button
            onClick={() => setIsProfileOpen(!isProfileOpen)}
            className="flex h-9 w-9 items-center justify-center rounded-full bg-drive-100 text-drive-700 font-semibold text-sm transition-transform hover:ring-2 hover:ring-drive-300 focus:outline-none"
            title="Account Menu"
          >
            {user?.full_name ? user.full_name.charAt(0).toUpperCase() : user?.email?.charAt(0).toUpperCase() || 'U'}
          </button>

          {/* Profile Dropdown */}
          {isProfileOpen && (
            <div className="absolute right-0 mt-2 w-72 rounded-2xl border border-slate-200 bg-white p-3 shadow-modal z-50 animate-in fade-in zoom-in-95 duration-100">
              <div className="flex items-center gap-3 border-b border-slate-100 pb-3 px-2">
                <div className="flex h-11 w-11 items-center justify-center rounded-full bg-drive-600 text-white font-bold text-base shadow-sm">
                  {user?.full_name ? user.full_name.charAt(0).toUpperCase() : user?.email?.charAt(0).toUpperCase() || 'U'}
                </div>
                <div className="overflow-hidden">
                  <p className="truncate text-sm font-semibold text-slate-800">
                    {user?.full_name || 'Drive User'}
                  </p>
                  <p className="truncate text-xs text-slate-500">{user?.email}</p>
                </div>
              </div>

              {/* Storage Info Snippet */}
              <div className="my-2 rounded-xl bg-slate-50 p-2.5">
                <div className="flex items-center justify-between text-xs text-slate-600 mb-1.5">
                  <span className="flex items-center gap-1 font-medium">
                    <HardDrive className="h-3.5 w-3.5 text-drive-600" /> Storage
                  </span>
                  <span>{formatBytes(user?.storage_used_bytes || 0)} of 5 GB</span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
                  <div
                    className="h-full bg-drive-600 rounded-full transition-all duration-300"
                    style={{
                      width: `${Math.min(100, Math.max(2, ((user?.storage_used_bytes || 0) / (5 * 1024 * 1024 * 1024)) * 100))}%`,
                    }}
                  />
                </div>
              </div>

              <div className="space-y-1">
                <Link
                  to="/storage"
                  onClick={() => setIsProfileOpen(false)}
                  className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs font-medium text-slate-700 hover:bg-slate-100 transition-colors"
                >
                  <HardDrive className="h-4 w-4 text-slate-500" />
                  Manage Storage
                </Link>
                <Link
                  to="/activity"
                  onClick={() => setIsProfileOpen(false)}
                  className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs font-medium text-slate-700 hover:bg-slate-100 transition-colors"
                >
                  <Activity className="h-4 w-4 text-slate-500" />
                  Activity Log
                </Link>
                <Link
                  to="/settings"
                  onClick={() => setIsProfileOpen(false)}
                  className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs font-medium text-slate-700 hover:bg-slate-100 transition-colors"
                >
                  <Settings className="h-4 w-4 text-slate-500" />
                  Account Settings
                </Link>
                <button
                  onClick={() => {
                    setIsProfileOpen(false);
                    logout();
                  }}
                  className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs font-medium text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut className="h-4 w-4 text-red-500" />
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
