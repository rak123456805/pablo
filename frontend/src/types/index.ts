export type UserRole = 'editor' | 'admin';

export interface User {
  id: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface Show {
  id: string;
  slug: string;
  title: string;
  synopsis: string | null;
  section: string | null;
  categories: string[];
  status: 'draft' | 'published';
  created_at: string;
  updated_at: string;
}

export interface ShowListOut {
  items: Show[];
  total: number;
  page: number;
  page_size: number;
}

export interface Season {
  id: string;
  show_id: string;
  season_number: number;
  created_at: string;
}

export interface Episode {
  id: string;
  show_id: string;
  season_id: string;
  episode_number: number;
  title: string;
  duration_seconds: number | null;
  language: string;
  content_group: string;
  status: 'draft' | 'published';
  external_id: string | null;
  artwork_available_seed: string | null;
  created_at: string;
  updated_at: string;
}

export interface EpisodeListOut {
  items: Episode[];
  total: number;
  page: number;
  page_size: number;
}

export interface Artwork {
  id: string;
  owner_type: 'show' | 'episode';
  owner_id: string;
  kind: 'poster' | 'banner' | 'thumbnail';
  storage_key: string;
  size_bytes: number;
  width_px: number;
  height_px: number;
  content_type: string;
  created_at: string;
  url: string | null;
}

export interface ValidationIssue {
  entity?: string | null;
  entity_id?: string | null;
  field?: string | null;
  code: string;
  severity: 'blocking' | 'warning' | 'info';
  message: string;
}

export interface ShowValidationEntry {
  show_id: string;
  show_title: string;
  slug: string;
  issues: ValidationIssue[];
}

export interface EpisodeValidationEntry {
  show_id: string;
  show_title: string;
  slug: string;
  episode_id: string;
  episode_title: string;
  season_number: number;
  episode_number: number;
  language: string;
  content_group: string;
  issues: ValidationIssue[];
}

export interface ValidationReport {
  generated_at: string;
  can_publish: boolean;
  show_issues: ShowValidationEntry[];
  episode_issues: EpisodeValidationEntry[];
  summary: {
    blocking: number;
    warning: number;
    info: number;
  };
}

export interface PublishRun {
  id: string;
  triggered_by: string | null;
  started_at: string;
  finished_at: string | null;
  status: string;
  shows_count: number | null;
  episodes_count: number | null;
  error_message: string | null;
  catalog_key: string | null;
}

export interface PublishRunListOut {
  items: PublishRun[];
  total: number;
}

// ─────────────────────────────────────────────────────────────────────────────
// Published Viewer Catalogue Interfaces
// ─────────────────────────────────────────────────────────────────────────────

export interface CatalogEpisodeEntry {
  content_group: string;
  episode_number: number;
  title: string;
  languages: string[];
  duration_seconds: number | null;
  artwork: Record<string, string>; // kind -> public URL
}

export interface CatalogSeasonEntry {
  season_number: number;
  episodes: CatalogEpisodeEntry[];
}

export interface CatalogShowEntry {
  slug: string;
  title: string;
  synopsis: string | null;
  section: string;
  categories: string[];
  artwork: Record<string, string>; // kind -> public URL
  seasons: CatalogSeasonEntry[];
  trailers?: CatalogEpisodeEntry[];
}

export interface CatalogOut {
  schema_version: string;
  generated_at: string;
  publish_run_id: string;
  sections: Record<string, CatalogShowEntry[]>;
}

export interface CatalogSearchResult {
  results: CatalogShowEntry[];
  total: number;
}
