import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Sparkles, Compass, SlidersHorizontal, Home } from 'lucide-react';

export const ViewerNavbar: React.FC = () => {
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/viewer' && location.pathname === '/viewer') return true;
    if (path !== '/viewer' && location.pathname.startsWith(path)) return true;
    return false;
  };

  return (
    <header className="bg-slate-950/80 backdrop-blur-xl border-b border-amber-900/20 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-8">
          <Link to="/viewer" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-amber-500 via-orange-500 to-rose-500 flex items-center justify-center text-white shadow-lg shadow-orange-950/40 group-hover:scale-105 transition-transform">
              <Sparkles className="w-5 h-5 fill-white/20" />
            </div>
            <div>
              <span className="font-black text-transparent bg-clip-text bg-gradient-to-r from-amber-200 via-orange-300 to-amber-400 tracking-tight text-xl block leading-none">
                Peblo<span className="text-orange-400 font-bold ml-1 text-sm">TV</span>
              </span>
              <span className="text-[10px] text-amber-400/80 font-medium tracking-wider uppercase">Story World</span>
            </div>
          </Link>

          {/* Viewer Nav Links */}
          <nav className="flex items-center gap-1.5">
            <Link
              to="/viewer"
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                isActive('/viewer')
                  ? 'bg-amber-500/10 text-amber-300 border border-amber-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`}
            >
              <Home className="w-4 h-4" />
              Stories & Shows
            </Link>

            <Link
              to="/viewer/explore"
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                isActive('/viewer/explore')
                  ? 'bg-amber-500/10 text-amber-300 border border-amber-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`}
            >
              <Compass className="w-4 h-4" />
              Explore & Search
            </Link>
          </nav>
        </div>

        {/* Switch to CMS Button */}
        <div className="flex items-center gap-3">
          <Link
            to="/shows"
            className="flex items-center gap-2 px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700/80 rounded-xl text-xs font-semibold shadow-sm transition-colors"
          >
            <SlidersHorizontal className="w-3.5 h-3.5 text-sky-400" />
            <span className="hidden sm:inline">CMS Studio</span>
          </Link>
        </div>
      </div>
    </header>
  );
};
