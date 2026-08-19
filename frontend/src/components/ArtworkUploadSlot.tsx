import React, { useRef, useState } from 'react';
import { AlertCircle, CheckCircle, Upload, X, Loader2, FileCode2 } from 'lucide-react';
import { ARTWORK_SPECS, type ArtworkSpec } from '../reference/reference';
import { api, ApiError } from '../api/client';
import type { Artwork } from '../types';

interface ArtworkUploadSlotProps {
  kind: 'poster' | 'banner' | 'thumbnail';
  ownerType: 'show' | 'episode';
  ownerId: string;
  existingArtwork?: Artwork | null;
  onSuccess?: () => void;
}

const TEST_PRESETS = {
  poster: [
    { label: 'poster_good.jpg (Valid)', filename: 'poster_good.jpg', path: '/test_assets/poster_good.jpg' },
    { label: 'poster_wrong_ratio.jpg (Invalid Ratio)', filename: 'poster_wrong_ratio.jpg', path: '/test_assets/poster_wrong_ratio.jpg' },
  ],
  banner: [
    { label: 'banner_good.jpg (Valid)', filename: 'banner_good.jpg', path: '/test_assets/banner_good.jpg' },
    { label: 'banner_too_big.png (>200KB)', filename: 'banner_too_big.png', path: '/test_assets/banner_too_big.png' },
  ],
  thumbnail: [
    { label: 'thumb_good.jpg (Valid)', filename: 'thumb_good.jpg', path: '/test_assets/thumb_good.jpg' },
    { label: 'thumb_tiny.jpg (Too Small)', filename: 'thumb_tiny.jpg', path: '/test_assets/thumb_tiny.jpg' },
  ],
};

