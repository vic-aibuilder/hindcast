import type { BriefInput } from './BriefForm'
import type { HindcastResult, PatternImage, SaturationPattern } from './types'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const SUB_SLICE_API: Record<BriefInput['subSlice'], string> = {
  'sneaker-streetwear': 'sneaker_streetwear',
  'contemporary-fashion': 'contemporary_fashion',
}

export interface QueryResponse {
  brief: string
  sub_slice: string
  cache_hit: boolean
  images: CorpusImage[]
  corpus_size: number
  patterns: ApiPattern[]
  retrieval_log: string[]
  source_breakdown: Record<string, number>
}

interface CorpusImage {
  image_url: string
  source_url?: string
  title?: string
  source?: string
  // Structured attribution — populated once retrieval captures it
  // (#27 item 3, Gary's half). Absent until then; we derive what we can.
  designer?: string
  year?: number
  project?: string
}

interface ApiPattern {
  title: string
  description: string
  dominant_terms?: string[]
  image_count?: number
  // Images that actually evidence this pattern — term-matched server-side
  // (#41). Same shape as the top-level `images` list. Absent until the
  // backend half lands; we fall back to an empty grid until then.
  evidence_images?: CorpusImage[]
}

// Derive a 4-digit year for an image without fabricating one (#33).
// Precedence:
//   1. the date in source_url's path (e.g. /2024/02/… → 2024) — the
//      publication year, the most consistent proxy we have;
//   2. a year mentioned in the title, as a fallback;
//   3. undefined — we omit the year rather than invent one.
// Years outside 2000..currentYear are rejected as noise (street numbers,
// collection codes, future-dated typos). Real structured years override
// this via img.year once retrieval captures attribution (#33 option b / #34).
function extractYear(text?: string, pattern: RegExp = /\b(20\d{2})\b/): number | undefined {
  const match = text?.match(pattern)
  if (!match) return undefined
  const year = Number(match[1])
  return year >= 2000 && year <= new Date().getFullYear() ? year : undefined
}

function deriveYear(title?: string, sourceUrl?: string): number | undefined {
  // Prefer a year in a URL path segment (/2024/…); fall back to the title.
  return extractYear(sourceUrl, /\/(20\d{2})(?=\/)/) ?? extractYear(title)
}

function toPatternImages(images: CorpusImage[]): PatternImage[] {
  return images.map(img => ({
    url: img.image_url,
    project: img.project ?? (img.title?.slice(0, 80) || 'Untitled project'),
    designer: img.designer ?? (img.source?.replace(/^www\./, '') || 'Unknown source'),
    year: img.year ?? deriveYear(img.title, img.source_url),
  }))
}

export function adaptQueryResponse(data: QueryResponse): HindcastResult {
  const patterns: SaturationPattern[] = (data.patterns ?? []).map((p) => ({
    title: p.title,
    description: p.description,
    // Term-matched images for this specific pattern (#41), not a positional
    // slice of the global corpus. Empty until the backend half lands.
    images: toPatternImages(p.evidence_images ?? []),
  }))

  const cacheNote = data.cache_hit ? 'cache hit' : 'live retrieval'
  const sources = Object.entries(data.source_breakdown ?? {})
    .map(([k, v]) => `${k.replace(/^www\./, '')} (${v})`)
    .join(', ')

  return {
    summary: sources
      ? `${patterns.length} patterns from a corpus of ${data.corpus_size} images (${cacheNote}). Sources: ${sources}.`
      : `${patterns.length} patterns from a corpus of ${data.corpus_size} images (${cacheNote}).`,
    patterns,
  }
}

export async function runQuery(input: BriefInput): Promise<QueryResponse> {
  const res = await fetch(`${API_URL}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      brief: input.brief,
      sub_slice: SUB_SLICE_API[input.subSlice],
    }),
  })

  if (!res.ok) {
    const detail = await res.text()
    throw new Error(detail || `Query failed (${res.status})`)
  }

  return res.json() as Promise<QueryResponse>
}
