/**
 * Starred favorite items view.
 */

import React from 'react';
import { Star } from 'lucide-react';

export const StarredPage = () => {
  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 pb-4">
        <h1 className="text-2xl font-bold tracking-tight text-slate-800">Starred</h1>
        <p className="text-xs text-slate-500 mt-1">
          Quickly access your starred and favorite files and directories.
        </p>
      </div>

      <div className="flex flex-col items-center justify-center rounded-3xl border-2 border-dashed border-slate-200 bg-white p-12 text-center shadow-sm">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-50 text-amber-500 mb-4">
          <Star className="h-8 w-8" />
        </div>
        <h3 className="text-base font-semibold text-slate-800">No starred items</h3>
        <p className="mt-1.5 max-w-sm text-xs text-slate-500">
          Add stars to items you want to easily find again.
        </p>
      </div>
    </div>
  );
};

export default StarredPage;
