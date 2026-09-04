import React, { useState, useEffect } from 'react';
import storageService from '../services/storageService';
import {
  Cloud,
  HardDrive,
  RefreshCw,
  Image,
  FileText,
  Video,
  Music,
  Code2,
  Archive,
  FolderArchive,
  Loader2,
  CheckCircle2,
} from 'lucide-react';

export const StoragePage = () => {
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState('');

  const fetchStorageData = async () => {
    setIsLoading(true);
    try {
      const data = await storageService.getSummary();
      setSummary(data);
    } catch (err) {
      console.error('Failed to load storage summary:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStorageData();
  }, []);

  const handleRecalculate = async () => {
    setIsSyncing(true);
    setSyncMessage('');
    try {
      const result = await storageService.recalculate();
      setSyncMessage('Storage synchronized successfully.');
      await fetchStorageData();
    } catch (err) {
      console.error('Failed to recalculate storage:', err);
    } finally {
      setIsSyncing(false);
    }
  };

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-drive-600" />
      </div>
    );
  }

  const usedBytes = summary?.used_bytes || 0;
  const quotaBytes = summary?.quota_bytes || 5368709120;
  const usedPercent = summary?.used_percentage || 0;

  const categories = [
    { key: 'images', name: 'Images', icon: Image, color: 'bg-emerald-500', data: summary?.categories?.images },
    { key: 'documents', name: 'Documents', icon: FileText, color: 'bg-blue-500', data: summary?.categories?.documents },
    { key: 'videos', name: 'Videos', icon: Video, color: 'bg-rose-500', data: summary?.categories?.videos },
    { key: 'audio', name: 'Audio', icon: Music, color: 'bg-amber-500', data: summary?.categories?.audio },
    { key: 'code', name: 'Code & Scripts', icon: Code2, color: 'bg-indigo-500', data: summary?.categories?.code },
    { key: 'archives', name: 'Archives', icon: Archive, color: 'bg-purple-500', data: summary?.categories?.archives },
  ];

  return (
    <div className="space-y-6">

      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-800">Storage Overview</h1>
          <p className="text-xs text-slate-500 mt-1">
            Monitor cloud consumption, breakdown by file types, and manage quota.
          </p>
        </div>

        <button
          onClick={handleRecalculate}
          disabled={isSyncing}
          className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 text-drive-600 ${isSyncing ? 'animate-spin' : ''}`} />
          <span>{isSyncing ? 'Synchronizing...' : 'Recalculate Usage'}</span>
        </button>
      </div>

      {syncMessage && (
        <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-700">
          <CheckCircle2 className="h-4 w-4 text-emerald-600" />
          <span>{syncMessage}</span>
        </div>
      )}

      <div className="rounded-3xl border border-slate-200 bg-white p-6 md:p-8 shadow-soft">
        <div className="flex items-center gap-4 mb-6">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-drive-50 text-drive-600 shadow-sm">
            <Cloud className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-800">
              {formatBytes(usedBytes)} of {formatBytes(quotaBytes)} used
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              {usedPercent.toFixed(1)}% of your available storage quota utilized
            </p>
          </div>
        </div>

        <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100 flex">
          {categories.map((cat) => {
            const pct = cat.data?.percentage_of_used || 0;
            if (pct <= 0) return null;
            return (
              <div
                key={cat.key}
                className={`h-full ${cat.color} transition-all duration-300`}
                style={{ width: `${(pct * usedPercent) / 100}%` }}
                title={`${cat.name}: ${formatBytes(cat.data?.bytes || 0)}`}
              />
            );
          })}
        </div>

        <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          {categories.map((cat) => {
            const Icon = cat.icon;
            const bytes = cat.data?.bytes || 0;
            const count = cat.data?.count || 0;
            return (
              <div key={cat.key} className="rounded-2xl border border-slate-100 bg-slate-50 p-3.5">
                <div className="flex items-center gap-2 mb-2">
                  <div className={`h-2.5 w-2.5 rounded-full ${cat.color}`} />
                  <span className="text-xs font-semibold text-slate-700">{cat.name}</span>
                </div>
                <p className="text-sm font-bold text-slate-800">{formatBytes(bytes)}</p>
                <p className="text-xs text-slate-400 mt-0.5">{count} files</p>
              </div>
            );
          })}
        </div>
      </div>

      {summary?.largest_files && summary.largest_files.length > 0 && (
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <h3 className="text-base font-bold text-slate-800 mb-4">Largest Files Taking Storage</h3>
          <div className="divide-y divide-slate-100">
            {summary.largest_files.map((file) => (
              <div key={file.id} className="flex items-center justify-between py-3">
                <div className="flex items-center gap-3 overflow-hidden">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-100 text-slate-600 flex-shrink-0">
                    <FileText className="h-4 w-4" />
                  </div>
                  <div className="overflow-hidden">
                    <p className="truncate text-xs font-semibold text-slate-800">{file.name}</p>
                    <p className="text-xs text-slate-400">{file.mime_type}</p>
                  </div>
                </div>
                <span className="text-xs font-bold text-slate-700 flex-shrink-0">
                  {formatBytes(file.size_bytes)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default StoragePage;
