import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  Plus,
  Layers,
  Edit2,
  Trash2,
  Globe,
  Film,
  FolderPlus,
  AlertTriangle,
} from 'lucide-react';
import { api, ApiError } from '../api/client';
import type { Episode, Season, Show } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { ShowModal } from '../components/ShowModal';
import { SeasonModal } from '../components/SeasonModal';
import { EpisodeModal } from '../components/EpisodeModal';
import { DeleteConfirmModal } from '../components/DeleteConfirmModal';

export const ShowDetailPage: React.FC = () => {
  const { id: showId } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Modals state
  const [isShowModalOpen, setIsShowModalOpen] = useState(false);
  const [isSeasonModalOpen, setIsSeasonModalOpen] = useState(false);
  const [isEpisodeModalOpen, setIsEpisodeModalOpen] = useState(false);
  const [selectedSeasonForEp, setSelectedSeasonForEp] = useState<{ id: string; number: number } | null>(null);
  const [episodeToEdit, setEpisodeToEdit] = useState<Episode | null>(null);

  // Delete Modals
  const [showToDelete, setShowToDelete] = useState<Show | null>(null);
  const [seasonToDelete, setSeasonToDelete] = useState<Season | null>(null);
  const [episodeToDelete, setEpisodeToDelete] = useState<Episode | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Queries
  const {
    data: show,
    isLoading: showLoading,
    isError: showIsError,
    error: showError,
    refetch: refetchShow,
  } = useQuery({
    queryKey: ['show', showId],
    queryFn: () => api.getShow(showId!),
    enabled: !!showId,
  });

  const { data: seasons = [], refetch: refetchSeasons } = useQuery({
    queryKey: ['seasons', showId],
    queryFn: () => api.listSeasons(showId!),
    enabled: !!showId,
  });

  const { data: episodesData, refetch: refetchEpisodes } = useQuery({
    queryKey: ['episodes', showId],
    queryFn: () => api.listEpisodes({ show_id: showId!, page_size: 100 }),
    enabled: !!showId,
  });

  const { data: valReport } = useQuery({
    queryKey: ['validationReport'],
    queryFn: api.getValidationReport,
    refetchInterval: 15000,
  });

  const refetchAll = () => {
    refetchShow();
    refetchSeasons();
    refetchEpisodes();
  };

  // Group episodes by season_id
  const episodesBySeason = React.useMemo(() => {
    const map = new Map<string, Episode[]>();
    if (!episodesData?.items) return map;
    for (const ep of episodesData.items) {
      const list = map.get(ep.season_id) || [];
      list.push(ep);
      map.set(ep.season_id, list);
    }
    return map;
  }, [episodesData]);

  // Map episode issues from validation report
  const epValidationMap = React.useMemo(() => {
    const map = new Map<string, { missingArtwork: boolean; hasBlockers: boolean; messages: string[] }>();
    if (!valReport) return map;

    for (const entry of valReport.episode_issues) {
      const missingArt = entry.issues.some((i: { code: string }) => i.code === 'MISSING_ARTWORK');
      const hasBlockers = entry.issues.some((i: { severity: string }) => i.severity === 'blocking');
      map.set(entry.episode_id, {
        missingArtwork: missingArt,
        hasBlockers,
        messages: entry.issues.map((i: { message: string }) => i.message),
      });
    }
    return map;
  }, [valReport]);

  if (showLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12 space-y-6 animate-pulse">
        <div className="h-8 bg-slate-800 rounded w-1/4" />
        <div className="h-32 bg-slate-900 border border-slate-800 rounded-2xl" />
      </div>
    );
  }

  if (showIsError || !show) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center space-y-4">
        <div className="w-16 h-16 rounded-full bg-rose-950/80 border border-rose-800 text-rose-400 flex items-center justify-center mx-auto">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-slate-100">Show Not Found</h2>
        <p className="text-xs text-slate-400">
          {showError instanceof ApiError ? showError.detail : 'The requested show does not exist or was deleted.'}
        </p>
        <Link
          to="/shows"
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Shows
        </Link>
      </div>
    );
  }

  const handleOpenAddEpModal = (seasonId: string, seasonNumber: number) => {
    setSelectedSeasonForEp({ id: seasonId, number: seasonNumber });
    setEpisodeToEdit(null);
    setIsEpisodeModalOpen(true);
  };

  const handleOpenEditEpModal = (ep: Episode, seasonNumber: number) => {
    setSelectedSeasonForEp({ id: ep.season_id, number: seasonNumber });
    setEpisodeToEdit(ep);
    setIsEpisodeModalOpen(true);
  };

  const handleConfirmDeleteShow = async () => {
    if (!show) return;
    setIsDeleting(true);
    try {
      await api.deleteShow(show.id);
      navigate('/shows');
    } catch (err) {
      alert('Failed to delete show');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleConfirmDeleteSeason = async () => {
    if (!seasonToDelete) return;
    setIsDeleting(true);
    try {
      await api.deleteSeason(show.id, seasonToDelete.id);
      setSeasonToDelete(null);
      refetchAll();
    } catch (err) {
      alert('Failed to delete season');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleConfirmDeleteEpisode = async () => {
    if (!episodeToDelete) return;
    setIsDeleting(true);
    try {
      await api.deleteEpisode(episodeToDelete.id);
      setEpisodeToDelete(null);
      refetchAll();
    } catch (err) {
      alert('Failed to delete episode');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Back button */}
      <div>
        <Link
          to="/shows"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-sky-400 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Shows List
        </Link>
      </div>

      {/* Show Info Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 md:p-8 shadow-2xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-3xl font-black text-slate-100 tracking-tight">{show.title}</h1>
              <StatusBadge status={show.status as 'draft' | 'published'} />
            </div>

            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
              <span className="font-mono bg-slate-950 px-2.5 py-1 rounded-md border border-slate-800 text-slate-300">
                slug: {show.slug}
              </span>
              {show.section ? (
                <span className="inline-flex items-center gap-1 font-mono uppercase bg-sky-950 text-sky-300 border border-sky-800 px-2.5 py-1 rounded-md font-semibold">
                  <Layers className="w-3.5 h-3.5" /> {show.section}
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 bg-amber-950/80 text-amber-300 border border-amber-800/80 px-2.5 py-1 rounded-md">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> No Section Assigned
                </span>
              )}
            </div>

            {show.synopsis && <p className="text-xs text-slate-300 max-w-3xl leading-relaxed">{show.synopsis}</p>}

            {/* Category pills */}
            <div className="flex flex-wrap gap-1.5 pt-1">
              {show.categories?.map((cat: string) => (
                <span key={cat} className="bg-slate-950 border border-slate-800 text-slate-400 text-[11px] px-2.5 py-0.5 rounded-full font-medium">
                  {cat}
                </span>
              ))}
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={() => setIsShowModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition-colors"
            >
              <Edit2 className="w-4 h-4 text-sky-400" /> Edit Details & Artwork
            </button>
            <button
              type="button"
              onClick={() => setShowToDelete(show)}
              className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-950/40 rounded-xl transition-colors"
              title="Delete show"
            >
              <Trash2 className="w-4.5 h-4.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Seasons Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100">Seasons & Episodes</h2>
          <p className="text-xs text-slate-400">
            Season 0 is reserved for Trailers. Regular seasons contain main content episodes and language variants.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setIsSeasonModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs rounded-xl shadow-md transition-colors"
        >
          <FolderPlus className="w-4 h-4" /> Add Season
        </button>
      </div>

      {/* Seasons & Episodes Accordion List */}
      <div className="space-y-6">
        {seasons.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center space-y-3">
            <Film className="w-8 h-8 text-slate-500 mx-auto" />
            <h3 className="text-sm font-bold text-slate-300">No Seasons Created Yet</h3>
            <p className="text-xs text-slate-500">Add Season 1 or Season 0 (Trailers) to start creating episodes.</p>
          </div>
        ) : (
          seasons.map((season: Season) => {
            const seasonEps = (episodesBySeason.get(season.id) || []).sort(
              (a, b) => a.episode_number - b.episode_number
            );
            const isSeasonZero = season.season_number === 0;

            return (
              <div
                key={season.id}
                className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-lg space-y-0"
              >
                {/* Season Header */}
                <div className="px-6 py-4 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span
                      className={`font-mono text-xs font-bold px-3 py-1 rounded-lg border ${
                        isSeasonZero
                          ? 'bg-amber-950/80 text-amber-300 border-amber-800/80'
                          : 'bg-sky-950/80 text-sky-300 border-sky-800/80'
                      }`}
                    >
                      {isSeasonZero ? 'SEASON 0 (TRAILERS)' : `SEASON ${season.season_number}`}
                    </span>
                    <span className="text-xs text-slate-400 font-medium">
                      {seasonEps.length} episode{seasonEps.length === 1 ? '' : 's'}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleOpenAddEpModal(season.id, season.season_number)}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-sky-300 text-xs font-medium rounded-lg border border-slate-700 transition-colors"
                    >
                      <Plus className="w-3.5 h-3.5" /> Add Episode
                    </button>
                    <button
                      type="button"
                      onClick={() => setSeasonToDelete(season)}
                      className="p-1.5 text-slate-500 hover:text-rose-400 rounded-lg transition-colors"
                      title="Delete season"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Episode List */}
                {seasonEps.length === 0 ? (
                  <div className="p-6 text-center text-xs text-slate-500 italic">
                    No episodes in this season. Click &quot;Add Episode&quot; above to create one.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs text-slate-300">
                      <thead className="bg-slate-950/40 text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider">
                        <tr>
                          <th className="px-6 py-3">Ep #</th>
                          <th className="px-6 py-3">Title</th>
                          <th className="px-6 py-3">Language</th>
                          <th className="px-6 py-3">Content Group</th>
                          <th className="px-6 py-3">Duration</th>
                          <th className="px-6 py-3">Status & Artwork</th>
                          <th className="px-6 py-3 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {seasonEps.map((ep) => {
                          const valInfo = epValidationMap.get(ep.id);
                          return (
                            <tr key={ep.id} className="hover:bg-slate-800/30 transition-colors">
                              <td className="px-6 py-3.5 font-mono font-bold text-slate-300">
                                E{ep.episode_number < 10 ? `0${ep.episode_number}` : ep.episode_number}
                              </td>
                              <td className="px-6 py-3.5 font-medium text-slate-100">
                                {ep.title}
                              </td>
                              <td className="px-6 py-3.5">
                                <span className="inline-flex items-center gap-1 font-mono uppercase bg-slate-950 border border-slate-800 text-slate-300 px-2 py-0.5 rounded text-[11px]">
                                  <Globe className="w-3 h-3 text-slate-400" />
                                  {ep.language}
                                </span>
                              </td>
                              <td className="px-6 py-3.5 font-mono text-[11px] text-slate-400">
                                {ep.content_group}
                              </td>
                              <td className="px-6 py-3.5 font-mono">
                                {ep.duration_seconds ? (
                                  <span className="text-slate-300">{ep.duration_seconds}s</span>
                                ) : (
                                  <span className="text-amber-400 text-[11px]">None set</span>
                                )}
                              </td>
                              <td className="px-6 py-3.5">
                                <StatusBadge
                                  status={ep.status as 'draft' | 'published'}
                                  hasMissingArtwork={valInfo?.missingArtwork}
                                  hasBlocker={valInfo?.hasBlockers}
                                  blockerMessage={valInfo?.messages.join('; ')}
                                  size="sm"
                                />
                              </td>
                              <td className="px-6 py-3.5 text-right">
                                <div className="flex items-center justify-end gap-1">
                                  <button
                                    type="button"
                                    onClick={() => handleOpenEditEpModal(ep, season.season_number)}
                                    className="p-1.5 text-slate-400 hover:text-sky-400 hover:bg-slate-800 rounded transition-colors"
                                    title="Edit episode & artwork"
                                  >
                                    <Edit2 className="w-3.5 h-3.5" />
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => setEpisodeToDelete(ep)}
                                    className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded transition-colors"
                                    title="Delete episode"
                                  >
                                    <Trash2 className="w-3.5 h-3.5" />
                                  </button>
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Show Modal */}
      <ShowModal
        isOpen={isShowModalOpen}
        onClose={() => setIsShowModalOpen(false)}
        showToEdit={show}
        onSuccess={refetchAll}
      />

      {/* Season Modal */}
      <SeasonModal
        isOpen={isSeasonModalOpen}
        onClose={() => setIsSeasonModalOpen(false)}
        showId={show.id}
        showTitle={show.title}
        existingSeasonNumbers={seasons.map((s: Season) => s.season_number)}
        onSuccess={refetchAll}
      />

      {/* Episode Modal */}
      {selectedSeasonForEp && (
        <EpisodeModal
          isOpen={isEpisodeModalOpen}
          onClose={() => setIsEpisodeModalOpen(false)}
          seasonId={selectedSeasonForEp.id}
          showSlug={show.slug}
          seasonNumber={selectedSeasonForEp.number}
          episodeToEdit={episodeToEdit}
          onSuccess={refetchAll}
        />
      )}

      {/* Delete Show Modal */}
      <DeleteConfirmModal
        isOpen={!!showToDelete}
        onClose={() => setShowToDelete(null)}
        onConfirm={handleConfirmDeleteShow}
        title={`Delete Show: ${show?.title}`}
        message="Are you sure you want to delete this show? All associated seasons and episodes will be permanently deleted."
        isDeleting={isDeleting}
      />

      {/* Delete Season Modal */}
      <DeleteConfirmModal
        isOpen={!!seasonToDelete}
        onClose={() => setSeasonToDelete(null)}
        onConfirm={handleConfirmDeleteSeason}
        title={`Delete Season ${seasonToDelete?.season_number}`}
        message="Are you sure you want to delete this season and all its episodes?"
        isDeleting={isDeleting}
      />

      {/* Delete Episode Modal */}
      <DeleteConfirmModal
        isOpen={!!episodeToDelete}
        onClose={() => setEpisodeToDelete(null)}
        onConfirm={handleConfirmDeleteEpisode}
        title={`Delete Episode: ${episodeToDelete?.title}`}
        message="Are you sure you want to delete this episode?"
        isDeleting={isDeleting}
      />
    </div>
  );
};
