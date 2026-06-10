import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Project } from '../types'
import { getProject } from '../api/projects'

export const useProjectStore = defineStore('project', () => {
  const current = ref<Project | null>(null)
  const loading = ref(false)

  async function load(id: number) {
    loading.value = true
    try {
      const { data } = await getProject(id)
      current.value = data
    } finally {
      loading.value = false
    }
  }

  function updateStatus(status: string) {
    if (current.value) {
      current.value.status = status
    }
  }

  return { current, loading, load, updateStatus }
})
