/**
 * Folder item component rendering in Grid or List layout.
 */

import React from 'react';
import { Folder, Star } from 'lucide-react';
import ContextMenu from './ContextMenu';
import { formatDate } from '../../utils/formatters';

export const FolderItem = ({
  folder,
  viewMode = 'grid',
  isSelected = false,
  onSelect,
  onOpen,
  onToggleStar,
  onDownload,
  onShare,
  onRename,
  onMove,
  onTags,
  onDelete,
}) => {
  const folderColor = folder.color || '#3B82F6';

  if (viewMode === 'list') {
    return (
      <div
        onClick={() => onSelect?.(folder.id)}
        onDoubleClick={() => onOpen?.(folder.id)}
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
              onSelect?.(folder.id);
            }}
            className="h-4 w-4 rounded border-slate-300 text-drive-600 focus:ring-drive-500 cursor-pointer"
          />

          <Folder
            className="h-5 w-5 shrink-0 transition-transform group-hover:scale-105"
            style={{ color: folderColor }}
          />

          <span className="truncate font-semibold text-slate-800">
            {folder.name}
          </span>
        </div>

        <div className="flex items-center gap-6 text-slate-500">
          <span className="hidden md:inline text-[11px]">
            {formatDate(folder.updated_at || folder.created_at)}
          </span>
          <span className="hidden sm:inline text-[11px] w-16 text-right">—</span>

          <div className="flex items-center gap-1">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggleStar?.(folder);
              }}
              className={`rounded-lg p-1 transition-colors ${
                folder.is_starred
                  ? 'text-amber-500'
                  : 'text-slate-300 opacity-0 group-hover:opacity-100 hover:text-amber-500'
              }`}
              title={folder.is_starred ? 'Remove Star' : 'Star'}
            >
              <Star className={`h-4 w-4 ${folder.is_starred ? 'fill-amber-500' : ''}`} />
            </button>

            <ContextMenu
              item={folder}
              isFolder={true}
              onDownload={onDownload}
              onShare={onShare}
              onToggleStar={onToggleStar}
              onRename={onRename}
              onMove={onMove}
              onTags={onTags}
              onDelete={onDelete}
            />
          </div>
        </div>
      </div>
    );
  }

  // Grid Card View
  return (
    <div
      onClick={() => onSelect?.(folder.id)}
      onDoubleClick={() => onOpen?.(folder.id)}
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
              onSelect?.(folder.id);
            }}
            className={`h-4 w-4 rounded border-slate-300 text-drive-600 focus:ring-drive-500 cursor-pointer ${
              isSelected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
            }`}
          />
          <Folder
            className="h-7 w-7 shrink-0 transition-transform group-hover:scale-105"
            style={{ color: folderColor }}
          />
        </div>

        <div className="flex items-center gap-0.5">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleStar?.(folder);
            }}
            className={`rounded-lg p-1 transition-colors ${
              folder.is_starred
                ? 'text-amber-500'
                : 'text-slate-300 opacity-0 group-hover:opacity-100 hover:text-amber-500'
            }`}
            title={folder.is_starred ? 'Remove Star' : 'Star'}
          >
            <Star className={`h-4 w-4 ${folder.is_starred ? 'fill-amber-500' : ''}`} />
          </button>

          <ContextMenu
            item={folder}
            isFolder={true}
            onDownload={onDownload}
            onShare={onShare}
            onToggleStar={onToggleStar}
            onRename={onRename}
            onMove={onMove}
            onTags={onTags}
            onDelete={onDelete}
          />
        </div>
      </div>

      <div className="mt-3">
        <h4 className="truncate font-semibold text-slate-800" title={folder.name}>
          {folder.name}
        </h4>
        <p className="mt-1 text-[11px] text-slate-400">
          {formatDate(folder.updated_at || folder.created_at)}
        </p>
      </div>
    </div>
  );
};

export default FolderItem;
