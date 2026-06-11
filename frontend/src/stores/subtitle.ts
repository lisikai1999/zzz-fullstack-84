import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { SubtitleItem, CorrectionRequest } from '@/types'
import * as subApi from '@/api/subtitles'

export const useSubtitleStore = defineStore('subtitle', () => {
  const subtitles = ref<SubtitleItem[]>([])
  const loading = ref(false)

  async function fetchSubtitles(projectId: string) {
    const res = await subApi.getSubtitles(projectId)
    subtitles.value = res.data.subtitles
  }

  async function splitFromAlignment(projectId: string, maxChars = 20, pauseThreshold = 300) {
    loading.value = true
    try {
      const res = await subApi.splitSubtitles(projectId, maxChars, pauseThreshold)
      subtitles.value = res.data.subtitles
    } finally {
      loading.value = false
    }
  }

  async function saveSubtitles(projectId: string) {
    const res = await subApi.updateSubtitles(projectId, subtitles.value)
    subtitles.value = res.data.subtitles
  }

  async function applyCorrection(projectId: string, correction: CorrectionRequest) {
    loading.value = true
    try {
      const res = await subApi.correctSubtitles(projectId, correction)
      subtitles.value = res.data.subtitles
    } finally {
      loading.value = false
    }
  }

  function updateSubtitle(index: number, updates: Partial<SubtitleItem>) {
    if (index >= 0 && index < subtitles.value.length) {
      subtitles.value[index] = { ...subtitles.value[index], ...updates }
    }
  }

  async function exportSubs(projectId: string, format: 'srt' | 'vtt' | 'ass') {
    const res = await subApi.exportSubtitles(projectId, format)
    const blob = new Blob([res.data], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `subtitles.${format}`
    a.click()
    URL.revokeObjectURL(url)
  }

  return { subtitles, loading, fetchSubtitles, splitFromAlignment, saveSubtitles, applyCorrection, updateSubtitle, exportSubs }
})
