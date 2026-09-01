import type { Priority } from '../types'

interface Props {
  priority: Priority
  /** Prefixed with "Suggested:" when it is the AI's opinion rather than the
   *  task's own stored priority, so the two are never confused. */
  suggested?: boolean
}

export function PriorityBadge({ priority, suggested = false }: Props) {
  return (
    <span className={`badge badge--${priority.toLowerCase()}`}>
      <span className="sr-only">{suggested ? 'Suggested priority: ' : 'Priority: '}</span>
      {suggested ? `Suggested: ${priority}` : priority}
    </span>
  )
}
