import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Search,
  Plus,
  ChevronLeft,
  ChevronRight,
  Tv,
  AlertTriangle,
  Film,
  Edit2,
  Trash2,
  Lock,
  Layers,
} from 'lucide-react';
import { LANGUAGES, SECTIONS } from '../reference/reference';
import { api, ApiError } from '../api/client';
import { useAuth } from '../context/AuthContext';
import type { Show } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { ShowModal } from '../components/ShowModal';
import { DeleteConfirmModal } from '../components/DeleteConfirmModal';

export const ShowsListPage: React.FC = () => {
  const { user, isEditor } = useAuth();

  // Filters state
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSection, setSelectedSection] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedLanguage, setSelectedLanguage] = useState<string>('');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  // Modal state
  const [isShowModalOpen, setIsShowModalOpen] = useState(false);
  const [showToEdit, setShowToEdit] = useState<Show | null>(null);
  const [showToDelete, setShowToDelete] = useState<Show | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Fetch Shows
  const {
    data: showsData,
    isLoading: showsLoading,
    isError: showsIsError,
    error: showsError,
    refetch: refetchShows,
  } = useQuery({
    queryKey: ['shows', selectedSection, selectedStatus, searchTerm, page],
    queryFn: () =>
      api.listShows({
        section: selectedSection || undefined,
        status: selectedStatus || undefined,
        q: searchTerm || undefined,
        page,
        page_size: pageSize,
      }),
  });

  // Fetch Validation Report to map show/episode blockers and missing artwork indicators
  const { data: valReport } = useQuery({
    queryKey: ['validationReport'],
    queryFn: api.getValidationReport,
    refetchInterval: 15000,
  });

  // Helper lookups for validation indicators
  const showBlockersMap = React.useMemo(() => {
    const map = new Map<string, { missingSection: boolean; blockersCount: number; messages: string[] }>();
    if (!valReport) return map;

    for (const entry of valReport.show_issues) {
      const blockers = entry.issues.filter((i: { severity: string }) => i.severity === 'blocking');
      const missingSection = entry.issues.some((i: { code: string }) => i.code === 'MISSING_SECTION');
      map.set(entry.show_id, {
        missingSection,
        blockersCount: blockers.length,
        messages: entry.issues.map((i: { message: string }) => i.message),
      });
    }
    return map;
  }, [valReport]);

  const showEpisodeIssuesMap = React.useMemo(() => {
    const map = new Map<string, { missingArtworkCount: number; epBlockersCount: number }>();
    if (!valReport) return map;

    for (const entry of valReport.episode_issues) {
      const current = map.get(entry.show_id) || { missingArtworkCount: 0, epBlockersCount: 0 };
      const missingArt = entry.issues.some((i: { code: string }) => i.code === 'MISSING_ARTWORK');
      const blockers = entry.issues.filter((i: { severity: string }) => i.severity === 'blocking').length;
      map.set(entry.show_id, {
        missingArtworkCount: current.missingArtworkCount + (missingArt ? 1 : 0),
        epBlockersCount: current.epBlockersCount + blockers,
      });
    }
    return map;
  }, [valReport]);

  const handleOpenCreateModal = () => {
    setShowToEdit(null);
    setIsShowModalOpen(true);
  };

  const handleOpenEditModal = (show: Show, e: React.MouseEvent) => {
    e.stopPropagation();
    setShowToEdit(show);
    setIsShowModalOpen(true);
  };

  const handleOpenDeleteModal = (show: Show, e: React.MouseEvent) => {
    e.stopPropagation();
    setShowToDelete(show);
  };

  const [deletedShowNotice, setDeletedShowNotice] = useState<string | null>(null);

  const handleConfirmDelete = async () => {
    if (!showToDelete) return;
    setIsDeleting(true);
    const title = showToDelete.title;
    try {
      await api.deleteShow(showToDelete.id);
      setShowToDelete(null);
      refetchShows();
      setDeletedShowNotice(
        `"${title}" deleted from CMS. To remove it from the live Viewer, click Publish Catalogue.`
      );
    } catch (err) {
      alert(err instanceof ApiError ? err.detail : 'Failed to delete show');
    } finally {
      setIsDeleting(false);
    }
  };

  // State 1: Permission Denied
  if (!user || !isEditor) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center space-y-4">
        <div className="w-16 h-16 rounded-full bg-rose-950/80 border border-rose-800 text-rose-400 flex items-center justify-center mx-auto">
          <Lock className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-slate-100">Permission Denied</h2>
        <p className="text-xs text-slate-400 max-w-md mx-auto">
          You need an Editor or Admin account to view and manage content. Please log in with valid credentials.
        </p>
      </div>
    );
  }

  const totalPages = showsData ? Math.ceil(showsData.total / pageSize) : 1;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Header & Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black tracking-tight text-slate-100">Shows Catalogue</h1>
            <span className="bg-sky-950 text-sky-400 border border-sky-800 text-xs px-2.5 py-0.5 rounded-full font-mono">
              {showsData?.total || 0} shows
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Manage kid shows, season metadata, language variants, and publication statuses.
          </p>
        </div>

        <button
          type="button"
          onClick={handleOpenCreateModal}
          className="flex items-center justify-center gap-2 px-4 py-2.5 bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-sky-950 transition-all hover:scale-[1.02] shrink-0"
        >
          <Plus className="w-4 h-4" />
          Create New Show
        </button>
      </div>

      {/* Delete Notice / Publish Reminder Banner */}
      {deletedShowNotice && (
        <div className="p-4 bg-amber-950/90 border border-amber-800 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-amber-200 text-xs shadow-lg animate-in fade-in">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
            <div>
              <p className="font-bold text-slate-100">{deletedShowNotice}</p>
              <p className="text-[11px] text-amber-300/80 mt-0.5">
                Deletions and metadata changes in CMS do not update the child viewer until an Admin publishes the catalogue.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Link
              to="/publish"
              className="px-3.5 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-extrabold text-xs rounded-xl shadow-md transition-colors"
            >
              Publish Catalogue Now &rarr;
            </Link>
            <button
              type="button"
              onClick={() => setDeletedShowNotice(null)}
              className="px-2 py-1 text-amber-400 hover:text-amber-200 font-bold"
            >
              &times;
            </button>
          </div>
        </div>
      )}

      {/* Filter Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
          {/* Search input */}
          <div className="relative md:col-span-2">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search by show title..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
            />
          </div>

          {/* Section filter */}
          <div>
            <select
              value={selectedSection}
              onChange={(e) => {
                setSelectedSection(e.target.value);
                setPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
            >
              <option value="">All Sections</option>
              {SECTIONS.map((sec) => (
                <option key={sec} value={sec}>
                  Section: {sec.toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          {/* Status filter */}
          <div>
            <select
              value={selectedStatus}
              onChange={(e) => {
                setSelectedStatus(e.target.value);
                setPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
            >
              <option value="">All Statuses</option>
              <option value="draft">Drafts</option>
              <option value="published">Published</option>
            </select>
          </div>

          {/* Language filter */}
          <div>
            <select
              value={selectedLanguage}
              onChange={(e) => {
                setSelectedLanguage(e.target.value);
                setPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
            >
              <option value="">All Languages</option>
              {LANGUAGES.map((lang) => (
                <option key={lang} value={lang}>
                  Language: {lang === 'en' ? 'English (en)' : 'Hindi (hi)'}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* State 2: API Error State */}
      {showsIsError && (
        <div className="p-6 bg-rose-950/80 border border-rose-800 rounded-2xl flex items-center justify-between text-rose-300 text-xs">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-rose-400 shrink-0" />
            <div>
              <p className="font-bold text-rose-200 text-sm">Failed to load shows</p>
              <p>{showsError instanceof ApiError ? showsError.detail : 'API request failed.'}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => refetchShows()}
            className="px-3 py-1.5 bg-rose-900 hover:bg-rose-800 text-white rounded-lg font-medium transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* State 3: Loading Skeleton */}
      {showsLoading && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden divide-y divide-slate-800 animate-pulse">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="p-5 flex items-center justify-between">
              <div className="space-y-2 flex-1">
                <div className="h-4 bg-slate-800 rounded w-1/3" />
                <div className="h-3 bg-slate-800/60 rounded w-1/2" />
              </div>
              <div className="h-6 bg-slate-800 rounded-full w-24" />
            </div>
          ))}
        </div>
      )}

      {/* State 4: Shows Table & Data List */}
      {!showsLoading && !showsIsError && showsData && (
        <>
          {showsData.items.length === 0 ? (
            /* State 5: Empty State */
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center space-y-3">
              <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mx-auto text-slate-500">
                <Film className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-slate-200">No shows found</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                No shows match your search query or filter criteria. Try resetting filters or create a new show.
              </p>
            </div>
          ) : (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider">
                    <tr>
                      <th className="px-5 py-3.5">Show & Slug</th>
                      <th className="px-5 py-3.5">Section</th>
                      <th className="px-5 py-3.5">Categories</th>
                      <th className="px-5 py-3.5">Validation & Status</th>
                      <th className="px-5 py-3.5 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {showsData.items.map((show: Show) => {
                      const valInfo = showBlockersMap.get(show.id);
                      const epValInfo = showEpisodeIssuesMap.get(show.id);

                      const hasMissingArtwork = (epValInfo?.missingArtworkCount || 0) > 0;
                      const totalBlockers = (valInfo?.blockersCount || 0) + (epValInfo?.epBlockersCount || 0);

                      return (
                        <tr
                          key={show.id}
                          onClick={() => window.location.assign(`/shows/${show.id}`)}
                          className="hover:bg-slate-800/40 transition-colors cursor-pointer group"
                        >
                          {/* Title & Slug */}
                          <td className="px-5 py-4">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-lg bg-sky-950 border border-sky-800/60 flex items-center justify-center text-sky-400 font-bold shrink-0">
                                <Tv className="w-4 h-4" />
                              </div>
                              <div>
                                <Link
                                  to={`/shows/${show.id}`}
                                  className="font-bold text-slate-100 group-hover:text-sky-400 transition-colors text-sm"
                                >
                                  {show.title}
                                </Link>
                                <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                                  slug: <span className="text-slate-300">{show.slug}</span>
                                </div>
                              </div>
                            </div>
                          </td>

                          {/* Section */}
                          <td className="px-5 py-4">
                            {show.section ? (
                              <span className="inline-flex items-center gap-1 bg-slate-950 border border-slate-800 px-2.5 py-1 rounded-md font-mono text-[11px] text-sky-300 font-semibold uppercase">
                                <Layers className="w-3 h-3 text-sky-400" />
                                {show.section}
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 bg-amber-950/60 border border-amber-800/60 text-amber-300 px-2 py-0.5 rounded text-[11px] font-medium">
                                <AlertTriangle className="w-3 h-3" />
                                No Section
                              </span>
                            )}
                          </td>

                          {/* Categories */}
                          <td className="px-5 py-4">
                            <div className="flex flex-wrap gap-1 max-w-xs">
                              {show.categories && show.categories.length > 0 ? (
                                show.categories.slice(0, 3).map((cat: string) => (
                                  <span
                                    key={cat}
                                    className="bg-slate-950 text-slate-400 border border-slate-800 px-2 py-0.5 rounded text-[10px]"
                                  >
                                    {cat}
                                  </span>
                                ))
                              ) : (
                                <span className="text-slate-500 text-[11px] italic">None</span>
                              )}
                              {show.categories && show.categories.length > 3 && (
                                <span className="text-slate-500 text-[10px]">
                                  +{show.categories.length - 3} more
                                </span>
                              )}
                            </div>
                          </td>

                          {/* Status & Validation Indicators */}
                          <td className="px-5 py-4">
                            <StatusBadge
                              status={show.status as 'draft' | 'published'}
                              hasMissingArtwork={hasMissingArtwork}
                              hasBlocker={totalBlockers > 0}
                              blockerMessage={`${totalBlockers} publish blocker(s) detected`}
                            />
                          </td>

                          {/* Actions */}
                          <td className="px-5 py-4 text-right">
                            <div className="flex items-center justify-end gap-1" onClick={(e) => e.stopPropagation()}>
                              <button
                                type="button"
                                onClick={(e) => handleOpenEditModal(show, e)}
                                className="p-1.5 text-slate-400 hover:text-sky-400 hover:bg-slate-800 rounded-lg transition-colors"
                                title="Edit show details & artwork"
                              >
                                <Edit2 className="w-4 h-4" />
                              </button>
                              <button
                                type="button"
                                onClick={(e) => handleOpenDeleteModal(show, e)}
                                className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
                                title="Delete show"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="px-6 py-4 bg-slate-950/80 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                  <span>
                    Showing Page <strong className="text-slate-200">{page}</strong> of{' '}
                    <strong className="text-slate-200">{totalPages}</strong>
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      disabled={page <= 1}
                      onClick={() => setPage((p) => Math.max(p - 1, 1))}
                      className="p-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 rounded-lg disabled:opacity-40"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      disabled={page >= totalPages}
                      onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                      className="p-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 rounded-lg disabled:opacity-40"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Show Form Modal */}
      <ShowModal
        isOpen={isShowModalOpen}
        onClose={() => setIsShowModalOpen(false)}
        showToEdit={showToEdit}
        onSuccess={refetchShows}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={!!showToDelete}
        onClose={() => setShowToDelete(null)}
        onConfirm={handleConfirmDelete}
        title={`Delete Show: ${showToDelete?.title}`}
        message="Are you sure you want to delete this show? All associated seasons and episodes will be permanently deleted."
        isDeleting={isDeleting}
      />
    </div>
  );
};
