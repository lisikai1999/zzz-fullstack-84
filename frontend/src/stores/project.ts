import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Project } from '@/types'
import * as projectApi from '@/api/projects'

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const loading = ref(false)

  async function fetchProjects() {
    loading.value = true
    try {
      const res = await projectApi.listProjects()
      projects.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchProject(id: string) {
    const res = await projectApi.getProject(id)
    currentProject.value = res.data
  }

  async function createProject(name: string, language: string) {
    const res = await projectApi.createProject(name, language)
    projects.value.unshift(res.data)
    return res.data
  }

  async function removeProject(id: string) {
    await projectApi.deleteProject(id)
    projects.value = projects.value.filter((p) => p.id !== id)
  }

  async function upload(projectId: string, audio: File, transcript: string) {
    await projectApi.uploadFiles(projectId, audio, transcript)
    await fetchProject(projectId)
  }

  return { projects, currentProject, loading, fetchProjects, fetchProject, createProject, removeProject, upload }
})
