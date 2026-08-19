import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Tv, Shield, UserCheck, Key, Mail, Loader2, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api, ApiError } from '../api/client';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setIsSubmitting(true);

    try {
      const res = await api.login(email, password);
      await login(res.access_token);
      navigate('/shows');
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMsg(err.detail);
      } else {
        setErrorMsg('Invalid email or password. Please verify your credentials and try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const setCredentials = (role: 'admin' | 'editor') => {
    if (role === 'admin') {
      setEmail('admin@peblo.local');
      setPassword('admin123');
    } else {
      setEmail('editor@peblo.local');
      setPassword('editor123');
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center px-4">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-md p-8 shadow-2xl space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-sky-600 to-indigo-500 flex items-center justify-center text-white mx-auto shadow-xl shadow-sky-950">
            <Tv className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight">Peblo TV CMS</h1>
          <p className="text-xs text-slate-400">Content Operations — Enter your credentials to sign in.</p>
        </div>

        {/* Credentials Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {errorMsg && (
            <div className="p-3 bg-rose-950/80 border border-rose-800 text-rose-300 rounded-xl text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@peblo.local or editor@peblo.local"
                required
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-sky-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Password</label>
            <div className="relative">
              <Key className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-sky-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3 bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-sky-950 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Sign in to CMS'}
          </button>
        </form>

        {/* Quick Credentials Fill Helpers */}
        <div className="pt-4 border-t border-slate-800 space-y-2">
          <p className="text-[11px] font-medium text-slate-400 text-center">Fill System Demo Credentials</p>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => setCredentials('admin')}
              className="flex items-center justify-center gap-1.5 p-2 bg-purple-950/50 hover:bg-purple-900/50 border border-purple-800/60 rounded-xl text-purple-300 text-xs font-semibold transition-colors"
            >
              <Shield className="w-3.5 h-3.5" />
              Fill Admin (admin123)
            </button>
            <button
              type="button"
              onClick={() => setCredentials('editor')}
              className="flex items-center justify-center gap-1.5 p-2 bg-blue-950/50 hover:bg-blue-900/50 border border-blue-800/60 rounded-xl text-blue-300 text-xs font-semibold transition-colors"
            >
              <UserCheck className="w-3.5 h-3.5" />
              Fill Editor (editor123)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
