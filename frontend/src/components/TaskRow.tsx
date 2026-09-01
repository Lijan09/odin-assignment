import { STATUSES, STATUS_LABELS } from '../types'
import type { Status, Task } from '../types'
import type { AnalysisState, StatusState } from '../useTasks'
import { AnalysisPanel } from './AnalysisPanel'
import { PriorityBadge } from './PriorityBadge'

interface Props {
  task: Task
  analysis: AnalysisState
  statusState: StatusState
  onStatusChange: (status: Status) => void
  onAnalyse: () => void
}

function formatDate(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return date.toLocaleDateString('en-AU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function TaskRow({
  task,
  analysis,
  statusState,
  onStatusChange,
  onAnalyse,
}: Props) {
  const selectId = `status-${task.id}`
  const statusErrorId = `status-error-${task.id}`

  return (
    <li className="row">
      <div className="row__main">
        <h2 className="row__title">{task.title}</h2>
        <p className="row__description">{task.description}</p>
        <p className="row__meta">
          <PriorityBadge priority={task.priority} />
          <span className="row__created">
            <span className="sr-only">Created </span>
            {formatDate(task.createdAt)}
          </span>
        </p>
      </div>

      <div className="row__controls">
        <label className="row__label" htmlFor={selectId}>
          Status<span className="sr-only"> for {task.title}</span>
        </label>
        <select
          id={selectId}
          className="select"
          value={task.status}
          disabled={statusState.saving}
          aria-describedby={statusState.error ? statusErrorId : undefined}
          onChange={(event) => onStatusChange(event.target.value as Status)}
        >
          {STATUSES.map((status) => (
            <option key={status} value={status}>
              {STATUS_LABELS[status]}
            </option>
          ))}
        </select>

        {statusState.saving && <p className="row__saving">Saving…</p>}
        {statusState.error && (
          <p className="row__status-error" id={statusErrorId} role="alert">
            {statusState.error} Status reverted to “{STATUS_LABELS[task.status]}”.
          </p>
        )}

        <button
          type="button"
          className="button button--analyse"
          onClick={onAnalyse}
          disabled={analysis.loading}
        >
          {analysis.loading ? 'Analysing…' : 'Analyse with AI'}
          <span className="sr-only"> {task.title}</span>
        </button>
      </div>

      <div className="row__output" aria-live="polite">
        {analysis.loading && <p className="row__analysing">Analysing this task…</p>}

        {analysis.error && (
          <div className="analysis-error" role="alert">
            <p className="analysis-error__message">Analysis failed — {analysis.error}</p>
            <button type="button" className="button button--retry" onClick={onAnalyse}>
              Retry<span className="sr-only"> analysis for {task.title}</span>
            </button>
          </div>
        )}

        {analysis.result && !analysis.loading && (
          <AnalysisPanel result={analysis.result} />
        )}
      </div>
    </li>
  )
}
