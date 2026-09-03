/**
 * Shared with me page displaying items shared by colleagues.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  Folder as FolderIcon,
  Shield,
  Download,
  Eye,
  RefreshCw,
  Copy,
  MessageSquare,
} from 'lucide-react';

import shareService from '../services/shareService';
import fileService from '../services/fileService';
import folderService from '../services/folderService';
import { formatBytes, formatDate, getFileIconDetails } from '../utils/formatters';

import FilePreviewModal from '../components/modals/FilePreviewModal';
import FileCommentsDrawer from '../components/modals/FileCommentsDrawer';
import MoveCopyModal from '../components/modals/MoveCopyModal';

export const SharedPage = () => {
  const navigate = useNavigate();
  const [sharedData, setSharedData] = useState({ shares: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Modals
  const [previewFile, setPreviewFile] = useState(null);
  const [commentTargetFile, setCommentTargetFile] = useState(null);
  const [copyTargetFile, setCopyTargetFile] = useState(null);

  const loadSharedItems = async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await shareService.listSharedWithMe();
      setSharedData(data || { shares: [] });
    } catch (err) {
      setError('Failed to load shared items.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSharedItems();
  }, []);

  const shares = sharedData.shares || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-800">Shared with me</h1>
          <p className="text-xs text-slate-500 mt-1">
            Files and folders shared with you by other collaborators.
          </p>
        </div>
        <button
          onClick={loadSharedItems}
          className="rounded-xl border border-slate-200 bg-white p-2 text-slate-600 hover:bg-slate-50 transition-colors shadow-sm"
          title="Refresh"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {error && (
        <div className="rounded-2xl bg-red-50 p-4 text-xs text-red-600 border border-red-200">
          {error}
        </div>
      )}

      {/* Content */}
      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <RefreshCw className="h-8 w-8 animate-spin text-drive-600" />
        </div>
      ) : shares.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-3xl border-2 border-dashed border-slate-200 bg-white p-12 text-center shadow-sm">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-drive-50 text-drive-600 mb-4">
            <Users className="h-8 w-8" />
          </div>
          <h3 className="text-base font-semibold text-slate-800">No shared items yet</h3>
          <p className="mt-1.5 max-w-sm text-xs text-slate-500">
            When other users share documents or directories with your account, they will appear here.
          </p>
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden divide-y divide-slate-100">
          <div className="grid grid-cols-12 bg-slate-50 px-4 py-3 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
            <div className="col-span-5 sm:col-span-6">Name</div>
            <div className="col-span-4 sm:col-span-3">Shared By / Role</div>
            <div className="col-span-3 sm:col-span-3 text-right">Actions</div>
          </div>

          {shares.map((share) => {
            const isFolder = Boolean(share.folder);
            const item = share.folder || share.file;
            if (!item) return null;

            const iconDetails = isFolder
              ? null
              : getFileIconDetails(item.mime_type, item.name);

            return (
              <div
                key={share.id}
                className="grid grid-cols-12 items-center px-4 py-3 text-xs hover:bg-slate-50 transition-colors"
              >
                {/* Item Icon & Name */}
                <div className="col-span-5 sm:col-span-6 flex items-center gap-3 overflow-hidden">
                  {isFolder ? (
                    <FolderIcon
                      className="h-6 w-6 shrink-0"
                      style={{ color: item.color || '#3B82F6' }}
                    />
                  ) : (
                    <div
                      className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${iconDetails.bg} ${iconDetails.color}`}
                    >
                      <iconDetails.icon className="h-4 w-4" />
                    </div>
                  )}

                  <div className="overflow-hidden">
                    <p
                      onClick={() => {
                        if (isFolder) {
                          navigate(`/?folder=${item.id}`);
                        } else {
                          setPreviewFile(item);
                        }
                      }}
                      className="truncate font-semibold text-slate-800 cursor-pointer hover:text-drive-600 transition-colors"
                      title={item.name}
                    >
                      {item.name}
                    </p>
                    <span className="text-[11px] text-slate-400">
                      {isFolder ? 'Folder' : formatBytes(item.size_bytes)}
                    </span>
                  </div>
                </div>

                {/* Granter & Role Badge */}
                <div className="col-span-4 sm:col-span-3 overflow-hidden">
                  <p className="truncate font-medium text-slate-700">
                    {share.granter_email || 'Drive User'}
                  </p>
                  <span
                    className={`inline-block mt-0.5 rounded px-1.5 py-0.5 text-[10px] font-bold ${
                      share.role === 'EDITOR'
                        ? 'bg-purple-100 text-purple-700'
                        : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    {share.role}
                  </span>
                </div>

                {/* Actions */}
                <div className="col-span-3 sm:col-span-3 flex items-center justify-end gap-1.5">
                  {!isFolder && (
                    <>
                      <button
                        onClick={() => setPreviewFile(item)}
                        className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                        title="Preview"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => fileService.downloadFile(item.id, item.name)}
                        className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                        title="Download"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => setCommentTargetFile(item)}
                        className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                        title="Comments"
                      >
                        <MessageSquare className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => setCopyTargetFile(item)}
                        className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                        title="Copy to My Drive"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                    </>
                  )}
                  {isFolder && (
                    <button
                      onClick={() => folderService.downloadZip(item.id, item.name)}
                      className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                      title="Download ZIP"
                    >
                      <Download className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modals */}
      <FilePreviewModal
        isOpen={Boolean(previewFile)}
        file={previewFile}
        onClose={() => setPreviewFile(null)}
      />

      <FileCommentsDrawer
        isOpen={Boolean(commentTargetFile)}
        file={commentTargetFile}
        onClose={() => setCommentTargetFile(null)}
      />

      <MoveCopyModal
        isOpen={Boolean(copyTargetFile)}
        item={copyTargetFile}
        isFolder={false}
        mode="copy"
        onClose={() => setCopyTargetFile(null)}
      />
    </div>
  );
};

export default SharedPage;
