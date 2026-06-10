import client from './client'
import type { SubtitleLine } from '../types'

export function getSubtitles(projectId: number) {
  return client.get<SubtitleLine[]>(`/api/projects/${projectId}/subtitles`)
}

export function updateSubtitle(projectId: number, lineId: number, data: { text?: string; start_time?: number; end_time?: number }) {
  return client.put<SubtitleLine>(`/api/projects/${projectId}/subtitles/${lineId}`, data)
}

export function resegment(projectId: number, params: { max_chars: number; min_pause: number }) {
  return client.post<SubtitleLine[]>(`/api/projects/${projectId}/subtitles/segment`, params)
}

export function shiftSubtitles(projectId: number, offsetMs: number) {
  return client.post<SubtitleLine[]>(`/api/projects/${projectId}/correct/shift`, { offset_ms: offsetMs })
}

export function scaleSubtitles(projectId: number, factor: number, anchorTime: number = 0) {
  return client.post<SubtitleLine[]>(`/api/projects/${projectId}/correct/scale`, { factor, anchor_time: anchorTime })
}

export function propagateAdjustment(projectId: number, lineId: number, newStart: number, newEnd: number) {
  return client.post<SubtitleLine[]>(`/api/projects/${projectId}/correct/propagate`, { line_id: lineId, new_start: newStart, new_end: newEnd })
}

export function exportSubtitles(projectId: number, format: 'srt' | 'ass') {
  return client.get(`/api/projects/${projectId}/export`, { params: { format }, responseType: 'blob' })
}
