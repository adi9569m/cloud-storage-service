import React from 'react';
import { ChevronRight, HardDrive, Home } from 'lucide-react';

export const Breadcrumbs = ({ breadcrumbs = [], currentFolderName = null, onNavigate }) => {
  return (
    <nav className="flex items-center gap-1.5 text-xs text-slate-500 overflow-x-auto py-1">

      <button
        onClick={() => onNavigate(null)}
        className="flex items-center gap-1.5 rounded-lg px-2 py-1 font-semibold text-slate-700 hover:bg-slate-100 hover:text-drive-600 transition-colors shrink-0"
      >
        <HardDrive className="h-4 w-4 text-drive-600" />
        <span>My Drive</span>
      </button>

      {breadcrumbs.map((crumb) => (
        <React.Fragment key={crumb.id}>
          <ChevronRight className="h-3.5 w-3.5 text-slate-400 shrink-0" />
          <button
            onClick={() => onNavigate(crumb.id)}
            className="truncate max-w-[140px] rounded-lg px-2 py-1 font-medium text-slate-600 hover:bg-slate-100 hover:text-drive-600 transition-colors"
            title={crumb.name}
          >
            {crumb.name}
          </button>
        </React.Fragment>
      ))}

      {currentFolderName && breadcrumbs.length === 0 && (
        <>
          <ChevronRight className="h-3.5 w-3.5 text-slate-400 shrink-0" />
          <span className="truncate max-w-[160px] font-semibold text-slate-800 px-2 py-1">
            {currentFolderName}
          </span>
        </>
      )}
    </nav>
  );
};

export default Breadcrumbs;
