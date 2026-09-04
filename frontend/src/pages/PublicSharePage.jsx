import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Cloud,
  Download,
  Lock,
  Folder as FolderIcon,
  ShieldCheck,
  ChevronRight,
  HardDrive,
  RefreshCw,
  Eye,
  KeyRound,
} from 'lucide-react';

import linkShareService from '../services/linkShareService';
import { formatBytes, formatDate, getFileIconDetails, getFileCategory } from '../utils/formatters';

export const PublicSharePage = () => {
  const { token } = useParams();

  const [linkData, setLinkData] = useState(null);
  const [folderContents, setFolderContents] = useState(null);
  const [currentFolderId, setCurrentFolderId] = useState(null);
  const [password, setPassword] = useState('');
  const [passwordSubmitted, setPasswordSubmitted] = useState(false);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const loadPublicLink = async (pwd = null) => {
    setIsLoading(true);
    setError('');
    try {
      const data = await linkShareService.inspectPublicLink(token, pwd);
      setLinkData(data);

      if (!data.requires_password) {
        if (data.folder) {
          loadFolderContents(data.folder.id, pwd);
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'This share link is invalid or has expired.');
    } finally {
      setIsLoading(false);
    }
  };

  const loadFolderContents = async (folderId, pwd = null) => {
    try {
      const contents = await linkShareService.getPublicFolderContents(token, folderId, pwd);
      setFolderContents(contents);
      setCurrentFolderId(folderId);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (token) {
      loadPublicLink();
    }
  }, [token]);

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    if (!password.trim()) return;

    setIsLoading(true);
    setError('');
    try {
      const accessData = await linkShareService.accessWithPassword(token, password.trim());
      setLinkData(accessData);
      setPasswordSubmitted(true);
      if (accessData.folder) {
        loadFolderContents(accessData.folder.id, password.trim());
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Incorrect password.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadFile = () => {
    if (linkData?.file) {
      linkShareService.downloadPublicFile(token, linkData.file.name, password || null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col justify-between">

      <header className="flex h-16 items-center justify-between border-b border-slate-800 bg-slate-900/90 px-6 backdrop-blur">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-drive-600 text-white shadow-sm">
            <Cloud className="h-5 w-5" />
          </div>
          <span className="text-base font-semibold tracking-tight text-white">
            Cloud Storage Service
          </span>
        </Link>

        <div className="flex items-center gap-2 text-xs text-slate-400">
          <ShieldCheck className="h-4 w-4 text-emerald-400" />
          <span>Secure Shared Link</span>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center p-4 md:p-8">
        {isLoading ? (
          <div className="flex flex-col items-center gap-3 text-slate-400">
            <RefreshCw className="h-8 w-8 animate-spin text-drive-500" />
            <p className="text-xs">Loading shared content...</p>
          </div>
        ) : error ? (
          <div className="max-w-md w-full rounded-3xl border border-red-900/50 bg-red-950/30 p-8 text-center shadow-xl">
            <div className="flex h-16 w-16 mx-auto items-center justify-center rounded-2xl bg-red-900/30 text-red-400 mb-4">
              <Lock className="h-8 w-8" />
            </div>
            <h2 className="text-lg font-bold text-white">Link Unavailable</h2>
            <p className="mt-2 text-xs text-red-300">{error}</p>
            <Link
              to="/"
              className="mt-6 inline-block rounded-xl bg-slate-800 px-5 py-2 text-xs font-semibold text-white hover:bg-slate-700"
            >
              Go to Homepage
            </Link>
          </div>
        ) : linkData?.requires_password && !passwordSubmitted ? (

          <div className="max-w-md w-full rounded-3xl border border-slate-800 bg-slate-900 p-8 shadow-2xl">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-500/10 text-amber-400 mb-4">
              <KeyRound className="h-7 w-7" />
            </div>
            <h2 className="text-xl font-bold text-white">Password Protected Link</h2>
            <p className="mt-1 text-xs text-slate-400">
              This shared link requires a passcode to view and download files.
            </p>

            <form onSubmit={handlePasswordSubmit} className="mt-6 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Enter Link Password
                </label>
                <input
                  type="password"
                  autoFocus
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Password"
                  className="w-full rounded-xl border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:border-drive-500 focus:outline-none focus:ring-2 focus:ring-drive-500/30"
                />
              </div>
              <button
                type="submit"
                disabled={!password.trim()}
                className="w-full rounded-xl bg-drive-600 py-2.5 text-xs font-semibold text-white hover:bg-drive-700 disabled:opacity-50 transition-colors shadow-lg"
              >
                Unlock Access
              </button>
            </form>
          </div>
        ) : linkData?.file ? (

          <div className="max-w-2xl w-full rounded-3xl border border-slate-800 bg-slate-900/90 p-6 md:p-8 shadow-2xl backdrop-blur">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 pb-6 border-b border-slate-800">
              <div className="flex items-center gap-4 overflow-hidden">
                {(() => {
                  const details = getFileIconDetails(linkData.file.mime_type, linkData.file.name);
                  const Icon = details.icon;
                  return (
                    <div className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl ${details.bg} ${details.color}`}>
                      <Icon className="h-7 w-7" />
                    </div>
                  );
                })()}
                <div className="overflow-hidden">
                  <h1 className="truncate text-lg md:text-xl font-bold text-white" title={linkData.file.name}>
                    {linkData.file.name}
                  </h1>
                  <p className="text-xs text-slate-400 mt-1">
                    {formatBytes(linkData.file.size_bytes)} • Modified {formatDate(linkData.file.updated_at || linkData.file.created_at)}
                  </p>
                </div>
              </div>

              <button
                onClick={handleDownloadFile}
                className="flex items-center justify-center gap-2 rounded-xl bg-drive-600 px-6 py-3 text-xs font-semibold text-white hover:bg-drive-700 transition-colors shadow-lg shrink-0"
              >
                <Download className="h-4 w-4" />
                <span>Download ({formatBytes(linkData.file.size_bytes)})</span>
              </button>
            </div>

            {getFileCategory(linkData.file.mime_type, linkData.file.name) === 'image' && (
              <div className="mt-6 flex justify-center overflow-hidden rounded-2xl bg-slate-950 p-4 border border-slate-800">
                <img
                  src={`/api/v1/public/links/${token}/download${password ? `?password=${encodeURIComponent(password)}` : ''}`}
                  alt={linkData.file.name}
                  className="max-h-96 rounded-xl object-contain"
                />
              </div>
            )}
          </div>
        ) : linkData?.folder ? (

          <div className="max-w-4xl w-full rounded-3xl border border-slate-800 bg-slate-900/90 p-6 shadow-2xl backdrop-blur space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <FolderIcon className="h-7 w-7 text-drive-500" />
                <div>
                  <h1 className="text-lg font-bold text-white">{linkData.folder.name}</h1>
                  <p className="text-xs text-slate-400">Public shared directory</p>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden divide-y divide-slate-800/60 text-xs">
              {folderContents?.subfolders?.map((sf) => (
                <div
                  key={sf.id}
                  onClick={() => loadFolderContents(sf.id, password || null)}
                  className="flex items-center justify-between p-3.5 hover:bg-slate-900 cursor-pointer transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <FolderIcon className="h-5 w-5 text-drive-400" />
                    <span className="font-semibold text-slate-200">{sf.name}</span>
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-500" />
                </div>
              ))}

              {folderContents?.files?.map((f) => {
                const { icon: Icon, color, bg } = getFileIconDetails(f.mime_type, f.name);
                return (
                  <div
                    key={f.id}
                    className="flex items-center justify-between p-3.5 hover:bg-slate-900 transition-colors"
                  >
                    <div className="flex items-center gap-3 overflow-hidden">
                      <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${bg} ${color}`}>
                        <Icon className="h-4 w-4" />
                      </div>
                      <div className="overflow-hidden">
                        <p className="truncate font-medium text-slate-200">{f.name}</p>
                        <span className="text-[11px] text-slate-500">{formatBytes(f.size_bytes)}</span>
                      </div>
                    </div>
                  </div>
                );
              })}

              {folderContents?.subfolders?.length === 0 && folderContents?.files?.length === 0 && (
                <div className="p-8 text-center text-slate-500">Folder is empty.</div>
              )}
            </div>
          </div>
        ) : null}
      </main>

      <footer className="border-t border-slate-800 py-4 text-center text-xs text-slate-500">
        Powered by Cloud Storage Service • End-to-end encrypted file sharing
      </footer>
    </div>
  );
};

export default PublicSharePage;
