import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
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
  RefreshCw,
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout, login, isAdmin } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  // Fetch validation report summary for top-bar status indicator
  const { data: valReport } = useQuery({
    queryKey: ['validationReport'],
    queryFn: api.getValidationReport,
    refetchInterval: 10000,
    enabled: !!user,
  });

  const handleQuickLogin = async (role: 'admin' | 'editor') => {
    try {
      const email = role === 'admin' ? 'admin@peblo.tv' : 'editor@peblo.tv';
      const password = role === 'admin' ? 'adminpass' : 'editorpass';
      const res = await api.login(email, password);
      await login(res.access_token);
      navigate('/shows');
    } catch (err) {
      alert(`Login as ${role} failed. Make sure backend and seed data are running.`);
    }
  };

  const isActive = (path: string) => location.pathname.startsWith(path);

  return (
    <header className="bg-slate-900/90 backdrop-blur-md border-b border-slate-800 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-8">
          <Link to="/shows" className="flex items-center gap-2.5 group">
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

          {/* Navigation Links */}
          {user && (
            <nav className="flex items-center gap-1">
              <Link
                to="/shows"
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isActive('/shows')
                    ? 'bg-sky-950/90 text-sky-300 border border-sky-800/80 shadow-sm'
                    : 'text-slate-300 hover:text-slate-100 hover:bg-slate-800/60'
                }`}
              >
                <Film className="w-4 h-4" />
                Shows & Episodes
              </Link>

              <Link
                to="/publish"
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isActive('/publish')
                    ? 'bg-sky-950/90 text-sky-300 border border-sky-800/80 shadow-sm'
                    : 'text-slate-300 hover:text-slate-100 hover:bg-slate-800/60'
                }`}
              >
                <Send className="w-4 h-4" />
                Publishing Room
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
                  <span className="text-emerald-400">Ready to Publish</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-400 animate-pulse" />
                  <span className="text-rose-300">
                    {valReport.summary.blocking} Blocker{valReport.summary.blocking > 1 ? 's' : ''}
                  </span>
                </>
              )}
            </Link>
          )}

          {/* User Profile & Quick Switch */}
          {user ? (
            <div className="flex items-center gap-3 bg-slate-950/80 border border-slate-800 rounded-lg px-3 py-1.5">
              <div className="flex flex-col text-right">
                <span className="text-xs font-medium text-slate-200">{user.email}</span>
                <div className="flex items-center justify-end gap-1.5 mt-0.5">
                  <span
                    className={`inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.2 rounded tracking-wide uppercase ${
                      isAdmin
                        ? 'bg-purple-950 text-purple-300 border border-purple-800/60'
                        : 'bg-blue-950 text-blue-300 border border-blue-800/60'
                    }`}
                  >
                    {isAdmin ? <Shield className="w-3 h-3" /> : <UserCheck className="w-3 h-3" />}
                    {user.role}
                  </span>

                  {/* Quick role toggle */}
                  <button
                    type="button"
                    onClick={() => handleQuickLogin(isAdmin ? 'editor' : 'admin')}
                    className="text-[10px] text-sky-400 hover:text-sky-300 underline font-mono flex items-center gap-0.5"
                    title={`Switch session to ${isAdmin ? 'Editor' : 'Admin'}`}
                  >
                    <RefreshCw className="w-2.5 h-2.5" />
                    Switch to {isAdmin ? 'Editor' : 'Admin'}
                  </button>
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
              <button
                type="button"
                onClick={() => handleQuickLogin('editor')}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition-colors"
              >
                Editor Login
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin('admin')}
                className="px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium rounded-lg shadow-sm transition-colors"
              >
                Admin Login
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
