<template>
  <div class="subtitle-editor">
    <div class="editor-list" ref="listRef">
      <div
        v-for="(sub, idx) in subtitles"
        :key="sub.id || idx"
        :ref="(el) => { if (idx === currentIndex) activeRowEl = el as HTMLElement }"
        :class="['subtitle-row', { active: idx === currentIndex }]"
        @click="$emit('seek', sub.start_time)"
      >
        <span class="row-index">{{ sub.index }}</span>
        <div class="row-times">
          <input
            class="time-input"
            :value="formatTime(sub.start_time)"
            @change="onStartChange(idx, $event)"
            @click.stop
          />
          <span class="time-sep">→</span>
          <input
            class="time-input"
            :value="formatTime(sub.end_time)"
            @change="onEndChange(idx, $event)"
            @click.stop
          />
        </div>
        <input
          class="row-text"
          :value="sub.text"
          @change="onTextChange(idx, $event)"
          @click.stop
        />
        <span class="row-duration">{{ ((sub.end_time - sub.start_time) * 1000).toFixed(0) }}ms</span>
      </div>
    </div>
    <el-empty v-if="subtitles.length === 0" description="暂无字幕，请先执行对齐和切分" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import type { SubtitleItem } from '@/types'

const props = defineProps<{
  subtitles: SubtitleItem[]
  currentIndex: number
}>()

const emit = defineEmits<{
  seek: [time: number]
  update: [index: number, updates: Partial<SubtitleItem>]
  cascade: [index: number, newStart: number]
}>()

const listRef = ref<HTMLElement | null>(null)
const activeRowEl = ref<HTMLElement | null>(null)

watch(() => props.currentIndex, () => {
  nextTick(() => {
    if (activeRowEl.value && listRef.value) {
      const container = listRef.value
      const row = activeRowEl.value
      const containerRect = container.getBoundingClientRect()
      const rowRect = row.getBoundingClientRect()
      if (rowRect.top < containerRect.top || rowRect.bottom > containerRect.bottom) {
        row.scrollIntoView({ block: 'center', behavior: 'smooth' })
      }
    }
  })
})

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  const ms = Math.floor((seconds % 1) * 1000)
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`
}

function parseTime(str: string): number {
  const parts = str.split(/[:.]/)
  if (parts.length >= 3) {
    const m = parseInt(parts[0]) || 0
    const s = parseInt(parts[1]) || 0
    const ms = parseInt(parts[2]) || 0
    return m * 60 + s + ms / 1000
  }
  return 0
}

function onStartChange(idx: number, event: Event) {
  const value = (event.target as HTMLInputElement).value
  const newStart = parseTime(value)
  emit('cascade', idx, newStart)
}

function onEndChange(idx: number, event: Event) {
  const value = (event.target as HTMLInputElement).value
  emit('update', idx, { end_time: parseTime(value) })
}

function onTextChange(idx: number, event: Event) {
  const value = (event.target as HTMLInputElement).value
  emit('update', idx, { text: value })
}
</script>

<style scoped>
.editor-list { max-height: 400px; overflow-y: auto; border: 1px solid #eee; border-radius: 6px; }
.subtitle-row {
  display: flex; align-items: center; gap: 8px; padding: 8px 10px;
  border-bottom: 1px solid #f5f5f5; cursor: pointer; transition: background 0.15s;
}
.subtitle-row:hover { background: #f5f7fa; }
.subtitle-row.active { background: #ecf5ff; border-left: 3px solid #409eff; }
.row-index { width: 28px; text-align: center; color: #999; font-size: 12px; flex-shrink: 0; }
.row-times { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }
.time-input {
  width: 95px; font-family: monospace; font-size: 12px; padding: 3px 5px;
  border: 1px solid #dcdfe6; border-radius: 4px; text-align: center;
}
.time-input:focus { border-color: #409eff; outline: none; }
.time-sep { color: #c0c4cc; font-size: 12px; }
.row-text {
  flex: 1; padding: 3px 8px; border: 1px solid transparent; border-radius: 4px;
  font-size: 14px; min-width: 0;
}
.row-text:focus { border-color: #409eff; outline: none; background: white; }
.row-duration { width: 50px; text-align: right; font-size: 11px; color: #aaa; flex-shrink: 0; }
</style>
