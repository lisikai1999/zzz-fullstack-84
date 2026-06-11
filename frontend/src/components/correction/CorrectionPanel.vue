<template>
  <div class="correction-panel">
    <el-tabs v-model="mode">
      <!-- Global Shift -->
      <el-tab-pane label="整体偏移" name="global_shift">
        <el-form label-width="100px">
          <el-form-item label="偏移量(ms)">
            <el-input-number v-model="offsetMs" :step="100" />
            <span class="hint">正值后移，负值前移</span>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="applyShift" :loading="loading">应用</el-button>
          </el-form-item>
        </el-form>
        <div class="quick-btns">
          <el-button size="small" @click="offsetMs = -500; applyShift()">-500ms</el-button>
          <el-button size="small" @click="offsetMs = -200; applyShift()">-200ms</el-button>
          <el-button size="small" @click="offsetMs = 200; applyShift()">+200ms</el-button>
          <el-button size="small" @click="offsetMs = 500; applyShift()">+500ms</el-button>
        </div>
      </el-tab-pane>

      <!-- Linear Scale -->
      <el-tab-pane label="线性缩放" name="linear_scale">
        <el-form label-width="100px">
          <el-form-item label="缩放因子">
            <el-input-number v-model="scaleFactor" :step="0.01" :precision="3" :min="0.1" :max="10" />
            <span class="hint">1.0=不变, >1拉伸, &lt;1压缩</span>
          </el-form-item>
          <el-form-item label="时间偏移(s)">
            <el-input-number v-model="scaleOffset" :step="0.1" :precision="2" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="applyScale" :loading="loading">应用</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- Single Cascade -->
      <el-tab-pane label="单条级联" name="single_cascade">
        <p class="desc">选择一条字幕并设定新的起始时间，相邻字幕自动跟着调整避免重叠。</p>
        <el-form label-width="100px">
          <el-form-item label="字幕序号">
            <el-input-number v-model="cascadeIndex" :min="0" :max="maxIndex" />
            <span class="hint">从0开始</span>
          </el-form-item>
          <el-form-item label="新起始时间(s)">
            <el-input-number v-model="cascadeNewStart" :step="0.1" :precision="3" :min="0" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="applyCascade" :loading="loading">应用</el-button>
          </el-form-item>
        </el-form>
        <p class="tip">提示：也可以直接在编辑器中修改起始时间或拖动波形上的色块来触发级联调整。</p>
      </el-tab-pane>

      <!-- Anchor Interpolation -->
      <el-tab-pane label="锚点校正" name="anchor_interpolation">
        <p class="desc">标记若干时间正确的锚点，中间的字幕按比例重新分布。</p>
        <div class="anchor-list">
          <div v-for="(anchor, idx) in anchors" :key="idx" class="anchor-item">
            <span class="anchor-label">字幕#</span>
            <el-input-number v-model="anchor.subtitle_index" :min="0" :max="maxIndex" size="small" />
            <span class="anchor-label">→</span>
            <el-input-number v-model="anchor.correct_start" :step="0.1" :precision="2" placeholder="正确时间(s)" size="small" />
            <el-button size="small" type="danger" text @click="anchors.splice(idx, 1)">删除</el-button>
          </div>
          <el-button size="small" @click="addAnchor">+ 添加锚点</el-button>
        </div>
        <el-button type="primary" @click="applyAnchor" :loading="loading" style="margin-top: 12px">
          应用
        </el-button>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useSubtitleStore } from '@/stores/subtitle'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ corrected: [] }>()
const store = useSubtitleStore()

const mode = ref('global_shift')
const loading = ref(false)

const offsetMs = ref(0)
const scaleFactor = ref(1.0)
const scaleOffset = ref(0)

const cascadeIndex = ref(0)
const cascadeNewStart = ref(0)

const anchors = ref<{ subtitle_index: number; correct_start: number }[]>([
  { subtitle_index: 0, correct_start: 0 },
  { subtitle_index: 10, correct_start: 10 },
])

const maxIndex = computed(() => Math.max(0, store.subtitles.length - 1))

function addAnchor() {
  anchors.value.push({ subtitle_index: 0, correct_start: 0 })
}

async function applyShift() {
  loading.value = true
  try {
    await store.applyCorrection(props.projectId, { mode: 'global_shift', offset_ms: offsetMs.value })
    ElMessage.success('偏移已应用')
    emit('corrected')
  } finally { loading.value = false }
}

async function applyScale() {
  loading.value = true
  try {
    await store.applyCorrection(props.projectId, { mode: 'linear_scale', scale_factor: scaleFactor.value, scale_offset: scaleOffset.value })
    ElMessage.success('缩放已应用')
    emit('corrected')
  } finally { loading.value = false }
}

async function applyCascade() {
  loading.value = true
  try {
    await store.applyCorrection(props.projectId, { mode: 'single_cascade', anchor_index: cascadeIndex.value, new_start: cascadeNewStart.value })
    ElMessage.success('级联调整已应用')
    emit('corrected')
  } finally { loading.value = false }
}

async function applyAnchor() {
  if (anchors.value.length < 2) {
    ElMessage.warning('至少需要2个锚点')
    return
  }
  loading.value = true
  try {
    await store.applyCorrection(props.projectId, { mode: 'anchor_interpolation', anchors: anchors.value })
    ElMessage.success('锚点校正已应用')
    emit('corrected')
  } finally { loading.value = false }
}
</script>

<style scoped>
.correction-panel { max-width: 560px; }
.hint { margin-left: 12px; color: #909399; font-size: 12px; }
.desc { color: #606266; font-size: 13px; margin-bottom: 12px; }
.tip { color: #909399; font-size: 12px; margin-top: 12px; font-style: italic; }
.quick-btns { display: flex; gap: 8px; margin-top: 8px; }
.anchor-list { display: flex; flex-direction: column; gap: 8px; }
.anchor-item { display: flex; align-items: center; gap: 8px; }
.anchor-label { font-size: 12px; color: #666; }
</style>
