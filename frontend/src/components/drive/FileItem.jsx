import React from 'react';
import { Star, Eye } from 'lucide-react';
import ContextMenu from './ContextMenu';
import { formatBytes, formatDate, getFileIconDetails } from '../../utils/formatters';

export const FileItem = ({
  file,
  viewMode = 'grid',
  isSelected = false,
  onSelect,
  onPreview,
  onDownload,
  onExtract,
  onShare,
  onToggleStar,
  onRename,
  onMove,
  onCopy,
  onTags,
  onVersions,
  onComments,
  onDelete,
}) => {
  const { icon: Icon, color, bg } = getFileIconDetails(file.mime_type, file.name);

  if (viewMode === 'list') {
    return (
      <div
        onClick={() => onSelect?.(file.id)}
        onDoubleClick={() => onPreview?.(file)}
        className={`group flex items-center justify-between px-4 py-2.5 rounded-xl border text-xs cursor-pointer transition-all ${
          isSelected
            ? 'border-drive-300 bg-drive-50/70 shadow-xs'
            : 'border-slate-200/80 bg-white hover:bg-slate-50 hover:border-slate-300'
        }`}
      >
        <div className="flex items-center gap-3 overflow-hidden flex-1">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={(e) => {
              e.stopPropagation();
              onSelect?.(file.id);
            }}
            className="h-4 w-4 rounded border-slate-300 text-drive-600 focus:ring-drive-500 cursor-pointer"
          />

          <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${bg} ${color}`}>
            <Icon className="h-4 w-4" />
          </div>

          <span className="truncate font-medium text-slate-800" title={file.name}>
            {file.name}
          </span>
        </div>

        <div className="flex items-center gap-6 text-slate-500">
          <span className="hidden md:inline text-[11px]">
            {formatDate(file.updated_at || file.created_at)}
          </span>
          <span className="hidden sm:inline text-[11px] w-16 text-right">
            {formatBytes(file.size_bytes)}
          </span>

          <div className="flex items-center gap-1">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggleStar?.(file);
              }}
              className={`rounded-lg p-1 transition-colors ${
                file.is_starred
                  ? 'text-amber-500'
                  : 'text-slate-300 opacity-0 group-hover:opacity-100 hover:text-amber-500'
              }`}
              title={file.is_starred ? 'Remove Star' : 'Star'}
            >
              <Star className={`h-4 w-4 ${file.is_starred ? 'fill-amber-500' : ''}`} />
            </button>

            <ContextMenu
              item={file}
              isFolder={false}
              onPreview={onPreview}
              onDownload={onDownload}
              onExtract={onExtract}
              onShare={onShare}
              onToggleStar={onToggleStar}
              onRename={onRename}
              onMove={onMove}
              onCopy={onCopy}
              onTags={onTags}
              onVersions={onVersions}
              onComments={onComments}
              onDelete={onDelete}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      onClick={() => onSelect?.(file.id)}
      onDoubleClick={() => onPreview?.(file)}
      className={`group relative flex flex-col justify-between rounded-2xl border p-4 text-xs cursor-pointer transition-all select-none ${
        isSelected
          ? 'border-drive-400 bg-drive-50/60 ring-2 ring-drive-200 shadow-sm'
          : 'border-slate-200/80 bg-white hover:border-slate-300 hover:shadow-md hover:-translate-y-0.5'
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5 overflow-hidden">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={(e) => {
              e.stopPropagation();
              onSelect?.(file.id);
            }}
            className={`h-4 w-4 rounded border-slate-300 text-drive-600 focus:ring-drive-500 cursor-pointer ${
              isSelected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
            }`}
          />
          <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${bg} ${color}`}>
            <Icon className="h-5 w-5" />
          </div>
        </div>

        <div className="flex items-center gap-0.5">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleStar?.(file);
            }}
            className={`rounded-lg p-1 transition-colors ${
              file.is_starred
                ? 'text-amber-500'
                : 'text-slate-300 opacity-0 group-hover:opacity-100 hover:text-amber-500'
            }`}
            title={file.is_starred ? 'Remove Star' : 'Star'}
          >
            <Star className={`h-4 w-4 ${file.is_starred ? 'fill-amber-500' : ''}`} />
          </button>

          <ContextMenu
            item={file}
            isFolder={false}
            onPreview={onPreview}
            onDownload={onDownload}
            onExtract={onExtract}
            onShare={onShare}
            onToggleStar={onToggleStar}
            onRename={onRename}
            onMove={onMove}
            onCopy={onCopy}
            onTags={onTags}
            onVersions={onVersions}
            onComments={onComments}
            onDelete={onDelete}
          />
        </div>
      </div>

      <div className="mt-3">
        <h4 className="truncate font-semibold text-slate-800" title={file.name}>
          {file.name}
        </h4>
        <div className="mt-1 flex items-center justify-between text-[11px] text-slate-400">
          <span>{formatBytes(file.size_bytes)}</span>
          <span>{formatDate(file.updated_at || file.created_at)}</span>
        </div>
      </div>
    </div>
  );
};

export default FileItem;
