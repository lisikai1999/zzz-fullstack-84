import api from './index'
import type { AlignmentResult, AlignmentProgress, WaveformData } from '@/types'

export function checkAlignmentEngine() {
  return api.get<{ available: boolean; message: string }>('/projects/alignment/status')
}

export function triggerAlignment(projectId: string) {
  return api.post<{ id: string; status: string; message: string }>(
    `/projects/${projectId}/align`
  )
}

export function getAlignment(projectId: string) {
  return api.get<AlignmentResult>(`/projects/${projectId}/alignment`)
}

export function getAlignmentProgress(projectId: string) {
  return api.get<AlignmentProgress>(`/projects/${projectId}/alignment/progress`)
}

export function getWaveform(projectId: string) {
  return api.get<WaveformData>(`/projects/${projectId}/waveform`)
}
