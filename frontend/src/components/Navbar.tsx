import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import {
  AlertTriangle,
  CheckCircle2,
  Tv,
  LogOut,
  Shield,
  UserCheck,
  Send,
  Film,
  BookOpen,
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout, isAdmin } = useAuth();
  const location = useLocation();

  // Fetch validation report summary for top-bar status indicator
  const { data: valReport } = useQuery({
    queryKey: ['validationReport'],
    queryFn: api.getValidationReport,
    refetchInterval: 10000,
    enabled: !!user,
  });

  const isActive = (path: string) => location.pathname.startsWith(path);

  return (
    <header className="bg-slate-900/90 backdrop-blur-md border-b border-slate-800 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo - Links to Viewer */}
        <div className="flex items-center gap-8">
          <Link to="/viewer" className="flex items-center gap-2.5 group" title="Open Peblo TV Viewer">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-500 flex items-center justify-center text-white shadow-lg shadow-sky-900/40 group-hover:scale-105 transition-transform">
              <Tv className="w-5 h-5" />
            </div>
            <div>
              <span className="font-extrabold text-slate-100 tracking-tight text-lg block leading-none">
                PEBLO <span className="text-sky-400 font-semibold">CMS</span>
              </span>
              <span className="text-[10px] text-slate-400 font-mono tracking-wider uppercase">Content Operations</span>
            </div>
          </Link>

          {/* Role-based Navigation Links */}
          {user && (
            <nav className="flex items-center gap-1">
              <Link
                to="/shows"
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isActive('/shows')
                    ? 'bg-sky-950/90 text-sky-300 border border-sky-800/80 shadow-sm'
                    : 'text-slate-300 hover:text-slate-100 hover:bg-slate-800/60'
                }`}
              >
                <Film className="w-4 h-4" />
                Shows & Episodes
              </Link>

              {isAdmin && (
                <Link
                  to="/publish"
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    isActive('/publish')
                      ? 'bg-purple-950/90 text-purple-300 border border-purple-800/80 shadow-sm'
                      : 'text-slate-300 hover:text-slate-100 hover:bg-slate-800/60'
                  }`}
                >
                  <Send className="w-4 h-4" />
                  Publishing Room
                </Link>
              )}

              <Link
                to={isAdmin ? '/admin/guide/admin' : '/admin/guide/editor'}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isActive('/admin/guide') || isActive('/guide')
                    ? 'bg-slate-800 text-amber-300 border border-amber-800/60 shadow-sm'
                    : 'text-slate-300 hover:text-slate-100 hover:bg-slate-800/60'
                }`}
              >
                <BookOpen className="w-4 h-4 text-amber-400" />
                {isAdmin ? 'Admin Guide' : 'Editor Guide'}
              </Link>
            </nav>
          )}
        </div>

        {/* Right Controls */}
        <div className="flex items-center gap-4">
          {/* Validation Status Indicator */}
          {user && valReport && (
            <Link
              to="/publish"
              className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border transition-colors bg-slate-950/80"
              title="Click to view full validation report"
            >
              {valReport.can_publish ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-emerald-400 font-bold">Ready to Publish</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-400 animate-pulse" />
                  <span className="text-rose-300 font-bold">
                    {valReport.summary.blocking} Blocker{valReport.summary.blocking > 1 ? 's' : ''}
                  </span>
                </>
              )}
            </Link>
          )}

          {/* User Profile & Role Badges */}
          {user ? (
            <div className="flex items-center gap-3 bg-slate-950/80 border border-slate-800 rounded-xl px-3 py-1.5">
              <div className="flex flex-col text-right">
                <span className="text-xs font-medium text-slate-200">{user.email}</span>
                <div className="flex items-center justify-end gap-1.5 mt-0.5">
                  <span
                    className={`inline-flex items-center gap-1 text-[10px] font-extrabold px-2 py-0.5 rounded-full tracking-wide uppercase ${
                      isAdmin
                        ? 'bg-purple-950 text-purple-300 border border-purple-700/80 shadow-xs'
                        : 'bg-blue-950 text-blue-300 border border-blue-700/80 shadow-xs'
                    }`}
                  >
                    {isAdmin ? <Shield className="w-3 h-3 text-purple-400" /> : <UserCheck className="w-3 h-3 text-blue-400" />}
                    {user.role}
                  </span>
                </div>
              </div>

              <button
                type="button"
                onClick={logout}
                className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded transition-colors"
                title="Log out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                to="/login"
                className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs rounded-xl shadow-md transition-colors"
              >
                Sign In
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
