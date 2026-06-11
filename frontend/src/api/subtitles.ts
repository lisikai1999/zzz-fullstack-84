import api from './index'
import type { SubtitleItem, CorrectionRequest } from '@/types'

export function splitSubtitles(projectId: string, maxChars = 20, pauseThresholdMs = 300) {
  return api.post<{ subtitles: SubtitleItem[] }>(`/projects/${projectId}/split`, {
    max_chars: maxChars,
    pause_threshold_ms: pauseThresholdMs,
  })
}

export function getSubtitles(projectId: string) {
  return api.get<{ subtitles: SubtitleItem[] }>(`/projects/${projectId}/subtitles`)
}

export function updateSubtitles(projectId: string, subtitles: SubtitleItem[]) {
  return api.put<{ subtitles: SubtitleItem[] }>(`/projects/${projectId}/subtitles`, {
    subtitles,
  })
}

export function correctSubtitles(projectId: string, correction: CorrectionRequest) {
  return api.post<{ subtitles: SubtitleItem[] }>(`/projects/${projectId}/correct`, correction)
}

export function exportSubtitles(projectId: string, format: 'srt' | 'vtt' | 'ass') {
  return api.get(`/projects/${projectId}/export`, {
    params: { format },
    responseType: 'blob',
  })
}
