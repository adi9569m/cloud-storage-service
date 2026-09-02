/**
 * Trash bin items and retention view.
 */

import React from 'react';
import { Trash2, AlertTriangle } from 'lucide-react';

export const TrashPage = () => {
  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 pb-4">
        <h1 className="text-2xl font-bold tracking-tight text-slate-800">Trash</h1>
        <p className="text-xs text-slate-500 mt-1">
          Items in trash are automatically purged after 30 days.
        </p>
      </div>

      <div className="flex flex-col items-center justify-center rounded-3xl border-2 border-dashed border-slate-200 bg-white p-12 text-center shadow-sm">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-rose-50 text-rose-500 mb-4">
          <Trash2 className="h-8 w-8" />
        </div>
        <h3 className="text-base font-semibold text-slate-800">Trash is empty</h3>
        <p className="mt-1.5 max-w-sm text-xs text-slate-500">
          Deleted items moved to trash will appear here.
        </p>
      </div>
    </div>
  );
};

export default TrashPage;
