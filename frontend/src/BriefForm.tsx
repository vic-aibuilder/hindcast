import { useState } from 'react'

export type SubSlice = 'sneaker-streetwear' | 'contemporary-fashion'

export interface BriefInput {
  subSlice: SubSlice
  brief: string
  keywords?: string
}

interface BriefFormProps {
  onSubmit: (input: BriefInput) => void
}

const SLICES: { value: SubSlice; label: string }[] = [
  { value: 'sneaker-streetwear', label: 'Sneaker / Streetwear' },
  { value: 'contemporary-fashion', label: 'Contemporary Fashion' },
]

export default function BriefForm({ onSubmit }: BriefFormProps) {
  const [subSlice, setSubSlice] = useState<SubSlice>('sneaker-streetwear')
  const [brief, setBrief] = useState('')
  const [keywords, setKeywords] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!brief.trim()) return
    onSubmit({ subSlice, brief: brief.trim(), keywords: keywords.trim() || undefined })
  }

  return (
    <form onSubmit={handleSubmit} className="form">
      <div className="field">
        <span className="field__lbl">Sub-Slice</span>
        <div className="pills" role="group" aria-label="Sub-slice">
          {SLICES.map(s => (
            <button
              key={s.value}
              type="button"
              className={'pill' + (subSlice === s.value ? ' pill--active' : '')}
              aria-pressed={subSlice === s.value}
              onClick={() => setSubSlice(s.value)}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <div className="city-row">
        <span className="city-row__lbl">City</span>
        <span className="city-row__val">New York City</span>
      </div>

      <div className="field">
        <label className="field__lbl" htmlFor="brief">Brief</label>
        <textarea
          id="brief"
          className="field__input"
          value={brief}
          onChange={e => setBrief(e.target.value)}
          rows={3}
          placeholder="Describe the space or brief…"
        />
      </div>

      <div className="field">
        <label className="field__lbl" htmlFor="keywords">
          Keywords <span className="field__opt">optional</span>
        </label>
        <input
          id="keywords"
          className="field__input"
          value={keywords}
          onChange={e => setKeywords(e.target.value)}
          placeholder="gallery, plinth, raw material…"
        />
      </div>

      <div className="submit-row">
        <button type="submit" className="btn" disabled={!brief.trim()}>
          Run Analysis
        </button>
        <span className="submit-note">30–60 sec. One brief, one deep saturation report.</span>
      </div>
    </form>
  )
}
