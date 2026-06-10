<template>
  <div class="alignment-preview">
    <div class="preview-content" v-if="currentLine">
      <span
        v-for="(word, i) in currentWords"
        :key="i"
        :class="['word', { active: isWordActive(word) }]"
      >{{ word.word }}</span>
    </div>
    <div class="preview-empty" v-else>
      <span>播放音频查看逐词高亮预览</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSubtitleStore } from '../stores/subtitle'
import { usePlaybackStore } from '../stores/playback'
import type { WordTimestamp } from '../types'

const subtitleStore = useSubtitleStore()
const playbackStore = usePlaybackStore()

const currentLine = computed(() => {
  const t = playbackStore.currentTime
  return subtitleStore.lines.find(l => t >= l.start_time && t <= l.end_time) || null
})

const currentWords = computed((): WordTimestamp[] => {
  return currentLine.value?.words || []
})

function isWordActive(word: WordTimestamp): boolean {
  const t = playbackStore.currentTime
  return t >= word.start && t <= word.end
}
</script>

<style scoped>
.alignment-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 20px;
}
.preview-content {
  font-size: 28px;
  line-height: 1.6;
  text-align: center;
}
.word {
  transition: color 0.1s, background-color 0.1s;
  padding: 2px 0;
  border-radius: 3px;
}
.word.active {
  color: #fff;
  background-color: #409eff;
}
.preview-empty {
  color: #999;
  font-size: 14px;
}
</style>
