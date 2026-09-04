import React, { useState, useRef, useEffect } from 'react';
import {
  MoreVertical,
  Eye,
  Download,
  Share2,
  Star,
  Edit2,
  FolderInput,
  Copy,
  Tag,
  History,
  MessageSquare,
  Trash2,
  Archive,
} from 'lucide-react';

export const ContextMenu = ({
  item,
  isFolder = false,
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
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  const handleAction = (callback) => {
    setIsOpen(false);
    callback?.(item);
  };

  return (
    <div className="relative inline-block" ref={menuRef}>
      <button
        onClick={(e) => {
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
        className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 focus:outline-none transition-colors"
        title="More actions"
      >
        <MoreVertical className="h-4 w-4" />
      </button>

      {isOpen && (
        <div
          onClick={(e) => e.stopPropagation()}
          className="absolute right-0 top-8 z-40 w-48 rounded-2xl border border-slate-200 bg-white p-1.5 shadow-modal animate-in fade-in zoom-in-95 duration-100 text-xs"
        >

          {!isFolder && onPreview && (
            <button
              onClick={() => handleAction(onPreview)}
              className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <Eye className="h-4 w-4 text-slate-500" />
              <span>Preview</span>
            </button>
          )}

          {onDownload && (
            <button
              onClick={() => handleAction(onDownload)}
              className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <Download className="h-4 w-4 text-slate-500" />
              <span>{isFolder ? 'Download ZIP' : 'Download'}</span>
            </button>
          )}

          {!isFolder && onExtract && (item.name?.toLowerCase().endsWith('.zip') || item.mime_type?.includes('zip')) && (
            <button
              onClick={() => handleAction(onExtract)}
              className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-amber-700 hover:bg-amber-50 transition-colors"
            >
              <Archive className="h-4 w-4 text-amber-600" />
              <span>Extract Archive</span>
            </button>
          )}

          {onShare && (
            <button
              onClick={() => handleAction(onShare)}
              className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <Share2 className="h-4 w-4 text-slate-500" />
              <span>Share & Links</span>
            </button>
          )}

          {onToggleStar && (
            <button
              onClick={() => handleAction(onToggleStar)}
              className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <Star
                className={`h-4 w-4 ${
                  item.is_starred ? 'text-amber-500 fill-amber-500' : 'text-slate-500'
                }`}
              />
              <span>{item.is_starred ? 'Remove Star' : 'Add Star'}</span>
            </button>
          )}

          {onTags && (
            <button
              onClick={() => handleAction(onTags)}
              className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <Tag className="h-4 w-4 text-slate-500" />
              <span>Tags & Labels</span>
            </button>
          )}

          <div className="my-1 border-t border-slate-100" />

          {onRename && (
            <button
              onClick={() => handleAction(onRename)}
              className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <Edit2 className="h-4 w-4 text-slate-500" />
              <span>Rename</span>
            </button>
          )}

          {onMove && (
            <button
              onClick={() => handleAction(onMove)}
              className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <FolderInput className="h-4 w-4 text-slate-500" />
              <span>Move to...</span>
            </button>
          )}

          {!isFolder && onCopy && (
            <button
              onClick={() => handleAction(onCopy)}
              className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <Copy className="h-4 w-4 text-slate-500" />
              <span>Make a copy</span>
            </button>
          )}

          {!isFolder && onVersions && (
            <button
              onClick={() => handleAction(onVersions)}
              className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <History className="h-4 w-4 text-slate-500" />
              <span>Version History</span>
            </button>
          )}

          {!isFolder && onComments && (
            <button
              onClick={() => handleAction(onComments)}
              className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <MessageSquare className="h-4 w-4 text-slate-500" />
              <span>Comments</span>
            </button>
          )}

          <div className="my-1 border-t border-slate-100" />

          {onDelete && (
            <button
              onClick={() => handleAction(onDelete)}
              className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-red-600 hover:bg-red-50 transition-colors"
            >
              <Trash2 className="h-4 w-4 text-red-500" />
              <span>Move to trash</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default ContextMenu;
