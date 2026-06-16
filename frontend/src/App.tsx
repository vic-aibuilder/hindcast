import { useState } from 'react'
import BriefForm, { type BriefInput, type SubSlice } from './BriefForm'
import AgentLog from './AgentLog'
import OutputLayout from './OutputLayout'
import type { HindcastResult } from './types'
import { adaptQueryResponse, runQuery } from './api'
import './App.css'

type AppState =
  | { status: 'idle' }
  | { status: 'loading'; input: BriefInput }
  | { status: 'done'; input: BriefInput; logs: string[]; result: HindcastResult }
  | { status: 'error'; input: BriefInput; message: string }

const SLICE_LABELS: Record<SubSlice, string> = {
  'sneaker-streetwear': 'Sneaker / Streetwear',
  'contemporary-fashion': 'Contemporary Fashion',
}

export default function App() {
  const [state, setState] = useState<AppState>({ status: 'idle' })

  async function handleSubmit(input: BriefInput) {
    setState({ status: 'loading', input })

    try {
      const data = await runQuery(input)
      setState({
        status: 'done',
        input,
        logs: data.retrieval_log,
        result: adaptQueryResponse(data),
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Pipeline query failed'
      setState({ status: 'error', input, message })
    }
  }

  function reset() {
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
          <p className="sub" style={{ marginBottom: '1.5rem' }}>
            Running live pipeline — retrieval, extraction, synthesis.
          </p>
          <AgentLog
            messages={[
              'Connecting to Hindcast API…',
              `Sub-slice: ${SLICE_LABELS[state.input.subSlice]}`,
              'Searching scoped publications via Tavily…',
            ]}
            active
            label={`Pipeline — ${SLICE_LABELS[state.input.subSlice]} · NYC`}
          />
        </section>
      )}

      {state.status === 'error' && (
        <section className="screen screen--input">
          <p className="load-title">Pipeline error</p>
          <p className="sub">{state.message}</p>
          <button type="button" className="btn" onClick={reset}>
            ← Try again
          </button>
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
            · NYC · 2025–present
          </div>
          <hr className="rule" />
          <OutputLayout result={state.result} />
        </section>
      )}
    </div>
  )
}
