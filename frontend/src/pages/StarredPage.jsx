import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Star, RefreshCw } from 'lucide-react';

import starService from '../services/starService';
import fileService from '../services/fileService';
import folderService from '../services/folderService';

import ViewSwitcher from '../components/drive/ViewSwitcher';
import FolderItem from '../components/drive/FolderItem';
import FileItem from '../components/drive/FileItem';

import FilePreviewModal from '../components/modals/FilePreviewModal';
import ShareModal from '../components/modals/ShareModal';
import RenameModal from '../components/modals/RenameModal';

export const StarredPage = () => {
  const navigate = useNavigate();
  const [data, setData] = useState({ files: [], folders: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const [viewMode, setViewMode] = useState('grid');
  const [sortBy, setSortBy] = useState('name');
  const [sortOrder, setSortOrder] = useState('asc');

  const [previewFile, setPreviewFile] = useState(null);
  const [shareTarget, setShareTarget] = useState(null);
  const [renameTarget, setRenameTarget] = useState(null);

  const loadStarred = async () => {
    setIsLoading(true);
    setError('');
    try {
      const res = await starService.listStarred();
      setData(res || { files: [], folders: [] });
    } catch (err) {
      setError('Failed to load starred items.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadStarred();
  }, []);

  const handleToggleStarFolder = async (folder) => {
    try {
      await folderService.toggleStar(folder.id);
      loadStarred();
    } catch (err) {
      console.error(err);
    }
  };

  const handleToggleStarFile = async (file) => {
    try {
      await fileService.toggleStar(file.id);
      loadStarred();
    } catch (err) {
      console.error(err);
    }
  };

  const folders = data.folders || [];
  const files = data.files || [];
  const isEmpty = folders.length === 0 && files.length === 0;

  return (
    <div className="space-y-6">

      <div className="flex items-center justify-between border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-800">Starred</h1>
          <p className="text-xs text-slate-500 mt-1">
            Quickly access your favorite and high-priority files and directories.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <ViewSwitcher
            viewMode={viewMode}
            onViewModeChange={setViewMode}
            sortBy={sortBy}
            sortOrder={sortOrder}
            onSortChange={(field, order) => {
              setSortBy(field);
              setSortOrder(order);
            }}
          />

          <button
            onClick={loadStarred}
            className="rounded-xl border border-slate-200 bg-white p-2 text-slate-600 hover:bg-slate-50 transition-colors shadow-sm"
            title="Refresh"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-2xl bg-red-50 p-4 text-xs text-red-600 border border-red-200">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <RefreshCw className="h-8 w-8 animate-spin text-drive-600" />
        </div>
      ) : isEmpty ? (
        <div className="flex flex-col items-center justify-center rounded-3xl border-2 border-dashed border-slate-200 bg-white p-12 text-center shadow-sm">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-50 text-amber-500 mb-4">
            <Star className="h-8 w-8 fill-amber-500" />
          </div>
          <h3 className="text-base font-semibold text-slate-800">No starred items</h3>
          <p className="mt-1.5 max-w-sm text-xs text-slate-500">
            Click the star icon next to any file or folder to bookmark it here for quick access.
          </p>
        </div>
      ) : (
        <div className="space-y-6">

          {folders.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Starred Folders ({folders.length})
              </h3>
              <div
                className={
                  viewMode === 'grid'
                    ? 'grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5'
                    : 'space-y-1.5'
                }
              >
                {folders.map((folder) => (
                  <FolderItem
                    key={folder.id}
                    folder={folder}
                    viewMode={viewMode}
                    onOpen={(id) => navigate(`/?folder=${id}`)}
                    onToggleStar={handleToggleStarFolder}
                    onDownload={() => folderService.downloadZip(folder.id, folder.name)}
                    onShare={(f) => setShareTarget({ item: f, isFolder: true })}
                    onRename={(f) => setRenameTarget({ item: f, isFolder: true })}
                  />
                ))}
              </div>
            </div>
          )}

          {files.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Starred Files ({files.length})
              </h3>
              <div
                className={
                  viewMode === 'grid'
                    ? 'grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5'
                    : 'space-y-1.5'
                }
              >
                {files.map((file) => (
                  <FileItem
                    key={file.id}
                    file={file}
                    viewMode={viewMode}
                    onPreview={(f) => setPreviewFile(f)}
                    onDownload={(f) => fileService.downloadFile(f.id, f.name)}
                    onShare={(f) => setShareTarget({ item: f, isFolder: false })}
                    onToggleStar={handleToggleStarFile}
                    onRename={(f) => setRenameTarget({ item: f, isFolder: false })}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <FilePreviewModal
        isOpen={Boolean(previewFile)}
        file={previewFile}
        onClose={() => setPreviewFile(null)}
        onToggleStar={handleToggleStarFile}
      />

      <ShareModal
        isOpen={Boolean(shareTarget)}
        onClose={() => setShareTarget(null)}
        item={shareTarget?.item}
        isFolder={shareTarget?.isFolder}
      />

      <RenameModal
        isOpen={Boolean(renameTarget)}
        item={renameTarget?.item}
        isFolder={renameTarget?.isFolder}
        onClose={() => setRenameTarget(null)}
        onSuccess={loadStarred}
      />
    </div>
  );
};

export default StarredPage;
