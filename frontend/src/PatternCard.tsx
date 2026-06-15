import type { SaturationPattern } from './types'

interface PatternCardProps {
  pattern: SaturationPattern
  index: number
  total: number
}

const pad = (n: number) => String(n).padStart(2, '0')

export default function PatternCard({ pattern, index, total }: PatternCardProps) {
  return (
    <article className="pattern">
      <div className="pattern__header">
        <div className="pattern__index">
          {pad(index)} / {pad(total)}
        </div>
        <h2 className="pattern__title">{pattern.title}</h2>
        <p className="pattern__desc">{pattern.description}</p>
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
