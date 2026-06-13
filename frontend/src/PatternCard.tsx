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
          {pattern.images.map((img, i) => (
            <figure key={i} className="pattern__fig">
              <img className="pattern__img" src={img.url} alt={img.project} loading="lazy" />
              <figcaption className="pattern__cap">
                {img.project} · {img.designer}{img.year ? ` · ${img.year}` : ''}
              </figcaption>
            </figure>
          ))}
        </div>
      )}
    </article>
  )
}
