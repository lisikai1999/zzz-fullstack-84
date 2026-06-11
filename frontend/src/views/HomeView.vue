<template>
  <div class="home-view">
    <div class="header">
      <h2>我的项目</h2>
      <el-button type="primary" @click="showCreate = true">新建项目</el-button>
    </div>

    <el-row :gutter="20" v-loading="store.loading">
      <el-col :span="8" v-for="project in store.projects" :key="project.id">
        <el-card class="project-card" shadow="hover" @click="goToProject(project.id)">
          <template #header>
            <div class="card-header">
              <span>{{ project.name }}</span>
              <el-tag size="small" :type="statusType(project.status)">
                {{ statusText(project.status) }}
              </el-tag>
            </div>
          </template>
          <div class="card-body">
            <p>语言：{{ project.language === 'zh' ? '中文' : '英文' }}</p>
            <p>创建时间：{{ new Date(project.created_at).toLocaleString() }}</p>
          </div>
          <div class="card-actions" @click.stop>
            <el-button type="danger" size="small" text @click="handleDelete(project.id)">
              删除
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="!store.loading && store.projects.length === 0" description="暂无项目" />

    <el-dialog v-model="showCreate" title="新建项目" width="400px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="项目名称">
          <el-input v-model="form.name" placeholder="输入项目名称" />
        </el-form-item>
        <el-form-item label="语言">
          <el-select v-model="form.language">
            <el-option label="中文" value="zh" />
            <el-option label="英文" value="en" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useProjectStore } from '@/stores/project'

const store = useProjectStore()
const router = useRouter()
const showCreate = ref(false)
const form = ref({ name: '', language: 'zh' })

onMounted(() => { store.fetchProjects() })

function goToProject(id: string) {
  router.push(`/project/${id}`)
}

async function handleCreate() {
  if (!form.value.name.trim()) {
    ElMessage.warning('请输入项目名称')
    return
  }
  const project = await store.createProject(form.value.name, form.value.language)
  showCreate.value = false
  form.value = { name: '', language: 'zh' }
  router.push(`/project/${project.id}`)
}

async function handleDelete(id: string) {
  await ElMessageBox.confirm('确定删除该项目？', '提示', { type: 'warning' })
  await store.removeProject(id)
  ElMessage.success('已删除')
}

function statusType(status: string) {
  const map: Record<string, string> = {
    created: 'info', uploaded: '', aligning: 'warning', aligned: 'success', split: 'success',
  }
  return map[status] || 'info'
}

function statusText(status: string) {
  const map: Record<string, string> = {
    created: '已创建', uploaded: '已上传', aligning: '对齐中', aligned: '已对齐', split: '已切分',
  }
  return map[status] || status
}
</script>

<style scoped>
.home-view { max-width: 1200px; margin: 0 auto; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.project-card { cursor: pointer; margin-bottom: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-body p { margin: 4px 0; color: #666; font-size: 14px; }
.card-actions { margin-top: 10px; text-align: right; }
</style>
