import React, { useState, useEffect } from 'react';
import { X, Tag as TagIcon, Plus, Check, Trash2, Palette } from 'lucide-react';
import tagService from '../../services/tagService';

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

export const TagManagerModal = ({ isOpen, onClose, item, isFolder = false, onTagsUpdated }) => {
  const [allTags, setAllTags] = useState([]);
  const [attachedTagIds, setAttachedTagIds] = useState(new Set());
  const [newTagName, setNewTagName] = useState('');
  const [selectedColor, setSelectedColor] = useState('#3B82F6');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen && item) {
      loadTags();
    }
  }, [isOpen, item]);

  if (!isOpen || !item) return null;

  const loadTags = async () => {
    setIsLoading(true);
    setError('');
    try {
      const [userTags, itemTags] = await Promise.all([
        tagService.listTags(),
        isFolder ? tagService.getFolderTags(item.id) : tagService.getFileTags(item.id),
      ]);

      setAllTags(userTags || []);
      const attached = new Set((itemTags || []).map((t) => t.id));
      setAttachedTagIds(attached);
    } catch (err) {
      setError('Failed to load tags.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateTag = async (e) => {
    e.preventDefault();
    if (!newTagName.trim()) return;

    setError('');
    try {
      const created = await tagService.createTag({
        name: newTagName.trim(),
        color: selectedColor,
      });

      await tagService.attachTag({
        tag_id: created.id,
        ...(isFolder ? { folder_id: item.id } : { file_id: item.id }),
      });

      setNewTagName('');
      loadTags();
      onTagsUpdated?.();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create tag.');
    }
  };

  const handleToggleTag = async (tagId) => {
    const isAttached = attachedTagIds.has(tagId);
    try {
      if (isAttached) {
        await tagService.detachTag({
          tag_id: tagId,
          ...(isFolder ? { folder_id: item.id } : { file_id: item.id }),
        });
        setAttachedTagIds((prev) => {
          const next = new Set(prev);
          next.delete(tagId);
          return next;
        });
      } else {
        await tagService.attachTag({
          tag_id: tagId,
          ...(isFolder ? { folder_id: item.id } : { file_id: item.id }),
        });
        setAttachedTagIds((prev) => new Set(prev).add(tagId));
      }
      onTagsUpdated?.();
    } catch (err) {
      setError('Failed to update tag attachment.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-modal transition-all animate-in zoom-in-95 duration-150">

        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-drive-50 text-drive-600">
              <TagIcon className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-800">Manage Tags</h3>
              <p className="text-xs text-slate-500 truncate max-w-xs">{item.name}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 focus:outline-none"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {error && (
          <div className="mt-3 rounded-xl bg-red-50 p-3 text-xs text-red-600 border border-red-200">
            {error}
          </div>
        )}

        <div className="mt-4 space-y-2">
          <h4 className="text-xs font-semibold text-slate-700">Attach existing labels</h4>
          {isLoading ? (
            <p className="text-xs text-slate-400 py-3 text-center">Loading tags...</p>
          ) : allTags.length === 0 ? (
            <p className="text-xs text-slate-400 italic py-2">No tags created yet.</p>
          ) : (
            <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto p-1">
              {allTags.map((tag) => {
                const isAttached = attachedTagIds.has(tag.id);
                return (
                  <button
                    key={tag.id}
                    onClick={() => handleToggleTag(tag.id)}
                    className={`flex items-center gap-2 rounded-xl px-3 py-1.5 text-xs font-medium border transition-all ${
                      isAttached
                        ? 'border-slate-800 bg-slate-900 text-white shadow-sm'
                        : 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    <span
                      className="h-2.5 w-2.5 rounded-full"
                      style={{ backgroundColor: tag.color || '#3B82F6' }}
                    />
                    <span>{tag.name}</span>
                    {isAttached && <Check className="h-3.5 w-3.5 text-emerald-400" />}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <form onSubmit={handleCreateTag} className="mt-5 border-t border-slate-100 pt-4 space-y-3">
          <h4 className="text-xs font-semibold text-slate-700">Create new tag</h4>
          <div className="flex gap-2">
            <input
              type="text"
              value={newTagName}
              onChange={(e) => setNewTagName(e.target.value)}
              placeholder="Tag name (e.g. Work, Finance)..."
              className="flex-1 rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs text-slate-800 placeholder-slate-400 focus:border-drive-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-drive-100"
            />
            <button
              type="submit"
              disabled={!newTagName.trim()}
              className="flex items-center gap-1 rounded-xl bg-drive-600 px-4 py-2 text-xs font-semibold text-white hover:bg-drive-700 disabled:opacity-50 transition-colors shadow-sm"
            >
              <Plus className="h-4 w-4" />
              <span>Add</span>
            </button>
          </div>

          <div className="flex items-center gap-2 pt-1">
            {PRESET_COLORS.map((hex) => (
              <button
                key={hex}
                type="button"
                onClick={() => setSelectedColor(hex)}
                className={`h-6 w-6 rounded-full transition-transform focus:outline-none ${
                  selectedColor === hex
                    ? 'ring-2 ring-slate-800 ring-offset-2 scale-110'
                    : 'opacity-80 hover:opacity-100'
                }`}
                style={{ backgroundColor: hex }}
              />
            ))}
          </div>
        </form>

        <div className="mt-6 flex justify-end border-t border-slate-100 pt-4">
          <button
            onClick={onClose}
            className="rounded-xl bg-slate-100 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-200 transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};

export default TagManagerModal;
