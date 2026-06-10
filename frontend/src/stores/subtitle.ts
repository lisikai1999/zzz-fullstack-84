import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { SubtitleLine } from '../types'
import { getSubtitles } from '../api/subtitles'

export const useSubtitleStore = defineStore('subtitle', () => {
  const lines = ref<SubtitleLine[]>([])
  const selectedId = ref<number | null>(null)
  const loading = ref(false)

  async function load(projectId: number) {
    loading.value = true
    try {
      const { data } = await getSubtitles(projectId)
      lines.value = data
    } finally {
      loading.value = false
    }
  }

  function setLines(newLines: SubtitleLine[]) {
    lines.value = newLines
  }

  function select(id: number | null) {
    selectedId.value = id
  }

  function updateLine(id: number, updates: Partial<SubtitleLine>) {
    const line = lines.value.find(l => l.id === id)
    if (line) {
      Object.assign(line, updates)
    }
  }

  return { lines, selectedId, loading, load, setLines, select, updateLine }
})
