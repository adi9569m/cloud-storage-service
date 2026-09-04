import React from 'react';
import {
  FileText,
  Image as ImageIcon,
  FileCode,
  Music,
  Video,
  Archive,
  FileSpreadsheet,
  FileQuestion,
} from 'lucide-react';

export const formatBytes = (bytes, decimals = 1) => {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

export const formatDate = (isoString) => {
  if (!isoString) return '—';
  const date = new Date(isoString);
  if (isNaN(date.getTime())) return '—';

  const now = new Date();
  const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } else if (diffDays === 1) {
    return 'Yesterday';
  } else if (diffDays < 7) {
    return date.toLocaleDateString([], { weekday: 'short' });
  } else if (now.getFullYear() === date.getFullYear()) {
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
  }
  return date.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
};

export const getFileCategory = (mimeType = '', filename = '') => {
  const mime = (mimeType || '').toLowerCase();
  const ext = (filename.split('.').pop() || '').toLowerCase();

  if (mime.startsWith('image/')) return 'image';
  if (mime.startsWith('video/')) return 'video';
  if (mime.startsWith('audio/')) return 'audio';
  if (mime === 'application/pdf' || ext === 'pdf') return 'pdf';
  if (
    mime.includes('spreadsheet') ||
    mime.includes('excel') ||
    mime.includes('csv') ||
    ['csv', 'xlsx', 'xls'].includes(ext)
  ) {
    return 'spreadsheet';
  }
  if (
    mime.startsWith('text/') ||
    mime.includes('json') ||
    mime.includes('javascript') ||
    mime.includes('python') ||
    mime.includes('xml') ||
    ['js', 'jsx', 'ts', 'tsx', 'py', 'html', 'css', 'json', 'md', 'yml', 'yaml', 'sql', 'sh', 'rs', 'go', 'c', 'cpp', 'java'].includes(ext)
  ) {
    return 'code';
  }
  if (
    mime.includes('zip') ||
    mime.includes('tar') ||
    mime.includes('gzip') ||
    mime.includes('compressed') ||
    ['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)
  ) {
    return 'archive';
  }
  if (
    mime.includes('word') ||
    mime.includes('document') ||
    ['doc', 'docx', 'txt', 'rtf'].includes(ext)
  ) {
    return 'document';
  }
  return 'file';
};

export const getFileIconDetails = (mimeType, filename) => {
  const category = getFileCategory(mimeType, filename);

  switch (category) {
    case 'image':
      return { icon: ImageIcon, color: 'text-purple-500', bg: 'bg-purple-50' };
    case 'video':
      return { icon: Video, color: 'text-rose-500', bg: 'bg-rose-50' };
    case 'audio':
      return { icon: Music, color: 'text-amber-500', bg: 'bg-amber-50' };
    case 'pdf':
      return { icon: FileText, color: 'text-red-500', bg: 'bg-red-50' };
    case 'spreadsheet':
      return { icon: FileSpreadsheet, color: 'text-emerald-500', bg: 'bg-emerald-50' };
    case 'code':
      return { icon: FileCode, color: 'text-blue-500', bg: 'bg-blue-50' };
    case 'archive':
      return { icon: Archive, color: 'text-amber-600', bg: 'bg-amber-50' };
    case 'document':
      return { icon: FileText, color: 'text-indigo-500', bg: 'bg-indigo-50' };
    default:
      return { icon: FileQuestion, color: 'text-slate-500', bg: 'bg-slate-100' };
  }
};
