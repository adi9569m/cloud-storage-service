import React, { useState, useEffect, useCallback } from 'react';
import {
  Activity,
  Filter,
  RefreshCw,
  FileUp,
  FileDown,
  Trash2,
  FolderPlus,
  Share2,
  Link,
  Tag,
  MessageSquare,
  History,
  Star,
  CheckCircle2,
  Info,
  Layers,
  ChevronRight,
  Loader2,
  Clock,
  Sparkles,
} from 'lucide-react';

import activityService from '../services/activityService';
import { formatDate } from '../utils/formatters';

const actionConfig = {
  FILE_UPLOAD: { label: 'Uploaded File', icon: FileUp, color: 'text-emerald-600 bg-emerald-50 border-emerald-200' },
  FILE_DOWNLOAD: { label: 'Downloaded File', icon: FileDown, color: 'text-blue-600 bg-blue-50 border-blue-200' },
  FILE_DELETE: { label: 'Deleted File', icon: Trash2, color: 'text-rose-600 bg-rose-50 border-rose-200' },
  FILE_RESTORE: { label: 'Restored File', icon: CheckCircle2, color: 'text-teal-600 bg-teal-50 border-teal-200' },
  FILE_RENAME: { label: 'Renamed File', icon: History, color: 'text-indigo-600 bg-indigo-50 border-indigo-200' },
  FILE_MOVE: { label: 'Moved File', icon: Layers, color: 'text-purple-600 bg-purple-50 border-purple-200' },
  FILE_COPY: { label: 'Copied File', icon: Layers, color: 'text-purple-600 bg-purple-50 border-purple-200' },
  FILE_STAR: { label: 'Starred File', icon: Star, color: 'text-amber-600 bg-amber-50 border-amber-200' },
  FILE_UNSTAR: { label: 'Unstarred File', icon: Star, color: 'text-slate-600 bg-slate-50 border-slate-200' },
  FILE_VERSION_UPLOAD: { label: 'New File Version', icon: FileUp, color: 'text-cyan-600 bg-cyan-50 border-cyan-200' },
  FILE_VERSION_RESTORE: { label: 'Restored Version', icon: History, color: 'text-teal-600 bg-teal-50 border-teal-200' },
  FOLDER_CREATE: { label: 'Created Folder', icon: FolderPlus, color: 'text-emerald-600 bg-emerald-50 border-emerald-200' },
  FOLDER_DELETE: { label: 'Deleted Folder', icon: Trash2, color: 'text-rose-600 bg-rose-50 border-rose-200' },
  FOLDER_RESTORE: { label: 'Restored Folder', icon: CheckCircle2, color: 'text-teal-600 bg-teal-50 border-teal-200' },
  FOLDER_RENAME: { label: 'Renamed Folder', icon: History, color: 'text-indigo-600 bg-indigo-50 border-indigo-200' },
  FOLDER_MOVE: { label: 'Moved Folder', icon: Layers, color: 'text-purple-600 bg-purple-50 border-purple-200' },
  SHARE_GRANTED: { label: 'Granted Share', icon: Share2, color: 'text-blue-600 bg-blue-50 border-blue-200' },
  SHARE_REVOKED: { label: 'Revoked Share', icon: Share2, color: 'text-rose-600 bg-rose-50 border-rose-200' },
  SHARE_UPDATED: { label: 'Updated Share', icon: Share2, color: 'text-indigo-600 bg-indigo-50 border-indigo-200' },
  LINK_SHARE_CREATED: { label: 'Created Public Link', icon: Link, color: 'text-cyan-600 bg-cyan-50 border-cyan-200' },
  LINK_SHARE_ACCESSED: { label: 'Public Link Viewed', icon: Link, color: 'text-slate-600 bg-slate-50 border-slate-200' },
  LINK_SHARE_DELETED: { label: 'Removed Public Link', icon: Link, color: 'text-rose-600 bg-rose-50 border-rose-200' },
  COMMENT_ADDED: { label: 'Added Comment', icon: MessageSquare, color: 'text-violet-600 bg-violet-50 border-violet-200' },
  COMMENT_DELETED: { label: 'Deleted Comment', icon: Trash2, color: 'text-rose-600 bg-rose-50 border-rose-200' },
  TAG_CREATED: { label: 'Created Tag', icon: Tag, color: 'text-pink-600 bg-pink-50 border-pink-200' },
  TAG_ASSIGNED: { label: 'Tagged Item', icon: Tag, color: 'text-pink-600 bg-pink-50 border-pink-200' },
  TAG_REMOVED: { label: 'Untagged Item', icon: Tag, color: 'text-slate-600 bg-slate-50 border-slate-200' },
};

