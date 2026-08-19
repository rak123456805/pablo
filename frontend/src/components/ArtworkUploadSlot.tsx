import React, { useRef, useState } from 'react';
import { AlertCircle, CheckCircle, Upload, X, Loader2 } from 'lucide-react';
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
  const [clientError, setClientError] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isValidated, setIsValidated] = useState<boolean>(!!existingArtwork);

  const labelTitle = kind.charAt(0).toUpperCase() + kind.slice(1);

  const validateClientSide = (file: File): Promise<{ width: number; height: number } | null> => {
    return new Promise((resolve) => {
      // 1. Check size KB
      const sizeKb = file.size / 1024;
      if (sizeKb > spec.maxKb) {
        setClientError(`File size (${sizeKb.toFixed(1)} KB) exceeds max limit of ${spec.maxKb} KB`);
        resolve(null);
        return;
      }

      // 2. Check image format & dimensions
      const img = new Image();
      const objectUrl = URL.createObjectURL(file);

      img.onload = () => {
        URL.revokeObjectURL(objectUrl);
        const { width, height } = img;
        const actualRatio = width / height;
        const targetRatio = spec.ratio;

        // Tolerance ±2%
        const isRatioValid = Math.abs(actualRatio - targetRatio) < 0.03;

        if (!isRatioValid) {
          setClientError(
            `Aspect ratio mismatch: Got ${width}x${height} (${actualRatio.toFixed(2)}:1). Target is ${spec.aspect} (${spec.width}x${spec.height}).`
          );
          resolve(null);
          return;
        }

        setClientError(null);
        resolve({ width, height });
      };

      img.onerror = () => {
        URL.revokeObjectURL(objectUrl);
        setClientError('Invalid image file. Please upload a valid JPEG, PNG, or WebP.');
        resolve(null);
      };

      img.src = objectUrl;
    });
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setServerError(null);
    setClientError(null);
    setIsValidated(false);

    // Client-side fast check
    const dims = await validateClientSide(file);
    if (!dims) {
      return;
    }

    // Live preview
    const tempUrl = URL.createObjectURL(file);
    setPreviewUrl(tempUrl);

    // Upload to backend
    setIsUploading(true);
    try {
      await api.uploadArtwork(ownerType, ownerId, kind, file);
      setIsValidated(true);
      if (onSuccess) onSuccess();
    } catch (err) {
      if (err instanceof ApiError) {
        setServerError(err.detail);
      } else {
        setServerError('Upload failed. Please check your connection and try again.');
      }
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async () => {
    if (!existingArtwork?.id) {
      setPreviewUrl(null);
      setClientError(null);
      setServerError(null);
      setIsValidated(false);
      return;
    }

    setIsDeleting(true);
    try {
      await api.deleteArtwork(existingArtwork.id);
      setPreviewUrl(null);
      setClientError(null);
      setServerError(null);
      setIsValidated(false);
      if (onSuccess) onSuccess();
    } catch (err) {
      if (err instanceof ApiError) {
        setServerError(err.detail);
      }
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex flex-col justify-between space-y-3">
      {/* Header Info */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <span className="font-semibold text-slate-100 text-sm">{labelTitle}</span>
          {isValidated && (
            <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded-full border border-emerald-800/50">
              <CheckCircle className="w-3.5 h-3.5" /> Validated
            </span>
          )}
        </div>
        <div className="text-xs text-slate-400 space-y-0.5">
          <p>Target: <span className="text-slate-300 font-mono">{spec.width} × {spec.height} px</span> ({spec.aspect})</p>
          <p>Max file size: <span className="text-slate-300 font-mono">{spec.maxKb} KB</span></p>
        </div>
      </div>

      {/* Preview Box */}
      <div className="relative group aspect-video bg-slate-950 rounded-lg border border-dashed border-slate-700 overflow-hidden flex items-center justify-center">
        {previewUrl ? (
          <>
            <img
              src={previewUrl}
              alt={`${labelTitle} preview`}
              className="w-full h-full object-cover"
            />
            {isUploading && (
              <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-xs flex items-center justify-center text-sky-400 gap-2">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span className="text-xs font-medium">Uploading...</span>
              </div>
            )}
            <div className="absolute inset-0 bg-slate-950/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="px-2.5 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded text-xs font-medium shadow-md transition-colors"
                disabled={isUploading || isDeleting}
              >
                Change
              </button>
              <button
                type="button"
                onClick={handleDelete}
                className="p-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded text-xs shadow-md transition-colors"
                disabled={isUploading || isDeleting}
                title="Delete artwork"
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
            <Upload className="w-6 h-6 text-slate-500 mb-1" />
            <span className="text-xs font-medium text-sky-400">Click to upload</span>
            <span className="text-[10px] text-slate-500 mt-0.5">JPEG, PNG, WebP</span>
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

      {/* Errors */}
      {(clientError || serverError) && (
        <div className="p-2.5 bg-rose-950/80 border border-rose-800/80 rounded-lg flex items-start gap-2 text-rose-300 text-xs">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          <div className="flex-1 space-y-0.5">
            <p className="font-medium text-rose-200">Validation Error</p>
            <p>{clientError || serverError}</p>
          </div>
        </div>
      )}
    </div>
  );
};
