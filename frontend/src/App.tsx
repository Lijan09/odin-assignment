import { useState } from 'react'

import './App.css'
import { FilterTabs } from './components/FilterTabs'
import { TaskRow } from './components/TaskRow'
import type { Status } from './types'
import { useTasks } from './useTasks'

const IDLE_ANALYSIS = { loading: false, result: null, error: null }
const IDLE_STATUS = { saving: false, error: null }

function SkeletonRow() {
  return (
    <li className="row row--skeleton" aria-hidden="true">
      <div className="row__main">
        <span className="skeleton skeleton--title" />
        <span className="skeleton skeleton--line" />
        <span className="skeleton skeleton--line skeleton--short" />
        <span className="skeleton skeleton--badge" />
      </div>
      <div className="row__controls">
        <span className="skeleton skeleton--control" />
        <span className="skeleton skeleton--control" />
      </div>
    </li>
  )
}

export default function App() {
  const [filter, setFilter] = useState<Status | null>(null)
  const {
    tasks,
    counts,
    total,
    loading,
    loadError,
    analyses,
    statusStates,
    reload,
    changeStatus,
    analyse,
  } = useTasks(filter)

  return (
    <main className="page">
      <h1 className="page__title">Task Review</h1>

      <FilterTabs active={filter} counts={counts} total={total} onChange={setFilter} />

      <div className="list" aria-busy={loading}>
        {loading && (
          <>
            <p className="list__loading">Loading tasks…</p>
            <ul className="list__items">
              <SkeletonRow />
              <SkeletonRow />
              <SkeletonRow />
            </ul>
          </>
        )}

        {!loading && loadError && (
          <div className="list__error" role="alert">
            <p className="list__error-title">Couldn’t load tasks</p>
            <p className="list__error-text">{loadError}</p>
            <button type="button" className="button button--retry" onClick={() => void reload()}>
              Retry<span className="sr-only"> loading tasks</span>
            </button>
          </div>
        )}

        {!loading && !loadError && tasks.length === 0 && (
          <p className="list__empty">No tasks with this status</p>
        )}

        {!loading && !loadError && tasks.length > 0 && (
          <ul className="list__items">
            {tasks.map((task) => (
              <TaskRow
                key={task.id}
                task={task}
                analysis={analyses[task.id] ?? IDLE_ANALYSIS}
                statusState={statusStates[task.id] ?? IDLE_STATUS}
                onStatusChange={(status) => void changeStatus(task.id, status)}
                onAnalyse={() => void analyse(task.id)}
              />
            ))}
          </ul>
        )}
      </div>

      <p className="page__note">Statuses available: New, In progress, Completed.</p>
    </main>
  )
}
