import React, { useState, useEffect } from 'react';
import {
  X,
  History,
  Download,
  UploadCloud,
  CheckCircle2,
  Clock,
  HardDrive,
  FileText,
} from 'lucide-react';
import fileService from '../../services/fileService';
import { formatBytes, formatDate } from '../../utils/formatters';

export const FileVersionModal = ({ isOpen, onClose, file, onVersionUploaded }) => {
  const [versions, setVersions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen && file) {
      loadVersions();
    }
  }, [isOpen, file]);

  if (!isOpen || !file) return null;

  const loadVersions = async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await fileService.listVersions(file.id);
      setVersions(data || []);
    } catch (err) {
      setError('Failed to load version history.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadVersion = (versionNumber) => {
    fileService.downloadFile(file.id, `${versionNumber}_${file.name}`, versionNumber);
  };

  const handleUploadNewVersion = async (e) => {
    const uploadedFile = e.target.files?.[0];
    if (!uploadedFile) return;

    setIsUploading(true);
    setError('');
    try {
      await fileService.uploadNewVersion(file.id, uploadedFile, (percent) => {
        setUploadProgress(percent);
      });
      setUploadProgress(0);
      loadVersions();
      onVersionUploaded?.();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload new version.');
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-modal transition-all animate-in zoom-in-95 duration-150">

        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-drive-50 text-drive-600">
              <History className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-800">Version History</h3>
              <p className="text-xs text-slate-500 truncate max-w-xs">{file.name}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 focus:outline-none"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3.5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-700">Upload New Snapshot</p>
              <p className="text-[11px] text-slate-500">Promotes new file as active version</p>
            </div>
            <label className="flex items-center gap-1.5 rounded-xl bg-drive-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-drive-700 cursor-pointer shadow-sm">
              <UploadCloud className="h-3.5 w-3.5" />
              <span>{isUploading ? `Uploading ${uploadProgress}%` : 'Upload Version'}</span>
              <input
                type="file"
                className="hidden"
                disabled={isUploading}
                onChange={handleUploadNewVersion}
              />
            </label>
          </div>
        </div>

        {error && (
          <div className="mt-3 rounded-xl bg-red-50 p-3 text-xs text-red-600 border border-red-200">
            {error}
          </div>
        )}

        <div className="mt-4 space-y-3">
          <h4 className="text-xs font-semibold text-slate-700">All Snapshots ({versions.length})</h4>

          {isLoading ? (
            <p className="text-xs text-slate-400 py-4 text-center">Loading versions...</p>
          ) : versions.length === 0 ? (
            <p className="text-xs text-slate-400 italic py-2">No version history found.</p>
          ) : (
            <div className="divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white max-h-60 overflow-y-auto">
              {versions.map((v) => (
                <div key={v.id} className="flex items-center justify-between p-3.5 text-xs">
                  <div className="flex items-center gap-3">
                    <div
                      className={`flex h-8 w-8 items-center justify-center rounded-lg font-bold ${
                        v.is_current
                          ? 'bg-emerald-50 text-emerald-600 border border-emerald-200'
                          : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      v{v.version_number}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-800">
                          {formatBytes(v.size_bytes)}
                        </span>
                        {v.is_current && (
                          <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold text-emerald-700">
                            Active
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400">{formatDate(v.created_at)}</p>
                    </div>
                  </div>

                  <button
                    onClick={() => handleDownloadVersion(v.version_number)}
                    className="flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors shadow-sm"
                    title={`Download version ${v.version_number}`}
                  >
                    <Download className="h-3.5 w-3.5" />
                    <span>Download</span>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mt-6 flex justify-end border-t border-slate-100 pt-4">
          <button
            onClick={onClose}
            className="rounded-xl bg-slate-100 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-200 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default FileVersionModal;
