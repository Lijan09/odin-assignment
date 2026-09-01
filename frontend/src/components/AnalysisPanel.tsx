import type { AnalysisResult } from '../types'
import { PriorityBadge } from './PriorityBadge'

export function AnalysisPanel({ result }: { result: AnalysisResult }) {
  return (
    <div className="analysis">
      <p className="analysis__heading">AI analysis</p>
      <dl className="analysis__grid">
        <dt>Category</dt>
        <dd className="analysis__category">{result.category}</dd>

        <dt>Suggested priority</dt>
        <dd>
          <PriorityBadge priority={result.priority} suggested />
        </dd>

        <dt>Summary</dt>
        <dd>{result.summary}</dd>
      </dl>
      <div className="analysis__action">
        <p className="analysis__action-label">Recommended action</p>
        <p className="analysis__action-text">{result.recommendedAction}</p>
      </div>
    </div>
  )
}
