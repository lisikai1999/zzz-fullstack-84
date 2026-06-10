<template>
  <div class="project-list">
    <el-card class="header-card">
      <div class="header">
        <h1>字幕对齐工具</h1>
        <el-button type="primary" @click="showCreate = true">新建项目</el-button>
      </div>
    </el-card>

    <el-table :data="projects" v-loading="loading" stripe>
      <el-table-column prop="name" label="项目名称" />
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ new Date(row.created_at).toLocaleString() }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="$router.push(`/project/${row.id}`)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showCreate" title="新建项目" width="400px">
      <el-input v-model="newName" placeholder="输入项目名称" />
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Project } from '../types'
import { listProjects, createProject, deleteProject } from '../api/projects'

const router = useRouter()
const projects = ref<Project[]>([])
const loading = ref(false)
const showCreate = ref(false)
const newName = ref('')
const creating = ref(false)

async function loadProjects() {
  loading.value = true
  try {
    const { data } = await listProjects()
    projects.value = data
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!newName.value.trim()) return
  creating.value = true
  try {
    const { data } = await createProject(newName.value.trim())
    showCreate.value = false
    newName.value = ''
    router.push(`/project/${data.id}`)
  } finally {
    creating.value = false
  }
}

async function handleDelete(id: number) {
  await ElMessageBox.confirm('确定删除此项目？', '确认')
  await deleteProject(id)
  ElMessage.success('已删除')
  loadProjects()
}

function statusType(status: string) {
  const map: Record<string, string> = { created: 'info', aligning: 'warning', aligned: 'success', segmented: 'success', error: 'danger' }
  return map[status] || 'info'
}

function statusLabel(status: string) {
  const map: Record<string, string> = { created: '已创建', aligning: '对齐中', aligned: '已对齐', segmented: '已切分', error: '错误' }
  return map[status] || status
}

onMounted(loadProjects)
</script>

<style scoped>
.project-list {
  max-width: 1000px;
  margin: 40px auto;
  padding: 0 20px;
}
.header-card {
  margin-bottom: 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
h1 {
  margin: 0;
  font-size: 24px;
}
</style>
