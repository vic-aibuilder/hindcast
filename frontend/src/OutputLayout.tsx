import type { HindcastResult } from './types'
import PatternCard from './PatternCard'

interface OutputLayoutProps {
  result: HindcastResult
}

export default function OutputLayout({ result }: OutputLayoutProps) {
  return (
    <div className="output">
      <p className="output__summary">{result.summary}</p>
      <div className="output__patterns">
        {result.patterns.map((pattern, i) => (
          <PatternCard
            key={i}
            pattern={pattern}
            index={i + 1}
            total={result.patterns.length}
          />
        ))}
      </div>
    </div>
  )
}
