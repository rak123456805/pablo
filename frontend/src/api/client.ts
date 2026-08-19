import type {
  Artwork,
  CatalogOut,
  CatalogSearchResult,
  Episode,
  EpisodeListOut,
  PublishRunListOut,
  PublishRun,
  Season,
  Show,
  ShowListOut,
  User,
  ValidationReport,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('peblo_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    ...getAuthHeader(),
    ...(options.headers || {}),
  };

  const response = await fetch(url, { ...options, headers });

  if (response.status === 204) {
    return {} as T;
  }

  if (!response.ok) {
    let errorMsg = `Request failed with status ${response.status}`;
    try {
      const data = await response.json();
      if (typeof data.detail === 'string') {
        errorMsg = data.detail;
      } else if (Array.isArray(data.detail)) {
        errorMsg = data.detail.map((d: any) => `${d.loc.join('.')}: ${d.msg}`).join(', ');
      }
    } catch {
      // ignore json parse error
    }

    if (response.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('peblo_token');
    }

    throw new ApiError(response.status, errorMsg);
  }

  return response.json();
}

export const api = {
  // Auth
  login: async (email: string, password: string): Promise<{ access_token: string }> => {
    return request('/auth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
  },

  getCurrentUser: async (): Promise<User> => {
    return request('/auth/me');
  },

  // Shows
  listShows: async (params: {
    section?: string;
    status?: string;
    q?: string;
    page?: number;
    page_size?: number;
  }): Promise<ShowListOut> => {
    const searchParams = new URLSearchParams();
    if (params.section) searchParams.append('section', params.section);
    if (params.status) searchParams.append('status', params.status);
    if (params.q) searchParams.append('q', params.q);
    if (params.page) searchParams.append('page', params.page.toString());
    if (params.page_size) searchParams.append('page_size', params.page_size.toString());

    const query = searchParams.toString();
    return request(`/admin/shows${query ? `?${query}` : ''}`);
  },

  getShow: async (id: string): Promise<Show> => {
    return request(`/admin/shows/${id}`);
  },

  createShow: async (data: {
    title: string;
    slug: string;
    synopsis?: string | null;
    section?: string | null;
    categories?: string[];
    status?: 'draft' | 'published';
  }): Promise<Show> => {
    return request('/admin/shows', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  updateShow: async (
    id: string,
    data: {
      title?: string;
      synopsis?: string | null;
      section?: string | null;
      categories?: string[];
      status?: 'draft' | 'published';
    }
  ): Promise<Show> => {
    return request(`/admin/shows/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  deleteShow: async (id: string): Promise<void> => {
    return request(`/admin/shows/${id}`, { method: 'DELETE' });
  },

  // Seasons
  listSeasons: async (showId: string): Promise<Season[]> => {
    return request(`/admin/shows/${showId}/seasons`);
  },

  createSeason: async (showId: string, season_number: number): Promise<Season> => {
    return request(`/admin/shows/${showId}/seasons`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ season_number }),
    });
  },

  deleteSeason: async (showId: string, seasonId: string): Promise<void> => {
    return request(`/admin/shows/${showId}/seasons/${seasonId}`, { method: 'DELETE' });
  },

  // Episodes
  listEpisodes: async (params: {
    show_id?: string;
    season_id?: string;
    status?: string;
    language?: string;
    page?: number;
    page_size?: number;
  }): Promise<EpisodeListOut> => {
    const searchParams = new URLSearchParams();
    if (params.show_id) searchParams.append('show_id', params.show_id);
    if (params.season_id) searchParams.append('season_id', params.season_id);
    if (params.status) searchParams.append('status', params.status);
    if (params.language) searchParams.append('language', params.language);
    if (params.page) searchParams.append('page', params.page.toString());
    if (params.page_size) searchParams.append('page_size', params.page_size.toString());

    const query = searchParams.toString();
    return request(`/admin/episodes${query ? `?${query}` : ''}`);
  },

  getEpisode: async (id: string): Promise<Episode> => {
    return request(`/admin/episodes/${id}`);
  },

  createEpisode: async (data: {
    season_id: string;
    episode_number: number;
    title: string;
    duration_seconds?: number | null;
    language: string;
    content_group: string;
    status?: 'draft' | 'published';
  }): Promise<Episode> => {
    return request('/admin/episodes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  updateEpisode: async (
    id: string,
    data: {
      title?: string;
      duration_seconds?: number | null;
      language?: string;
      content_group?: string;
      status?: 'draft' | 'published';
    }
  ): Promise<Episode> => {
    return request(`/admin/episodes/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  deleteEpisode: async (id: string): Promise<void> => {
    return request(`/admin/episodes/${id}`, { method: 'DELETE' });
  },

  // Artwork
  uploadArtwork: async (
    owner_type: 'show' | 'episode',
    owner_id: string,
    kind: 'poster' | 'banner' | 'thumbnail',
    file: File
  ): Promise<Artwork> => {
    const formData = new FormData();
    formData.append('owner_type', owner_type);
    formData.append('owner_id', owner_id);
    formData.append('kind', kind);
    formData.append('file', file);

    const token = localStorage.getItem('peblo_token');
    const response = await fetch(`${API_BASE_URL}/admin/artwork`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });

    if (!response.ok) {
      let errorMsg = `Artwork upload failed (${response.status})`;
      try {
        const data = await response.json();
        if (data.detail) errorMsg = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      } catch {
        // ignore
      }
      throw new ApiError(response.status, errorMsg);
    }

    return response.json();
  },

  deleteArtwork: async (id: string): Promise<void> => {
    return request(`/admin/artwork/${id}`, { method: 'DELETE' });
  },

  // Validation Report
  getValidationReport: async (): Promise<ValidationReport> => {
    return request('/admin/validation/report');
  },

  // Publish
  publishCatalog: async (): Promise<PublishRun> => {
    return request('/admin/catalog/publish', { method: 'POST' });
  },

  listPublishRuns: async (page = 1, page_size = 20): Promise<PublishRunListOut> => {
    return request(`/admin/catalog/runs?page=${page}&page_size=${page_size}`);
  },

  // Public Viewer Catalogue Endpoints (NO admin endpoints, NO auth required)
  getCatalog: async (): Promise<CatalogOut> => {
    const url = `${API_BASE_URL}/catalog`;
    const response = await fetch(url);
    if (!response.ok) {
      let errorMsg = `Catalogue fetch failed (${response.status})`;
      try {
        const data = await response.json();
        if (data.detail) errorMsg = data.detail;
      } catch {
        // ignore
      }
      throw new ApiError(response.status, errorMsg);
    }
    return response.json();
  },

  searchCatalog: async (params: {
    q?: string;
    category?: string;
    language?: string;
    section?: string;
  }): Promise<CatalogSearchResult> => {
    const searchParams = new URLSearchParams();
    if (params.q) searchParams.append('q', params.q);
    if (params.category) searchParams.append('category', params.category);
    if (params.language) searchParams.append('language', params.language);
    if (params.section) searchParams.append('section', params.section);

    const query = searchParams.toString();
    const url = `${API_BASE_URL}/catalog/search${query ? `?${query}` : ''}`;
    const response = await fetch(url);
    if (!response.ok) {
      let errorMsg = `Catalogue search failed (${response.status})`;
      try {
        const data = await response.json();
        if (data.detail) errorMsg = data.detail;
      } catch {
        // ignore
      }
      throw new ApiError(response.status, errorMsg);
    }
    return response.json();
  },
};
