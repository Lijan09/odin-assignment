export const STATUSES = ['NEW', 'IN_PROGRESS', 'COMPLETED'] as const
export type Status = (typeof STATUSES)[number]

export const PRIORITIES = ['LOW', 'MEDIUM', 'HIGH'] as const
export type Priority = (typeof PRIORITIES)[number]

export type Category =
  | 'DOCUMENT_REQUEST'
  | 'COMPLIANCE_CHECK'
  | 'CLIENT_FOLLOW_UP'
  | 'ESCALATION'

export interface Task {
  id: number
  title: string
  description: string
  priority: Priority
  status: Status
  createdAt: string
}

/** Matches the backend's AnalysisResult exactly, including its camelCase keys. */
export interface AnalysisResult {
  category: Category
  priority: Priority
  summary: string
  recommendedAction: string
}

export const STATUS_LABELS: Record<Status, string> = {
  NEW: 'New',
  IN_PROGRESS: 'In progress',
  COMPLETED: 'Completed',
}
