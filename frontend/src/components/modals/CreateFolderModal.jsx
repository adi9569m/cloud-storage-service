import React, { useState } from 'react';
import { X, FolderPlus, Palette } from 'lucide-react';
import folderService from '../../services/folderService';

const COLOR_OPTIONS = [
  { name: 'Default Blue', hex: '#3B82F6', bg: 'bg-blue-500' },
  { name: 'Emerald Green', hex: '#10B981', bg: 'bg-emerald-500' },
  { name: 'Amber Orange', hex: '#F59E0B', bg: 'bg-amber-500' },
  { name: 'Rose Red', hex: '#F43F5E', bg: 'bg-rose-500' },
  { name: 'Purple', hex: '#8B5CF6', bg: 'bg-purple-500' },
  { name: 'Indigo', hex: '#6366F1', bg: 'bg-indigo-500' },
  { name: 'Slate Gray', hex: '#64748B', bg: 'bg-slate-500' },
  { name: 'Cyan', hex: '#06B6D4', bg: 'bg-cyan-500' },
];

export const CreateFolderModal = ({ isOpen, onClose, parentId = null, onSuccess }) => {
  const [folderName, setFolderName] = useState('');
  const [selectedColor, setSelectedColor] = useState('#3B82F6');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!folderName.trim()) {
      setError('Folder name cannot be empty');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      await folderService.createFolder({
        name: folderName.trim(),
        parent_id: parentId,
        color: selectedColor,
      });
      setFolderName('');
      setSelectedColor('#3B82F6');
      onSuccess?.();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create folder. Name may already exist.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-modal transition-all animate-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-drive-50 text-drive-600">
              <FolderPlus className="h-5 w-5" />
            </div>
            <h3 className="text-base font-semibold text-slate-800">New Folder</h3>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 focus:outline-none"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          {error && (
            <div className="rounded-xl bg-red-50 p-3 text-xs text-red-600 border border-red-200">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Folder Name
            </label>
            <input
              type="text"
              autoFocus
              value={folderName}
              onChange={(e) => setFolderName(e.target.value)}
              placeholder="e.g. Project Documents"
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:border-drive-500 focus:bg-white focus:outline-none focus:ring-4 focus:ring-drive-100"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-2 flex items-center gap-1.5">
              <Palette className="h-3.5 w-3.5 text-slate-500" />
              Folder Color
            </label>
            <div className="flex flex-wrap items-center gap-2.5">
              {COLOR_OPTIONS.map((color) => (
                <button
                  key={color.hex}
                  type="button"
                  onClick={() => setSelectedColor(color.hex)}
                  title={color.name}
                  className={`h-7 w-7 rounded-full ${color.bg} transition-transform focus:outline-none ${
                    selectedColor === color.hex
                      ? 'ring-4 ring-slate-300 scale-110'
                      : 'hover:scale-105 opacity-80 hover:opacity-100'
                  }`}
                />
              ))}
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !folderName.trim()}
              className="rounded-xl bg-drive-600 px-5 py-2 text-xs font-semibold text-white hover:bg-drive-700 disabled:opacity-50 transition-colors shadow-sm"
            >
              {isSubmitting ? 'Creating...' : 'Create Folder'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateFolderModal;
