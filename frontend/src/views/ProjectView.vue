<template>
  <div class="project-view" v-loading="!project">
    <div v-if="project" class="workspace">
      <!-- Header -->
      <div class="workspace-header">
        <el-page-header @back="$router.push('/')">
          <template #content>
            <span>{{ project.name }}</span>
            <el-tag :type="statusType" size="small" style="margin-left: 12px">
              {{ statusText }}
            </el-tag>
          </template>
        </el-page-header>
      </div>

      <!-- Waveform + Regions -->
      <div class="waveform-section">
        <div ref="waveformRef" class="waveform-container"></div>
        <div class="playback-controls">
          <el-button-group>
            <el-button @click="player.toggle()">
              {{ player.isPlaying.value ? '⏸ 暂停' : '▶ 播放' }}
            </el-button>
            <el-button @click="player.seekTo(0)">⏮ 重置</el-button>
          </el-button-group>
          <div class="zoom-control">
            <span class="ctrl-label">缩放</span>
            <el-slider
              v-model="zoomLevel"
              :min="20"
              :max="500"
              :step="10"
              style="width: 160px"
              @input="player.zoom(zoomLevel)"
            />
          </div>
          <div class="speed-control">
            <span class="ctrl-label">速度</span>
            <el-select v-model="playbackRate" size="small" style="width: 75px" @change="player.setPlaybackRate(playbackRate)">
              <el-option :value="0.5" label="0.5x" />
              <el-option :value="0.75" label="0.75x" />
              <el-option :value="1" label="1x" />
              <el-option :value="1.25" label="1.25x" />
              <el-option :value="1.5" label="1.5x" />
              <el-option :value="2" label="2x" />
            </el-select>
          </div>
          <span class="time-display">
            {{ formatTime(player.currentTime.value) }} / {{ formatTime(player.duration.value) }}
          </span>
          <span v-if="saving" class="save-status saving">保存中...</span>
          <span v-else-if="dirty" class="save-status dirty">未保存</span>
        </div>
      </div>

      <!-- Tab panels -->
      <el-tabs v-model="activeTab" class="workspace-tabs">
        <!-- Upload & Align -->
        <el-tab-pane label="上传对齐" name="upload">
          <UploadPanel :project-id="project.id" @uploaded="onUploaded" />
          <div v-if="project.status !== 'created'" class="align-section">
            <el-alert
              v-if="alignStore.engineAvailable === false"
              type="error"
              :closable="false"
              show-icon
              style="margin-bottom: 12px"
            >
              <template #title>对齐引擎未安装</template>
              {{ alignStore.engineMessage }}
            </el-alert>
            <el-button
              type="primary"
              :loading="alignStore.isAligning"
              @click="handleAlign"
              :disabled="alignStore.isAligning || alignStore.engineAvailable === false"
            >
              {{ alignStore.isAligning ? '对齐中...' : '开始对齐' }}
            </el-button>
            <el-progress
              v-if="alignStore.isAligning || alignStore.progress.percent > 0"
              :percentage="Math.max(0, alignStore.progress.percent)"
              :status="alignStore.progress.percent < 0 ? 'exception' : alignStore.progress.percent >= 100 ? 'success' : undefined"
              style="margin-top: 12px"
            />
            <div v-if="alignStore.isAligning" class="stage-text">
              {{ stageText(alignStore.progress.stage) }}
            </div>
            <el-alert
              v-if="alignStore.progress.percent < 0 && alignStore.progress.error"
              type="error"
              :closable="false"
              style="margin-top: 12px"
            >
              {{ alignStore.progress.error }}
            </el-alert>
            <div v-if="alignStore.alignment?.status === 'completed'" class="align-done">
              <el-button type="success" @click="handleSplit">
                自动切分字幕
              </el-button>
            </div>
          </div>
        </el-tab-pane>

        <!-- Subtitle Editor -->
        <el-tab-pane label="字幕编辑" name="editor">
          <div class="editor-toolbar">
            <el-button size="small" type="primary" @click="handleSplit">自动切分</el-button>
            <el-button size="small" @click="handleSave">保存</el-button>
            <el-divider direction="vertical" />
            <el-button-group>
              <el-button size="small" @click="handleExport('srt')">SRT</el-button>
              <el-button size="small" @click="handleExport('vtt')">VTT</el-button>
              <el-button size="small" @click="handleExport('ass')">ASS</el-button>
            </el-button-group>
          </div>
          <SubtitleEditor
            :subtitles="subStore.subtitles"
            :current-index="currentSubtitleIndex"
            @seek="player.seekTo($event)"
            @update="onSubtitleUpdate"
            @cascade="onCascadeAdjust"
          />
        </el-tab-pane>

        <!-- Preview -->
        <el-tab-pane label="对齐预览" name="preview">
          <AlignmentPreview
            :word-alignments="alignStore.wordAlignments"
            :current-word-index="currentWordIndex"
          />
        </el-tab-pane>

        <!-- Correction -->
        <el-tab-pane label="时间校正" name="correction">
          <CorrectionPanel :project-id="project.id" @corrected="onCorrected" />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useDebounceFn } from '@vueuse/core'
