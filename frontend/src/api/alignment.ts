import client from './client'
import type { AlignmentTask } from '../types'

export function startAlignment(projectId: number) {
  return client.post<AlignmentTask>(`/api/projects/${projectId}/align`)
}

export function getTask(taskId: string) {
  return client.get<AlignmentTask>(`/api/tasks/${taskId}`)
}
