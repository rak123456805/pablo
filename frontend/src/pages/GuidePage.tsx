import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  BookOpen,
  CheckCircle2,
  ShieldAlert,
  Image,
  Send,
  HelpCircle,
  FileCheck,
  UserCheck,
  Shield,
  Layers,
  ArrowRight,
  Info,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { ARTWORK_SPECS } from '../reference/reference';

export const GuidePage: React.FC = () => {
  const location = useLocation();
  const { isAdmin } = useAuth();

  // Determine explicit role mode:
  // If path is /admin/guide/editor -> show Editor guide
  // If path is /admin/guide/admin -> show Admin guide
  // Otherwise -> use logged-in user's role (Admin vs Editor)
  const isEditorPath = location.pathname.endsWith('/editor');
  const isAdminPath = location.pathname.endsWith('/admin');

  const showAdminGuide = isAdminPath || (isAdmin && !isEditorPath);
  const showEditorGuide = isEditorPath || (!isAdmin && !isAdminPath);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8"
    >
      {/* Header */}
      <div className="space-y-3 border-b border-slate-800 pb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-sky-950 border border-sky-800 flex items-center justify-center text-sky-400 shadow-md">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-3xl font-black text-slate-100 tracking-tight">
                {showAdminGuide ? 'Admin Operational Guide' : 'Editor Operational Guide'}
              </h1>
              <p className="text-xs text-slate-400">
                {showAdminGuide
                  ? 'Review content validation, audit release readiness, and execute atomic catalogue publishing releases.'
                  : 'Manage shows, seasons, episodes, upload validated artwork, and fix content validation issues.'}
              </p>
            </div>
          </div>

          {/* Current Active Role Badge */}
          <div className="flex items-center gap-2">
            <span
              className={`inline-flex items-center gap-1.5 text-xs font-extrabold px-3 py-1 rounded-full border shadow-sm ${
                showAdminGuide
                  ? 'bg-purple-950 text-purple-300 border border-purple-700'
                  : 'bg-blue-950 text-blue-300 border border-blue-700'
              }`}
            >
              {showAdminGuide ? <Shield className="w-3.5 h-3.5 text-purple-400" /> : <UserCheck className="w-3.5 h-3.5 text-blue-400" />}
              {showAdminGuide ? 'Admin View Only' : 'Editor View Only'}
            </span>
          </div>
        </div>
      </div>

      {/* EDITOR GUIDE CONTENT (Only visible to Editor role) */}
      {showEditorGuide && (
        <div className="space-y-8">
          {/* Hero Subtitle */}
          <div className="p-6 bg-gradient-to-r from-blue-950/60 to-slate-900 border border-blue-900/50 rounded-3xl space-y-2 shadow-lg">
            <div className="flex items-center gap-2 text-blue-300 text-xs font-bold uppercase tracking-wider">
              <UserCheck className="w-4 h-4" /> Editor Responsibility Scope
            </div>
            <h2 className="text-xl font-extrabold text-slate-100">Editor Guide</h2>
            <p className="text-xs text-slate-300 leading-relaxed">
              Manage stories, artwork and catalogue readiness. As an Editor, your responsibility is to create high-quality content metadata, upload validated artwork, and fix validation issues.
            </p>
          </div>

          {/* Capabilities Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4">
              <h3 className="text-sm font-extrabold text-emerald-400 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" /> 1. What You Can Do
              </h3>
              <ul className="space-y-2 text-xs text-slate-300 list-disc list-inside leading-relaxed">
                <li>Create and edit show details, titles, synopses, and categories</li>
                <li>Create and edit seasons and episode entries</li>
                <li>Upload poster, banner, and thumbnail artwork</li>
                <li>Review the CMS Validation Report for data quality issues</li>
                <li>Fix content problems, missing artwork, or duration fields</li>
              </ul>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4">
              <h3 className="text-sm font-extrabold text-rose-400 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4" /> 2. What You Cannot Do
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Editors cannot publish the catalogue.
              </p>
              <div className="p-3 bg-rose-950/40 border border-rose-800/60 rounded-xl text-xs text-rose-300 font-bold">
                &ldquo;Only an Admin can publish the catalogue.&rdquo;
              </div>
            </div>
          </div>

          {/* 3. Recommended Workflow */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4">
            <h3 className="text-sm font-extrabold text-slate-100 flex items-center gap-2">
              <Layers className="w-4 h-4 text-sky-400" /> 3. Recommended 7-Step Workflow
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-3 pt-2">
              {[
                { step: '1', title: 'Create Show', desc: 'Create or edit show details' },
                { step: '2', title: 'Add Seasons', desc: 'Add seasons & episode list' },
                { step: '3', title: 'Upload Artwork', desc: 'Poster, banner & thumbnail' },
                { step: '4', title: 'Check Validation', desc: 'Verify dimensions & spec' },
                { step: '5', title: 'Open Report', desc: 'Review Validation Report' },
                { step: '6', title: 'Fix Blockers', desc: 'Resolve all blocking issues' },
                { step: '7', title: 'Ask Admin', desc: 'Notify Admin to publish' },
              ].map((item) => (
                <div key={item.step} className="p-3 bg-slate-950 border border-slate-800 rounded-2xl space-y-1">
                  <span className="text-[10px] font-mono font-bold text-sky-400 bg-sky-950 px-2 py-0.5 rounded">
                    Step {item.step}
                  </span>
                  <h4 className="text-xs font-bold text-slate-200">{item.title}</h4>
                  <p className="text-[11px] text-slate-400 leading-tight">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* 4. Artwork Requirements */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4">
            <h3 className="text-sm font-extrabold text-slate-100 flex items-center gap-2">
              <Image className="w-4 h-4 text-amber-400" /> 4. Artwork Requirements (from reference.json)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
                <span className="text-xs font-bold text-amber-400 uppercase tracking-wider block">Poster Artwork</span>
                <p className="text-xs text-slate-300">Target aspect ratio: <strong>2:3</strong></p>
                <p className="text-xs text-slate-300">Dimensions: <strong>600 &times; 900 px</strong></p>
                <p className="text-xs text-slate-300">Max size: <strong>200 KB ({ARTWORK_SPECS.poster?.maxKb || 200} KB)</strong></p>
                <p className="text-[11px] text-slate-400 italic">Used on show cards & search rows.</p>
              </div>

              <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
                <span className="text-xs font-bold text-orange-400 uppercase tracking-wider block">Banner Artwork</span>
                <p className="text-xs text-slate-300">Target aspect ratio: <strong>16:9</strong></p>
                <p className="text-xs text-slate-300">Dimensions: <strong>1280 &times; 720 px</strong></p>
                <p className="text-xs text-slate-300">Max size: <strong>200 KB ({ARTWORK_SPECS.banner?.maxKb || 200} KB)</strong></p>
                <p className="text-[11px] text-slate-400 italic">Used on featured hero displays.</p>
              </div>

              <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider block">Thumbnail Artwork</span>
                <p className="text-xs text-slate-300">Target aspect ratio: <strong>16:9</strong></p>
                <p className="text-xs text-slate-300">Dimensions: <strong>640 &times; 360 px</strong></p>
                <p className="text-xs text-slate-300">Max size: <strong>200 KB ({ARTWORK_SPECS.thumbnail?.maxKb || 200} KB)</strong></p>
                <p className="text-[11px] text-slate-400 italic">Used on episode cards & lists.</p>
              </div>
            </div>
          </div>

          {/* 5. Common Problems & 6. What Happens After */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-3">
              <h3 className="text-sm font-extrabold text-amber-400 flex items-center gap-2">
                <HelpCircle className="w-4 h-4" /> 5. Common Problems to Watch For
              </h3>
              <ul className="space-y-1.5 text-xs text-slate-300 list-disc list-inside">
                <li><strong>Missing Artwork</strong> on published episodes or shows</li>
                <li><strong>Missing Duration</strong> field on published episodes</li>
                <li><strong>Invalid Dimensions</strong> or wrong aspect ratio on uploaded artwork</li>
                <li><strong>Duplicate Language Variants</strong> for the same content_group</li>
                <li><strong>Missing Required Section</strong> on published shows</li>
              </ul>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-3">
              <h3 className="text-sm font-extrabold text-emerald-400 flex items-center gap-2">
                <FileCheck className="w-4 h-4" /> 6. What Happens After You Fix Everything
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                When all blocking issues are resolved:
              </p>
              <div className="flex items-center gap-2 text-xs text-slate-200 font-semibold pt-1">
                <span>Validation Passes</span>
                <ArrowRight className="w-3.5 h-3.5 text-sky-400" />
                <span>Admin Reviews</span>
                <ArrowRight className="w-3.5 h-3.5 text-sky-400" />
                <span>Admin Publishes</span>
                <ArrowRight className="w-3.5 h-3.5 text-sky-400" />
                <span className="text-emerald-400">Visible in Viewer</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ADMIN GUIDE CONTENT (Only visible to Admin role) */}
      {showAdminGuide && (
        <div className="space-y-8">
          {/* Hero Subtitle */}
          <div className="p-6 bg-gradient-to-r from-purple-950/60 to-slate-900 border border-purple-900/50 rounded-3xl space-y-2 shadow-lg">
            <div className="flex items-center gap-2 text-purple-300 text-xs font-bold uppercase tracking-wider">
              <Shield className="w-4 h-4" /> Admin Responsibility Scope
            </div>
            <h2 className="text-xl font-extrabold text-slate-100">Admin Guide</h2>
            <p className="text-xs text-slate-300 leading-relaxed">
              Review content and publish the catalogue. As an Admin, you hold full permission to audit content validation, trigger catalogue releases, and view publish history.
            </p>
          </div>

          {/* Capabilities Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4">
              <h3 className="text-sm font-extrabold text-purple-400 flex items-center gap-2">
                <Shield className="w-4 h-4" /> 1. What You Can Do
              </h3>
              <ul className="space-y-2 text-xs text-slate-300 list-disc list-inside leading-relaxed">
                <li>Everything an Editor can do (Create/Edit shows, episodes, artwork)</li>
                <li>Review live validation reports</li>
                <li>Trigger atomic catalogue publishing releases</li>
                <li>View complete publish history and historical versions</li>
              </ul>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4">
              <h3 className="text-sm font-extrabold text-amber-400 flex items-center gap-2">
                <Info className="w-4 h-4" /> 3. Important Publishing Rule
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                The viewer reads <strong>ONLY</strong> the published catalogue file (GET /catalog). Changes made in the CMS do not become visible to child viewers until an Admin publishes the catalogue.
              </p>
            </div>
          </div>

          {/* 2. Publishing Workflow */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4">
            <h3 className="text-sm font-extrabold text-slate-100 flex items-center gap-2">
              <Send className="w-4 h-4 text-purple-400" /> 2. Admin 7-Step Publishing Workflow
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-3 pt-2">
              {[
                { step: '1', title: 'Open Report', desc: 'Open Validation Report' },
                { step: '2', title: 'Check Blockers', desc: 'Verify 0 blocking issues' },
                { step: '3', title: 'Confirm Ready', desc: 'Ensure catalogue is ready' },
                { step: '4', title: 'Click Publish', desc: 'Click Publish Catalogue' },
                { step: '5', title: 'Wait Release', desc: 'Wait for success notification' },
                { step: '6', title: 'Review Run', desc: 'Inspect run metadata' },
                { step: '7', title: 'Verify Viewer', desc: 'Open viewer & verify' },
              ].map((item) => (
                <div key={item.step} className="p-3 bg-slate-950 border border-slate-800 rounded-2xl space-y-1">
                  <span className="text-[10px] font-mono font-bold text-purple-400 bg-purple-950 px-2 py-0.5 rounded">
                    Step {item.step}
                  </span>
                  <h4 className="text-xs font-bold text-slate-200">{item.title}</h4>
                  <p className="text-[11px] text-slate-400 leading-tight">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* 4. If Publishing is Blocked & 5. Publish History */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-3">
              <h3 className="text-sm font-extrabold text-rose-400 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4" /> 4. If Publishing is Blocked
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                If the Validation Report displays blocking issues:
              </p>
              <ul className="space-y-1 text-xs text-slate-300 list-disc list-inside">
                <li>Identify the exact blocking records and error codes</li>
                <li>Fix them directly if permitted or delegate to an Editor</li>
                <li>Re-run validation until blocking issue count is 0</li>
                <li>Trigger Publish Catalogue only when validation passes cleanly</li>
              </ul>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-3">
              <h3 className="text-sm font-extrabold text-sky-400 flex items-center gap-2">
                <Layers className="w-4 h-4" /> 5. Publish History Audit
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Every publish execution creates an immutable record tracking:
              </p>
              <ul className="space-y-1 text-xs text-slate-300 list-disc list-inside">
                <li>Who triggered the release (User ID / Admin email)</li>
                <li>Timestamp started and finished</li>
                <li>Final status (Success / Failed)</li>
                <li>Total published shows & collapsed episodes count</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Navigation Quick Link */}
      <div className="pt-4 flex items-center justify-between border-t border-slate-800">
        <Link
          to="/shows"
          className="inline-flex items-center gap-2 text-xs font-bold text-sky-400 hover:text-sky-300 transition-colors"
        >
          &larr; Return to Shows & Episodes Studio
        </Link>
        {isAdmin && (
          <Link
            to="/publish"
            className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs rounded-xl shadow-md transition-colors"
          >
            Open Publishing Room &rarr;
          </Link>
        )}
      </div>
    </motion.div>
  );
};
