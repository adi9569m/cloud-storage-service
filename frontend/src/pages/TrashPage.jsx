/**
 * Trash bin management page for restoring and permanently purging items.
 */

import React, { useState, useEffect } from 'react';
import {
  Trash2,
  RotateCcw,
  AlertTriangle,
  Folder,
  RefreshCw,
  Sparkles,
} from 'lucide-react';

import trashService from '../services/trashService';
import fileService from '../services/fileService';
import folderService from '../services/folderService';
import { formatBytes, formatDate, getFileIconDetails } from '../utils/formatters';

export const TrashPage = () => {
  const [trashData, setTrashData] = useState({ files: [], folders: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const loadTrash = async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await trashService.listTrash();
      setTrashData(data || { files: [], folders: [] });
    } catch (err) {
      setError('Failed to load trash items.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadTrash();
  }, []);

  const handleRestoreAll = async () => {
    if (window.confirm('Restore all items from Trash back to their original locations?')) {
      try {
        await trashService.restoreAll();
        setSuccessMessage('All items restored successfully!');
        loadTrash();
        setTimeout(() => setSuccessMessage(''), 3000);
      } catch (err) {
        setError('Failed to restore all trash items.');
      }
    }
  };

  const handleEmptyTrash = async () => {
    if (
      window.confirm(
        'Permanently delete all items in Trash? This action CANNOT be undone and storage will be reclaimed.'
      )
    ) {
      try {
        await trashService.emptyTrash();
        setSuccessMessage('Trash bin emptied successfully!');
        loadTrash();
        setTimeout(() => setSuccessMessage(''), 3000);
      } catch (err) {
        setError('Failed to empty trash.');
      }
    }
  };

  const handleRestoreItem = async (item, isFolder) => {
    try {
      if (isFolder) {
        await folderService.restore(item.id);
      } else {
        await fileService.restore(item.id);
      }
      loadTrash();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to restore item.');
    }
  };

  const handlePurgeItem = async (item, isFolder) => {
    if (
      window.confirm(
        `Permanently delete "${item.name}"? This action cannot be undone.`
      )
    ) {
      try {
        if (isFolder) {
          await folderService.permanentDelete(item.id);
        } else {
          await fileService.permanentDelete(item.id);
        }
        loadTrash();
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to permanently delete item.');
      }
    }
  };

  const folders = trashData.folders || [];
  const files = trashData.files || [];
  const isEmpty = folders.length === 0 && files.length === 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 border-b border-slate-200 pb-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-800">Trash Bin</h1>
          <p className="text-xs text-slate-500 mt-1">
            Items in trash are automatically purged permanently after 30 days.
          </p>
        </div>

        {!isEmpty && (
          <div className="flex items-center gap-2.5">
            <button
              onClick={handleRestoreAll}
              className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm"
            >
              <RotateCcw className="h-3.5 w-3.5 text-drive-600" />
              <span>Restore All</span>
            </button>
            <button
              onClick={handleEmptyTrash}
              className="flex items-center gap-1.5 rounded-xl bg-rose-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-rose-700 transition-colors shadow-sm"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>Empty Trash</span>
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="rounded-2xl bg-red-50 p-4 text-xs text-red-600 border border-red-200">
          {error}
        </div>
      )}

      {successMessage && (
        <div className="rounded-2xl bg-emerald-50 p-4 text-xs text-emerald-700 border border-emerald-200">
          {successMessage}
        </div>
      )}

      {/* Content */}
      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <RefreshCw className="h-8 w-8 animate-spin text-drive-600" />
        </div>
      ) : isEmpty ? (
        <div className="flex flex-col items-center justify-center rounded-3xl border-2 border-dashed border-slate-200 bg-white p-12 text-center shadow-sm">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-rose-50 text-rose-500 mb-4">
            <Trash2 className="h-8 w-8" />
          </div>
          <h3 className="text-base font-semibold text-slate-800">Trash is empty</h3>
          <p className="mt-1.5 max-w-sm text-xs text-slate-500">
            Items moved to the trash will appear here for recovery before automatic 30-day purging.
          </p>
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden divide-y divide-slate-100">
          <div className="grid grid-cols-12 bg-slate-50 px-4 py-3 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
            <div className="col-span-6 sm:col-span-6">Name</div>
            <div className="col-span-3 sm:col-span-3">Deleted Date</div>
            <div className="col-span-3 sm:col-span-3 text-right">Actions</div>
          </div>

          {/* Trashed Folders */}
          {folders.map((folder) => (
            <div
              key={folder.id}
              className="grid grid-cols-12 items-center px-4 py-3 text-xs hover:bg-slate-50 transition-colors"
            >
              <div className="col-span-6 sm:col-span-6 flex items-center gap-3 overflow-hidden">
                <Folder className="h-5 w-5 shrink-0 text-slate-400" />
                <span className="truncate font-semibold text-slate-700" title={folder.name}>
                  {folder.name}
                </span>
              </div>
              <div className="col-span-3 sm:col-span-3 text-[11px] text-slate-400">
                {formatDate(folder.deleted_at || folder.updated_at)}
              </div>
              <div className="col-span-3 sm:col-span-3 flex items-center justify-end gap-2">
                <button
                  onClick={() => handleRestoreItem(folder, true)}
                  className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-xs"
                  title="Restore"
                >
                  <RotateCcw className="h-3.5 w-3.5 text-drive-600" />
                  <span className="hidden sm:inline">Restore</span>
                </button>
                <button
                  onClick={() => handlePurgeItem(folder, true)}
                  className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition-colors"
                  title="Delete Permanently"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}

          {/* Trashed Files */}
          {files.map((file) => {
            const { icon: Icon, color, bg } = getFileIconDetails(file.mime_type, file.name);
            return (
              <div
                key={file.id}
                className="grid grid-cols-12 items-center px-4 py-3 text-xs hover:bg-slate-50 transition-colors"
              >
                <div className="col-span-6 sm:col-span-6 flex items-center gap-3 overflow-hidden">
                  <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${bg} ${color}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="overflow-hidden">
                    <p className="truncate font-medium text-slate-700" title={file.name}>
                      {file.name}
                    </p>
                    <span className="text-[11px] text-slate-400">{formatBytes(file.size_bytes)}</span>
                  </div>
                </div>

                <div className="col-span-3 sm:col-span-3 text-[11px] text-slate-400">
                  {formatDate(file.deleted_at || file.updated_at)}
                </div>

                <div className="col-span-3 sm:col-span-3 flex items-center justify-end gap-2">
                  <button
                    onClick={() => handleRestoreItem(file, false)}
                    className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-xs"
                    title="Restore"
                  >
                    <RotateCcw className="h-3.5 w-3.5 text-drive-600" />
                    <span className="hidden sm:inline">Restore</span>
                  </button>
                  <button
                    onClick={() => handlePurgeItem(file, false)}
                    className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition-colors"
                    title="Delete Permanently"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default TrashPage;
