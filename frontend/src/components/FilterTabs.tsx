import { STATUSES, STATUS_LABELS } from '../types'
import type { Status } from '../types'

interface Props {
  active: Status | null
  counts: Record<string, number>
  total: number
  onChange: (status: Status | null) => void
}

export function FilterTabs({ active, counts, total, onChange }: Props) {
  const tabs: Array<{ value: Status | null; label: string; count: number }> = [
    { value: null, label: 'All', count: total },
    ...STATUSES.map((status) => ({
      value: status as Status | null,
      label: STATUS_LABELS[status],
      count: counts[status] ?? 0,
    })),
  ]

  return (
    <div className="tabs" role="tablist" aria-label="Filter tasks by status">
      {tabs.map((tab) => {
        const selected = tab.value === active
        return (
          <button
            key={tab.label}
            type="button"
            role="tab"
            aria-selected={selected}
            className={`tab${selected ? ' tab--active' : ''}`}
            onClick={() => onChange(tab.value)}
          >
            {tab.label}
            <span className="tab__count"> {tab.count}</span>
          </button>
        )
      })}
    </div>
  )
}
