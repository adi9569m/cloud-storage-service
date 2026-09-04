/**
 * Floating Toast viewport container displaying stacked toast alerts with animations.
 */

import React from 'react';
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from 'lucide-react';

const toastConfig = {
  success: {
    icon: CheckCircle2,
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    text: 'text-emerald-800',
    iconColor: 'text-emerald-600',
    progress: 'bg-emerald-500',
  },
  error: {
    icon: AlertCircle,
    bg: 'bg-rose-50',
    border: 'border-rose-200',
    text: 'text-rose-800',
    iconColor: 'text-rose-600',
    progress: 'bg-rose-500',
  },
  warning: {
    icon: AlertTriangle,
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    text: 'text-amber-800',
    iconColor: 'text-amber-600',
    progress: 'bg-amber-500',
  },
  info: {
    icon: Info,
    bg: 'bg-drive-50',
    border: 'border-drive-200',
    text: 'text-drive-800',
    iconColor: 'text-drive-600',
    progress: 'bg-drive-500',
  },
};

export const ToastContainer = ({ toasts = [], onDismiss }) => {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex max-w-sm flex-col gap-3 pointer-events-none">
      {toasts.map((toast) => {
        const config = toastConfig[toast.type] || toastConfig.info;
        const Icon = config.icon;

        return (
          <div
            key={toast.id}
            className={`pointer-events-auto flex items-start gap-3 rounded-2xl border p-4 shadow-modal backdrop-blur-sm transition-all duration-300 animate-in fade-in slide-in-from-bottom-5 ${config.bg} ${config.border} ${config.text}`}
          >
            <Icon className={`h-5 w-5 flex-shrink-0 mt-0.5 ${config.iconColor}`} />
            <div className="flex-1 overflow-hidden">
              {toast.title && (
                <p className="text-xs font-bold uppercase tracking-wider opacity-90 mb-0.5">
                  {toast.title}
                </p>
              )}
              <p className="text-xs font-medium leading-relaxed break-words">{toast.message}</p>
            </div>
            <button
              onClick={() => onDismiss(toast.id)}
              className="flex-shrink-0 rounded-lg p-1 opacity-60 hover:opacity-100 hover:bg-black/5 transition-colors focus:outline-none"
              title="Dismiss"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
};

export default ToastContainer;
