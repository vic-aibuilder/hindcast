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
}

interface ApiPattern {
  title: string
  description: string
  dominant_terms?: string[]
  image_count?: number
}

function toPatternImages(images: CorpusImage[], offset: number, count: number): PatternImage[] {
  return images.slice(offset, offset + count).map(img => ({
    url: img.image_url,
    project: img.title?.slice(0, 80) || 'Untitled project',
    designer: img.source?.replace(/^www\./, '') || 'Unknown source',
    year: 2025,
  }))
}

export function adaptQueryResponse(data: QueryResponse): HindcastResult {
  const corpus = data.images ?? []
  const patterns: SaturationPattern[] = (data.patterns ?? []).map((p, i) => {
    const perPattern = Math.min(8, Math.max(4, p.image_count ?? 8))
    const offset = i * 8
    return {
      title: p.title,
      description: p.description,
      images: toPatternImages(corpus, offset, perPattern),
    }
  })

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
