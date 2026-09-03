/**
 * Interactive Cloud Drive "My Drive" file and folder explorer dashboard.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import {
  FolderPlus,
  UploadCloud,
  Sparkles,
  Folder as FolderIcon,
  File as FileIcon,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';

// Services
import folderService from '../services/folderService';
import fileService from '../services/fileService';
import batchService from '../services/batchService';

// Drive & Layout Components
import Breadcrumbs from '../components/drive/Breadcrumbs';
import ViewSwitcher from '../components/drive/ViewSwitcher';
import FolderItem from '../components/drive/FolderItem';
import FileItem from '../components/drive/FileItem';
import BatchActionBar from '../components/drive/BatchActionBar';

// Modals
import CreateFolderModal from '../components/modals/CreateFolderModal';
import FileUploadModal from '../components/modals/FileUploadModal';
import FilePreviewModal from '../components/modals/FilePreviewModal';
import ShareModal from '../components/modals/ShareModal';
import FileVersionModal from '../components/modals/FileVersionModal';
import FileCommentsDrawer from '../components/modals/FileCommentsDrawer';
import TagManagerModal from '../components/modals/TagManagerModal';
import MoveCopyModal from '../components/modals/MoveCopyModal';
import RenameModal from '../components/modals/RenameModal';

export const DashboardPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const currentFolderId = searchParams.get('folder') || null;

  // Data states
  const [contents, setContents] = useState({ folders: [], files: [], breadcrumbs: [] });
  const [currentFolderDetail, setCurrentFolderDetail] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // View & Sort states
  const [viewMode, setViewMode] = useState('grid');
  const [sortBy, setSortBy] = useState('name');
  const [sortOrder, setSortOrder] = useState('asc');

  // Selection states
  const [selectedFolderIds, setSelectedFolderIds] = useState(new Set());
  const [selectedFileIds, setSelectedFileIds] = useState(new Set());

  // Modal dialog states
  const [isCreateFolderOpen, setIsCreateFolderOpen] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [previewFile, setPreviewFile] = useState(null);
  const [shareTarget, setShareTarget] = useState(null); // { item, isFolder }
  const [versionTargetFile, setVersionTargetFile] = useState(null);
  const [commentTargetFile, setCommentTargetFile] = useState(null);
  const [tagTarget, setTagTarget] = useState(null); // { item, isFolder }
  const [moveCopyTarget, setMoveCopyTarget] = useState(null); // { item, isFolder, mode: 'move'|'copy' }
  const [renameTarget, setRenameTarget] = useState(null); // { item, isFolder }

  // Load Folder Contents
  const loadContents = useCallback(async () => {
    setIsLoading(true);
    setError('');
    try {
      if (currentFolderId) {
        const [contentsData, detailData] = await Promise.all([
          folderService.getFolderContents(currentFolderId, sortBy, sortOrder),
          folderService.getFolderDetail(currentFolderId),
        ]);
        setContents(contentsData);
        setCurrentFolderDetail(detailData);
      } else {
        const contentsData = await folderService.getRootContents(sortBy, sortOrder);
        setContents(contentsData);
        setCurrentFolderDetail(null);
      }
    } catch (err) {
      console.error(err);
      setError('Failed to load drive items.');
    } finally {
      setIsLoading(false);
    }
  }, [currentFolderId, sortBy, sortOrder]);

  useEffect(() => {
    loadContents();
    setSelectedFolderIds(new Set());
    setSelectedFileIds(new Set());

    const handleRefresh = () => {
      loadContents();
    };
    window.addEventListener('drive-refresh', handleRefresh);
    return () => window.removeEventListener('drive-refresh', handleRefresh);
  }, [loadContents]);

  // Handle Drag and Drop anywhere on dashboard
  const onDrop = useCallback(
    async (acceptedFiles) => {
      if (!acceptedFiles || acceptedFiles.length === 0) return;
      setIsUploadOpen(true);
    },
    []
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    noClick: true,
    noKeyboard: true,
  });

  // Navigation handlers
  const handleNavigateFolder = (folderId) => {
    if (folderId) {
      setSearchParams({ folder: folderId });
    } else {
      setSearchParams({});
    }
  };

  // Selection handlers
  const handleSelectFolder = (id) => {
    setSelectedFolderIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleSelectFile = (id) => {
    setSelectedFileIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleClearSelection = () => {
    setSelectedFolderIds(new Set());
    setSelectedFileIds(new Set());
  };

  // Star toggle
  const handleToggleStarFolder = async (folder) => {
    try {
      await folderService.toggleStar(folder.id);
      loadContents();
    } catch (err) {
      console.error(err);
    }
  };

  const handleToggleStarFile = async (file) => {
    try {
      await fileService.toggleStar(file.id);
      loadContents();
    } catch (err) {
      console.error(err);
    }
  };

  // Single Delete handlers
  const handleDeleteFolder = async (folder) => {
    if (window.confirm(`Move folder "${folder.name}" and all its contents to Trash?`)) {
      try {
        await folderService.softDelete(folder.id);
        loadContents();
      } catch (err) {
        alert(err.response?.data?.detail || 'Failed to move folder to trash.');
      }
    }
  };

  const handleDeleteFile = async (file) => {
    if (window.confirm(`Move file "${file.name}" to Trash?`)) {
      try {
        await fileService.softDelete(file.id);
        loadContents();
      } catch (err) {
        alert(err.response?.data?.detail || 'Failed to move file to trash.');
      }
    }
  };

  // Batch Operations
  const handleBatchDownload = async () => {
    try {
      await batchService.batchDownloadZip({
        folder_ids: Array.from(selectedFolderIds),
        file_ids: Array.from(selectedFileIds),
      });
    } catch (err) {
      alert('Failed to download batch ZIP.');
    }
  };

  const handleBatchStar = async () => {
    try {
      await batchService.batchStar({
        folder_ids: Array.from(selectedFolderIds),
        file_ids: Array.from(selectedFileIds),
        is_starred: true,
      });
      loadContents();
      handleClearSelection();
    } catch (err) {
      alert('Failed to star items.');
    }
  };

  const handleBatchDelete = async () => {
    const total = selectedFolderIds.size + selectedFileIds.size;
    if (window.confirm(`Move ${total} items to Trash?`)) {
      try {
        await batchService.batchDelete({
          folder_ids: Array.from(selectedFolderIds),
          file_ids: Array.from(selectedFileIds),
        });
        loadContents();
        handleClearSelection();
      } catch (err) {
        alert('Failed to move items to trash.');
      }
    }
  };

  const totalSelected = selectedFolderIds.size + selectedFileIds.size;

  return (
    <div {...getRootProps()} className="min-h-full space-y-6 relative outline-none pb-16">
      <input {...getInputProps()} />

      {/* Drag overlay indicator */}
      {isDragActive && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-drive-900/60 backdrop-blur-sm">
          <div className="flex flex-col items-center gap-3 rounded-3xl bg-white p-8 text-center shadow-2xl">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-drive-100 text-drive-600">
              <UploadCloud className="h-8 w-8" />
            </div>
            <h3 className="text-lg font-bold text-slate-800">Drop files here to upload</h3>
            <p className="text-xs text-slate-500">
              Uploading directly to {currentFolderDetail?.name || 'My Drive'}
            </p>
          </div>
        </div>
      )}

      {/* Breadcrumb Navigation & Action Toolbar */}
      <div className="flex flex-col gap-4 border-b border-slate-200 pb-4 md:flex-row md:items-center md:justify-between">
        <Breadcrumbs
          breadcrumbs={contents.breadcrumbs || []}
          currentFolderName={currentFolderDetail?.name}
          onNavigate={handleNavigateFolder}
        />

        <div className="flex flex-wrap items-center gap-2.5">
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

          <div className="h-4 w-px bg-slate-200 mx-1 hidden sm:block" />

          <button
            onClick={() => setIsCreateFolderOpen(true)}
            className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm"
          >
            <FolderPlus className="h-4 w-4 text-drive-600" />
            <span>New Folder</span>
          </button>

          <button
            onClick={() => setIsUploadOpen(true)}
            className="flex items-center gap-2 rounded-xl bg-drive-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-drive-700 transition-colors shadow-sm"
          >
            <UploadCloud className="h-4 w-4" />
            <span>Upload File</span>
          </button>

          <button
            onClick={loadContents}
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

      {/* Main Content Areas */}
      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="flex flex-col items-center gap-3 text-slate-400">
            <RefreshCw className="h-8 w-8 animate-spin text-drive-600" />
            <p className="text-xs">Loading items...</p>
          </div>
        </div>
      ) : contents.folders?.length === 0 && contents.files?.length === 0 ? (
        /* Empty State */
        <div className="flex flex-col items-center justify-center rounded-3xl border-2 border-dashed border-slate-200 bg-white p-12 text-center shadow-sm">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-drive-50 text-drive-600 mb-4">
            <UploadCloud className="h-8 w-8" />
          </div>
          <h3 className="text-base font-semibold text-slate-800">This folder is empty</h3>
          <p className="mt-1.5 max-w-sm text-xs text-slate-500">
            Drag and drop files here, or use the "Upload File" and "New Folder" buttons above.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Folders Section */}
          {contents.folders?.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Folders ({contents.folders.length})
              </h3>
              <div
                className={
                  viewMode === 'grid'
                    ? 'grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5'
                    : 'space-y-1.5'
                }
              >
                {contents.folders.map((folder) => (
                  <FolderItem
                    key={folder.id}
                    folder={folder}
                    viewMode={viewMode}
                    isSelected={selectedFolderIds.has(folder.id)}
                    onSelect={handleSelectFolder}
                    onOpen={handleNavigateFolder}
                    onToggleStar={handleToggleStarFolder}
                    onDownload={() => folderService.downloadZip(folder.id, folder.name)}
                    onShare={(f) => setShareTarget({ item: f, isFolder: true })}
                    onRename={(f) => setRenameTarget({ item: f, isFolder: true })}
                    onMove={(f) => setMoveCopyTarget({ item: f, isFolder: true, mode: 'move' })}
                    onTags={(f) => setTagTarget({ item: f, isFolder: true })}
                    onDelete={handleDeleteFolder}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Files Section */}
          {contents.files?.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Files ({contents.files.length})
              </h3>
              <div
                className={
                  viewMode === 'grid'
                    ? 'grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5'
                    : 'space-y-1.5'
                }
              >
                {contents.files.map((file) => (
                  <FileItem
                    key={file.id}
                    file={file}
                    viewMode={viewMode}
                    isSelected={selectedFileIds.has(file.id)}
                    onSelect={handleSelectFile}
                    onPreview={(f) => setPreviewFile(f)}
                    onDownload={(f) => fileService.downloadFile(f.id, f.name)}
                    onShare={(f) => setShareTarget({ item: f, isFolder: false })}
                    onToggleStar={handleToggleStarFile}
                    onRename={(f) => setRenameTarget({ item: f, isFolder: false })}
                    onMove={(f) => setMoveCopyTarget({ item: f, isFolder: false, mode: 'move' })}
                    onCopy={(f) => setMoveCopyTarget({ item: f, isFolder: false, mode: 'copy' })}
                    onTags={(f) => setTagTarget({ item: f, isFolder: false })}
                    onVersions={(f) => setVersionTargetFile(f)}
                    onComments={(f) => setCommentTargetFile(f)}
                    onDelete={handleDeleteFile}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Floating Batch Action Bar */}
      <BatchActionBar
        selectedCount={totalSelected}
        onClearSelection={handleClearSelection}
        onBatchDownload={handleBatchDownload}
        onBatchStar={handleBatchStar}
        onBatchDelete={handleBatchDelete}
      />

      {/* Modals & Drawers */}
      <CreateFolderModal
        isOpen={isCreateFolderOpen}
        onClose={() => setIsCreateFolderOpen(false)}
        parentId={currentFolderId}
        onSuccess={loadContents}
      />

      <FileUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        folderId={currentFolderId}
        folderName={currentFolderDetail?.name || 'Root'}
        onSuccess={loadContents}
      />

      <FilePreviewModal
        isOpen={Boolean(previewFile)}
        file={previewFile}
        onClose={() => setPreviewFile(null)}
        onToggleStar={handleToggleStarFile}
        onShare={(f) => setShareTarget({ item: f, isFolder: false })}
        onOpenVersions={(f) => setVersionTargetFile(f)}
      />

      <ShareModal
        isOpen={Boolean(shareTarget)}
        onClose={() => setShareTarget(null)}
        item={shareTarget?.item}
        isFolder={shareTarget?.isFolder}
      />

      <FileVersionModal
        isOpen={Boolean(versionTargetFile)}
        file={versionTargetFile}
        onClose={() => setVersionTargetFile(null)}
        onVersionUploaded={loadContents}
      />

      <FileCommentsDrawer
        isOpen={Boolean(commentTargetFile)}
        file={commentTargetFile}
        onClose={() => setCommentTargetFile(null)}
      />

      <TagManagerModal
        isOpen={Boolean(tagTarget)}
        item={tagTarget?.item}
        isFolder={tagTarget?.isFolder}
        onClose={() => setTagTarget(null)}
        onTagsUpdated={loadContents}
      />

      <MoveCopyModal
        isOpen={Boolean(moveCopyTarget)}
        item={moveCopyTarget?.item}
        isFolder={moveCopyTarget?.isFolder}
        mode={moveCopyTarget?.mode || 'move'}
        onClose={() => setMoveCopyTarget(null)}
        onSuccess={loadContents}
      />

      <RenameModal
        isOpen={Boolean(renameTarget)}
        item={renameTarget?.item}
        isFolder={renameTarget?.isFolder}
        onClose={() => setRenameTarget(null)}
        onSuccess={loadContents}
      />
    </div>
  );
};

export default DashboardPage;
