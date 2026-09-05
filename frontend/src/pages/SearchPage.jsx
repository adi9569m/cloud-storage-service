import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Search,
  Filter,
  Folder as FolderIcon,
  Star,
  Download,
  Eye,
  RefreshCw,
  SlidersHorizontal,
} from 'lucide-react';

import searchService from '../services/searchService';
import fileService from '../services/fileService';
import folderService from '../services/folderService';
import { formatBytes, formatDate, getFileIconDetails } from '../utils/formatters';

import FilePreviewModal from '../components/modals/FilePreviewModal';
import ShareModal from '../components/modals/ShareModal';

const TYPE_FILTERS = [
  { value: 'all', label: 'All Items' },
  { value: 'documents', label: 'Documents' },
  { value: 'images', label: 'Images' },
  { value: 'videos', label: 'Videos' },
  { value: 'audio', label: 'Audio' },
  { value: 'code', label: 'Code & Text' },
  { value: 'archives', label: 'Archives' },
  { value: 'folders', label: 'Folders Only' },
];

export const SearchPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const query = searchParams.get('q') || '';
  const [searchInput, setSearchInput] = useState(query);
  const [typeFilter, setTypeFilter] = useState('all');
  const [isStarredOnly, setIsStarredOnly] = useState(false);
  const [sortBy, setSortBy] = useState('updated_at');
  const [sortOrder, setSortOrder] = useState('desc');

  const [results, setResults] = useState({ items: [], total: 0, facets: {} });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const [previewFile, setPreviewFile] = useState(null);
  const [shareTarget, setShareTarget] = useState(null);

  useEffect(() => {
    setSearchInput(query);
    executeSearch();
  }, [query, typeFilter, isStarredOnly, sortBy, sortOrder]);

  const executeSearch = async () => {
    setIsLoading(true);
    setError('');
    try {
      const res = await searchService.search({
        q: query || undefined,
        type: typeFilter,
        is_starred: isStarredOnly ? true : undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        page_size: 50,
      });
      setResults(res || { items: [], total: 0, facets: {} });
    } catch (err) {
      setError('Search request failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchInput.trim()) {
      setSearchParams({ q: searchInput.trim() });
    } else {
      setSearchParams({});
    }
  };

  const items = results.items || [];

  return (
    <div className="space-y-6">

      <div className="flex flex-col gap-4 border-b border-slate-200 pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-800">Search Results</h1>
            <p className="text-xs text-slate-500 mt-1">
              {query ? (
                <>
                  Showing results for <span className="font-semibold text-slate-700">"{query}"</span> ({results.total} found)
                </>
              ) : (
                'Filter and explore all items in your Drive'
              )}
            </p>
          </div>

          <form onSubmit={handleSearchSubmit} className="flex gap-2 max-w-md w-full sm:w-auto">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-400" />
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Search filenames..."
                className="w-full rounded-xl border border-slate-200 bg-white py-2 pl-9 pr-4 text-xs text-slate-800 placeholder-slate-400 focus:border-drive-500 focus:outline-none focus:ring-2 focus:ring-drive-100 shadow-sm"
              />
            </div>
            <button
              type="submit"
              className="rounded-xl bg-drive-600 px-4 py-2 text-xs font-semibold text-white hover:bg-drive-700 transition-colors shadow-sm"
            >
              Search
            </button>
          </form>
        </div>

        <div className="flex flex-wrap items-center gap-2 pt-1">

          <div className="flex flex-wrap items-center gap-1.5 overflow-x-auto">
            {TYPE_FILTERS.map((f) => (
              <button
                key={f.value}
                onClick={() => setTypeFilter(f.value)}
                className={`rounded-xl px-3 py-1.5 text-xs font-semibold transition-colors ${
                  typeFilter === f.value
                    ? 'bg-drive-600 text-white shadow-xs'
                    : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          <div className="h-4 w-px bg-slate-200 mx-1 hidden md:block" />

          <button
            onClick={() => setIsStarredOnly(!isStarredOnly)}
            className={`flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs font-semibold transition-colors ${
              isStarredOnly
                ? 'bg-amber-100 text-amber-800 border border-amber-300'
                : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
          >
            <Star className={`h-3.5 w-3.5 ${isStarredOnly ? 'fill-amber-500 text-amber-500' : 'text-slate-400'}`} />
            <span>Starred</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-2xl bg-red-50 p-4 text-xs text-red-600 border border-red-200">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <RefreshCw className="h-8 w-8 animate-spin text-drive-600" />
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-3xl border-2 border-dashed border-slate-200 bg-white p-12 text-center shadow-sm">
          <Search className="h-10 w-10 text-slate-300 mb-3" />
          <h3 className="text-base font-semibold text-slate-800">No matching items found</h3>
          <p className="mt-1.5 max-w-sm text-xs text-slate-500">
            Try adjusting your search keywords or switching category filters.
          </p>
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden divide-y divide-slate-100">
          <div className="grid grid-cols-12 bg-slate-50 px-4 py-3 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
            <div className="col-span-6">Name</div>
            <div className="col-span-3">Modified</div>
            <div className="col-span-3 text-right">Size / Actions</div>
          </div>

          {items.map((item) => {
            const isFolder = item.resource_type?.toLowerCase() === 'folder';
            const iconDetails = isFolder
              ? null
              : getFileIconDetails(item.mime_type, item.name);

            return (
              <div
                key={item.id}
                className="grid grid-cols-12 items-center px-4 py-3 text-xs hover:bg-slate-50 transition-colors"
              >

                <div className="col-span-6 flex items-center gap-3 overflow-hidden">
                  {isFolder ? (
                    <FolderIcon
                      className="h-5 w-5 shrink-0"
                      style={{ color: item.color || '#3B82F6' }}
                    />
                  ) : (
                    <div
                      className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${iconDetails.bg} ${iconDetails.color}`}
                    >
                      <iconDetails.icon className="h-4 w-4" />
                    </div>
                  )}

                  <div className="overflow-hidden">
                    <p
                      onClick={() => {
                        if (isFolder) {
                          navigate(`/?folder=${item.id}`);
                        } else {
                          setPreviewFile(item);
                        }
                      }}
                      className="truncate font-semibold text-slate-800 cursor-pointer hover:text-drive-600 transition-colors"
                      title={item.name}
                    >
                      {item.name}
                    </p>
                    {item.folder_path && (
                      <span className="text-[10px] text-slate-400 truncate block">
                        in {item.folder_path}
                      </span>
                    )}
                  </div>
                </div>

                <div className="col-span-3 text-[11px] text-slate-500">
                  {formatDate(item.updated_at || item.created_at)}
                </div>

                <div className="col-span-3 flex items-center justify-end gap-2">
                  <span className="text-[11px] text-slate-500 mr-2 hidden sm:inline">
                    {isFolder ? 'Folder' : formatBytes(item.size_bytes)}
                  </span>

                  {!isFolder && (
                    <>
                      <button
                        onClick={() => setPreviewFile(item)}
                        className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                        title="Preview"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => fileService.downloadFile(item.id, item.name)}
                        className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                        title="Download"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                    </>
                  )}
                  {isFolder && (
                    <button
                      onClick={() => folderService.downloadZip(item.id, item.name)}
                      className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                      title="Download ZIP"
                    >
                      <Download className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <FilePreviewModal
        isOpen={Boolean(previewFile)}
        file={previewFile}
        onClose={() => setPreviewFile(null)}
      />

      <ShareModal
        isOpen={Boolean(shareTarget)}
        item={shareTarget?.item}
        isFolder={shareTarget?.isFolder}
        onClose={() => setShareTarget(null)}
      />
    </div>
  );
};

export default SearchPage;
