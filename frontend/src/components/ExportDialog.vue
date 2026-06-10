<template>
  <el-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" title="导出字幕" width="400px">
    <div class="export-options">
      <el-radio-group v-model="format">
        <el-radio value="srt">SRT 格式</el-radio>
        <el-radio value="ass">ASS 格式</el-radio>
      </el-radio-group>
    </div>
    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" @click="handleExport" :loading="exporting">下载</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { exportSubtitles } from '../api/subtitles'

const props = defineProps<{ modelValue: boolean; projectId: number }>()
const emit = defineEmits<{ 'update:modelValue': [val: boolean] }>()

const format = ref<'srt' | 'ass'>('srt')
const exporting = ref(false)

async function handleExport() {
  exporting.value = true
  try {
    const response = await exportSubtitles(props.projectId, format.value)
    const blob = new Blob([response.data], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `subtitles.${format.value}`
    a.click()
    URL.revokeObjectURL(url)
    emit('update:modelValue', false)
  } finally {
    exporting.value = false
  }
}
</script>

<style scoped>
.export-options {
  padding: 20px 0;
}
</style>
