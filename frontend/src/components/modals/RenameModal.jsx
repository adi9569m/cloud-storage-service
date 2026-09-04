import React, { useState, useEffect } from 'react';
import { X, Edit2 } from 'lucide-react';
import fileService from '../../services/fileService';
import folderService from '../../services/folderService';

export const RenameModal = ({
  isOpen,
  onClose,
  item,
  isFolder = false,
  onSuccess,
}) => {
  const [newName, setNewName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen && item) {
      setNewName(item.name || '');
      setError('');
    }
  }, [isOpen, item]);

  if (!isOpen || !item) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newName.trim()) {
      setError('Name cannot be empty.');
      return;
    }

    if (newName.trim() === item.name) {
      onClose();
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      if (isFolder) {
        await folderService.updateFolder(item.id, { name: newName.trim() });
      } else {
        await fileService.rename(item.id, newName.trim());
      }
      onSuccess?.();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to rename item.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-modal transition-all animate-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-drive-50 text-drive-600">
              <Edit2 className="h-4 w-4" />
            </div>
            <h3 className="text-sm font-semibold text-slate-800">
              Rename {isFolder ? 'Folder' : 'File'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 focus:outline-none"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {error && (
            <div className="rounded-xl bg-red-50 p-2.5 text-xs text-red-600 border border-red-200">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              New Name
            </label>
            <input
              type="text"
              autoFocus
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs text-slate-800 placeholder-slate-400 focus:border-drive-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-drive-100"
            />
          </div>

          <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl px-3.5 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !newName.trim()}
              className="rounded-xl bg-drive-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-drive-700 disabled:opacity-50 transition-colors shadow-sm"
            >
              {isSubmitting ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RenameModal;
