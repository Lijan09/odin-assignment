import type { AnalysisResult, Status, Task } from './types'

// Vite proxies /api to the backend in development, so the browser only ever
// talks to its own origin and CORS never comes into play.
const BASE = '/api'

/** The error envelope the backend returns for every failure. */
interface ApiErrorBody {
  error?: string
  message?: string
}

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...init,
    })
  } catch {
    // fetch only rejects on network-level failures.
    throw new ApiError('Could not reach the server.', 0)
  }

  if (!response.ok) {
    let message = `Request failed (${response.status}).`
    try {
      const body = (await response.json()) as ApiErrorBody
      if (body.message) message = body.message
    } catch {
      // A non-JSON error body is not worth failing over; keep the default.
    }
    throw new ApiError(message, response.status)
  }

  return (await response.json()) as T
}

export function fetchTasks(status: Status | null): Promise<Task[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : ''
  return request<Task[]>(`/tasks${query}`)
}

export function updateTaskStatus(id: number, status: Status): Promise<Task> {
  return request<Task>(`/tasks/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  })
}

export function analyseTask(id: number): Promise<AnalysisResult> {
  return request<AnalysisResult>(`/tasks/${id}/analyse`, { method: 'POST' })
}
