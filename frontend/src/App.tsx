import { useEffect, useRef, useState } from 'react'
import BriefForm, { type BriefInput, type SubSlice } from './BriefForm'
import AgentLog from './AgentLog'
import OutputLayout from './OutputLayout'
import type { HindcastResult } from './types'
import './App.css'

type AppState =
  | { status: 'idle' }
  | { status: 'loading'; input: BriefInput; logs: string[] }
  | { status: 'done'; input: BriefInput; logs: string[]; result: HindcastResult }

const SLICE_LABELS: Record<SubSlice, string> = {
  'sneaker-streetwear': 'Sneaker / Streetwear',
  'contemporary-fashion': 'Contemporary Fashion',
}

const MOCK_LOGS = [
  'Querying Tavily: retail spaces NYC 2025…',
  'Scanning HighSnobiety, Sole Collector, Sneaker News, SSENSE…',
  'Retrieving Are.na channel references…',
  'Self-assessment: corpus coverage sufficient, 3 gaps flagged…',
  'Running schema extractor across 24 images…',
  'Attributes extracted: material finish, display density, colorway range…',
  'Synthesizing saturation patterns…',
  'Done — 5 patterns identified',
]

const MOCK_RESULT: HindcastResult = {
  summary:
    'Five recurring patterns dominate the current sneaker/streetwear retail interior in NYC. The moves below have reached the point where they no longer read as choices.',
  patterns: [
    {
      title: 'Full-Height Dark Wood Paneling',
      description:
        'Walnut or dark oak floor-to-ceiling millwork, typically backlit or paired with recessed track. Appears across flagship and mid-tier equally. The premium register it once carried is gone.',
      observation:
        'The most universal move in the set — present regardless of budget or brand tier, which is precisely why it has stopped signalling anything.',
      images: [
        { url: 'https://picsum.photos/seed/a1/400/300', project: 'Nike House of Innovation', designer: 'Nike In-House', year: 2026 },
        { url: 'https://picsum.photos/seed/a2/400/300', project: 'Aimé Leon Dore Flagship', designer: 'ALD In-House', year: 2025 },
        { url: 'https://picsum.photos/seed/a3/400/300', project: 'New Balance Queens', designer: 'Virgile+Partners', year: 2025 },
        { url: 'https://picsum.photos/seed/a4/400/300', project: 'Jordan Brand The Bronx', designer: 'Nike In-House', year: 2026 },
        { url: 'https://picsum.photos/seed/a5/400/300', project: 'Fear of God Athletics', designer: 'Jerry Lorenzo Studio', year: 2026 },
        { url: 'https://picsum.photos/seed/a6/400/300', project: 'A-Cold-Wall Brooklyn', designer: 'Samuel Ross Studio', year: 2025 },
        { url: 'https://picsum.photos/seed/a7/400/300', project: 'Cactus Plant Flea Market', designer: 'CPFM In-House', year: 2025 },
        { url: 'https://picsum.photos/seed/a8/400/300', project: 'Union Pop-up Staten Island', designer: 'Union In-House', year: 2026 },
      ],
    },
    {
      title: 'Overhead Lightbox Grid',
      description:
        'Diffuse white lightbox panels arranged in a ceiling grid, often with exposed track filling the gaps. Reads as neutral but has become the default industrial-clean ceiling solution.',
      observation:
        'Appears in roughly two-thirds of the set, almost always paired with exposed track. Rarely the focal move — more often the unexamined default overhead.',
      images: [
        { url: 'https://picsum.photos/seed/b1/400/300', project: 'Adidas Brand Center 5th Ave', designer: 'Checkland Kindleysides', year: 2026 },
        { url: 'https://picsum.photos/seed/b2/400/300', project: 'On Running Brooklyn', designer: 'Studio Modijefsky', year: 2025 },
        { url: 'https://picsum.photos/seed/b3/400/300', project: 'Flight Club Bowery', designer: 'Flight Club In-House', year: 2025 },
        { url: 'https://picsum.photos/seed/b4/400/300', project: 'Saucony Queens', designer: 'Saucony In-House', year: 2026 },
        { url: 'https://picsum.photos/seed/b5/400/300', project: 'New Balance 999 The Bronx', designer: 'NB In-House', year: 2025 },
        { url: 'https://picsum.photos/seed/b6/400/300', project: 'Asics Staten Island', designer: 'Asics In-House', year: 2026 },
        { url: 'https://picsum.photos/seed/b7/400/300', project: 'Brooks Running Brooklyn', designer: 'Brooks In-House', year: 2025 },
        { url: 'https://picsum.photos/seed/b8/400/300', project: 'Hoka Queens', designer: 'Hoka In-House', year: 2026 },
      ],
    },
    {
      title: 'Stainless Steel Modular Fixture System',
      description:
        'Chrome rail and perforated steel shelving assembled from a modular grid system. Initially read as technical precision; now identifiable as the DTC fixture default.',
      observation:
        'Reads as technical precision on first encounter, as template by the third. The same system recurs across unrelated brands.',
      images: [
        { url: 'https://picsum.photos/seed/c1/400/300', project: 'GOAT Flagship', designer: 'GOAT In-House', year: 2026 },
        { url: 'https://picsum.photos/seed/c2/400/300', project: 'Concepts Brooklyn', designer: 'Concepts In-House', year: 2025 },
        { url: 'https://picsum.photos/seed/c3/400/300', project: 'Stadium Goods SoHo', designer: 'Stadium Goods In-House', year: 2026 },
        { url: 'https://picsum.photos/seed/c4/400/300', project: 'Round Two The Bronx', designer: 'Round Two In-House', year: 2025 },
        { url: 'https://picsum.photos/seed/c5/400/300', project: 'KLEKT Queens', designer: 'KLEKT In-House', year: 2026 },
        { url: 'https://picsum.photos/seed/c6/400/300', project: 'Sneaker Politics Staten Island', designer: 'SP In-House', year: 2025 },
        { url: 'https://picsum.photos/seed/c7/400/300', project: 'Trophy Room Brooklyn', designer: 'Trophy Room In-House', year: 2025 },
        { url: 'https://picsum.photos/seed/c8/400/300', project: 'Social Status Harlem', designer: 'Social Status In-House', year: 2026 },
      ],
    },
    {
      title: 'Salon Wall Display',
      description:
        'Individual pairs mounted sole-out in a continuous grid across a primary wall. Borrowed from archive and gallery display; now the dominant sneaker merchandising format in the borough.',
      observation:
        'The dominant merchandising format in the borough; mid-density mixed display is essentially absent from the set.',
      images: [
        { url: 'https://picsum.photos/seed/d1/400/300', project: 'Extra Butter LES', designer: 'Extra Butter In-House', year: 2025 },
        { url: 'https://picsum.photos/seed/d2/400/300', project: 'Bodega Brooklyn', designer: 'Bodega In-House', year: 2026 },
        { url: 'https://picsum.photos/seed/d3/400/300', project: 'Dover Street Market Manhattan', designer: 'DSM In-House', year: 2025 },
        { url: 'https://picsum.photos/seed/d4/400/300', project: 'Packer Shoes Queens', designer: 'Packer In-House', year: 2026 },
        { url: 'https://picsum.photos/seed/d5/400/300', project: 'Feature Pop-up The Bronx', designer: 'Feature In-House', year: 2025 },
        { url: 'https://picsum.photos/seed/d6/400/300', project: 'Sneaker District Staten Island', designer: 'SD In-House', year: 2026 },
        { url: 'https://picsum.photos/seed/d7/400/300', project: 'Atmos Brooklyn', designer: 'Atmos In-House', year: 2025 },
        { url: 'https://picsum.photos/seed/d8/400/300', project: 'Bait Queens', designer: 'Bait In-House', year: 2025 },
      ],
    },
    {
      title: 'Polished Concrete Floor with Painted Court Insert',
      description:
        'Raw or sealed concrete base with a painted sport-court zone — half-court, lane, or key — laid into the floor. The sport reference has moved from statement to expected.',
      observation:
        'The sport reference has shifted from statement to expectation — present even where the brand has no athletic lineage.',
      images: [
        { url: 'https://picsum.photos/seed/e1/400/300', project: 'Nike SoHo', designer: 'Nike In-House', year: 2026 },
        { url: 'https://picsum.photos/seed/e2/400/300', project: 'Foot Locker Power Store The Bronx', designer: 'Checkland Kindleysides', year: 2025 },
        { url: 'https://picsum.photos/seed/e3/400/300', project: 'Puma Brooklyn', designer: 'Puma In-House', year: 2025 },
        { url: 'https://picsum.photos/seed/e4/400/300', project: 'Reebok Queens', designer: 'Reebok In-House', year: 2026 },
        { url: 'https://picsum.photos/seed/e5/400/300', project: 'Converse Staten Island', designer: 'Converse In-House', year: 2025 },
        { url: 'https://picsum.photos/seed/e6/400/300', project: 'Vans Brooklyn', designer: 'Vans In-House', year: 2025 },
        { url: 'https://picsum.photos/seed/e7/400/300', project: 'Timberland The Bronx', designer: 'Timberland In-House', year: 2026 },
        { url: 'https://picsum.photos/seed/e8/400/300', project: 'Merrell Queens', designer: 'Merrell In-House', year: 2025 },
      ],
    },
  ],
}

