/**
 * Layout grid/list view switcher and sorting dropdown.
 */

import React from 'react';
import { LayoutGrid, List, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';

export const ViewSwitcher = ({
  viewMode,
  onViewModeChange,
  sortBy,
  sortOrder,
  onSortChange,
}) => {
  const sortOptions = [
    { value: 'name', label: 'Name' },
    { value: 'created_at', label: 'Date Created' },
    { value: 'updated_at', label: 'Last Modified' },
    { value: 'size', label: 'File Size' },
  ];

  const handleToggleOrder = () => {
    onSortChange(sortBy, sortOrder === 'asc' ? 'desc' : 'asc');
  };

  return (
    <div className="flex items-center gap-2 text-xs">
      {/* Sort Select */}
      <div className="flex items-center gap-1 rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 shadow-sm">
        <span className="text-slate-400 font-medium hidden sm:inline">Sort:</span>
        <select
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value, sortOrder)}
          className="bg-transparent font-medium text-slate-700 focus:outline-none cursor-pointer"
        >
          {sortOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <button
          onClick={handleToggleOrder}
          className="rounded p-0.5 text-slate-500 hover:bg-slate-100 transition-colors"
          title={`Sort ${sortOrder === 'asc' ? 'Ascending' : 'Descending'}`}
        >
          {sortOrder === 'asc' ? <ArrowUp className="h-3.5 w-3.5" /> : <ArrowDown className="h-3.5 w-3.5" />}
        </button>
      </div>

      {/* Grid vs List View Buttons */}
      <div className="flex items-center rounded-xl border border-slate-200 bg-white p-0.5 shadow-sm">
        <button
          onClick={() => onViewModeChange('grid')}
          className={`rounded-lg p-1.5 transition-colors ${
            viewMode === 'grid'
              ? 'bg-drive-50 text-drive-700 shadow-xs'
              : 'text-slate-400 hover:text-slate-600'
          }`}
          title="Grid view"
        >
          <LayoutGrid className="h-4 w-4" />
        </button>
        <button
          onClick={() => onViewModeChange('list')}
          className={`rounded-lg p-1.5 transition-colors ${
            viewMode === 'list'
              ? 'bg-drive-50 text-drive-700 shadow-xs'
              : 'text-slate-400 hover:text-slate-600'
          }`}
          title="List view"
        >
          <List className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};

export default ViewSwitcher;
