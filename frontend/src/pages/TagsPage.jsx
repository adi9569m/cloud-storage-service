import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Tag as TagIcon,
  Plus,
  Trash2,
  Edit2,
  Folder as FolderIcon,
  RefreshCw,
  Eye,
  Download,
} from 'lucide-react';

import tagService from '../services/tagService';
import fileService from '../services/fileService';
import folderService from '../services/folderService';
import { formatBytes, formatDate, getFileIconDetails } from '../utils/formatters';

import FilePreviewModal from '../components/modals/FilePreviewModal';

const PRESET_COLORS = [
  '#3B82F6',
  '#10B981',
  '#F59E0B',
  '#EF4444',
  '#8B5CF6',
  '#EC4899',
  '#06B6D4',
  '#64748B',
];

export const TagsPage = () => {
  const navigate = useNavigate();
  const [tags, setTags] = useState([]);
  const [selectedTag, setSelectedTag] = useState(null);
  const [taggedItems, setTaggedItems] = useState({ files: [], folders: [] });

  const [newTagName, setNewTagName] = useState('');
  const [selectedColor, setSelectedColor] = useState('#3B82F6');
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingItems, setIsLoadingItems] = useState(false);
  const [error, setError] = useState('');

  const [previewFile, setPreviewFile] = useState(null);

  const loadTags = async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await tagService.listTags();
      setTags(data || []);
      if (data && data.length > 0 && !selectedTag) {
        setSelectedTag(data[0]);
      }
    } catch (err) {
      setError('Failed to load tags.');
    } finally {
      setIsLoading(false);
    }
  };

  const loadTaggedItems = async (tagId) => {
    setIsLoadingItems(true);
    try {
      const res = await tagService.getTaggedItems(tagId);
      setTaggedItems(res || { files: [], folders: [] });
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingItems(false);
    }
  };

  useEffect(() => {
    loadTags();
  }, []);

  useEffect(() => {
    if (selectedTag) {
      loadTaggedItems(selectedTag.id);
    }
  }, [selectedTag]);

  const handleCreateTag = async (e) => {
    e.preventDefault();
    if (!newTagName.trim()) return;

    try {
      const created = await tagService.createTag({
        name: newTagName.trim(),
        color: selectedColor,
      });
      setNewTagName('');
      loadTags();
      setSelectedTag(created);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create tag.');
    }
  };

  const handleDeleteTag = async (tagId, e) => {
    e.stopPropagation();
    if (window.confirm('Delete this tag label? Items will not be deleted.')) {
      try {
        await tagService.deleteTag(tagId);
        if (selectedTag?.id === tagId) {
          setSelectedTag(null);
          setTaggedItems({ files: [], folders: [] });
        }
        loadTags();
      } catch (err) {
        setError('Failed to delete tag.');
      }
    }
  };

  return (
    <div className="space-y-6">

      <div className="flex items-center justify-between border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-800">Tags & Labels</h1>
          <p className="text-xs text-slate-500 mt-1">
            Organize files and folders into custom color-coded categories across your Drive.
          </p>
        </div>
        <button
          onClick={loadTags}
          className="rounded-xl border border-slate-200 bg-white p-2 text-slate-600 hover:bg-slate-50 transition-colors shadow-sm"
          title="Refresh"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {error && (
        <div className="rounded-2xl bg-red-50 p-4 text-xs text-red-600 border border-red-200">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">

        <div className="lg:col-span-1 space-y-4">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Create New Tag
            </h3>
            <form onSubmit={handleCreateTag} className="space-y-3">
              <input
                type="text"
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
                placeholder="Tag name (e.g. Work, Taxes)..."
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-800 placeholder-slate-400 focus:border-drive-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-drive-100"
              />

              <div className="flex items-center gap-1.5 flex-wrap">
                {PRESET_COLORS.map((hex) => (
                  <button
                    key={hex}
                    type="button"
                    onClick={() => setSelectedColor(hex)}
                    className={`h-5 w-5 rounded-full transition-transform focus:outline-none ${
                      selectedColor === hex
                        ? 'ring-2 ring-slate-800 ring-offset-2 scale-110'
                        : 'opacity-80 hover:opacity-100'
                    }`}
                    style={{ backgroundColor: hex }}
                  />
                ))}
              </div>

              <button
                type="submit"
                disabled={!newTagName.trim()}
                className="flex w-full items-center justify-center gap-1.5 rounded-xl bg-drive-600 py-2 text-xs font-semibold text-white hover:bg-drive-700 disabled:opacity-50 transition-colors shadow-sm"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Add Tag</span>
              </button>
            </form>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-3 shadow-sm space-y-1">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 px-2 py-1.5">
              Tags ({tags.length})
            </h3>
            {tags.length === 0 ? (
              <p className="text-xs text-slate-400 italic p-2">No tags created yet.</p>
            ) : (
              tags.map((tag) => {
                const isSelected = selectedTag?.id === tag.id;
                return (
                  <div
                    key={tag.id}
                    onClick={() => setSelectedTag(tag)}
                    className={`group flex items-center justify-between rounded-xl px-3 py-2 text-xs font-medium cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-drive-50 text-drive-700 font-semibold shadow-xs'
                        : 'text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center gap-2 overflow-hidden">
                      <span
                        className="h-3 w-3 shrink-0 rounded-full"
                        style={{ backgroundColor: tag.color || '#3B82F6' }}
                      />
                      <span className="truncate">{tag.name}</span>
                    </div>

                    <button
                      onClick={(e) => handleDeleteTag(tag.id, e)}
                      className="rounded p-1 text-slate-400 opacity-0 group-hover:opacity-100 hover:bg-red-50 hover:text-red-600 transition-all"
                      title="Delete tag"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>

        <div className="lg:col-span-3 space-y-4">
          {selectedTag ? (
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <span
                    className="h-3.5 w-3.5 rounded-full"
                    style={{ backgroundColor: selectedTag.color || '#3B82F6' }}
                  />
                  <h2 className="text-base font-bold text-slate-800">
                    Items tagged with "{selectedTag.name}"
                  </h2>
                </div>
                <span className="text-xs text-slate-400">
                  {taggedItems.folders?.length || 0} folders • {taggedItems.files?.length || 0} files
                </span>
              </div>

              {isLoadingItems ? (
                <div className="flex h-48 items-center justify-center">
                  <RefreshCw className="h-6 w-6 animate-spin text-drive-600" />
                </div>
              ) : taggedItems.folders?.length === 0 && taggedItems.files?.length === 0 ? (
                <div className="flex flex-col items-center justify-center p-12 text-center">
                  <TagIcon className="h-8 w-8 text-slate-300 mb-2" />
                  <p className="text-xs font-semibold text-slate-600">No items with this tag</p>
                  <p className="text-[11px] text-slate-400 mt-1">
                    Attach this tag to files or folders from the 3-dots actions menu in My Drive.
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-slate-100">

                  {taggedItems.folders?.map((f) => (
                    <div
                      key={f.id}
                      className="flex items-center justify-between py-3 px-2 hover:bg-slate-50 rounded-xl text-xs"
                    >
                      <div className="flex items-center gap-2.5 overflow-hidden">
                        <FolderIcon
                          className="h-5 w-5 shrink-0"
                          style={{ color: f.color || '#3B82F6' }}
                        />
                        <span
                          onClick={() => navigate(`/?folder=${f.id}`)}
                          className="font-semibold text-slate-800 cursor-pointer hover:text-drive-600 truncate"
                        >
                          {f.name}
                        </span>
                      </div>
                      <button
                        onClick={() => folderService.downloadZip(f.id, f.name)}
                        className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                        title="Download ZIP"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                    </div>
                  ))}

                  {taggedItems.files?.map((f) => {
                    const { icon: Icon, color, bg } = getFileIconDetails(f.mime_type, f.name);
                    return (
                      <div
                        key={f.id}
                        className="flex items-center justify-between py-3 px-2 hover:bg-slate-50 rounded-xl text-xs"
                      >
                        <div className="flex items-center gap-2.5 overflow-hidden">
                          <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${bg} ${color}`}>
                            <Icon className="h-4 w-4" />
                          </div>
                          <div className="overflow-hidden">
                            <p
                              onClick={() => setPreviewFile(f)}
                              className="font-medium text-slate-800 cursor-pointer hover:text-drive-600 truncate"
                            >
                              {f.name}
                            </p>
                            <span className="text-[11px] text-slate-400">
                              {formatBytes(f.size_bytes)}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => setPreviewFile(f)}
                            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                            title="Preview"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => fileService.downloadFile(f.id, f.name)}
                            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                            title="Download"
                          >
                            <Download className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center rounded-3xl border-2 border-dashed border-slate-200 bg-white p-12 text-center shadow-sm">
              <TagIcon className="h-8 w-8 text-slate-300 mb-2" />
              <p className="text-sm font-semibold text-slate-600">Select a tag</p>
              <p className="text-xs text-slate-400 mt-1">
                Choose a tag from the left panel to browse its associated files.
              </p>
            </div>
          )}
        </div>
      </div>

      <FilePreviewModal
        isOpen={Boolean(previewFile)}
        file={previewFile}
        onClose={() => setPreviewFile(null)}
      />
    </div>
  );
};

export default TagsPage;