import { ElMessage } from 'element-plus'
import { useProjectStore } from '@/stores/project'
import { useAlignmentStore } from '@/stores/alignment'
import { useSubtitleStore } from '@/stores/subtitle'
import { useAudioPlayer } from '@/composables/useAudioPlayer'
import { useSubtitleSync } from '@/composables/useSubtitleSync'
import UploadPanel from '@/components/alignment/UploadPanel.vue'
import SubtitleEditor from '@/components/editor/SubtitleEditor.vue'
import AlignmentPreview from '@/components/editor/AlignmentPreview.vue'
import CorrectionPanel from '@/components/correction/CorrectionPanel.vue'
import type { SubtitleItem } from '@/types'

const route = useRoute()
const projectStore = useProjectStore()
const alignStore = useAlignmentStore()
const subStore = useSubtitleStore()

const waveformRef = ref<HTMLElement | null>(null)
const player = useAudioPlayer(waveformRef)
const activeTab = ref('upload')
const zoomLevel = ref(50)
const playbackRate = ref(1)

const project = computed(() => projectStore.currentProject)

const saving = ref(false)
const dirty = ref(false)

const debouncedSave = useDebounceFn(async () => {
  if (!project.value || !dirty.value) return
  saving.value = true
  try {
    await subStore.saveSubtitles(project.value.id)
    dirty.value = false
  } catch (e: any) {
    ElMessage.error('自动保存失败')
  } finally {
    saving.value = false
  }
}, 800)

function markDirtyAndSave() {
  dirty.value = true
  debouncedSave()
}

const { currentSubtitleIndex, currentWordIndex } = useSubtitleSync(
  player.currentTime,
  computed(() => subStore.subtitles),
  computed(() => alignStore.wordAlignments)
)

// Highlight active region on waveform during playback
watch(currentSubtitleIndex, (idx) => {
  player.highlightRegion(idx)
})

// Re-render regions whenever subtitles change
watch(() => subStore.subtitles, (subs) => {
  if (subs.length > 0) {
    player.renderSubtitleRegions(subs)
  }
}, { deep: true })

// Handle region drag/resize → update subtitle store + cascade + auto-save
player.onRegionUpdate.value = (event) => {
  const sub = subStore.subtitles[event.subtitleIndex]
  if (!sub) return

  subStore.updateSubtitle(event.subtitleIndex, {
    start_time: Math.max(0, parseFloat(event.start.toFixed(3))),
    end_time: parseFloat(event.end.toFixed(3)),
  })

  cascadeFromIndex(event.subtitleIndex)
  markDirtyAndSave()
}

function cascadeFromIndex(idx: number) {
  const subs = subStore.subtitles
  // Forward cascade
  for (let i = idx + 1; i < subs.length; i++) {
    if (subs[i].start_time < subs[i - 1].end_time) {
      const dur = subs[i].end_time - subs[i].start_time
      subStore.updateSubtitle(i, {
        start_time: subs[i - 1].end_time,
        end_time: Math.max(subs[i - 1].end_time + 0.5, subs[i - 1].end_time + dur),
      })
    } else {
      break
    }
  }
  // Backward cascade
  for (let i = idx - 1; i >= 0; i--) {
    if (subs[i].end_time > subs[i + 1].start_time) {
      const dur = subs[i].end_time - subs[i].start_time
      subStore.updateSubtitle(i, {
        end_time: subs[i + 1].start_time,
        start_time: Math.max(0, subs[i + 1].start_time - dur),
      })
    } else {
      break
    }
  }
}

