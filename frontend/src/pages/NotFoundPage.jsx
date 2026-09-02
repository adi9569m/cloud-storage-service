/**
 * 404 Not Found fallback view.
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { CloudOff, ArrowLeft } from 'lucide-react';

export const NotFoundPage = () => {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-surface-light px-4 text-center">
      <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-slate-100 text-slate-400 mb-6">
        <CloudOff className="h-10 w-10" />
      </div>
      <h1 className="text-4xl font-extrabold tracking-tight text-slate-800">404</h1>
      <h2 className="mt-2 text-lg font-semibold text-slate-700">Page not found</h2>
      <p className="mt-1 text-sm text-slate-500 max-w-sm">
        The cloud resource or page you are looking for does not exist or has been moved.
      </p>
      <Link
        to="/"
        className="mt-6 inline-flex items-center gap-2 rounded-xl bg-drive-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-drive-700 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        <span>Return to Drive</span>
      </Link>
    </div>
  );
};

export default NotFoundPage;
