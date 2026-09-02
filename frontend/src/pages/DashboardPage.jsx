/**
 * Dashboard "My Drive" root view with action bar and storage greeting.
 */

import React from 'react';
import useAuth from '../hooks/useAuth';
import {
  FolderPlus,
  UploadCloud,
  LayoutGrid,
  List,
  ArrowUpDown,
  FileText,
  Clock,
  Sparkles,
  ShieldCheck,
} from 'lucide-react';

export const DashboardPage = () => {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      {/* Top Banner / Welcome card */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-drive-600 via-drive-700 to-indigo-800 p-6 md:p-8 text-white shadow-soft">
        <div className="relative z-10 max-w-xl">
          <div className="inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-xs font-medium backdrop-blur-sm mb-3">
            <Sparkles className="h-3.5 w-3.5 text-amber-300" />
            <span>Cloud Storage Dashboard</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
            Welcome back, {user?.full_name || 'Drive User'}!
          </h1>
          <p className="mt-2 text-sm text-drive-100 leading-relaxed">
            Manage your files, organize documents with color tags, share folders with your team, and access your media from anywhere.
          </p>
        </div>

        {/* Decorative background circle */}
        <div className="absolute -right-10 -bottom-10 h-64 w-64 rounded-full bg-white/10 blur-2xl pointer-events-none" />
      </div>

      {/* Action Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div className="flex items-center gap-2">
          <h2 className="text-xl font-bold text-slate-800">My Drive</h2>
        </div>

        <div className="flex items-center gap-2">
          <button
            className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm"
            title="Create New Folder"
          >
            <FolderPlus className="h-4 w-4 text-drive-600" />
            <span>New Folder</span>
          </button>
          <button
            className="flex items-center gap-2 rounded-xl bg-drive-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-drive-700 transition-colors shadow-sm"
            title="Upload Files"
          >
            <UploadCloud className="h-4 w-4" />
            <span>Upload File</span>
          </button>
        </div>
      </div>

      {/* Empty State / Drive Placeholder */}
      <div className="flex flex-col items-center justify-center rounded-3xl border-2 border-dashed border-slate-200 bg-white p-12 text-center shadow-sm">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-drive-50 text-drive-600 mb-4">
          <UploadCloud className="h-8 w-8" />
        </div>
        <h3 className="text-base font-semibold text-slate-800">Welcome to your Cloud Drive</h3>
        <p className="mt-1.5 max-w-sm text-xs text-slate-500">
          Drag and drop files here to upload, or use the action buttons above to organize your cloud storage.
        </p>
        <div className="mt-6 flex items-center gap-2 text-xs text-slate-400">
          <ShieldCheck className="h-4 w-4 text-emerald-500" />
          <span>Encrypted with 256-bit AES storage security</span>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
