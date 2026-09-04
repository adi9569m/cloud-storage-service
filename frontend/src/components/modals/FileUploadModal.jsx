import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { X, UploadCloud, File as FileIcon, CheckCircle2, AlertCircle, Trash2 } from 'lucide-react';
import fileService from '../../services/fileService';
import { formatBytes, getFileIconDetails } from '../../utils/formatters';

export const FileUploadModal = ({ isOpen, onClose, folderId = null, folderName = 'Root', onSuccess }) => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState({});
  const [uploadStatus, setUploadStatus] = useState({});
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const onDrop = useCallback((acceptedFiles) => {
    setSelectedFiles((prev) => {
      const existingNames = new Set(prev.map((f) => f.name));
      const newUnique = acceptedFiles.filter((f) => !existingNames.has(f.name));
      return [...prev, ...newUnique];
    });
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
    maxSize: 500 * 1024 * 1024,
  });

  if (!isOpen) return null;

  const removeFile = (index) => {
    if (isUploading) return;
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleStartUpload = async () => {
    if (selectedFiles.length === 0) return;

    setIsUploading(true);
    setErrorMessage('');
    let anySuccess = false;

    for (let i = 0; i < selectedFiles.length; i++) {
      const file = selectedFiles[i];
      const fileKey = `${file.name}-${i}`;

      setUploadStatus((prev) => ({ ...prev, [fileKey]: 'uploading' }));
      setUploadProgress((prev) => ({ ...prev, [fileKey]: 0 }));

      try {
        await fileService.directUpload(file, folderId, (percent) => {
          setUploadProgress((prev) => ({ ...prev, [fileKey]: percent }));
        });

        setUploadStatus((prev) => ({ ...prev, [fileKey]: 'success' }));
        anySuccess = true;
      } catch (err) {
        setUploadStatus((prev) => ({ ...prev, [fileKey]: 'error' }));
        setErrorMessage(
          err.response?.data?.detail || `Failed to upload ${file.name}. Storage quota or limit exceeded.`
        );
      }
    }

    setIsUploading(false);
    if (anySuccess) {
      onSuccess?.();
    }
  };

  const allCompleted =
    selectedFiles.length > 0 &&
    selectedFiles.every((_, i) => {
      const st = uploadStatus[`${selectedFiles[i].name}-${i}`];
      return st === 'success' || st === 'error';
    });

  const handleClose = () => {
    if (isUploading) return;
    setSelectedFiles([]);
    setUploadProgress({});
    setUploadStatus({});
    setErrorMessage('');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-modal transition-all animate-in zoom-in-95 duration-150 flex flex-col max-h-[90vh]">

        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-drive-50 text-drive-600">
              <UploadCloud className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-800">Upload Files</h3>
              <p className="text-xs text-slate-500">Destination: <span className="font-semibold text-slate-700">{folderName}</span></p>
            </div>
          </div>
          <button
            onClick={handleClose}
            disabled={isUploading}
            className="rounded-full p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 focus:outline-none disabled:opacity-50"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="mt-4 flex-1 overflow-y-auto space-y-4 pr-1">
          {errorMessage && (
            <div className="rounded-xl bg-red-50 p-3 text-xs text-red-600 border border-red-200">
              {errorMessage}
            </div>
          )}

          <div
            {...getRootProps()}
            className={`flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-6 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-drive-500 bg-drive-50/50'
                : 'border-slate-200 bg-slate-50/50 hover:bg-slate-50 hover:border-slate-300'
            }`}
          >
            <input {...getInputProps()} />
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white shadow-sm text-drive-600 mb-3">
              <UploadCloud className="h-6 w-6" />
            </div>
            <p className="text-sm font-semibold text-slate-700">
              {isDragActive ? 'Drop the files here...' : 'Click to browse or drag & drop files here'}
            </p>
            <p className="mt-1 text-xs text-slate-400">
              Supports documents, images, audio, video, code, archives up to 500 MB each
            </p>
          </div>

          {selectedFiles.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-600 px-1">
                <span>Selected Files ({selectedFiles.length})</span>
                <span>Total: {formatBytes(selectedFiles.reduce((acc, f) => acc + f.size, 0))}</span>
              </div>

              <div className="divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white max-h-48 overflow-y-auto">
                {selectedFiles.map((file, idx) => {
                  const fileKey = `${file.name}-${idx}`;
                  const { icon: Icon, color, bg } = getFileIconDetails(file.type, file.name);
                  const status = uploadStatus[fileKey];
                  const progress = uploadProgress[fileKey] || 0;

                  return (
                    <div key={fileKey} className="flex items-center justify-between p-3 gap-3 text-xs">
                      <div className="flex items-center gap-2.5 overflow-hidden flex-1">
                        <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${bg} ${color}`}>
                          <Icon className="h-4 w-4" />
                        </div>
                        <div className="overflow-hidden flex-1">
                          <p className="truncate font-medium text-slate-800">{file.name}</p>
                          <p className="text-[11px] text-slate-400">{formatBytes(file.size)}</p>
                          {status === 'uploading' && (
                            <div className="mt-1.5 h-1 w-full rounded-full bg-slate-100 overflow-hidden">
                              <div
                                className="h-full bg-drive-600 transition-all duration-150"
                                style={{ width: `${progress}%` }}
                              />
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="shrink-0 flex items-center gap-2">
                        {status === 'success' && <CheckCircle2 className="h-4 w-4 text-emerald-500" />}
                        {status === 'error' && <AlertCircle className="h-4 w-4 text-rose-500" />}
                        {!status && !isUploading && (
                          <button
                            onClick={() => removeFile(idx)}
                            className="rounded-full p-1 text-slate-400 hover:bg-slate-100 hover:text-rose-500 transition-colors"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 mt-4">
          <button
            type="button"
            onClick={handleClose}
            disabled={isUploading}
            className="rounded-xl px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors disabled:opacity-50"
          >
            {allCompleted ? 'Done' : 'Cancel'}
          </button>
          {!allCompleted && (
            <button
              type="button"
              onClick={handleStartUpload}
              disabled={isUploading || selectedFiles.length === 0}
              className="flex items-center gap-2 rounded-xl bg-drive-600 px-5 py-2 text-xs font-semibold text-white hover:bg-drive-700 disabled:opacity-50 transition-colors shadow-sm"
            >
              <UploadCloud className="h-4 w-4" />
              <span>{isUploading ? 'Uploading...' : `Upload (${selectedFiles.length})`}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default FileUploadModal;
