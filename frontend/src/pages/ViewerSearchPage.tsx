import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Search, Sparkles, Filter, X } from 'lucide-react';
import { CATEGORIES } from '../reference/reference';
import { api, ApiError } from '../api/client';
import { ViewerImage } from '../components/ViewerImage';

export const ViewerSearchPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const queryQ = searchParams.get('q') || '';
  const queryCat = searchParams.get('category') || '';
  const queryLang = searchParams.get('language') || '';
  const querySec = searchParams.get('section') || '';

  const [searchTerm, setSearchTerm] = useState(queryQ);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newParams = new URLSearchParams(searchParams);
    if (searchTerm) newParams.set('q', searchTerm);
    else newParams.delete('q');
    setSearchParams(newParams);
  };

  const setFilter = (key: string, value: string) => {
    const newParams = new URLSearchParams(searchParams);
    if (value) newParams.set(key, value);
    else newParams.delete(key);
    setSearchParams(newParams);
  };

  // Fetch search results from public published endpoint (NO admin, NO auth)
  const {
    data: searchData,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['catalogSearch', queryQ, queryCat, queryLang, querySec],
    queryFn: () =>
      api.searchCatalog({
        q: queryQ || undefined,
        category: queryCat || undefined,
        language: queryLang || undefined,
        section: querySec || undefined,
      }),
  });

  const activeFiltersCount = [queryCat, queryLang, querySec].filter(Boolean).length;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8"
    >
      {/* Header & Search Bar */}
      <div className="space-y-4 max-w-3xl">
        <h1 className="text-3xl font-black text-slate-100 tracking-tight">Explore & Search Stories</h1>
        <p className="text-xs text-slate-400">
          Find your favorite kids shows, songs, and bilingual stories from the published catalogue.
        </p>

        {/* Search input form */}
        <form onSubmit={handleSearchSubmit} className="relative">
          <Search className="w-5 h-5 text-amber-400 absolute left-4 top-3.5" />
          <input
            type="text"
            placeholder="Search by show title, episode name, or topic..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-900 border border-amber-900/40 rounded-2xl pl-12 pr-28 py-3.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 shadow-xl"
          />
          <button
            type="submit"
            className="absolute right-2 top-2 px-4 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-extrabold text-xs rounded-xl shadow-md transition-colors"
          >
            Search
          </button>
        </form>
      </div>

      {/* Filter Controls */}
      <div className="space-y-3 bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-amber-400" />
            <span className="text-xs font-bold text-slate-200">Filter Catalogue</span>
            {activeFiltersCount > 0 && (
              <span className="bg-amber-500 text-slate-950 text-[10px] font-bold px-2 py-0.5 rounded-full">
                {activeFiltersCount} active
              </span>
            )}
          </div>

          {activeFiltersCount > 0 && (
            <button
              type="button"
              onClick={() => setSearchParams(new URLSearchParams())}
              className="text-xs text-slate-400 hover:text-amber-300 flex items-center gap-1 font-medium"
            >
              <X className="w-3.5 h-3.5" /> Clear Filters
            </button>
          )}
        </div>

        {/* Language selector toggle */}
        <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-slate-800/80">
          <span className="text-xs font-medium text-slate-400 mr-2">Language:</span>
          <button
            type="button"
            onClick={() => setFilter('language', '')}
            className={`px-3 py-1 rounded-xl text-xs font-semibold transition-colors ${
              !queryLang
                ? 'bg-amber-500 text-slate-950 shadow-sm'
                : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-slate-200'
            }`}
          >
            All Languages
          </button>
          <button
            type="button"
            onClick={() => setFilter('language', 'en')}
            className={`px-3 py-1 rounded-xl text-xs font-semibold transition-colors ${
              queryLang === 'en'
                ? 'bg-amber-500 text-slate-950 shadow-sm'
                : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-slate-200'
            }`}
          >
            English (en)
          </button>
          <button
            type="button"
            onClick={() => setFilter('language', 'hi')}
            className={`px-3 py-1 rounded-xl text-xs font-semibold transition-colors ${
              queryLang === 'hi'
                ? 'bg-amber-500 text-slate-950 shadow-sm'
                : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-slate-200'
            }`}
          >
            Hindi (hi)
          </button>
        </div>

        {/* Category Pills */}
        <div className="flex flex-wrap gap-1.5 pt-2 border-t border-slate-800/80 max-h-32 overflow-y-auto">
          {CATEGORIES.map((cat) => {
            const isSelected = queryCat === cat;
            return (
              <button
                key={cat}
                type="button"
                onClick={() => setFilter('category', isSelected ? '' : cat)}
                className={`px-2.5 py-1 rounded-full text-xs font-medium transition-all ${
                  isSelected
                    ? 'bg-amber-500 text-slate-950 font-bold shadow-md'
                    : 'bg-slate-950 text-slate-400 border border-slate-800 hover:border-amber-900/60 hover:text-amber-200'
                }`}
              >
                {cat}
              </button>
            );
          })}
        </div>
      </div>

      {/* Results Section */}
      {isLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4 animate-pulse">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="aspect-[2/3] bg-slate-900 rounded-2xl" />
          ))}
        </div>
      ) : isError ? (
        <div className="p-8 bg-rose-950/80 border border-rose-800 rounded-3xl text-center text-xs text-rose-300">
          Failed to search catalogue: {error instanceof ApiError ? error.detail : 'Search failed.'}
        </div>
      ) : searchData && searchData.results.length === 0 ? (
        /* Friendly Empty State */
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-12 text-center space-y-4 max-w-lg mx-auto">
          <div className="w-16 h-16 rounded-full bg-amber-950/80 border border-amber-800/80 text-amber-400 flex items-center justify-center mx-auto shadow-xl">
            <Sparkles className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-bold text-slate-200">No stories found</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            We couldn&apos;t find any stories matching your search or filters. Try choosing a different category or clear filters to see all published content.
          </p>
          <button
            type="button"
            onClick={() => setSearchParams(new URLSearchParams())}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded-xl shadow-md transition-colors"
          >
            Show All Published Stories
          </button>
        </div>
      ) : searchData ? (
        <div className="space-y-6">
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
            <span>Found {searchData.results.length} show(s)</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-5">
            {searchData.results.map((show) => {
              const posterUrl = show.artwork?.['poster'];
              const episodeCount = show.seasons.reduce((acc, s) => acc + s.episodes.length, 0);

              return (
                <motion.div
                  key={show.slug}
                  whileHover={{ scale: 1.04 }}
                  transition={{ duration: 0.2 }}
                  className="group"
                >
                  <Link to={`/viewer/shows/${show.slug}`} className="block space-y-2">
                    {/* Poster Artwork (2:3 aspect ratio) */}
                    <ViewerImage
                      src={posterUrl}
                      alt={show.title}
                      kind="poster"
                      fallbackTitle={show.title}
                      className="w-full shadow-lg group-hover:border-amber-500/50 transition-colors"
                    />

                    {/* Title & Info */}
                    <div className="space-y-1">
                      <h3 className="font-bold text-slate-100 text-xs truncate group-hover:text-amber-300 transition-colors">
                        {show.title}
                      </h3>
                      <div className="flex items-center justify-between text-[11px] text-slate-400">
                        <span className="capitalize">{show.categories[0] || show.section}</span>
                        <span className="font-mono text-amber-400/90 font-medium">
                          {episodeCount} ep{episodeCount === 1 ? '' : 's'}
                        </span>
                      </div>
                    </div>
                  </Link>
                </motion.div>
              );
            })}
          </div>
        </div>
      ) : null}
    </motion.div>
  );
};
