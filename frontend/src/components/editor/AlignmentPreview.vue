<template>
  <div class="alignment-preview">
    <div class="word-container" v-if="wordAlignments.length > 0">
      <span
        v-for="(word, idx) in wordAlignments"
        :key="idx"
        :class="['word', { active: idx === currentWordIndex, past: idx < currentWordIndex }]"
      >{{ word.char }}</span>
    </div>
    <el-empty v-else description="暂无对齐结果，请先执行对齐" />
  </div>
</template>

<script setup lang="ts">
import type { WordAlignment } from '@/types'

defineProps<{
  wordAlignments: WordAlignment[]
  currentWordIndex: number
}>()
</script>

<style scoped>
.alignment-preview { padding: 20px; }
.word-container { line-height: 2.5; font-size: 20px; }
.word {
  display: inline; padding: 2px 1px; border-radius: 3px;
  transition: all 0.15s;
}
.word.active { background: #409eff; color: white; transform: scale(1.1); }
.word.past { color: #999; }
</style>