const statusType = computed(() => {
  const map: Record<string, string> = {
    created: 'info', uploaded: '', aligning: 'warning', aligned: 'success', split: 'success',
  }
  return map[project.value?.status || ''] || 'info'
})

const statusText = computed(() => {
  const map: Record<string, string> = {
    created: '已创建', uploaded: '已上传', aligning: '对齐中', aligned: '已对齐', split: '已切分',
  }
  return map[project.value?.status || ''] || ''
})

onMounted(async () => {
  const id = route.params.id as string
  await projectStore.fetchProject(id)
  await alignStore.checkEngine()
  if (project.value?.audio_path) {
    player.init(`/uploads/${id}/audio_16k.wav`)
    await alignStore.fetchAlignment(id)
    await subStore.fetchSubtitles(id)
    if (subStore.subtitles.length > 0) {
      activeTab.value = 'editor'
    }
  }
})

function onUploaded() {
  const id = route.params.id as string
  projectStore.fetchProject(id)
  player.init(`/uploads/${id}/audio_16k.wav`)
}

async function handleAlign() {
  try {
    await alignStore.triggerAlignment(project.value!.id)
  } catch (e: any) {
    ElMessage.error(e.message || '对齐失败')
  }
}

// Watch for alignment completion to auto-switch tab
watch(() => alignStore.alignment?.status, (status) => {
  if (status === 'completed') {
    ElMessage.success('对齐完成')
  }
})

async function handleSplit() {
  await subStore.splitFromAlignment(project.value!.id)
  ElMessage.success('切分完成')
  activeTab.value = 'editor'
}

async function handleSave() {
  await subStore.saveSubtitles(project.value!.id)
  ElMessage.success('已保存')
}

async function handleExport(format: 'srt' | 'vtt' | 'ass') {
  await subStore.exportSubs(project.value!.id, format)
  ElMessage.success(`已导出 ${format.toUpperCase()}`)
}

function onSubtitleUpdate(index: number, updates: Partial<SubtitleItem>) {
  subStore.updateSubtitle(index, updates)
  cascadeFromIndex(index)
  markDirtyAndSave()
}

function onCascadeAdjust(index: number, newStart: number) {
  const sub = subStore.subtitles[index]
  if (!sub) return
  const dur = sub.end_time - sub.start_time
  subStore.updateSubtitle(index, { start_time: newStart, end_time: newStart + dur })
  cascadeFromIndex(index)
  markDirtyAndSave()
}

function onCorrected() {
  player.renderSubtitleRegions(subStore.subtitles)
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

function stageText(stage: string): string {
  const map: Record<string, string> = {
    loading_model: '加载模型中...',
    aligning: '正在对齐...',
    saving: '保存结果...',
    done: '完成',
    error: '出错',
  }
  return map[stage] || stage
}
</script>

<style scoped>
.project-view { max-width: 1400px; margin: 0 auto; }
.workspace-header { margin-bottom: 16px; }
.waveform-section {
  border: 1px solid #e4e7ed; border-radius: 8px; padding: 16px; margin-bottom: 16px;
  background: #fafafa;
}
.waveform-container { min-height: 128px; }
.playback-controls { display: flex; align-items: center; margin-top: 12px; gap: 16px; flex-wrap: wrap; }
.ctrl-label { font-size: 12px; color: #666; margin-right: 6px; }
.zoom-control, .speed-control { display: flex; align-items: center; }
.time-display { font-family: monospace; font-size: 14px; color: #666; margin-left: auto; }
.save-status { font-size: 12px; margin-left: 12px; }
.save-status.saving { color: #e6a23c; }
.save-status.dirty { color: #f56c6c; }
.workspace-tabs { min-height: 400px; }
.align-section { margin-top: 16px; }
.align-done { margin-top: 12px; }
.stage-text { margin-top: 8px; color: #666; font-size: 13px; }
.editor-toolbar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; align-items: center; }
</style>
