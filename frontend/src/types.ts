export interface PatternImage {
  url: string
  // Real attribution from retrieval (#33b/#48). Each is optional — omitted
  // when the backend couldn't confidently extract it (no derived fallback).
  project?: string
  designer?: string
  year?: number
}

export interface SaturationPattern {
  title: string
  description: string
  observation?: string
  images: PatternImage[]
}

export interface HindcastResult {
  summary: string
  patterns: SaturationPattern[]
}
