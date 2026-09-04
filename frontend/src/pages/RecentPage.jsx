/**
 * Recent Files page grouping files chronologically (Today, Yesterday, This Week, Older).
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Clock,
  Sparkles,
  File as FileIcon,
  Eye,
  Download,
  Share2,
  Star,
  Trash2,
  MoreVertical,
  History,
  Tag,
  MessageSquare,
  Loader2,
  RefreshCw,
} from 'lucide-react';

import fileService from '../services/fileService';
import starService from '../services/starService';
import { formatBytes, formatDate, getFileIconDetails } from '../utils/formatters';

// Modals
import FilePreviewModal from '../components/modals/FilePreviewModal';
import ShareModal from '../components/modals/ShareModal';
import FileVersionModal from '../components/modals/FileVersionModal';
import FileCommentsDrawer from '../components/modals/FileCommentsDrawer';
import TagManagerModal from '../components/modals/TagManagerModal';
import RenameModal from '../components/modals/RenameModal';
import { useToast } from '../context/ToastContext';

export const RecentPage = () => {
  const [files, setFiles] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const toast = useToast();

  // Modal dialog states
  const [previewFile, setPreviewFile] = useState(null);
  const [shareTarget, setShareTarget] = useState(null);
  const [versionTargetFile, setVersionTargetFile] = useState(null);
  const [commentTargetFile, setCommentTargetFile] = useState(null);
  const [tagTarget, setTagTarget] = useState(null);
  const [renameTarget, setRenameTarget] = useState(null);

  const loadRecentFiles = useCallback(async () => {
    setIsLoading(true);
    setError('');
    try {
      // Fetch files ordered by recently updated
      const rootData = await fileService.searchFiles('', {
        limit: 100,
      });
      // Sort by updated_at descending
      const sorted = (rootData || []).sort(
        (a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at)
      );
      setFiles(sorted);
    } catch (err) {
      console.error(err);
      setError('Failed to load recent files.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRecentFiles();
  }, [loadRecentFiles]);

  const handleToggleStar = async (e, file) => {
    e.stopPropagation();
    try {
      if (file.is_starred) {
        await starService.unstarItem({ file_id: file.id });
        toast.info(`Unstarred ${file.name}`);
      } else {
        await starService.starItem({ file_id: file.id });
        toast.success(`Starred ${file.name}`);
      }
      setFiles((prev) =>
        prev.map((f) => (f.id === file.id ? { ...f, is_starred: !f.is_starred } : f))
      );
    } catch (err) {
      toast.error('Failed to update star status');
    }
  };

  const handleDownload = async (e, file) => {
    e.stopPropagation();
    try {
      const { download_url } = await fileService.getFileDownloadUrl(file.id);
      window.open(download_url, '_blank');
      toast.success(`Downloading ${file.name}`);
    } catch (err) {
      toast.error('Failed to download file');
    }
  };

  const handleDelete = async (e, file) => {
    e.stopPropagation();
    if (window.confirm(`Move "${file.name}" to Trash?`)) {
      try {
        await fileService.deleteFile(file.id);
        toast.success(`Moved ${file.name} to Trash`);
        setFiles((prev) => prev.filter((f) => f.id !== file.id));
      } catch (err) {
        toast.error('Failed to delete file');
      }
    }
  };

  // Group files into chronological buckets
  const groupedFiles = useMemo(() => {
    const now = new Date();
    const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    const startOfYesterday = startOfToday - 86400000;
    const startOfWeek = startOfToday - 6 * 86400000;
    const startOfMonth = startOfToday - 29 * 86400000;

    const groups = {
      today: [],
      yesterday: [],
      thisWeek: [],
      thisMonth: [],
      older: [],
    };

    files.forEach((file) => {
      const fileTime = new Date(file.updated_at || file.created_at).getTime();
      if (fileTime >= startOfToday) {
        groups.today.push(file);
      } else if (fileTime >= startOfYesterday) {
        groups.yesterday.push(file);
      } else if (fileTime >= startOfWeek) {
        groups.thisWeek.push(file);
      } else if (fileTime >= startOfMonth) {
        groups.thisMonth.push(file);
      } else {
        groups.older.push(file);
      }
    });

    return [
      { key: 'today', title: 'Today', items: groups.today },
      { key: 'yesterday', title: 'Yesterday', items: groups.yesterday },
      { key: 'thisWeek', title: 'Earlier this week', items: groups.thisWeek },
      { key: 'thisMonth', title: 'Earlier this month', items: groups.thisMonth },
      { key: 'older', title: 'Older', items: groups.older },
    ].filter((g) => g.items.length > 0);
  }, [files]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-drive-50 text-drive-600 shadow-sm">
              <Clock className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-800">Recent</h1>
              <p className="text-xs text-slate-500">
                Files you have recently uploaded, modified, or accessed.
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={loadRecentFiles}
          disabled={isLoading}
          className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 text-drive-600 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs font-medium text-rose-700">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="flex h-96 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-drive-600" />
        </div>
      ) : files.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-3xl border-2 border-dashed border-slate-200 bg-white p-12 text-center shadow-soft">
          <div className="flex h-16 w-16 items-center justify-center rounded-3xl bg-drive-50 text-drive-600 mb-4 shadow-sm">
            <Clock className="h-8 w-8" />
          </div>
          <h3 className="text-base font-bold text-slate-800 mb-1">No recent activity</h3>
          <p className="max-w-md text-xs text-slate-500 mb-6">
            Files you upload, edit, or view will appear here in chronological order.
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {groupedFiles.map((group) => (
            <div key={group.key} className="space-y-3">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 px-1">
                {group.title} ({group.items.length})
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {group.items.map((file) => {
                  const { icon: Icon, bg, color } = getFileIconDetails(file.mime_type, file.name);

                  return (
                    <div
                      key={file.id}
                      onClick={() => setPreviewFile(file)}
                      className="group relative flex flex-col justify-between rounded-3xl border border-slate-200 bg-white p-4 shadow-soft hover:shadow-md hover:border-drive-300 transition-all cursor-pointer"
                    >
                      <div>
                        {/* Card Top */}
                        <div className="flex items-start justify-between gap-2 mb-3">
                          <div
                            className={`flex h-10 w-10 items-center justify-center rounded-2xl ${bg} ${color} shadow-xs`}
                          >
                            <Icon className="h-5 w-5" />
                          </div>

                          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={(e) => handleToggleStar(e, file)}
                              className={`rounded-lg p-1.5 transition-colors ${
                                file.is_starred
                                  ? 'text-amber-500 hover:bg-amber-50'
                                  : 'text-slate-400 hover:bg-slate-100'
                              }`}
                              title={file.is_starred ? 'Unstar' : 'Star'}
                            >
                              <Star
                                className={`h-4 w-4 ${file.is_starred ? 'fill-amber-400' : ''}`}
                              />
                            </button>
                            <button
                              onClick={(e) => handleDownload(e, file)}
                              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
                              title="Download"
                            >
                              <Download className="h-4 w-4" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setShareTarget({ item: file, isFolder: false });
                              }}
                              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
                              title="Share"
                            >
                              <Share2 className="h-4 w-4" />
                            </button>
                          </div>
                        </div>

                        {/* Title & metadata */}
                        <h4
                          className="truncate text-sm font-semibold text-slate-800 group-hover:text-drive-700 transition-colors"
                          title={file.name}
                        >
                          {file.name}
                        </h4>
                        <p className="text-xs text-slate-400 mt-1">
                          {formatBytes(file.size_bytes)} • {formatDate(file.updated_at || file.created_at)}
                        </p>
                      </div>

                      {/* Card Bottom / Tags Preview */}
                      <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3 text-xs text-slate-400">
                        <span className="truncate max-w-[120px]">
                          v{file.current_version || 1}
                        </span>

                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setCommentTargetFile(file);
                            }}
                            className="p-1 text-slate-400 hover:text-drive-600 transition-colors"
                            title="Comments"
                          >
                            <MessageSquare className="h-3.5 w-3.5" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setVersionTargetFile(file);
                            }}
                            className="p-1 text-slate-400 hover:text-drive-600 transition-colors"
                            title="Versions"
                          >
                            <History className="h-3.5 w-3.5" />
                          </button>
                          <button
                            onClick={(e) => handleDelete(e, file)}
                            className="p-1 text-slate-400 hover:text-rose-600 transition-colors"
                            title="Move to Trash"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modals */}
      {previewFile && (
        <FilePreviewModal
          file={previewFile}
          onClose={() => setPreviewFile(null)}
          onDownload={() => handleDownload({ stopPropagation: () => {} }, previewFile)}
          onShare={() => setShareTarget({ item: previewFile, isFolder: false })}
          onViewVersions={() => setVersionTargetFile(previewFile)}
          onOpenComments={() => setCommentTargetFile(previewFile)}
        />
      )}

      {shareTarget && (
        <ShareModal
          item={shareTarget.item}
          isFolder={shareTarget.isFolder}
          onClose={() => setShareTarget(null)}
        />
      )}

      {versionTargetFile && (
        <FileVersionModal
          file={versionTargetFile}
          onClose={() => setVersionTargetFile(null)}
          onVersionRestored={() => loadRecentFiles()}
        />
      )}

      {commentTargetFile && (
        <FileCommentsDrawer
          file={commentTargetFile}
          onClose={() => setCommentTargetFile(null)}
        />
      )}

      {tagTarget && (
        <TagManagerModal
          item={tagTarget.item}
          isFolder={tagTarget.isFolder}
          onClose={() => setTagTarget(null)}
          onTagsUpdated={() => loadRecentFiles()}
        />
      )}

      {renameTarget && (
        <RenameModal
          item={renameTarget.item}
          isFolder={renameTarget.isFolder}
          onClose={() => setRenameTarget(null)}
          onSuccess={() => loadRecentFiles()}
        />
      )}
    </div>
  );
};

export default RecentPage;
