export const SECTIONS = ['featured', 'series', 'minisodes', 'songs'] as const;

export const CATEGORIES = [
  'adventure',
  'folk',
  'friendship',
  'india',
  'language',
  'learning',
  'maths',
  'music',
  'nature',
  'reading',
  'science',
  'singalong',
  'stories',
  'travel',
  'values',
] as const;

export const LANGUAGES = ['en', 'hi'] as const;

export type SectionType = typeof SECTIONS[number];
export type CategoryType = typeof CATEGORIES[number];
export type LanguageType = typeof LANGUAGES[number];

export interface ArtworkSpec {
  aspect: string;
  width: number;
  height: number;
  ratio: number;
  maxKb: number;
}

export const ARTWORK_SPECS: Record<'poster' | 'banner' | 'thumbnail', ArtworkSpec> = {
  poster: {
    aspect: '2:3',
    width: 600,
    height: 900,
    ratio: 600 / 900,
    maxKb: 200,
  },
  banner: {
    aspect: '16:9',
    width: 1280,
    height: 720,
    ratio: 1280 / 720,
    maxKb: 200,
  },
  thumbnail: {
    aspect: '16:9',
    width: 640,
    height: 360,
    ratio: 640 / 360,
    maxKb: 200,
  },
};
