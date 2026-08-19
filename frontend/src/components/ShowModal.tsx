import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { X, Loader2, Save, Image as ImageIcon } from 'lucide-react';
import { CATEGORIES, SECTIONS } from '../reference/reference';
import { api, ApiError } from '../api/client';
import type { Show } from '../types';
import { ArtworkUploadSlot } from './ArtworkUploadSlot';

const showSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  slug: z
    .string()
    .min(1, 'Slug is required')
    .regex(/^[a-z0-9-]+$/, 'Slug must be lowercase alphanumeric with hyphens'),
  synopsis: z.string().optional(),
  section: z.string().optional().nullable(),
  categories: z.array(z.string()),
  status: z.enum(['draft', 'published']),
});

type ShowFormData = z.infer<typeof showSchema>;

interface ShowModalProps {
  isOpen: boolean;
  onClose: () => void;
  showToEdit?: Show | null;
  onSuccess: () => void;
}

export const ShowModal: React.FC<ShowModalProps> = ({
  isOpen,
  onClose,
  showToEdit,
  onSuccess,
}) => {
  const isEditing = !!showToEdit;
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'details' | 'artwork'>('details');

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ShowFormData>({
    resolver: zodResolver(showSchema),
    defaultValues: {
      title: '',
      slug: '',
      synopsis: '',
      section: null,
      categories: [],
      status: 'draft',
    },
  });

  const selectedCategories = watch('categories') || [];
  const titleValue = watch('title');

  // Auto-generate slug when creating
  useEffect(() => {
    if (!isEditing && titleValue) {
      const generatedSlug = titleValue
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, '')
        .trim()
        .replace(/\s+/g, '-');
      setValue('slug', generatedSlug, { shouldValidate: true });
    }
  }, [titleValue, isEditing, setValue]);

  useEffect(() => {
    if (showToEdit) {
      reset({
        title: showToEdit.title,
        slug: showToEdit.slug,
        synopsis: showToEdit.synopsis || '',
        section: showToEdit.section || null,
        categories: showToEdit.categories || [],
        status: showToEdit.status as 'draft' | 'published',
      });
      // Fetch artwork for show if editing
      fetchArtworks();
    } else {
      reset({
        title: '',
        slug: '',
        synopsis: '',
        section: null,
        categories: [],
        status: 'draft',
      });
    }
    setErrorMsg(null);
    setActiveTab('details');
  }, [showToEdit, isOpen, reset]);

  const fetchArtworks = async () => {
    if (!showToEdit) return;
    try {
      // Artwork can be fetched by getting show details if we need to or we can load artwork specs
    } catch {
      // ignore
    }
  };

  if (!isOpen) return null;

  const onSubmit = async (data: ShowFormData) => {
    setErrorMsg(null);

    // Spec enforcement: Published show requires section
    if (data.status === 'published' && !data.section) {
      setErrorMsg('Cannot publish show because it has no section assigned. Please choose a section first.');
      return;
    }

    try {
      if (isEditing && showToEdit) {
        await api.updateShow(showToEdit.id, {
          title: data.title,
          synopsis: data.synopsis || null,
          section: data.section || null,
          categories: data.categories,
          status: data.status,
        });
      } else {
        await api.createShow({
          title: data.title,
          slug: data.slug,
          synopsis: data.synopsis || null,
          section: data.section || null,
          categories: data.categories,
          status: data.status,
        });
      }
      onSuccess();
      onClose();
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMsg(err.detail);
      } else {
        setErrorMsg('Failed to save show. Please check network and try again.');
      }
    }
  };

  const toggleCategory = (cat: string) => {
    const current = selectedCategories;
    if (current.includes(cat)) {
      setValue('categories', current.filter((c: string) => c !== cat), { shouldValidate: true });
    } else {
      setValue('categories', [...current, cat], { shouldValidate: true });
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl shadow-2xl overflow-hidden my-8">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
          <div>
            <h2 className="text-lg font-bold text-slate-100">
              {isEditing ? `Edit Show: ${showToEdit?.title}` : 'Create New Show'}
            </h2>
            <p className="text-xs text-slate-400">
              Configure title, section routing, categories, and artwork specifications.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded-lg transition-colors"
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
              Show Details
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
              Artwork Upload Slots
            </button>
          </div>
        )}

        {/* Form Body */}
        {activeTab === 'details' ? (
          <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-5">
            {errorMsg && (
              <div className="p-3 bg-rose-950/80 border border-rose-800 text-rose-300 rounded-xl text-xs">
                {errorMsg}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Title */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Title *</label>
                <input
                  type="text"
                  {...register('title')}
                  placeholder="e.g. Jungle Tales"
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
                {errors.title && <p className="text-rose-400 text-[11px] mt-1">{errors.title.message}</p>}
              </div>

              {/* Slug */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Slug *</label>
                <input
                  type="text"
                  {...register('slug')}
                  disabled={isEditing}
                  placeholder="jungle-tales"
                  className={`w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 ${
                    isEditing ? 'opacity-60 cursor-not-allowed' : ''
                  }`}
                />
                {errors.slug && <p className="text-rose-400 text-[11px] mt-1">{errors.slug.message}</p>}
              </div>
            </div>

            {/* Synopsis */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Synopsis</label>
              <textarea
                {...register('synopsis')}
                rows={3}
                placeholder="Short description for viewers..."
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Section */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Section <span className="text-slate-400 font-normal">(Required for Published)</span>
                </label>
                <select
                  {...register('section')}
                  value={watch('section') || ''}
                  onChange={(e) => setValue('section', e.target.value || null)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-sky-500"
                >
                  <option value="">-- No Section (Draft Only) --</option>
                  {SECTIONS.map((sec) => (
                    <option key={sec} value={sec}>
                      {sec.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              {/* Status */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Publication Status</label>
                <select
                  {...register('status')}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-sky-500"
                >
                  <option value="draft">Draft (Work in progress)</option>
                  <option value="published">Published (Ready for catalogue)</option>
                </select>
              </div>
            </div>

            {/* Categories */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-2">Categories</label>
              <div className="flex flex-wrap gap-1.5 p-3 bg-slate-950 border border-slate-800 rounded-xl max-h-36 overflow-y-auto">
                {CATEGORIES.map((cat) => {
                  const isSelected = selectedCategories.includes(cat);
                  return (
                    <button
                      key={cat}
                      type="button"
                      onClick={() => toggleCategory(cat)}
                      className={`px-2.5 py-1 rounded-full text-xs font-medium transition-all ${
                        isSelected
                          ? 'bg-sky-600 text-white shadow-sm'
                          : 'bg-slate-900 text-slate-400 border border-slate-800 hover:border-slate-700 hover:text-slate-200'
                      }`}
                    >
                      {cat}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Footer buttons */}
            <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex items-center gap-2 px-5 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg shadow-md transition-colors disabled:opacity-50"
              >
                {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                {isEditing ? 'Save Changes' : 'Create Show'}
              </button>
            </div>
          </form>
        ) : (
          /* Artwork Tab */
          <div className="p-6 space-y-4">
            <p className="text-xs text-slate-400">
              Upload artwork for <span className="font-semibold text-slate-200">{showToEdit?.title}</span>. Each slot validates target resolution and max file size (200 KB).
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <ArtworkUploadSlot
                kind="poster"
                ownerType="show"
                ownerId={showToEdit!.id}
                onSuccess={onSuccess}
              />
              <ArtworkUploadSlot
                kind="banner"
                ownerType="show"
                ownerId={showToEdit!.id}
                onSuccess={onSuccess}
              />
              <ArtworkUploadSlot
                kind="thumbnail"
                ownerType="show"
                ownerId={showToEdit!.id}
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
