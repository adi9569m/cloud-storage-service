/**
 * Universal file preview modal supporting images, video, audio, PDF, and code/text inspection.
 */

import React, { useState, useEffect } from 'react';
import {
  X,
  Download,
  Share2,
  Star,
  ExternalLink,
  FileText,
  FileCode,
  Sparkles,
  Info,
  Calendar,
  HardDrive,
  Layers,
  History,
} from 'lucide-react';
import fileService from '../../services/fileService';
import { formatBytes, formatDate, getFileCategory, getFileIconDetails } from '../../utils/formatters';

export const FilePreviewModal = ({
  isOpen,
  onClose,
  file,
  onToggleStar,
  onShare,
  onOpenVersions,
}) => {
  const [textContent, setTextContent] = useState(null);
  const [isLoadingText, setIsLoadingText] = useState(false);
  const [textError, setTextError] = useState('');
  const [isStarred, setIsStarred] = useState(file?.is_starred || false);

  useEffect(() => {
    if (file) {
      setIsStarred(file.is_starred);
      const category = getFileCategory(file.mime_type, file.name);
      if (category === 'code' || category === 'document') {
        fetchTextContent(file.id);
      } else {
        setTextContent(null);
      }
    }
  }, [file]);

  if (!isOpen || !file) return null;

  const category = getFileCategory(file.mime_type, file.name);
  const { icon: Icon, color, bg } = getFileIconDetails(file.mime_type, file.name);
  const previewStreamUrl = fileService.getPreviewUrl(file.id);

  const fetchTextContent = async (fileId) => {
    setIsLoadingText(true);
    setTextError('');
    try {
      const data = await fileService.getTextContent(fileId);
      setTextContent(data);
    } catch (err) {
      setTextError('Unable to preview text content.');
    } finally {
      setIsLoadingText(false);
    }
  };

  const handleStarClick = async () => {
    try {
      await fileService.toggleStar(file.id);
      setIsStarred(!isStarred);
      onToggleStar?.(file.id);
    } catch (err) {
      console.error(err);
    }
  };

  const handleDownload = () => {
    fileService.downloadFile(file.id, file.name);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-2 md:p-6 animate-in fade-in duration-200">
      <div className="relative flex h-full max-h-[92vh] w-full max-w-6xl flex-col rounded-3xl bg-slate-900 text-white shadow-2xl overflow-hidden border border-slate-800">
        {/* Top Navigation Bar */}
        <div className="flex h-16 shrink-0 items-center justify-between border-b border-slate-800 bg-slate-900/90 px-4 md:px-6 backdrop-blur">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${bg} ${color}`}>
              <Icon className="h-5 w-5" />
            </div>
            <div className="overflow-hidden">
              <h2 className="truncate text-sm md:text-base font-semibold text-white">
                {file.name}
              </h2>
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <span>{formatBytes(file.size_bytes)}</span>
                <span>•</span>
                <span>{formatDate(file.updated_at || file.created_at)}</span>
              </div>
            </div>
          </div>

          {/* Action Toolbar */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleStarClick}
              title={isStarred ? 'Unstar' : 'Star'}
              className={`rounded-xl p-2 transition-colors ${
                isStarred
                  ? 'bg-amber-500/20 text-amber-400 hover:bg-amber-500/30'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <Star className={`h-4 w-4 ${isStarred ? 'fill-amber-400' : ''}`} />
            </button>

            {onShare && (
              <button
                onClick={() => onShare(file)}
                title="Share"
                className="rounded-xl p-2 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
              >
                <Share2 className="h-4 w-4" />
              </button>
            )}

            {onOpenVersions && (
              <button
                onClick={() => onOpenVersions(file)}
                title="Version History"
                className="rounded-xl p-2 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
              >
                <History className="h-4 w-4" />
              </button>
            )}

            <button
              onClick={handleDownload}
              title="Download File"
              className="flex items-center gap-1.5 rounded-xl bg-drive-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-drive-700 transition-colors shadow-sm"
            >
              <Download className="h-4 w-4" />
              <span className="hidden sm:inline">Download</span>
            </button>

            <button
              onClick={onClose}
              className="rounded-xl p-2 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors focus:outline-none"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Content Viewer Body */}
        <div className="flex flex-1 overflow-hidden">
          {/* Main Display Area */}
          <div className="flex flex-1 items-center justify-center bg-slate-950/60 p-4 overflow-auto">
            {/* 1. Image Preview */}
            {category === 'image' && (
              <img
                src={previewStreamUrl}
                alt={file.name}
                className="max-h-full max-w-full rounded-xl object-contain shadow-lg"
              />
            )}

            {/* 2. Video Preview */}
            {category === 'video' && (
              <video
                controls
                autoPlay
                className="max-h-full max-w-full rounded-2xl shadow-lg focus:outline-none"
                src={previewStreamUrl}
              >
                Your browser does not support HTML5 video streaming.
              </video>
            )}

            {/* 3. Audio Preview */}
            {category === 'audio' && (
              <div className="flex flex-col items-center justify-center gap-6 p-8 rounded-3xl bg-slate-900 border border-slate-800 shadow-xl max-w-md w-full">
                <div className="flex h-24 w-24 items-center justify-center rounded-3xl bg-amber-500/20 text-amber-400">
                  <Icon className="h-12 w-12" />
                </div>
                <div className="text-center">
                  <h3 className="text-base font-semibold">{file.name}</h3>
                  <p className="text-xs text-slate-400 mt-1">{formatBytes(file.size_bytes)}</p>
                </div>
                <audio controls className="w-full" src={previewStreamUrl}>
                  Your browser does not support audio playback.
                </audio>
              </div>
            )}

            {/* 4. PDF Preview */}
            {category === 'pdf' && (
              <iframe
                src={previewStreamUrl}
                title={file.name}
                className="h-full w-full rounded-xl border border-slate-800 bg-white"
              />
            )}

            {/* 5. Code & Text Inspection */}
            {(category === 'code' || category === 'document') && (
              <div className="h-full w-full overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 flex flex-col font-mono text-xs">
                <div className="flex items-center justify-between border-b border-slate-800 bg-slate-950 px-4 py-2 text-slate-400">
                  <div className="flex items-center gap-2">
                    <FileCode className="h-4 w-4 text-blue-400" />
                    <span>{file.name}</span>
                  </div>
                  {textContent && (
                    <span>{textContent.line_count} lines • {textContent.encoding}</span>
                  )}
                </div>

                <div className="flex-1 overflow-auto p-4 text-slate-200">
                  {isLoadingText ? (
                    <div className="flex h-full items-center justify-center text-slate-400">
                      Loading code preview...
                    </div>
                  ) : textError ? (
                    <div className="flex h-full flex-col items-center justify-center gap-3 text-slate-400">
                      <p>{textError}</p>
                      <button
                        onClick={handleDownload}
                        className="rounded-xl bg-slate-800 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-700"
                      >
                        Download File Instead
                      </button>
                    </div>
                  ) : (
                    <pre className="leading-relaxed whitespace-pre-wrap selection:bg-drive-600">
                      {textContent?.content || 'Empty file'}
                    </pre>
                  )}
                </div>
              </div>
            )}

            {/* 6. Fallback Generic File Display */}
            {category !== 'image' &&
              category !== 'video' &&
              category !== 'audio' &&
              category !== 'pdf' &&
              category !== 'code' &&
              category !== 'document' && (
                <div className="flex flex-col items-center justify-center gap-4 text-center p-8">
                  <div className={`flex h-20 w-20 items-center justify-center rounded-3xl ${bg} ${color}`}>
                    <Icon className="h-10 w-10" />
                  </div>
                  <h3 className="text-base font-semibold">{file.name}</h3>
                  <p className="max-w-xs text-xs text-slate-400">
                    No inline preview available for this file format ({file.mime_type || 'Unknown MIME'}).
                  </p>
                  <button
                    onClick={handleDownload}
                    className="flex items-center gap-2 rounded-xl bg-drive-600 px-5 py-2.5 text-xs font-semibold text-white hover:bg-drive-700 shadow-md"
                  >
                    <Download className="h-4 w-4" />
                    Download File ({formatBytes(file.size_bytes)})
                  </button>
                </div>
              )}
          </div>

          {/* Right Info Sidebar */}
          <div className="hidden lg:flex w-72 flex-col border-l border-slate-800 bg-slate-900/60 p-5 text-xs space-y-5">
            <div className="flex items-center gap-2 font-semibold text-slate-200">
              <Info className="h-4 w-4 text-drive-400" />
              <span>File Details</span>
            </div>

            <div className="space-y-4 text-slate-300">
              <div>
                <span className="text-[11px] text-slate-500 uppercase tracking-wider">Type</span>
                <p className="mt-0.5 font-medium">{file.mime_type || 'Generic file'}</p>
              </div>

              <div>
                <span className="text-[11px] text-slate-500 uppercase tracking-wider">Size</span>
                <p className="mt-0.5 font-medium">{formatBytes(file.size_bytes)}</p>
              </div>

              <div>
                <span className="text-[11px] text-slate-500 uppercase tracking-wider">Created</span>
                <p className="mt-0.5 font-medium">{formatDate(file.created_at)}</p>
              </div>

              <div>
                <span className="text-[11px] text-slate-500 uppercase tracking-wider">Modified</span>
                <p className="mt-0.5 font-medium">{formatDate(file.updated_at || file.created_at)}</p>
              </div>

              <div>
                <span className="text-[11px] text-slate-500 uppercase tracking-wider">Active Version</span>
                <p className="mt-0.5 font-medium">Version {file.current_version_number || 1}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FilePreviewModal;
