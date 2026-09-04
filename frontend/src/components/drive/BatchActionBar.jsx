import React from 'react';
import {
  X,
  Download,
  Star,
  FolderInput,
  Trash2,
  CheckSquare,
} from 'lucide-react';

export const BatchActionBar = ({
  selectedCount = 0,
  onClearSelection,
  onBatchDownload,
  onBatchStar,
  onBatchMove,
  onBatchDelete,
}) => {
  if (selectedCount === 0) return null;

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 flex items-center gap-3 rounded-2xl bg-slate-900 px-5 py-3 text-white shadow-2xl border border-slate-800 animate-in fade-in slide-in-from-bottom-5 duration-200 text-xs">
      <div className="flex items-center gap-2 border-r border-slate-700 pr-3">
        <CheckSquare className="h-4 w-4 text-drive-400" />
        <span className="font-semibold">{selectedCount} selected</span>
      </div>

      <div className="flex items-center gap-1.5">
        {onBatchDownload && (
          <button
            onClick={onBatchDownload}
            className="flex items-center gap-1.5 rounded-xl bg-slate-800 px-3 py-1.5 text-slate-200 hover:bg-slate-700 hover:text-white transition-colors"
            title="Download ZIP"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Download ZIP</span>
          </button>
        )}

        {onBatchStar && (
          <button
            onClick={onBatchStar}
            className="flex items-center gap-1.5 rounded-xl bg-slate-800 px-3 py-1.5 text-slate-200 hover:bg-slate-700 hover:text-amber-400 transition-colors"
            title="Star selected"
          >
            <Star className="h-3.5 w-3.5" />
            <span>Star</span>
          </button>
        )}

        {onBatchMove && (
          <button
            onClick={onBatchMove}
            className="flex items-center gap-1.5 rounded-xl bg-slate-800 px-3 py-1.5 text-slate-200 hover:bg-slate-700 hover:text-white transition-colors"
            title="Move selected"
          >
            <FolderInput className="h-3.5 w-3.5" />
            <span>Move</span>
          </button>
        )}

        {onBatchDelete && (
          <button
            onClick={onBatchDelete}
            className="flex items-center gap-1.5 rounded-xl bg-red-600/30 px-3 py-1.5 text-red-300 hover:bg-red-600 hover:text-white transition-colors"
            title="Delete selected"
          >
            <Trash2 className="h-3.5 w-3.5" />
            <span>Trash</span>
          </button>
        )}
      </div>

      <button
        onClick={onClearSelection}
        className="rounded-full p-1 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors ml-2"
        title="Deselect All"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
};

export default BatchActionBar;
