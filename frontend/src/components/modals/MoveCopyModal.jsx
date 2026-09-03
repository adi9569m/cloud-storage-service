/**
 * Modal to move or copy files/folders to a destination folder chosen from the directory tree.
 */

import React, { useState, useEffect } from 'react';
import { X, Folder, FolderTree, ChevronRight, Check, HardDrive } from 'lucide-react';
import folderService from '../../services/folderService';
import fileService from '../../services/fileService';

export const MoveCopyModal = ({
  isOpen,
  onClose,
  item,
  isFolder = false,
  mode = 'move', // 'move' | 'copy'
  onSuccess,
}) => {
  const [folderTree, setFolderTree] = useState([]);
  const [selectedFolderId, setSelectedFolderId] = useState(null); // null means Root
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadFolderTree();
      setSelectedFolderId(null);
    }
  }, [isOpen]);

  if (!isOpen || !item) return null;

  const loadFolderTree = async () => {
    setIsLoading(true);
    setError('');
    try {
      const tree = await folderService.getFolderTree();
      setFolderTree(tree || []);
    } catch (err) {
      setError('Failed to load folder hierarchy.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExecute = async () => {
    setIsSubmitting(true);
    setError('');

    try {
      if (mode === 'move') {
        if (isFolder) {
          await folderService.moveFolder(item.id, selectedFolderId);
        } else {
          await fileService.move(item.id, selectedFolderId);
        }
      } else {
        // Copy mode (files only supported by copy endpoint)
        if (!isFolder) {
          await fileService.copy(item.id, selectedFolderId, `Copy of ${item.name}`);
        }
      }
      onSuccess?.();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || `Failed to ${mode} item.`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderTreeNodes = (nodes, depth = 0) => {
    return nodes.map((node) => {
      // Don't allow moving folder into itself
      if (isFolder && node.id === item.id) return null;

      const isSelected = selectedFolderId === node.id;

      return (
        <React.Fragment key={node.id}>
          <button
            type="button"
            onClick={() => setSelectedFolderId(node.id)}
            style={{ paddingLeft: `${(depth + 1) * 16}px` }}
            className={`flex w-full items-center justify-between py-2 pr-3 text-xs rounded-xl transition-colors ${
              isSelected
                ? 'bg-drive-50 text-drive-700 font-semibold'
                : 'text-slate-700 hover:bg-slate-50'
            }`}
          >
            <div className="flex items-center gap-2 truncate">
              <Folder
                className="h-4 w-4 shrink-0"
                style={{ color: node.color || '#3B82F6' }}
              />
              <span className="truncate">{node.name}</span>
            </div>
            {isSelected && <Check className="h-4 w-4 text-drive-600" />}
          </button>
          {node.children && node.children.length > 0 && renderTreeNodes(node.children, depth + 1)}
        </React.Fragment>
      );
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-modal transition-all animate-in zoom-in-95 duration-150 flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-drive-50 text-drive-600">
              <FolderTree className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-800 capitalize">
                {mode} "{item.name}"
              </h3>
              <p className="text-xs text-slate-500">Select target destination</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 focus:outline-none"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {error && (
          <div className="mt-3 rounded-xl bg-red-50 p-2.5 text-xs text-red-600 border border-red-200">
            {error}
          </div>
        )}

        {/* Folder Directory Browser */}
        <div className="mt-4 flex-1 overflow-y-auto space-y-1 rounded-xl border border-slate-200 bg-slate-50/50 p-2">
          {/* Root Directory Button */}
          <button
            type="button"
            onClick={() => setSelectedFolderId(null)}
            className={`flex w-full items-center justify-between py-2 px-3 text-xs rounded-xl transition-colors ${
              selectedFolderId === null
                ? 'bg-drive-50 text-drive-700 font-semibold'
                : 'text-slate-700 hover:bg-slate-50'
            }`}
          >
            <div className="flex items-center gap-2">
              <HardDrive className="h-4 w-4 text-drive-600" />
              <span>My Drive (Root level)</span>
            </div>
            {selectedFolderId === null && <Check className="h-4 w-4 text-drive-600" />}
          </button>

          {/* Hierarchical Subfolders */}
          {isLoading ? (
            <p className="text-xs text-slate-400 py-4 text-center">Loading directories...</p>
          ) : (
            renderTreeNodes(folderTree)
          )}
        </div>

        {/* Footer */}
        <div className="mt-5 flex items-center justify-end gap-3 border-t border-slate-100 pt-4">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleExecute}
            disabled={isSubmitting}
            className="rounded-xl bg-drive-600 px-5 py-2 text-xs font-semibold text-white hover:bg-drive-700 disabled:opacity-50 transition-colors shadow-sm capitalize"
          >
            {isSubmitting ? 'Processing...' : `${mode} Here`}
          </button>
        </div>
      </div>
    </div>
  );
};

export default MoveCopyModal;
