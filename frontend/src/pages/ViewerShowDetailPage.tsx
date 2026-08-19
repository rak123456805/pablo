import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  Play,
  Clock,
  Sparkles,
} from 'lucide-react';
import { api } from '../api/client';
import type { CatalogEpisodeEntry, CatalogShowEntry } from '../types';
import { ViewerImage } from '../components/ViewerImage';

export const ViewerShowDetailPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const [selectedLanguage, setSelectedLanguage] = useState<string>('all');
  const [activeEpisode, setActiveEpisode] = useState<CatalogEpisodeEntry | null>(null);

  // Fetch full published catalogue (NO auth, NO admin endpoint)
  const { data: catalog, isLoading, isError } = useQuery({
    queryKey: ['publishedCatalog'],
    queryFn: api.getCatalog,
  });

  // Find target show by slug across all sections in the published catalogue
  const show = React.useMemo<CatalogShowEntry | null>(() => {
    if (!catalog?.sections || !slug) return null;
    for (const shows of Object.values(catalog.sections)) {
      const match = shows.find((s) => s.slug === slug);
      if (match) return match;
    }
    return null;
  }, [catalog, slug]);

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-6 animate-pulse">
        <div className="aspect-[21/9] bg-slate-900 rounded-3xl" />
      </div>
    );
  }

  if (isError || !show) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center space-y-4">
        <h2 className="text-xl font-bold text-slate-100">Show Not Found</h2>
        <p className="text-xs text-slate-400">
          The requested show could not be found in the published catalogue.
        </p>
        <Link
          to="/viewer"
          className="inline-flex items-center gap-2 px-4 py-2 bg-amber-500 text-slate-950 text-xs font-bold rounded-xl"
        >
          <ArrowLeft className="w-4 h-4" /> Return to Story World
        </Link>
      </div>
    );
  }

  // Artwork URLs from published JSON
  const bannerUrl = show.artwork?.['banner'];
  const posterUrl = show.artwork?.['poster'];

  // Season 0 trailers & promos (EXCLUDED from normal seasons)
  const trailers = show.trailers || [];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10"
    >
      {/* Back button */}
      <div>
        <Link
          to="/viewer"
          className="inline-flex items-center gap-1.5 text-xs font-bold text-amber-400/90 hover:text-amber-300 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Stories
        </Link>
      </div>

      {/* Hero Banner Backdrop with Floating Poster Card */}
      <section className="relative rounded-3xl overflow-hidden border border-amber-900/30 bg-slate-900 shadow-2xl">
        {/* Banner Artwork Backdrop */}
        <div className="relative aspect-[16/9] md:aspect-[24/9] w-full overflow-hidden">
          <ViewerImage
            src={bannerUrl}
            alt={show.title}
            kind="banner"
            fallbackTitle={show.title}
            className="w-full h-full object-cover rounded-none border-none shadow-none"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/70 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-r from-slate-950 via-slate-950/40 to-transparent" />
        </div>

        {/* Floating Poster Overlay & Info */}
        <div className="relative md:absolute md:bottom-0 inset-x-0 p-6 md:p-8 flex flex-col md:flex-row items-start md:items-end gap-6 z-10">
          {/* Poster Artwork Card (2:3 aspect ratio) */}
          <div className="w-32 sm:w-40 shrink-0 shadow-2xl rounded-2xl overflow-hidden border-2 border-amber-500/40">
            <ViewerImage
              src={posterUrl}
              alt={show.title}
              kind="poster"
              fallbackTitle={show.title}
            />
          </div>

          {/* Show Meta */}
          <div className="space-y-3 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[11px] font-bold px-3 py-0.5 rounded-full font-mono uppercase tracking-wider">
                {show.section} Section
              </span>
            </div>

            <h1 className="text-3xl md:text-4xl font-black text-slate-100 tracking-tight">
              {show.title}
            </h1>

            {show.synopsis && (
              <p className="text-xs md:text-sm text-slate-300 max-w-2xl leading-relaxed">
                {show.synopsis}
              </p>
            )}

            {/* Categories */}
            <div className="flex flex-wrap gap-1.5 pt-1">
              {show.categories.map((cat) => (
                <span
                  key={cat}
                  className="bg-slate-900/90 text-amber-200/90 border border-amber-900/40 text-[11px] px-2.5 py-0.5 rounded-full"
                >
                  {cat}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Active Episode Player Modal / Overlay */}
      {activeEpisode && (
        <div className="p-6 bg-amber-950/40 border border-amber-800/80 rounded-3xl space-y-3 shadow-xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-amber-300 font-bold text-sm">
              <Play className="w-4 h-4 fill-amber-300" /> Playing: {activeEpisode.title}
            </div>
            <button
              type="button"
              onClick={() => setActiveEpisode(null)}
              className="text-xs text-amber-400 hover:text-amber-200 underline font-medium"
            >
              Close Player
            </button>
          </div>
          <div className="aspect-video bg-slate-950 rounded-2xl border border-slate-800 flex items-center justify-center relative overflow-hidden">
            <ViewerImage
              src={activeEpisode.artwork?.['thumbnail']}
              alt={activeEpisode.title}
              kind="thumbnail"
              fallbackTitle={activeEpisode.title}
              className="w-full h-full object-cover rounded-none"
            />
            <div className="absolute inset-0 bg-slate-950/40 flex items-center justify-center">
              <div className="w-16 h-16 rounded-full bg-amber-500 text-slate-950 flex items-center justify-center shadow-2xl">
                <Play className="w-8 h-8 fill-slate-950 ml-1" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Season 0: Trailers & Sneak Peeks (Separated from normal seasons!) */}
      {trailers.length > 0 && (
        <section className="space-y-4 bg-amber-950/20 border border-amber-900/30 rounded-3xl p-6">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-amber-400" />
            <h2 className="text-lg font-black text-slate-100 tracking-tight">Trailers & Sneak Peeks</h2>
            <span className="text-xs text-amber-400/80 font-mono">({trailers.length} trailer)</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {trailers.map((trailer) => {
              const thumbUrl = trailer.artwork?.['thumbnail'];
              return (
                <div
                  key={trailer.content_group}
                  onClick={() => setActiveEpisode(trailer)}
                  className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden hover:border-amber-500/50 transition-all cursor-pointer group p-3 space-y-2"
                >
                  {/* Thumbnail Artwork (16:9 ratio) */}
                  <ViewerImage
                    src={thumbUrl}
                    alt={trailer.title}
                    kind="thumbnail"
                    fallbackTitle={trailer.title}
                  />

                  <div className="flex items-center justify-between">
                    <h3 className="font-bold text-xs text-slate-100 group-hover:text-amber-300 transition-colors">
                      {trailer.title}
                    </h3>
                    <div className="flex gap-1">
                      {trailer.languages.map((lang) => (
                        <span
                          key={lang}
                          className="bg-amber-500/20 text-amber-300 text-[10px] font-mono font-bold px-1.5 py-0.2 rounded uppercase"
                        >
                          {lang}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Regular Seasons & Episodes List */}
      <section className="space-y-8">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-black text-slate-100 tracking-tight">Episodes & Seasons</h2>
          {/* Language filter toggle for episodes */}
          <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 p-1 rounded-xl text-xs">
            <span className="text-slate-400 font-medium px-2">Filter Language:</span>
            {['all', 'en', 'hi'].map((lang) => (
              <button
                key={lang}
                type="button"
                onClick={() => setSelectedLanguage(lang)}
                className={`px-2.5 py-1 rounded-lg font-bold uppercase transition-colors ${
                  selectedLanguage === lang
                    ? 'bg-amber-500 text-slate-950 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {lang}
              </button>
            ))}
          </div>
        </div>

        {show.seasons.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 text-center text-xs text-slate-400">
            No regular seasons published yet.
          </div>
        ) : (
          show.seasons.map((season) => {
            const filteredEps = season.episodes.filter((ep) =>
              selectedLanguage === 'all' ? true : ep.languages.includes(selectedLanguage)
            );

            return (
              <div key={season.season_number} className="space-y-4">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-xs font-black bg-amber-500/20 text-amber-300 border border-amber-500/40 px-3 py-1 rounded-xl uppercase">
                    Season {season.season_number}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">
                    {filteredEps.length} episode{filteredEps.length === 1 ? '' : 's'}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
                  {filteredEps.map((ep) => {
                    const thumbUrl = ep.artwork?.['thumbnail'];

                    return (
                      <motion.div
                        key={ep.content_group}
                        whileHover={{ y: -4 }}
                        transition={{ duration: 0.2 }}
                        onClick={() => setActiveEpisode(ep)}
                        className="bg-slate-900 border border-slate-800 hover:border-amber-500/50 rounded-2xl overflow-hidden p-3.5 space-y-3 cursor-pointer group shadow-lg"
                      >
                        {/* Thumbnail Artwork (16:9 aspect ratio) */}
                        <div className="relative">
                          <ViewerImage
                            src={thumbUrl}
                            alt={ep.title}
                            kind="thumbnail"
                            fallbackTitle={ep.title}
                          />
                          <div className="absolute bottom-2 right-2 bg-slate-950/80 backdrop-blur-xs text-slate-200 text-[10px] font-mono px-2 py-0.5 rounded-full flex items-center gap-1">
                            <Clock className="w-3 h-3 text-amber-400" />
                            {ep.duration_seconds ? `${ep.duration_seconds}s` : 'N/A'}
                          </div>
                        </div>

                        {/* Title & Language Variant Choices (ONE Card per content_group!) */}
                        <div className="space-y-1.5">
                          <div className="flex items-start justify-between gap-2">
                            <h3 className="font-extrabold text-sm text-slate-100 group-hover:text-amber-300 transition-colors leading-tight">
                              E{ep.episode_number}: {ep.title}
                            </h3>
                          </div>

                          {/* Language Choice Badges */}
                          <div className="flex items-center justify-between pt-1 border-t border-slate-800/80">
                            <span className="text-[10px] text-slate-500 font-mono">Languages:</span>
                            <div className="flex gap-1">
                              {ep.languages.map((lang) => (
                                <span
                                  key={lang}
                                  className="bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[10px] font-mono font-bold px-2 py-0.5 rounded uppercase"
                                >
                                  {lang}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            );
          })
        )}
      </section>
    </motion.div>
  );
};
