import { PRIORITIES, STATUSES, STATUS_LABELS } from '../types'
import type { Priority, Status, Task } from '../types'
import type { AnalysisState, FieldState } from '../useTasks'
import { AnalysisPanel } from './AnalysisPanel'
import { PriorityBadge } from './PriorityBadge'

interface Props {
  task: Task
  analysis: AnalysisState
  statusState: FieldState
  priorityState: FieldState
  onStatusChange: (status: Status) => void
  onPriorityChange: (priority: Priority) => void
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
  priorityState,
  onStatusChange,
  onPriorityChange,
  onAnalyse,
}: Props) {
  const selectId = `status-${task.id}`
  const statusErrorId = `status-error-${task.id}`
  const priorityId = `priority-${task.id}`
  const priorityErrorId = `priority-error-${task.id}`

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

        <label className="row__label" htmlFor={priorityId}>
          Priority<span className="sr-only"> for {task.title}</span>
        </label>
        <select
          id={priorityId}
          className="select"
          value={task.priority}
          disabled={priorityState.saving}
          aria-describedby={priorityState.error ? priorityErrorId : undefined}
          onChange={(event) => onPriorityChange(event.target.value as Priority)}
        >
          {PRIORITIES.map((priority) => (
            <option key={priority} value={priority}>
              {priority}
            </option>
          ))}
        </select>

        {priorityState.saving && <p className="row__saving">Saving…</p>}
        {priorityState.error && (
          <p className="row__status-error" id={priorityErrorId} role="alert">
            {priorityState.error} Priority reverted to “{task.priority}”.
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
