import type { SaturationPattern } from './types'

interface PatternCardProps {
  pattern: SaturationPattern
  index: number
  total: number
}

const pad = (n: number) => String(n).padStart(2, '0')

// Descriptions are exactly 3 sentences in a single string (synthesizer spec),
// with the final sentence always the data observation. Honor real paragraph
// breaks if any exist; otherwise lift that closing observation out so it can
// render as a distinct, muted data line set apart from the prose above it.
function splitDescription(description: string): { body: string[]; dataLine: string | null } {
  const paras = description.split(/\n{2,}/).map((p) => p.trim()).filter(Boolean)
  if (paras.length > 1) return { body: paras, dataLine: null }
  const sentences = description.split(/(?<=[.])\s+/).map((s) => s.trim()).filter(Boolean)
  if (sentences.length > 1) {
    return {
      body: [sentences.slice(0, -1).join(' ')],
      dataLine: sentences[sentences.length - 1],
    }
  }
  return { body: [description], dataLine: null }
}

export default function PatternCard({ pattern, index, total }: PatternCardProps) {
  const { body, dataLine } = splitDescription(pattern.description)
  return (
    <article className="pattern">
      <div className="pattern__header">
        <div className="pattern__index">
          {pad(index)} / {pad(total)}
        </div>
        <h2 className="pattern__title">{pattern.title}</h2>
        {body.map((para, i) => (
          <p key={i} className="pattern__desc">
            {para}
          </p>
        ))}
        {dataLine && <p className="pattern__data">{dataLine}</p>}
        {pattern.observation && <p className="pattern__obs">{pattern.observation}</p>}
      </div>
      {pattern.images.length === 0 ? (
        <p className="pattern__empty">
          No saturated examples in this corpus — open ground.
        </p>
      ) : (
        <div className="pattern__grid">
          {pattern.images.map((img, i) => {
            // Build the caption from whatever attribution we actually have —
            // omitted fields drop out cleanly instead of leaving stray " · ".
            const caption = [img.project, img.designer, img.year]
              .filter(Boolean)
              .join(' · ')
            return (
              <figure key={i} className="pattern__fig">
                <img
                  className="pattern__img"
                  src={img.url}
                  alt={img.project ?? 'Saturated example'}
                  loading="lazy"
                />
                {caption && <figcaption className="pattern__cap">{caption}</figcaption>}
              </figure>
            )
          })}
        </div>
      )}
    </article>
  )
}
