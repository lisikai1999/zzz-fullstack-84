<template>
  <div class="correction-panel">
    <h4>时间校正</h4>
    <div class="correction-row">
      <span>整体偏移 (ms):</span>
      <el-input-number v-model="shiftMs" :step="100" size="small" style="width: 140px" />
      <el-button size="small" type="primary" @click="handleShift" :loading="shifting">应用</el-button>
    </div>
    <div class="correction-row">
      <span>线性缩放:</span>
      <el-slider v-model="scaleFactor" :min="0.5" :max="2.0" :step="0.01" style="width: 140px" />
      <span class="factor-label">{{ scaleFactor.toFixed(2) }}x</span>
      <el-button size="small" type="primary" @click="handleScale" :loading="scaling">应用</el-button>
    </div>
    <div class="correction-row">
      <span>锚点时间 (s):</span>
      <el-input-number v-model="anchorTime" :min="0" :step="1" size="small" style="width: 120px" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useSubtitleStore } from '../stores/subtitle'
import { shiftSubtitles, scaleSubtitles } from '../api/subtitles'

const route = useRoute()
const subtitleStore = useSubtitleStore()
const projectId = computed(() => Number(route.params.id))

const shiftMs = ref(0)
const scaleFactor = ref(1.0)
const anchorTime = ref(0)
const shifting = ref(false)
const scaling = ref(false)

async function handleShift() {
  if (shiftMs.value === 0) return
  shifting.value = true
  try {
    const { data } = await shiftSubtitles(projectId.value, shiftMs.value)
    subtitleStore.setLines(data)
    ElMessage.success(`已偏移 ${shiftMs.value}ms`)
    shiftMs.value = 0
  } catch {
    ElMessage.error('偏移失败')
  } finally {
    shifting.value = false
  }
}

async function handleScale() {
  if (scaleFactor.value === 1.0) return
  scaling.value = true
  try {
    const { data } = await scaleSubtitles(projectId.value, scaleFactor.value, anchorTime.value)
    subtitleStore.setLines(data)
    ElMessage.success(`已缩放 ${scaleFactor.value.toFixed(2)}x`)
    scaleFactor.value = 1.0
  } catch {
    ElMessage.error('缩放失败')
  } finally {
    scaling.value = false
  }
}
</script>

<style scoped>
.correction-panel {
  padding: 12px 16px;
}
h4 {
  margin: 0 0 12px;
  font-size: 14px;
}
.correction-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 13px;
}
.factor-label {
  font-family: monospace;
  min-width: 40px;
}
</style>
