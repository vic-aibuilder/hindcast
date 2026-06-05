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
      <div className="pattern__index">
        {pad(index)} / {pad(total)}
      </div>
      <h2 className="pattern__title">{pattern.title}</h2>
      <p className="pattern__desc">{pattern.description}</p>
      {pattern.observation && <p className="pattern__obs">{pattern.observation}</p>}
      <div className="pattern__grid">
        {pattern.images.map((img, i) => (
          <figure key={i} className="pattern__fig">
            <img className="pattern__img" src={img.url} alt={img.project} loading="lazy" />
            <figcaption className="pattern__cap">
              <span className="pattern__name">{img.project}</span>
              <span className="pattern__meta">
                {img.designer} · {img.year}
              </span>
            </figcaption>
          </figure>
        ))}
      </div>
    </article>
  )
}
