import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { AlignmentResult, AlignmentProgress, WordAlignment } from '@/types'
import * as alignApi from '@/api/alignment'

export const useAlignmentStore = defineStore('alignment', () => {
  const alignment = ref<AlignmentResult | null>(null)
  const progress = ref<AlignmentProgress>({ percent: 0, stage: 'idle' })
  const wordAlignments = ref<WordAlignment[]>([])
  const isAligning = ref(false)
  const engineAvailable = ref<boolean | null>(null)
  const engineMessage = ref('')

  let progressTimer: ReturnType<typeof setInterval> | null = null

  async function checkEngine() {
    try {
      const res = await alignApi.checkAlignmentEngine()
      engineAvailable.value = res.data.available
      engineMessage.value = res.data.message
    } catch {
      engineAvailable.value = null
      engineMessage.value = '无法检查对齐引擎状态'
    }
  }

  async function triggerAlignment(projectId: string) {
    isAligning.value = true
    progress.value = { percent: 0, stage: 'starting' }

    try {
      await alignApi.triggerAlignment(projectId)
      startProgressPolling(projectId)
    } catch (e: any) {
      isAligning.value = false
      const detail = e?.response?.data?.detail || '对齐请求失败'
      progress.value = { percent: -1, stage: 'error', error: detail }
      throw new Error(detail)
    }
  }

  function startProgressPolling(projectId: string) {
    if (progressTimer) clearInterval(progressTimer)
    progressTimer = setInterval(async () => {
      const res = await alignApi.getAlignmentProgress(projectId)
      progress.value = res.data
      if (res.data.percent >= 100 || res.data.percent < 0) {
        stopProgressPolling()
        isAligning.value = false
        if (res.data.percent >= 100) {
          await fetchAlignment(projectId)
        }
      }
    }, 1000)
  }

  function stopProgressPolling() {
    if (progressTimer) {
      clearInterval(progressTimer)
      progressTimer = null
    }
  }

  async function fetchAlignment(projectId: string) {
    try {
      const res = await alignApi.getAlignment(projectId)
      alignment.value = res.data
      wordAlignments.value = res.data.word_alignments || []
    } catch {
      alignment.value = null
      wordAlignments.value = []
    }
  }

  return {
    alignment, progress, wordAlignments, isAligning,
    engineAvailable, engineMessage,
    checkEngine, triggerAlignment, fetchAlignment, stopProgressPolling,
  }
})