export const ActivityPage = () => {
  const [activities, setActivities] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const [resourceTypeFilter, setResourceTypeFilter] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [page, setPage] = useState(0);
  const limit = 25;

  const loadActivities = useCallback(async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await activityService.listActivities({
        resource_type: resourceTypeFilter || null,
        action: actionFilter || null,
        limit,
        offset: page * limit,
      });
      setActivities(data.activities || []);
      setTotalCount(data.total || 0);
    } catch (err) {
      console.error(err);
      setError('Failed to load activity stream.');
    } finally {
      setIsLoading(false);
    }
  }, [resourceTypeFilter, actionFilter, page]);

  useEffect(() => {
    loadActivities();
  }, [loadActivities]);

  const totalPages = Math.ceil(totalCount / limit) || 1;

  return (
    <div className="space-y-6">

      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-drive-50 text-drive-600 shadow-sm">
            <Activity className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-800">Activity Log</h1>
            <p className="text-xs text-slate-500">
              Audit trail of actions, uploads, shares, and administrative operations.
            </p>
          </div>
        </div>

        <button
          onClick={loadActivities}
          disabled={isLoading}
          className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 text-drive-600 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-soft">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-600 mr-2">
          <Filter className="h-4 w-4 text-drive-600" />
          <span>Filter by:</span>
        </div>

        <select
          value={resourceTypeFilter}
          onChange={(e) => {
            setResourceTypeFilter(e.target.value);
            setPage(0);
          }}
          className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 focus:border-drive-400 focus:bg-white focus:outline-none"
        >
          <option value="">All Resource Types</option>
          <option value="FILE">Files</option>
          <option value="FOLDER">Folders</option>
          <option value="SHARE">Collaborator Shares</option>
          <option value="LINK_SHARE">Public Links</option>
        </select>

        <select
          value={actionFilter}
          onChange={(e) => {
            setActionFilter(e.target.value);
            setPage(0);
          }}
          className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 focus:border-drive-400 focus:bg-white focus:outline-none"
        >
          <option value="">All Actions</option>
          <option value="FILE_UPLOAD">File Upload</option>
          <option value="FILE_DOWNLOAD">File Download</option>
          <option value="FILE_DELETE">File Deletion</option>
          <option value="FILE_RESTORE">File Restore</option>
          <option value="FILE_VERSION_UPLOAD">New Version</option>
          <option value="FOLDER_CREATE">Folder Create</option>
          <option value="FOLDER_DELETE">Folder Delete</option>
          <option value="SHARE_GRANTED">Share Granted</option>
          <option value="LINK_SHARE_CREATED">Link Created</option>
          <option value="COMMENT_ADDED">Comment Added</option>
          <option value="TAG_ASSIGNED">Tag Assigned</option>
        </select>

        {(resourceTypeFilter || actionFilter) && (
          <button
            onClick={() => {
              setResourceTypeFilter('');
              setActionFilter('');
              setPage(0);
            }}
            className="text-xs font-semibold text-drive-600 hover:text-drive-700 transition-colors ml-auto"
          >
            Clear Filters
          </button>
        )}
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
      ) : activities.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-3xl border-2 border-dashed border-slate-200 bg-white p-12 text-center shadow-soft">
          <div className="flex h-16 w-16 items-center justify-center rounded-3xl bg-drive-50 text-drive-600 mb-4 shadow-sm">
            <Activity className="h-8 w-8" />
          </div>
          <h3 className="text-base font-bold text-slate-800 mb-1">No activities recorded</h3>
          <p className="max-w-md text-xs text-slate-500">
            {resourceTypeFilter || actionFilter
              ? 'No activity entries matched the selected filter criteria.'
              : 'As you interact with files and folders, your audit history will be logged here.'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="rounded-3xl border border-slate-200 bg-white shadow-soft divide-y divide-slate-100 overflow-hidden">
            {activities.map((item) => {
              const config = actionConfig[item.action] || {
                label: item.action?.replace(/_/g, ' ') || 'Action',
                icon: Activity,
                color: 'text-slate-600 bg-slate-50 border-slate-200',
              };
              const Icon = config.icon;

              return (
                <div
                  key={item.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 hover:bg-slate-50/70 transition-colors"
                >
                  <div className="flex items-start sm:items-center gap-3 overflow-hidden">
                    <div
                      className={`flex h-10 w-10 items-center justify-center rounded-2xl border flex-shrink-0 ${config.color}`}
                    >
                      <Icon className="h-5 w-5" />
                    </div>

                    <div className="overflow-hidden">
                      <div className="flex flex-wrap items-center gap-2 mb-0.5">
                        <span className="text-xs font-bold text-slate-800">{config.label}</span>
                        <span className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-500">
                          {item.resource_type}
                        </span>
                      </div>
                      <p className="truncate text-xs font-medium text-slate-600">
                        {item.details?.filename ||
                          item.details?.name ||
                          item.details?.folder_name ||
                          item.details?.recipient_email ||
                          (item.resource_id ? `ID: ${item.resource_id.substring(0, 8)}...` : 'System Event')}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 text-xs text-slate-400 sm:self-center pl-13 sm:pl-0">
                    {item.ip_address && (
                      <span className="hidden md:inline rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-mono text-slate-500">
                        {item.ip_address}
                      </span>
                    )}
                    <span className="flex items-center gap-1 font-medium whitespace-nowrap">
                      <Clock className="h-3.5 w-3.5" />
                      {formatDate(item.created_at)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between px-2 pt-2 text-xs text-slate-500">
              <span>
                Showing {page * limit + 1} to {Math.min((page + 1) * limit, totalCount)} of {totalCount} events
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="rounded-xl border border-slate-200 bg-white px-3 py-1.5 font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40 transition-colors"
                >
                  Previous
                </button>
                <span className="font-semibold text-slate-700">
                  Page {page + 1} of {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                  disabled={page >= totalPages - 1}
                  className="rounded-xl border border-slate-200 bg-white px-3 py-1.5 font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40 transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ActivityPage;
