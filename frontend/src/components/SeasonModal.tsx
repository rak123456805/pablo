import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { X, Loader2, PlusCircle } from 'lucide-react';
import { api, ApiError } from '../api/client';

const seasonSchema = z.object({
  season_number: z.number({ message: 'Season number is required' }).min(0, 'Season number must be >= 0'),
});

type SeasonFormData = z.infer<typeof seasonSchema>;

interface SeasonModalProps {
  isOpen: boolean;
  onClose: () => void;
  showId: string;
  showTitle: string;
  existingSeasonNumbers: number[];
  onSuccess: () => void;
}

export const SeasonModal: React.FC<SeasonModalProps> = ({
  isOpen,
  onClose,
  showId,
  showTitle,
  existingSeasonNumbers,
  onSuccess,
}) => {
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const nextSeasonNum = existingSeasonNumbers.length > 0
    ? Math.max(...existingSeasonNumbers.filter((n) => n > 0), 0) + 1
    : 1;

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SeasonFormData>({
    resolver: zodResolver(seasonSchema),
    defaultValues: {
      season_number: nextSeasonNum,
    },
  });

  if (!isOpen) return null;

  const onSubmit = async (data: SeasonFormData) => {
    setErrorMsg(null);
    if (existingSeasonNumbers.includes(data.season_number)) {
      setErrorMsg(`Season ${data.season_number} already exists for ${showTitle}.`);
      return;
    }

    try {
      await api.createSeason(showId, data.season_number);
      onSuccess();
      onClose();
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMsg(err.detail);
      } else {
        setErrorMsg('Failed to create season.');
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-base font-bold text-slate-100">Add Season to {showTitle}</h3>
          <button
            type="button"
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-slate-100 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
          {errorMsg && (
            <div className="p-3 bg-rose-950/80 border border-rose-800 text-rose-300 rounded-xl text-xs">
              {errorMsg}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Season Number *
            </label>
            <input
              type="number"
              {...register('season_number', { valueAsNumber: true })}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-sky-500"
            />
            {errors.season_number && (
              <p className="text-rose-400 text-[11px] mt-1">{errors.season_number.message}</p>
            )}
            <p className="text-[11px] text-slate-500 mt-1">
              Note: <span className="text-amber-400 font-semibold">Season 0</span> is reserved for Trailers & Promos. Regular seasons start at 1.
            </p>
          </div>

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
              {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <PlusCircle className="w-4 h-4" />}
              Add Season
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