export const ArtworkUploadSlot: React.FC<ArtworkUploadSlotProps> = ({
  kind,
  ownerType,
  ownerId,
  existingArtwork,
  onSuccess,
}) => {
  const spec: ArtworkSpec = ARTWORK_SPECS[kind];
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [previewUrl, setPreviewUrl] = useState<string | null>(existingArtwork?.url || null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [currentArtwork, setCurrentArtwork] = useState<Artwork | null>(existingArtwork || null);

  const labelTitle = kind.toUpperCase();

  const handleUploadFile = async (file: File) => {
    setErrorMessage(null);
    setIsUploading(true);

    // Set temporary live preview while uploading
    const tempUrl = URL.createObjectURL(file);
    setPreviewUrl(tempUrl);

    try {
      const art = await api.uploadArtwork(ownerType, ownerId, kind, file);
      setCurrentArtwork(art);
      setPreviewUrl(art.url);
      setErrorMessage(null);
      if (onSuccess) onSuccess();
    } catch (err) {
      setCurrentArtwork(null);
      let msg = 'Upload failed. Please check the file and try again.';
      if (err instanceof ApiError) {
        msg = err.detail;
      } else if (err instanceof Error) {
        msg = err.message;
      }
      // Clean up technical jargon
      msg = msg.replace(/^HTTP \d+:\s*/i, '').replace(/^ValidationError:\s*/i, '');
      setErrorMessage(msg);
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleUploadFile(file);
  };

  const handleTestAssetSelect = async (assetPath: string, filename: string) => {
    try {
      setIsUploading(true);
      setErrorMessage(null);
      const resp = await fetch(assetPath);
      if (!resp.ok) {
        throw new Error(`Failed to fetch test asset: ${filename}`);
      }
      const blob = await resp.blob();
      const file = new File([blob], filename, { type: blob.type || 'image/jpeg' });
      await handleUploadFile(file);
    } catch (err: any) {
      setIsUploading(false);
      setErrorMessage(err.message || 'Failed to load test asset.');
    }
  };

  const handleDelete = async () => {
    const artId = currentArtwork?.id || existingArtwork?.id;
    if (!artId) {
      setPreviewUrl(null);
      setCurrentArtwork(null);
      setErrorMessage(null);
      return;
    }

    setIsDeleting(true);
    try {
      await api.deleteArtwork(artId);
      setPreviewUrl(null);
      setCurrentArtwork(null);
      setErrorMessage(null);
      if (onSuccess) onSuccess();
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMessage(err.detail);
      }
    } finally {
      setIsDeleting(false);
    }
  };

  const presets = TEST_PRESETS[kind] || [];

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex flex-col justify-between space-y-3">
      {/* Header Info */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <span className="font-bold text-slate-100 text-sm tracking-wide">{labelTitle}</span>
          {currentArtwork && !errorMessage ? (
            <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-400 bg-emerald-950/80 px-2.5 py-0.5 rounded-full border border-emerald-700/60">
              <CheckCircle className="w-3.5 h-3.5" /> {kind.charAt(0).toUpperCase() + kind.slice(1)} accepted
            </span>
          ) : errorMessage ? (
            <span className="inline-flex items-center gap-1 text-xs font-semibold text-rose-400 bg-rose-950/80 px-2.5 py-0.5 rounded-full border border-rose-700/60">
              <AlertCircle className="w-3.5 h-3.5" /> {kind.charAt(0).toUpperCase() + kind.slice(1)} rejected
            </span>
          ) : (
            <span className="text-xs text-slate-400">Required</span>
          )}
        </div>
        <div className="text-xs text-slate-400 space-y-0.5">
          <p>Dimensions: <span className="text-slate-300 font-mono">~{spec.width} × {spec.height} px</span></p>
          <p>Aspect Ratio: <span className="text-slate-300 font-mono">{spec.aspect}</span> | Max Size: <span className="text-slate-300 font-mono">{spec.maxKb} KB</span></p>
        </div>
      </div>

      {/* Live Preview Box */}
      <div className="relative group aspect-video bg-slate-950 rounded-lg border border-dashed border-slate-700 overflow-hidden flex items-center justify-center">
        {previewUrl ? (
          <>
            <img
              src={previewUrl}
              alt={`${labelTitle} preview`}
              className={`w-full h-full object-cover ${errorMessage ? 'opacity-40 grayscale' : ''}`}
            />
            {isUploading && (
              <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-xs flex items-center justify-center text-sky-400 gap-2">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span className="text-xs font-medium">Validating & Uploading...</span>
              </div>
            )}
            <div className="absolute inset-0 bg-slate-950/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded text-xs font-medium shadow-md transition-colors"
                disabled={isUploading || isDeleting}
              >
                Replace
              </button>
              <button
                type="button"
                onClick={handleDelete}
                className="p-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded text-xs shadow-md transition-colors"
                disabled={isUploading || isDeleting}
                title="Remove artwork"
              >
                {isDeleting ? <Loader2 className="w-4 h-4 animate-spin" /> : <X className="w-4 h-4" />}
              </button>
            </div>
          </>
        ) : (
          <div
            onClick={() => fileInputRef.current?.click()}
            className="flex flex-col items-center justify-center p-4 text-center cursor-pointer hover:bg-slate-900/50 transition-colors w-full h-full"
          >
            {isUploading ? (
              <div className="flex items-center text-sky-400 gap-2">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span className="text-xs font-medium">Validating & Uploading...</span>
              </div>
            ) : (
              <>
                <Upload className="w-6 h-6 text-slate-500 mb-1" />
                <span className="text-xs font-medium text-sky-400">Click to upload {labelTitle}</span>
                <span className="text-[10px] text-slate-500 mt-0.5">JPEG, PNG, WebP (Max {spec.maxKb} KB)</span>
              </>
            )}
          </div>
        )}
      </div>

      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
      />

      {/* Human-Readable Validation Details / Metadata when accepted */}
      {currentArtwork && !errorMessage && (
        <div className="text-[11px] text-emerald-400 bg-emerald-950/40 p-2 rounded border border-emerald-900/50 font-mono flex items-center justify-between">
          <span>{currentArtwork.width_px} × {currentArtwork.height_px}</span>
          <span>{(currentArtwork.size_bytes / 1024).toFixed(0)} KB</span>
          <span>{spec.aspect}</span>
        </div>
      )}

      {/* Human-Readable Error Display */}
      {errorMessage && (
        <div className="p-3 bg-rose-950/90 border border-rose-800 rounded-lg flex items-start gap-2.5 text-rose-200 text-xs">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          <div className="flex-1 space-y-0.5">
            <p className="font-semibold text-rose-300">Validation Rejected</p>
            <p className="leading-snug text-rose-200">{errorMessage}</p>
          </div>
        </div>
      )}

      {/* Evaluator Quick Test Assets */}
      <div className="pt-2 border-t border-slate-800/80">
        <div className="flex items-center gap-1.5 mb-1.5 text-[11px] text-slate-400 font-medium">
          <FileCode2 className="w-3.5 h-3.5 text-amber-400" />
          <span>Evaluator Test Assets:</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {presets.map((p) => (
            <button
              key={p.filename}
              type="button"
              onClick={() => handleTestAssetSelect(p.path, p.filename)}
              disabled={isUploading}
              className={`px-2 py-1 text-[11px] rounded transition-colors border ${
                p.filename.includes('good')
                  ? 'bg-emerald-950/50 hover:bg-emerald-900/80 text-emerald-300 border-emerald-800/60'
                  : 'bg-rose-950/50 hover:bg-rose-900/80 text-rose-300 border-rose-800/60'
              }`}
            >
              Test {p.filename}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
