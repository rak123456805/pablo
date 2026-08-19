import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Send,
  AlertTriangle,
  CheckCircle2,
  Shield,
  Loader2,
  Tv,
  Film,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';
import { api, ApiError } from '../api/client';
import { useAuth } from '../context/AuthContext';
import type { PublishRun, ShowValidationEntry, EpisodeValidationEntry, ValidationIssue } from '../types';

export const PublishPage: React.FC = () => {
  const { isAdmin } = useAuth();
  const queryClient = useQueryClient();

  const [isPublishing, setIsPublishing] = useState(false);
  const [publishSuccessMsg, setPublishSuccessMsg] = useState<string | null>(null);
  const [publishErrorMsg, setPublishErrorMsg] = useState<string | null>(null);

  // Fetch Validation Report
  const {
    data: report,
    isLoading: reportLoading,
    isError: reportIsError,
    error: reportError,
    refetch: refetchReport,
  } = useQuery({
    queryKey: ['validationReport'],
    queryFn: api.getValidationReport,
    refetchInterval: 10000,
  });

  // Fetch Publish Runs
  const {
    data: runsData,
    isLoading: runsLoading,
    refetch: refetchRuns,
  } = useQuery({
    queryKey: ['publishRuns'],
    queryFn: () => api.listPublishRuns(1, 20),
    refetchInterval: 15000,
  });

  const handlePublish = async () => {
    if (!isAdmin) {
      alert('Only Admin users are permitted to publish the catalogue.');
      return;
    }

    setPublishErrorMsg(null);
    setPublishSuccessMsg(null);
    setIsPublishing(true);

    try {
      const run: PublishRun = await api.publishCatalog();
      setPublishSuccessMsg(
        `Successfully published catalogue! Run ID: ${run.id}. Published ${run.shows_count} shows and ${run.episodes_count} episode entries.`
      );
      refetchReport();
      refetchRuns();
      queryClient.invalidateQueries({ queryKey: ['publishedCatalog'] });
      queryClient.invalidateQueries({ queryKey: ['catalogSearch'] });
    } catch (err) {
      if (err instanceof ApiError) {
        setPublishErrorMsg(err.detail);
      } else {
        setPublishErrorMsg('Publish run failed. Please check server logs.');
      }
    } finally {
      setIsPublishing(false);
    }
  };

  const blockingCount = report?.summary.blocking || 0;
  const warningCount = report?.summary.warning || 0;
  const canPublish = report?.can_publish ?? false;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black tracking-tight text-slate-100">Publishing Control Room</h1>
            <span className="bg-sky-950 text-sky-400 border border-sky-800 text-xs px-2.5 py-0.5 rounded-full font-mono">
              Atomic Deploy Pipeline
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Inspect live database validation reports, audit blocking issues, and deploy the kids viewer catalogue.
          </p>
        </div>

        <button
          type="button"
          onClick={() => {
            refetchReport();
            refetchRuns();
          }}
          className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 text-xs font-medium rounded-xl transition-colors shrink-0"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Re-scan Database
        </button>
      </div>

      {/* Main Readiness & Publish Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 md:p-8 shadow-2xl space-y-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div
              className={`w-12 h-12 rounded-2xl flex items-center justify-center text-white shadow-xl ${
                canPublish
                  ? 'bg-gradient-to-tr from-emerald-600 to-teal-500 shadow-emerald-950'
                  : 'bg-gradient-to-tr from-rose-600 to-amber-600 shadow-rose-950'
              }`}
            >
              {canPublish ? <CheckCircle2 className="w-7 h-7" /> : <AlertTriangle className="w-7 h-7" />}
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-100">
                {canPublish ? 'Catalogue Ready to Publish' : 'Publishing Blocked'}
              </h2>
              <p className="text-xs text-slate-400">
                {canPublish
                  ? 'All publication rules passed. Database state is valid and clean.'
                  : `${blockingCount} blocking issue(s) preventing catalogue publish.`}
              </p>
            </div>
          </div>

          {/* Quick Summary Pill */}
          <div className="hidden sm:flex items-center gap-3">
            <div className="text-right">
              <span className="text-[10px] text-slate-400 uppercase font-mono tracking-wider block">Blocking</span>
              <span className={`text-base font-black font-mono ${blockingCount > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                {blockingCount}
              </span>
            </div>
            <div className="h-8 w-px bg-slate-800" />
            <div className="text-right">
              <span className="text-[10px] text-slate-400 uppercase font-mono tracking-wider block">Warnings</span>
              <span className="text-base font-black font-mono text-amber-400">{warningCount}</span>
            </div>
          </div>
        </div>

        {/* Success Banner */}
        {publishSuccessMsg && (
          <div className="p-4 bg-emerald-950/80 border border-emerald-800 text-emerald-300 rounded-2xl text-xs flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
            <div className="flex-1 font-medium">{publishSuccessMsg}</div>
          </div>
        )}

        {/* Failure Banner */}
        {publishErrorMsg && (
          <div className="p-4 bg-rose-950/80 border border-rose-800 text-rose-300 rounded-2xl text-xs flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div className="flex-1 space-y-1">
              <p className="font-bold text-rose-200 text-sm">Publish Execution Failed</p>
              <p>{publishErrorMsg}</p>
            </div>
          </div>
        )}

        {/* Publish Action Area */}
        <div className="bg-slate-950/80 border border-slate-800/80 rounded-2xl p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-bold text-slate-200">Catalogue Promotion Action</h3>
              <p className="text-xs text-slate-400">
                Atomically compiles published shows into catalogue JSON and replaces live output.
              </p>
            </div>

            <button
              type="button"
              onClick={handlePublish}
              disabled={!canPublish || !isAdmin || isPublishing}
              className={`flex items-center justify-center gap-2.5 px-6 py-3 rounded-xl font-bold text-xs shadow-xl transition-all shrink-0 ${
                canPublish && isAdmin
                  ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-950 hover:scale-[1.02]'
                  : 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed'
              }`}
            >
              {isPublishing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Publishing Catalogue...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Publish Catalogue
                </>
              )}
            </button>
          </div>

          {/* Explanation when disabled */}
          {!canPublish && (
            <div className="p-3.5 bg-rose-950/40 border border-rose-900/60 rounded-xl text-xs text-rose-300 space-y-1">
              <p className="font-semibold text-rose-200 flex items-center gap-1.5">
                <AlertCircle className="w-4 h-4 text-rose-400" />
                Publish button is disabled because blocking issues exist:
              </p>
              <p className="text-rose-300/90 pl-5">
                Review the detailed inspection report below and resolve all blocking issues in the CMS before deploying.
              </p>
            </div>
          )}

          {!isAdmin && canPublish && (
            <div className="p-3 bg-amber-950/40 border border-amber-900/60 rounded-xl text-xs text-amber-300 flex items-center gap-2">
              <Shield className="w-4 h-4 text-amber-400 shrink-0" />
              <span>Role Restriction: You are logged in as an <strong>Editor</strong>. Only <strong>Admin</strong> users can trigger catalogue publication.</span>
            </div>
          )}
        </div>
      </div>

      {/* Validation Report Inspection Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-100">Live Database Inspection Report</h2>
            <p className="text-xs text-slate-400">
              Identifies data quality issues preventing catalogue deployment.
            </p>
          </div>
          {report && (
            <span className="text-[11px] font-mono text-slate-500">
              Last scanned: {new Date(report.generated_at).toLocaleTimeString()}
            </span>
          )}
        </div>

        {reportLoading ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center text-xs text-slate-400 animate-pulse">
            Inspecting database state...
          </div>
        ) : reportIsError ? (
          <div className="p-6 bg-rose-950/80 border border-rose-800 rounded-2xl text-rose-300 text-xs">
            Failed to generate validation report: {reportError instanceof ApiError ? reportError.detail : 'API error'}
          </div>
        ) : report ? (
          <div className="space-y-4">
            {/* Show Issues */}
            {report.show_issues.length > 0 && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-lg space-y-0">
                <div className="px-6 py-3.5 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                    Show-Level Validation Issues ({report.show_issues.length})
                  </h3>
                </div>

                <div className="divide-y divide-slate-800/80">
                  {report.show_issues.map((showEntry: ShowValidationEntry) => (
                    <div key={showEntry.show_id} className="p-4 sm:px-6 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Tv className="w-4 h-4 text-sky-400" />
                          <span className="font-bold text-slate-100 text-xs">{showEntry.show_title}</span>
                          <span className="font-mono text-[10px] text-slate-500">({showEntry.slug})</span>
                        </div>
                        <a
                          href={`/shows/${showEntry.show_id}`}
                          className="text-[11px] text-sky-400 hover:text-sky-300 font-medium underline"
                        >
                          Fix in CMS &rarr;
                        </a>
                      </div>

                      <div className="space-y-1.5 pl-6">
                        {showEntry.issues.map((issue: ValidationIssue, idx: number) => (
                          <div
                            key={idx}
                            className={`p-2.5 rounded-lg border text-xs flex items-start gap-2 ${
                              issue.severity === 'blocking'
                                ? 'bg-rose-950/50 border-rose-800/80 text-rose-200'
                                : 'bg-amber-950/50 border-amber-800/80 text-amber-200'
                            }`}
                          >
                            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                            <div className="flex-1">
                              <span className="font-mono text-[10px] font-bold uppercase tracking-wider mr-2">
                                [{issue.code}]
                              </span>
                              {issue.message}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Episode Issues */}
            {report.episode_issues.length > 0 && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-lg space-y-0">
                <div className="px-6 py-3.5 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                    Episode-Level Validation Issues ({report.episode_issues.length})
                  </h3>
                </div>

                <div className="divide-y divide-slate-800/80">
                  {report.episode_issues.map((epEntry: EpisodeValidationEntry) => (
                    <div key={epEntry.episode_id} className="p-4 sm:px-6 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Film className="w-4 h-4 text-sky-400" />
                          <span className="font-bold text-slate-100 text-xs">
                            {epEntry.show_title} &mdash; S{epEntry.season_number}E{epEntry.episode_number}: {epEntry.episode_title}
                          </span>
                          <span className="font-mono text-[10px] bg-slate-950 border border-slate-800 px-1.5 py-0.5 rounded text-slate-400 uppercase">
                            {epEntry.language}
                          </span>
                        </div>
                        <a
                          href={`/shows/${epEntry.show_id}`}
                          className="text-[11px] text-sky-400 hover:text-sky-300 font-medium underline"
                        >
                          Fix in CMS &rarr;
                        </a>
                      </div>

                      <div className="space-y-1.5 pl-6">
                        {epEntry.issues.map((issue: ValidationIssue, idx: number) => (
                          <div
                            key={idx}
                            className={`p-2.5 rounded-lg border text-xs flex items-start gap-2 ${
                              issue.severity === 'blocking'
                                ? 'bg-rose-950/50 border-rose-800/80 text-rose-200'
                                : 'bg-amber-950/50 border-amber-800/80 text-amber-200'
                            }`}
                          >
                            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                            <div className="flex-1">
                              <span className="font-mono text-[10px] font-bold uppercase tracking-wider mr-2">
                                [{issue.code}]
                              </span>
                              {issue.message}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Clean State */}
            {report.show_issues.length === 0 && report.episode_issues.length === 0 && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center space-y-2">
                <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
                <h3 className="text-sm font-bold text-slate-200">No Issues Detected</h3>
                <p className="text-xs text-slate-400">All content meets catalogue publication standards.</p>
              </div>
            )}
          </div>
        ) : null}
      </div>

      {/* Publish Run History */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-100">Publish Execution History</h2>
          <span className="text-xs text-slate-400 font-mono">
            {runsData?.total || 0} total runs
          </span>
        </div>

        {runsLoading ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 text-center text-xs text-slate-500 animate-pulse">
            Loading run history...
          </div>
        ) : runsData && runsData.items.length > 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider">
                  <tr>
                    <th className="px-5 py-3.5">Run ID</th>
                    <th className="px-5 py-3.5">Status</th>
                    <th className="px-5 py-3.5">Started At</th>
                    <th className="px-5 py-3.5">Finished At</th>
                    <th className="px-5 py-3.5">Counts</th>
                    <th className="px-5 py-3.5">Error / Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {runsData.items.map((run: PublishRun) => (
                    <tr key={run.id} className="hover:bg-slate-800/40 transition-colors font-mono text-[11px]">
                      <td className="px-5 py-3.5 font-bold text-slate-200">{run.id.slice(0, 8)}...</td>
                      <td className="px-5 py-3.5">
                        {run.status === 'success' ? (
                          <span className="inline-flex items-center gap-1 bg-emerald-950 text-emerald-400 border border-emerald-800 px-2 py-0.5 rounded font-bold">
                            <CheckCircle2 className="w-3 h-3" /> SUCCESS
                          </span>
                        ) : run.status === 'running' ? (
                          <span className="inline-flex items-center gap-1 bg-sky-950 text-sky-400 border border-sky-800 px-2 py-0.5 rounded font-bold">
                            <Loader2 className="w-3 h-3 animate-spin" /> RUNNING
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 bg-rose-950 text-rose-400 border border-rose-800 px-2 py-0.5 rounded font-bold">
                            <AlertTriangle className="w-3 h-3" /> FAILED
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-3.5 text-slate-400">
                        {new Date(run.started_at).toLocaleString()}
                      </td>
                      <td className="px-5 py-3.5 text-slate-400">
                        {run.finished_at ? new Date(run.finished_at).toLocaleString() : '-'}
                      </td>
                      <td className="px-5 py-3.5 text-slate-300">
                        {run.shows_count !== null ? `${run.shows_count} shows, ${run.episodes_count} eps` : '-'}
                      </td>
                      <td className="px-5 py-3.5 text-rose-300 max-w-xs truncate">
                        {run.error_message || run.catalog_key || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 text-center text-xs text-slate-500 italic">
            No publish runs recorded yet.
          </div>
        )}
      </div>
    </div>
  );
};
