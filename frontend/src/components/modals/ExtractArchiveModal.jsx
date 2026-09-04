import React, { useState } from 'react';
import { X, Archive, FolderCheck, Loader2 } from 'lucide-react';
import fileService from '../../services/fileService';
import { useToast } from '../../context/ToastContext';

export const ExtractArchiveModal = ({ isOpen, onClose, file, currentFolderId = null, onSuccess }) => {
  const [createSubfolder, setCreateSubfolder] = useState(true);
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState('');
  const { addToast } = useToast();

  if (!isOpen || !file) return null;

  const handleExtract = async (e) => {
    e.preventDefault();
    setIsExtracting(true);
    setError('');

    try {
      const res = await fileService.extractArchive(file.id, {
        destination_folder_id: currentFolderId,
        create_subfolder: createSubfolder,
      });

      addToast({
        type: 'success',
        title: 'Archive Extracted',
        message: `Extracted ${res.files_count} file(s) across ${res.folders_count} folder(s).`,
      });

      onSuccess?.();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to extract archive.');
    } finally {
      setIsExtracting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-modal transition-all animate-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-50 text-amber-600">
              <Archive className="h-5 w-5" />
            </div>
            <h3 className="text-base font-semibold text-slate-800">Extract Archive</h3>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 focus:outline-none"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleExtract} className="mt-5 space-y-4">
          {error && (
            <div className="rounded-xl bg-red-50 p-3 text-xs text-red-600 border border-red-200">
              {error}
            </div>
          )}

          <div className="rounded-xl bg-slate-50 p-3.5 border border-slate-200">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Archive File</p>
            <p className="mt-1 text-sm font-semibold text-slate-800 truncate">{file.name}</p>
          </div>

          <label className="flex items-start gap-3 rounded-xl border border-slate-200 p-3 cursor-pointer hover:bg-slate-50 transition-colors">
            <input
              type="checkbox"
              checked={createSubfolder}
              onChange={(e) => setCreateSubfolder(e.target.checked)}
              className="mt-0.5 h-4 w-4 rounded border-slate-300 text-drive-600 focus:ring-drive-500"
            />
            <div className="text-xs">
              <p className="font-semibold text-slate-700">Extract into dedicated folder</p>
              <p className="text-slate-500 mt-0.5">Creates a new folder matching the archive name.</p>
            </div>
          </label>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              disabled={isExtracting}
              className="rounded-xl px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isExtracting}
              className="flex items-center gap-1.5 rounded-xl bg-drive-600 px-5 py-2 text-xs font-semibold text-white hover:bg-drive-700 disabled:opacity-50 transition-colors shadow-sm"
            >
              {isExtracting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Extracting...
                </>
              ) : (
                <>
                  <FolderCheck className="h-4 w-4" />
                  Extract Now
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ExtractArchiveModal;
