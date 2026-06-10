<template>
  <div class="editor" v-loading="projectStore.loading">
    <header class="editor-header">
      <el-page-header @back="$router.push('/')">
        <template #content>
          <span>{{ projectStore.current?.name }}</span>
          <el-tag :type="statusType" style="margin-left: 12px">{{ statusLabel }}</el-tag>
        </template>
      </el-page-header>
      <div class="header-actions">
        <el-button @click="showUpload = true">上传文件</el-button>
        <el-button type="primary" @click="handleAlign" :loading="aligning"
          :disabled="!canAlign">开始对齐</el-button>
        <el-button @click="showCorrection = !showCorrection">时间校正</el-button>
        <el-button @click="showExport = true" :disabled="subtitleStore.lines.length === 0">导出</el-button>
      </div>
    </header>

    <div class="editor-body">
      <div class="left-panel">
        <WaveformPlayer
          v-if="projectStore.current?.audio_path"
          :audio-url="`/uploads/${projectStore.current.id}/${audioFilename}`"
          class="waveform-section"
        />
        <SubtitleTimeline class="timeline-section" />
        <AlignmentPreview class="preview-section" />
      </div>
      <div class="right-panel">
        <CorrectionPanel v-if="showCorrection" class="correction-section" />
        <SubtitleTable class="table-section" />
      </div>
    </div>

    <el-progress
      v-if="taskId && taskStatus !== 'completed'"
      :percentage="Math.round(taskProgress * 100)"
      :status="taskStatus === 'failed' ? 'exception' : undefined"
      style="position: fixed; bottom: 0; left: 0; right: 0; padding: 8px 20px; background: #fff; z-index: 100;"
    />

    <UploadDialog v-model="showUpload" :project-id="projectId" @done="onUploadDone" />
    <ExportDialog v-model="showExport" :project-id="projectId" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useProjectStore } from '../stores/project'
import { useSubtitleStore } from '../stores/subtitle'
import { useWebSocket } from '../composables/useWebSocket'
import { startAlignment } from '../api/alignment'
import WaveformPlayer from '../components/WaveformPlayer.vue'
import SubtitleTimeline from '../components/SubtitleTimeline.vue'
import SubtitleTable from '../components/SubtitleTable.vue'
import AlignmentPreview from '../components/AlignmentPreview.vue'
import CorrectionPanel from '../components/CorrectionPanel.vue'
import UploadDialog from '../components/UploadDialog.vue'
import ExportDialog from '../components/ExportDialog.vue'

const route = useRoute()
const projectStore = useProjectStore()
const subtitleStore = useSubtitleStore()

const projectId = computed(() => Number(route.params.id))
const showUpload = ref(false)
const showExport = ref(false)
const showCorrection = ref(false)
const aligning = ref(false)
const taskId = ref<string | null>(null)

const { progress: taskProgress, status: taskStatus } = useWebSocket(taskId)

const audioFilename = computed(() => {
  if (!projectStore.current?.audio_path) return ''
  return projectStore.current.audio_path.split('/').pop() || ''
})

const canAlign = computed(() => {
  const p = projectStore.current
  return p && p.audio_path && p.transcript_path && p.status !== 'aligning'
})

const statusType = computed(() => {
  const map: Record<string, string> = { created: 'info', aligning: 'warning', aligned: 'success', segmented: 'success', error: 'danger' }
  return map[projectStore.current?.status || ''] || 'info'
})

const statusLabel = computed(() => {
  const map: Record<string, string> = { created: '已创建', aligning: '对齐中', aligned: '已对齐', segmented: '已切分', error: '错误' }
  return map[projectStore.current?.status || ''] || ''
})

async function handleAlign() {
  aligning.value = true
  try {
    const { data } = await startAlignment(projectId.value)
    taskId.value = data.id
    projectStore.updateStatus('aligning')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '启动对齐失败')
  } finally {
    aligning.value = false
  }
}

watch(taskStatus, (s) => {
  if (s === 'completed') {
    projectStore.updateStatus('segmented')
    subtitleStore.load(projectId.value)
    ElMessage.success('对齐完成')
    taskId.value = null
  } else if (s === 'failed') {
    projectStore.updateStatus('error')
    ElMessage.error('对齐失败')
    taskId.value = null
  }
})

function onUploadDone() {
  projectStore.load(projectId.value)
}

onMounted(async () => {
  await projectStore.load(projectId.value)
  await subtitleStore.load(projectId.value)
})
</script>

<style scoped>
.editor {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid #ebeef5;
  flex-shrink: 0;
}
.header-actions {
  display: flex;
  gap: 8px;
}
.editor-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}
.left-panel {
  flex: 3;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-right: 1px solid #ebeef5;
}
.right-panel {
  flex: 2;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.waveform-section {
  height: 160px;
  flex-shrink: 0;
  border-bottom: 1px solid #ebeef5;
}
.timeline-section {
  height: 80px;
  flex-shrink: 0;
  border-bottom: 1px solid #ebeef5;
}
.preview-section {
  flex: 1;
  overflow: hidden;
}
.correction-section {
  flex-shrink: 0;
  border-bottom: 1px solid #ebeef5;
}
.table-section {
  flex: 1;
  overflow: auto;
}
</style>
