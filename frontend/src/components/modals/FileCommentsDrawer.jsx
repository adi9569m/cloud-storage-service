import React, { useState, useEffect } from 'react';
import { X, MessageSquare, Send, Trash2, Clock, User } from 'lucide-react';
import fileService from '../../services/fileService';
import { formatDate } from '../../utils/formatters';

export const FileCommentsDrawer = ({ isOpen, onClose, file }) => {
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen && file) {
      loadComments();
    }
  }, [isOpen, file]);

  if (!isOpen || !file) return null;

  const loadComments = async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await fileService.listComments(file.id);
      setComments(data?.comments || data || []);
    } catch (err) {
      setError('Failed to load comments.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    setIsSubmitting(true);
    setError('');
    try {
      await fileService.addComment(file.id, newComment.trim());
      setNewComment('');
      loadComments();
    } catch (err) {
      setError('Failed to post comment.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteComment = async (commentId) => {
    try {
      await fileService.deleteComment(commentId);
      loadComments();
    } catch (err) {
      setError('Failed to delete comment.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="flex h-full w-full max-w-md flex-col bg-white shadow-2xl animate-in slide-in-from-right duration-200">

        <div className="flex items-center justify-between border-b border-slate-100 p-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-drive-50 text-drive-600">
              <MessageSquare className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-800">Comments</h3>
              <p className="text-xs text-slate-400 truncate max-w-[220px]">{file.name}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 focus:outline-none"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {error && (
            <div className="rounded-xl bg-red-50 p-2.5 text-xs text-red-600 border border-red-200">
              {error}
            </div>
          )}

          {isLoading ? (
            <div className="flex h-32 items-center justify-center text-xs text-slate-400">
              Loading comments...
            </div>
          ) : comments.length === 0 ? (
            <div className="flex h-48 flex-col items-center justify-center text-center">
              <MessageSquare className="h-8 w-8 text-slate-300 mb-2" />
              <p className="text-xs font-semibold text-slate-600">No comments yet</p>
              <p className="text-[11px] text-slate-400 mt-1 max-w-[200px]">
                Start a discussion or leave notes on this file for your team.
              </p>
            </div>
          ) : (
            comments.map((c) => (
              <div
                key={c.id}
                className="group relative rounded-2xl border border-slate-100 bg-slate-50/50 p-3.5 transition-colors hover:bg-slate-50"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <div className="flex h-6 w-6 items-center justify-center rounded-full bg-drive-100 text-drive-700 text-[10px] font-bold">
                      {c.user_name ? c.user_name.charAt(0).toUpperCase() : 'U'}
                    </div>
                    <span className="text-xs font-semibold text-slate-700">
                      {c.user_name || 'Collaborator'}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-400">{formatDate(c.created_at)}</span>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-wrap pl-8">
                  {c.content}
                </p>

                <button
                  onClick={() => handleDeleteComment(c.id)}
                  className="absolute top-3 right-3 hidden group-hover:block p-1 text-slate-400 hover:text-red-600"
                  title="Delete comment"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            ))
          )}
        </div>

        <form onSubmit={handleAddComment} className="border-t border-slate-100 p-4 bg-white">
          <div className="flex gap-2">
            <input
              type="text"
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Add a comment or note..."
              className="flex-1 rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-800 placeholder-slate-400 focus:border-drive-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-drive-100"
            />
            <button
              type="submit"
              disabled={isSubmitting || !newComment.trim()}
              className="flex items-center justify-center rounded-xl bg-drive-600 px-4 py-2.5 text-white hover:bg-drive-700 disabled:opacity-50 transition-colors shadow-sm"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default FileCommentsDrawer;
