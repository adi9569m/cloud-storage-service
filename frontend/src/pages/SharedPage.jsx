/**
 * Shared with me files and folders view.
 */

import React from 'react';
import { Users, Shield } from 'lucide-react';

export const SharedPage = () => {
  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 pb-4">
        <h1 className="text-2xl font-bold tracking-tight text-slate-800">Shared with me</h1>
        <p className="text-xs text-slate-500 mt-1">
          Files and directories shared with your account by other collaborators.
        </p>
      </div>

      <div className="flex flex-col items-center justify-center rounded-3xl border-2 border-dashed border-slate-200 bg-white p-12 text-center shadow-sm">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-drive-50 text-drive-600 mb-4">
          <Users className="h-8 w-8" />
        </div>
        <h3 className="text-base font-semibold text-slate-800">No shared files yet</h3>
        <p className="mt-1.5 max-w-sm text-xs text-slate-500">
          When colleagues share files or folders with you, they will appear here.
        </p>
      </div>
    </div>
  );
};

export default SharedPage;
