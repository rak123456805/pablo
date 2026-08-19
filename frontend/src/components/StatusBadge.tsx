import React from 'react';
import { AlertTriangle, CheckCircle2, Clock, ImageOff } from 'lucide-react';

interface StatusBadgeProps {
  status?: 'draft' | 'published';
  hasMissingArtwork?: boolean;
  hasBlocker?: boolean;
  blockerMessage?: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  hasMissingArtwork,
  hasBlocker,
  blockerMessage,
  size = 'md',
}) => {
  const isSm = size === 'sm';
  const py = isSm ? 'py-0.5' : 'py-1';
  const px = isSm ? 'px-2' : 'px-2.5';
  const text = isSm ? 'text-xs' : 'text-xs font-medium';

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {status === 'published' ? (
        <span
          className={`inline-flex items-center gap-1 bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 rounded-full ${px} ${py} ${text}`}
        >
          <CheckCircle2 className={isSm ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
          Published
        </span>
      ) : status === 'draft' ? (
        <span
          className={`inline-flex items-center gap-1 bg-slate-800/80 text-slate-300 border border-slate-700 rounded-full ${px} ${py} ${text}`}
        >
          <Clock className={isSm ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
          Draft
        </span>
      ) : null}

      {hasMissingArtwork && (
        <span
          className={`inline-flex items-center gap-1 bg-amber-950/80 text-amber-300 border border-amber-800/80 rounded-full ${px} ${py} ${text}`}
          title="Missing artwork upload"
        >
          <ImageOff className={isSm ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
          No Artwork
        </span>
      )}

      {hasBlocker && (
        <span
          className={`inline-flex items-center gap-1 bg-rose-950/90 text-rose-300 border border-rose-800/80 rounded-full ${px} ${py} ${text}`}
          title={blockerMessage || 'Publish blocker detected'}
        >
          <AlertTriangle className={isSm ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
          Blocker
        </span>
      )}
    </div>
  );
};
