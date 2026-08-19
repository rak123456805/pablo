import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { X, Loader2, Save, Image as ImageIcon } from 'lucide-react';
import { LANGUAGES } from '../reference/reference';
import { api, ApiError } from '../api/client';
import type { Episode } from '../types';
import { ArtworkUploadSlot } from './ArtworkUploadSlot';

const episodeSchema = z.object({
  episode_number: z.number().min(1, 'Episode number must be >= 1'),
  title: z.string().min(1, 'Episode title is required'),
  duration_seconds: z.number().nullable().optional(),
  language: z.string().min(1, 'Language is required'),
  content_group: z.string().min(1, 'Content Group is required'),
  status: z.enum(['draft', 'published']),
});

type EpisodeFormData = z.infer<typeof episodeSchema>;

interface EpisodeModalProps {
  isOpen: boolean;
  onClose: () => void;
  seasonId: string;
  showSlug: string;
  seasonNumber: number;
  episodeToEdit?: Episode | null;
  onSuccess: () => void;
}

export const EpisodeModal: React.FC<EpisodeModalProps> = ({
  isOpen,
  onClose,
  seasonId,
  showSlug,
  seasonNumber,
  episodeToEdit,
  onSuccess,
}) => {
  const isEditing = !!episodeToEdit;
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'details' | 'artwork'>('details');

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<EpisodeFormData>({
    resolver: zodResolver(episodeSchema),
    defaultValues: {
      episode_number: 1,
      title: '',
      duration_seconds: null,
      language: 'en',
      content_group: `${showSlug}-s${seasonNumber < 10 ? `0${seasonNumber}` : seasonNumber}e01`,
      status: 'draft',
    },
  });

  const epNumber = watch('episode_number');

  // Auto-generate content group format: slug-s01e01
  useEffect(() => {
    if (!isEditing && epNumber) {
      const sStr = seasonNumber < 10 ? `0${seasonNumber}` : `${seasonNumber}`;
      const eStr = epNumber < 10 ? `0${epNumber}` : `${epNumber}`;
      setValue('content_group', `${showSlug}-s${sStr}e${eStr}`);
    }
  }, [epNumber, seasonNumber, showSlug, isEditing, setValue]);

  useEffect(() => {
    if (episodeToEdit) {
      reset({
        episode_number: episodeToEdit.episode_number,
        title: episodeToEdit.title,
        duration_seconds: episodeToEdit.duration_seconds,
        language: episodeToEdit.language,
        content_group: episodeToEdit.content_group,
        status: episodeToEdit.status as 'draft' | 'published',
      });
    } else {
      const sStr = seasonNumber < 10 ? `0${seasonNumber}` : `${seasonNumber}`;
      reset({
        episode_number: 1,
        title: '',
        duration_seconds: null,
        language: 'en',
        content_group: `${showSlug}-s${sStr}e01`,
        status: 'draft',
      });
    }
    setErrorMsg(null);
    setActiveTab('details');
  }, [episodeToEdit, isOpen, reset, seasonNumber, showSlug]);

  if (!isOpen) return null;

  const onSubmit = async (data: EpisodeFormData) => {
    setErrorMsg(null);

    // Business rule: Published episode requires duration
    if (data.status === 'published' && (!data.duration_seconds || data.duration_seconds <= 0)) {
      setErrorMsg('Cannot publish episode: duration is required for published episodes.');
      return;
    }

    try {
      if (isEditing && episodeToEdit) {
        await api.updateEpisode(episodeToEdit.id, {
          title: data.title,
          duration_seconds: data.duration_seconds || null,
          language: data.language,
          content_group: data.content_group,
          status: data.status,
        });
      } else {
        await api.createEpisode({
          season_id: seasonId,
          episode_number: data.episode_number,
          title: data.title,
          duration_seconds: data.duration_seconds || null,
          language: data.language,
          content_group: data.content_group,
          status: data.status,
        });
      }
      onSuccess();
      onClose();
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMsg(err.detail);
      } else {
        setErrorMsg('Failed to save episode.');
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden my-8">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-100">
              {isEditing ? `Edit Episode: ${episodeToEdit?.title}` : `New Episode (Season ${seasonNumber})`}
            </h3>
            <p className="text-xs text-slate-400">
              Configure content group, language variant, duration, and artwork.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-slate-100 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs if editing */}
        {isEditing && (
          <div className="flex border-b border-slate-800 bg-slate-950/50 px-6">
            <button
              type="button"
              onClick={() => setActiveTab('details')}
              className={`py-3 px-4 text-xs font-semibold border-b-2 transition-colors ${
                activeTab === 'details'
                  ? 'border-sky-500 text-sky-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Episode Details
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('artwork')}
              className={`py-3 px-4 text-xs font-semibold border-b-2 transition-colors flex items-center gap-1.5 ${
                activeTab === 'artwork'
                  ? 'border-sky-500 text-sky-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <ImageIcon className="w-3.5 h-3.5" />
              Episode Artwork
            </button>
          </div>
        )}

        {/* Content */}
        {activeTab === 'details' ? (
          <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
            {errorMsg && (
              <div className="p-3 bg-rose-950/80 border border-rose-800 text-rose-300 rounded-xl text-xs">
                {errorMsg}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Ep number */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Episode Number *</label>
                <input
                  type="number"
                  {...register('episode_number', { valueAsNumber: true })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-sky-500"
                />
                {errors.episode_number && (
                  <p className="text-rose-400 text-[11px] mt-1">{errors.episode_number.message}</p>
                )}
              </div>

              {/* Title */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Episode Title *</label>
                <input
                  type="text"
                  {...register('title')}
                  placeholder="e.g. The Big Tree"
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
                {errors.title && (
                  <p className="text-rose-400 text-[11px] mt-1">{errors.title.message}</p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Language */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Language *</label>
                <select
                  {...register('language')}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-sky-500"
                >
                  {LANGUAGES.map((lang) => (
                    <option key={lang} value={lang}>
                      {lang === 'en' ? 'English (en)' : 'Hindi (hi)'}
                    </option>
                  ))}
                </select>
              </div>

              {/* Duration */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Duration (seconds) <span className="text-slate-400 font-normal">(Required for Published)</span>
                </label>
                <input
                  type="number"
                  {...register('duration_seconds', {
                    setValueAs: (v: any) => (v === '' || v === null || isNaN(Number(v)) ? null : Number(v)),
                  })}
                  placeholder="e.g. 300"
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
              </div>
            </div>

            {/* Content Group */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Content Group Identifier *</label>
              <input
                type="text"
                {...register('content_group')}
                placeholder="e.g. jungle-tales-s01e01"
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
              />
              {errors.content_group && (
                <p className="text-rose-400 text-[11px] mt-1">{errors.content_group.message}</p>
              )}
              <p className="text-[11px] text-slate-400 mt-1">
                Episodes with the same Content Group across different languages collapse into one catalogue entry.
              </p>
            </div>

            {/* Status */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Status</label>
              <select
                {...register('status')}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-sky-500"
              >
                <option value="draft">Draft</option>
                <option value="published">Published</option>
              </select>
            </div>

            {/* Footer */}
            <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex items-center gap-2 px-5 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg disabled:opacity-50"
              >
                {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                {isEditing ? 'Save Episode' : 'Create Episode'}
              </button>
            </div>
          </form>
        ) : (
          /* Artwork Upload Slots */
          <div className="p-6 space-y-4">
            <p className="text-xs text-slate-400">
              Upload artwork for <span className="font-semibold text-slate-200">{episodeToEdit?.title}</span>.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <ArtworkUploadSlot
                kind="poster"
                ownerType="episode"
                ownerId={episodeToEdit!.id}
                onSuccess={onSuccess}
              />
              <ArtworkUploadSlot
                kind="banner"
                ownerType="episode"
                ownerId={episodeToEdit!.id}
                onSuccess={onSuccess}
              />
              <ArtworkUploadSlot
                kind="thumbnail"
                ownerType="episode"
                ownerId={episodeToEdit!.id}
                onSuccess={onSuccess}
              />
            </div>
            <div className="flex justify-end pt-4 border-t border-slate-800">
              <button
                type="button"
                onClick={onClose}
                className="px-5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg"
              >
                Done
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
