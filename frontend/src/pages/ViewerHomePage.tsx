import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, Play, ChevronRight } from 'lucide-react';
import { api, ApiError } from '../api/client';
import type { CatalogShowEntry } from '../types';
import { ViewerImage } from '../components/ViewerImage';

export const ViewerHomePage: React.FC = () => {
  // Fetch published catalogue (NO auth, NO admin endpoint)
  const {
    data: catalog,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['publishedCatalog'],
    queryFn: api.getCatalog,
    staleTime: 30000,
  });

  // Pick hero show dynamically (first available show in featured or series section)
  const featuredHeroShow = useMemo<CatalogShowEntry | null>(() => {
    if (!catalog?.sections) return null;
    const featuredList = catalog.sections['featured'] || [];
    if (featuredList.length > 0) return featuredList[0];

    // Fallback to first show in any section
    for (const shows of Object.values(catalog.sections)) {
      if (shows.length > 0) return shows[0];
    }
    return null;
  }, [catalog]);

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-10 animate-pulse">
        {/* Hero Skeleton */}
        <div className="w-full aspect-[21/9] bg-slate-900 rounded-3xl border border-slate-800" />
        {/* Section Skeleton */}
        <div className="space-y-4">
          <div className="h-6 bg-slate-800 rounded w-48" />
          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="aspect-[2/3] bg-slate-900 rounded-2xl" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Catalogue not yet published state
  if (isError) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center space-y-5">
        <div className="w-16 h-16 rounded-3xl bg-amber-950/80 border border-amber-800/80 text-amber-400 flex items-center justify-center mx-auto shadow-2xl">
          <Sparkles className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-black text-slate-100 tracking-tight">Catalogue Under Construction</h2>
        <p className="text-sm text-slate-400 max-w-md mx-auto leading-relaxed">
          {error instanceof ApiError && error.status === 404
            ? 'No catalogue has been published yet. Log into the CMS Studio to publish your first content catalogue!'
            : 'Unable to load published catalogue. Please make sure backend is running.'}
        </p>
        <Link
          to="/publish"
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-amber-950 transition-colors"
        >
          Open CMS Publishing Room &rarr;
        </Link>
      </div>
    );
  }

  // Active section keys from published catalogue
  const sectionKeys = Object.keys(catalog?.sections || {}).filter(
    (key) => (catalog?.sections[key]?.length || 0) > 0
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-12"
    >
      {/* 1. Featured Hero (Uses BANNER Artwork!) */}
      {featuredHeroShow && (
        <section className="relative rounded-3xl overflow-hidden border border-amber-900/30 bg-slate-900 shadow-2xl group">
          {/* Banner Artwork Backdrop */}
          <div className="relative aspect-[16/9] md:aspect-[21/9] w-full overflow-hidden">
            <ViewerImage
              src={featuredHeroShow.artwork?.['banner']}
              alt={featuredHeroShow.title}
              kind="banner"
              fallbackTitle={featuredHeroShow.title}
              className="w-full h-full object-cover rounded-none border-none shadow-none"
            />
            {/* Dark warm overlay gradient */}
            <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/60 to-transparent" />
            <div className="absolute inset-0 bg-gradient-to-r from-slate-950 via-slate-950/40 to-transparent" />
          </div>

          {/* Hero Content overlay */}
          <div className="absolute bottom-0 inset-x-0 p-6 md:p-10 space-y-3 z-10">
            <div className="flex flex-wrap items-center gap-2">
              <span className="bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[11px] font-bold px-3 py-0.5 rounded-full font-mono uppercase tracking-wider">
                Featured Show
              </span>
              <span className="bg-slate-900/80 backdrop-blur-xs text-slate-300 text-[11px] font-medium px-2.5 py-0.5 rounded-full border border-slate-700">
                {featuredHeroShow.section.toUpperCase()}
              </span>
            </div>

            <h1 className="text-3xl md:text-5xl font-black text-slate-100 tracking-tight drop-shadow-md">
              {featuredHeroShow.title}
            </h1>

            {featuredHeroShow.synopsis && (
              <p className="text-xs md:text-sm text-slate-300 max-w-2xl line-clamp-2 leading-relaxed drop-shadow-sm">
                {featuredHeroShow.synopsis}
              </p>
            )}

            {/* Categories */}
            <div className="flex flex-wrap gap-1.5 pt-1">
              {featuredHeroShow.categories.map((cat) => (
                <span
                  key={cat}
                  className="bg-slate-900/90 text-amber-200/90 border border-amber-900/40 text-[11px] px-2.5 py-0.5 rounded-full"
                >
                  {cat}
                </span>
              ))}
            </div>

            {/* Actions */}
            <div className="pt-2 flex items-center gap-3">
              <Link
                to={`/viewer/shows/${featuredHeroShow.slug}`}
                className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-slate-950 font-black text-xs rounded-2xl shadow-xl shadow-orange-950/60 transition-transform active:scale-95"
              >
                <Play className="w-4 h-4 fill-slate-950" /> Watch Stories
              </Link>
            </div>
          </div>
        </section>
      )}

      {/* 2. Dynamic Section Rows (Uses POSTER Artwork!) */}
      {sectionKeys.length === 0 ? (
        <div className="p-12 text-center text-slate-400 text-xs bg-slate-900 rounded-3xl border border-slate-800">
          No published shows found in any section.
        </div>
      ) : (
        sectionKeys.map((sectionKey) => {
          const shows = catalog!.sections[sectionKey] || [];
          if (shows.length === 0) return null;

          return (
            <section key={sectionKey} className="space-y-4">
              {/* Section Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-amber-500" />
                  <h2 className="text-xl font-black text-slate-100 tracking-tight capitalize">
                    {sectionKey} Section
                  </h2>
                  <span className="text-xs text-slate-500 font-mono">({shows.length} shows)</span>
                </div>

                <Link
                  to={`/viewer/explore?section=${sectionKey}`}
                  className="text-xs text-amber-400 hover:text-amber-300 font-bold flex items-center gap-1 transition-colors"
                >
                  Explore All <ChevronRight className="w-4 h-4" />
                </Link>
              </div>

              {/* Horizontal Scroll Row */}
              <div className="flex items-center gap-4 overflow-x-auto pb-4 pt-1 scrollbar-thin">
                {shows.map((show) => {
                  const posterUrl = show.artwork?.['poster'];
                  const episodeCount = show.seasons.reduce((acc, s) => acc + s.episodes.length, 0);

                  return (
                    <motion.div
                      key={show.slug}
                      whileHover={{ scale: 1.04 }}
                      transition={{ duration: 0.2 }}
                      className="w-40 sm:w-48 shrink-0 group"
                    >
                      <Link to={`/viewer/shows/${show.slug}`} className="block space-y-2">
                        {/* Show Poster Artwork (2:3 aspect ratio) */}
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
            </section>
          );
        })
      )}
    </motion.div>
  );
};
