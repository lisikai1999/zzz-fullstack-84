import client from './client'
import type { Project } from '../types'

export function listProjects() {
  return client.get<Project[]>('/api/projects')
}

export function createProject(name: string) {
  return client.post<Project>('/api/projects', { name })
}

export function getProject(id: number) {
  return client.get<Project>(`/api/projects/${id}`)
}

export function deleteProject(id: number) {
  return client.delete(`/api/projects/${id}`)
}

export function uploadAudio(projectId: number, file: File) {
  const form = new FormData()
  form.append('file', file)
  return client.post(`/api/projects/${projectId}/upload/audio`, form)
}

export function uploadTranscript(projectId: number, file: File) {
  const form = new FormData()
  form.append('file', file)
  return client.post(`/api/projects/${projectId}/upload/transcript`, form)
}
