export interface PatternImage {
  url: string
  project: string
  designer: string
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
