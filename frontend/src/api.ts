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

// Pull a 4-digit year out of the title only when one is actually present.
// Returns undefined rather than fabricating a year — real years arrive via
// img.year once retrieval captures structured attribution (#27 item 3).
function deriveYear(title?: string): number | undefined {
  const match = title?.match(/\b(20\d{2})\b/)
  return match ? Number(match[1]) : undefined
}

function toPatternImages(images: CorpusImage[]): PatternImage[] {
  return images.map(img => ({
    url: img.image_url,
    project: img.project ?? (img.title?.slice(0, 80) || 'Untitled project'),
    designer: img.designer ?? (img.source?.replace(/^www\./, '') || 'Unknown source'),
    year: img.year ?? deriveYear(img.title),
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