export default function App() {
  const [state, setState] = useState<AppState>({ status: 'idle' })
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [])

  function handleSubmit(input: BriefInput) {
    if (intervalRef.current) clearInterval(intervalRef.current)
    setState({ status: 'loading', input, logs: [] })

    let i = 0
    intervalRef.current = setInterval(() => {
      i++
      const next = MOCK_LOGS.slice(0, i)
      if (i >= MOCK_LOGS.length) {
        clearInterval(intervalRef.current!)
        setState({ status: 'done', input, logs: next, result: MOCK_RESULT })
      } else {
        setState({ status: 'loading', input, logs: next })
      }
    }, 600)
  }

  function reset() {
    if (intervalRef.current) clearInterval(intervalRef.current)
    setState({ status: 'idle' })
  }

  return (
    <div className="page">
      <nav className="nav">
        <span className="nav__wordmark">Hindcast</span>
        <span className="nav__right">Snarkitecture · Anti-Trend Engine</span>
      </nav>

      {state.status === 'idle' && (
        <section className="screen screen--input">
          <span className="tag">Vertical: Brand &amp; Retail</span>
          <h1 className="headline">
            What is everyone
            <br />
            else doing?
          </h1>
          <p className="sub">
            Submit a brief. Hindcast maps what's already everywhere in that
            context — the moves everyone is making, and the open ground where
            contrast still lives.
          </p>
          <BriefForm onSubmit={handleSubmit} />
        </section>
      )}

      {state.status === 'loading' && (
        <section className="screen screen--loading">
          <p className="load-title">Reading the landscape…</p>
          <AgentLog
            messages={state.logs}
            active
            label={`Retrieval Agent — ${SLICE_LABELS[state.input.subSlice]} · NYC`}
          />
        </section>
      )}

      {state.status === 'done' && (
        <section className="screen screen--results">
          <header className="results-hdr">
            <div>
              <div className="results-hdr__vertical">
                Brand &amp; Retail — {SLICE_LABELS[state.input.subSlice]}
              </div>
              <div className="results-hdr__title">New York City</div>
            </div>
            <button type="button" className="results-hdr__back" onClick={reset}>
              ← New Brief
            </button>
          </header>
          <hr className="rule" />
          <div className="results-hdr__meta">
            <strong>{state.result.patterns.length} patterns</strong> identified
            · NYC · past 18 months
          </div>
          <hr className="rule" />
          <OutputLayout result={state.result} />
        </section>
      )}
    </div>
  )
}
