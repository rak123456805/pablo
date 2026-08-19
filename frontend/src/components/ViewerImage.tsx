import React, { useState } from 'react';
import { Sparkles, Tv, Film } from 'lucide-react';

interface ViewerImageProps {
  src?: string | null;
  alt: string;
  kind: 'poster' | 'banner' | 'thumbnail';
  className?: string;
  fallbackTitle?: string;
}

export const ViewerImage: React.FC<ViewerImageProps> = ({
  src,
  alt,
  kind,
  className = '',
  fallbackTitle = '',
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);

  const aspectClass =
    kind === 'poster' ? 'aspect-[2/3]' : 'aspect-[16/9]';

  // Warm gradients for fallback cards
  const gradientStyles = [
    'from-amber-600 to-orange-700 text-amber-100',
    'from-indigo-600 to-purple-700 text-indigo-100',
    'from-sky-600 to-teal-700 text-sky-100',
    'from-rose-600 to-pink-700 text-rose-100',
    'from-emerald-600 to-teal-700 text-emerald-100',
  ];

  // Hash string to pick deterministic gradient
  const hash = (fallbackTitle || alt).split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const selectedGradient = gradientStyles[hash % gradientStyles.length];

  const showFallback = !src || hasError;

  return (
    <div
      className={`relative overflow-hidden bg-slate-900 rounded-2xl border border-slate-800/80 shadow-md ${aspectClass} ${className}`}
    >
      {/* Skeleton overlay while loading */}
      {!isLoaded && !showFallback && (
        <div className="absolute inset-0 bg-slate-800 animate-pulse flex items-center justify-center text-slate-600">
          <Sparkles className="w-5 h-5 animate-spin" />
        </div>
      )}

      {/* Actual Image */}
      {!showFallback && (
        <img
          src={src}
          alt={alt}
          loading="lazy"
          onLoad={() => setIsLoaded(true)}
          onError={() => setHasError(true)}
          className={`w-full h-full object-cover transition-opacity duration-500 ${
            isLoaded ? 'opacity-100' : 'opacity-0'
          }`}
        />
      )}

      {/* Fallback Warm Card when image fails or is absent */}
      {showFallback && (
        <div
          className={`w-full h-full bg-gradient-to-br ${selectedGradient} p-4 flex flex-col justify-between select-none relative overflow-hidden`}
        >
          {/* Background pattern circles */}
          <div className="absolute -right-6 -bottom-6 w-24 h-24 rounded-full bg-white/10 blur-xl pointer-events-none" />
          <div className="absolute -left-6 -top-6 w-20 h-20 rounded-full bg-black/10 blur-lg pointer-events-none" />

          <div className="flex items-center justify-between text-white/80 z-10">
            <span className="text-[10px] font-bold uppercase tracking-widest font-mono bg-black/20 px-2 py-0.5 rounded-full backdrop-blur-xs">
              {kind}
            </span>
            {kind === 'poster' ? (
              <Tv className="w-4 h-4" />
            ) : (
              <Film className="w-4 h-4" />
            )}
          </div>

          <div className="z-10 space-y-1 mt-auto">
            <p className="font-extrabold text-sm tracking-tight leading-tight drop-shadow-sm line-clamp-2">
              {fallbackTitle || alt}
            </p>
            <span className="text-[10px] text-white/70 font-medium block">Peblo TV Original</span>
          </div>
        </div>
      )}
    </div>
  );
};
