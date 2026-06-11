import api from './index'
import type { Project } from '@/types'

export function createProject(name: string, language = 'zh') {
  return api.post<Project>('/projects', { name, language })
}

export function listProjects() {
  return api.get<Project[]>('/projects')
}

export function getProject(id: string) {
  return api.get<Project>(`/projects/${id}`)
}

export function deleteProject(id: string) {
  return api.delete(`/projects/${id}`)
}

export function uploadFiles(projectId: string, audio: File, transcript: string) {
  const form = new FormData()
  form.append('audio', audio)
  form.append('transcript', transcript)
  return api.post(`/projects/${projectId}/upload`, form)
}
