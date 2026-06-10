<template>
  <div class="subtitle-table">
    <el-table
      :data="subtitleStore.lines"
      highlight-current-row
      @current-change="onRowSelect"
      :row-class-name="rowClassName"
      size="small"
      height="100%"
    >
      <el-table-column label="#" width="50" prop="index" />
      <el-table-column label="开始" width="120">
        <template #default="{ row }">
          <el-input
            size="small"
            :model-value="formatTime(row.start_time)"
            @change="(val: string) => handleTimeChange(row.id, 'start_time', val)"
          />
        </template>
      </el-table-column>
      <el-table-column label="结束" width="120">
        <template #default="{ row }">
          <el-input
            size="small"
            :model-value="formatTime(row.end_time)"
            @change="(val: string) => handleTimeChange(row.id, 'end_time', val)"
          />
        </template>
      </el-table-column>
      <el-table-column label="内容">
        <template #default="{ row }">
          <el-input
            size="small"
            :model-value="row.text"
            @change="(val: string) => handleTextChange(row.id, val)"
          />
        </template>
      </el-table-column>
      <el-table-column label="时长" width="70">
        <template #default="{ row }">
          {{ (row.end_time - row.start_time).toFixed(1) }}s
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { useSubtitleStore } from '../stores/subtitle'
import { usePlaybackStore } from '../stores/playback'
import { updateSubtitle } from '../api/subtitles'
import { formatTime, parseTime } from '../composables/useTimeFormat'
import { useRoute } from 'vue-router'
import { computed } from 'vue'
import type { SubtitleLine } from '../types'

const route = useRoute()
const subtitleStore = useSubtitleStore()
const playbackStore = usePlaybackStore()
const projectId = computed(() => Number(route.params.id))

function onRowSelect(row: SubtitleLine | null) {
  if (row) {
    subtitleStore.select(row.id)
  }
}

function rowClassName({ row }: { row: SubtitleLine }) {
  const t = playbackStore.currentTime
  if (t >= row.start_time && t <= row.end_time) return 'current-row'
  return ''
}

async function handleTimeChange(lineId: number, field: 'start_time' | 'end_time', val: string) {
  const seconds = parseTime(val)
  subtitleStore.updateLine(lineId, { [field]: seconds })
  await updateSubtitle(projectId.value, lineId, { [field]: seconds })
}

async function handleTextChange(lineId: number, val: string) {
  subtitleStore.updateLine(lineId, { text: val })
  await updateSubtitle(projectId.value, lineId, { text: val })
}
</script>

<style scoped>
.subtitle-table {
  height: 100%;
}
:deep(.current-row) {
  background-color: #ecf5ff !important;
}
</style>
