<template>
  <div class="waveform-player" ref="containerRef">
    <canvas
      ref="canvasRef"
      @mousedown="onCanvasMouseDown"
      @mousemove="onCanvasMouseMove"
      @mouseup="onCanvasMouseUp"
      @mouseleave="onCanvasMouseUp"
      @dblclick="onCanvasDblClick"
      @wheel.prevent="onWheel"
    ></canvas>
    <!-- Scrollbar / viewport indicator -->
    <div class="viewport-bar" v-if="zoom > 1" @mousedown.prevent="onScrollbarDown">
      <div class="viewport-thumb" :style="thumbStyle"></div>
    </div>
    <div class="controls">
      <el-button-group>
        <el-button size="small" @click="togglePlay">
          {{ playbackStore.isPlaying ? '⏸' : '▶' }}
        </el-button>
        <el-button size="small" @click="stop">⏹</el-button>
      </el-button-group>
      <span class="time-display">{{ formatTime(playbackStore.currentTime) }} / {{ formatTime(playbackStore.duration) }}</span>
      <div class="zoom-controls">
        <el-button size="small" @click="zoomIn" :disabled="zoom >= 50">+</el-button>
        <span class="zoom-label">{{ zoom.toFixed(1) }}x</span>
        <el-button size="small" @click="zoomOut" :disabled="zoom <= 1">-</el-button>
        <el-button size="small" @click="zoomFit">适配</el-button>
      </div>
      <el-slider v-model="volume" :max="100" :show-tooltip="false" style="width: 80px; margin-left: 8px;" @input="onVolumeChange" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { usePlaybackStore } from '../stores/playback'
import { useSubtitleStore } from '../stores/subtitle'
import { formatTime } from '../composables/useTimeFormat'
import { propagateAdjustment } from '../api/subtitles'
import { useRoute } from 'vue-router'

const props = defineProps<{ audioUrl: string }>()

const route = useRoute()
const playbackStore = usePlaybackStore()
const subtitleStore = useSubtitleStore()
const containerRef = ref<HTMLElement>()
const canvasRef = ref<HTMLCanvasElement>()
const volume = ref(80)

// Zoom/scroll state
const zoom = ref(1)
const scrollTime = ref(0) // left edge of viewport in seconds

let audioContext: AudioContext | null = null
let audioBuffer: AudioBuffer | null = null
let sourceNode: AudioBufferSourceNode | null = null
let gainNode: GainNode | null = null
let peaks: Float32Array | null = null
let animFrame = 0
let startedAt = 0
let pausedAt = 0
let isPlaying = false

let dragState: {
  lineId: number
  edge: 'start' | 'end' | 'body'
  startX: number
  origStart: number
  origEnd: number
} | null = null

let panState: { startX: number; origScroll: number } | null = null
let scrollbarDrag: { startX: number; origScroll: number } | null = null

// Viewport thumb style for scrollbar
const thumbStyle = computed(() => {
  const duration = playbackStore.duration || 1
  const viewDuration = duration / zoom.value
  const thumbWidth = Math.max(20, (viewDuration / duration) * 100)
  const thumbLeft = (scrollTime.value / duration) * 100
  return {
    width: `${thumbWidth}%`,
    left: `${Math.min(thumbLeft, 100 - thumbWidth)}%`,
  }
})

// Visible time range
function getViewStart(): number { return scrollTime.value }
function getViewEnd(): number {
  const duration = playbackStore.duration || 1
  return Math.min(scrollTime.value + duration / zoom.value, duration)
}

function timeToX(time: number): number {
  const canvas = canvasRef.value!
  const viewStart = getViewStart()
  const viewDuration = (playbackStore.duration || 1) / zoom.value
  return ((time - viewStart) / viewDuration) * canvas.width
}

function xToTime(x: number): number {
  const canvas = canvasRef.value!
  const viewStart = getViewStart()
  const viewDuration = (playbackStore.duration || 1) / zoom.value
  return viewStart + (x / canvas.width) * viewDuration
}

function clampScroll() {
  const duration = playbackStore.duration || 1
  const viewDuration = duration / zoom.value
  scrollTime.value = Math.max(0, Math.min(scrollTime.value, duration - viewDuration))
}

// --- Zoom ---
function zoomIn() {
  zoomAt(zoom.value * 1.5, playbackStore.currentTime)
}

function zoomOut() {
  zoomAt(zoom.value / 1.5, playbackStore.currentTime)
}

function zoomFit() {
  zoom.value = 1
  scrollTime.value = 0
}

function zoomAt(newZoom: number, anchorTime: number) {
  newZoom = Math.max(1, Math.min(50, newZoom))
  const duration = playbackStore.duration || 1
  const oldViewDuration = duration / zoom.value
  const newViewDuration = duration / newZoom
  // Keep anchorTime at the same relative X position
  const relX = (anchorTime - scrollTime.value) / oldViewDuration
  zoom.value = newZoom
  scrollTime.value = anchorTime - relX * newViewDuration
  clampScroll()
}

function onWheel(e: WheelEvent) {
  const canvas = canvasRef.value!
  const rect = canvas.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseTime = xToTime(mouseX)

  if (e.ctrlKey || e.metaKey) {
    // Zoom centered on mouse position
    const factor = e.deltaY < 0 ? 1.3 : 1 / 1.3
    zoomAt(zoom.value * factor, mouseTime)
  } else {
    // Horizontal scroll
    const duration = playbackStore.duration || 1
    const viewDuration = duration / zoom.value
    scrollTime.value += (e.deltaY + e.deltaX) * viewDuration * 0.002
    clampScroll()
  }
}

// --- Audio loading ---
onMounted(async () => {
  resize()
  window.addEventListener('resize', resize)
  document.addEventListener('mouseup', onGlobalMouseUp)
  document.addEventListener('mousemove', onGlobalMouseMove)
  await loadAudio()
  startRenderLoop()
})

onUnmounted(() => {
  window.removeEventListener('resize', resize)
  document.removeEventListener('mouseup', onGlobalMouseUp)
  document.removeEventListener('mousemove', onGlobalMouseMove)
  cancelAnimationFrame(animFrame)
  stopPlayback()
  audioContext?.close()
})

async function loadAudio() {
  try {
    audioContext = new AudioContext()
    gainNode = audioContext.createGain()
    gainNode.gain.value = volume.value / 100
    gainNode.connect(audioContext.destination)

    const response = await fetch(props.audioUrl)
    const arrayBuffer = await response.arrayBuffer()
    audioBuffer = await audioContext.decodeAudioData(arrayBuffer)

    playbackStore.setDuration(audioBuffer.duration)
    peaks = computePeaks(audioBuffer)
    draw()
  } catch (e) {
    console.error('Failed to load audio:', e)
  }
}

function computePeaks(buffer: AudioBuffer): Float32Array {
  const channel = buffer.getChannelData(0)
  // Store enough peaks for max zoom: ~1 peak per ms
  const numPeaks = Math.min(channel.length, Math.max(4000, Math.ceil(buffer.duration * 100)))
  const samplesPerPeak = Math.floor(channel.length / numPeaks)
  const result = new Float32Array(numPeaks)
  for (let i = 0; i < numPeaks; i++) {
    let max = 0
    const start = i * samplesPerPeak
    const end = Math.min(start + samplesPerPeak, channel.length)
    for (let j = start; j < end; j++) {
      const abs = Math.abs(channel[j])
      if (abs > max) max = abs
    }
    result[i] = max
  }
  return result
}

function resize() {
  const canvas = canvasRef.value
  const container = containerRef.value
  if (!canvas || !container) return
  const controlsH = zoom.value > 1 ? 48 : 36
  canvas.width = container.clientWidth
  canvas.height = container.clientHeight - controlsH
  draw()
}

// --- Rendering ---
function draw() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')!
  const { width, height } = canvas
  const duration = playbackStore.duration || 1
  const viewStart = getViewStart()
  const viewEnd = getViewEnd()
  const viewDuration = viewEnd - viewStart

  ctx.clearRect(0, 0, width, height)

  // Background
  ctx.fillStyle = '#f8f9fa'
  ctx.fillRect(0, 0, width, height)

  // Time markers
  ctx.fillStyle = '#bbb'
  ctx.font = '10px monospace'
  ctx.strokeStyle = '#e8e8e8'
  ctx.lineWidth = 1
  const step = getTimeStep(viewDuration, width)
  const firstMark = Math.floor(viewStart / step) * step
  for (let t = firstMark; t <= viewEnd; t += step) {
    const x = timeToX(t)
    if (x < 0 || x > width) continue
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, height)
    ctx.stroke()
    const label = formatTimeShort(t)
    ctx.fillText(label, x + 2, height - 3)
  }

  // Subtitle regions
  subtitleStore.lines.forEach((line, i) => {
    const x1 = timeToX(line.start_time)
    const x2 = timeToX(line.end_time)
    if (x2 < 0 || x1 > width) return

    const hue = (i * 37) % 360
    const selected = line.id === subtitleStore.selectedId
    ctx.fillStyle = selected ? `hsla(${hue}, 75%, 60%, 0.35)` : `hsla(${hue}, 60%, 65%, 0.18)`
    ctx.fillRect(Math.max(0, x1), 0, Math.min(x2, width) - Math.max(0, x1), height)

    ctx.strokeStyle = `hsla(${hue}, 70%, 50%, 0.6)`
    ctx.lineWidth = 1.5
    if (x1 >= 0 && x1 <= width) {
      ctx.beginPath(); ctx.moveTo(x1, 0); ctx.lineTo(x1, height); ctx.stroke()
    }
    if (x2 >= 0 && x2 <= width) {
      ctx.beginPath(); ctx.moveTo(x2, 0); ctx.lineTo(x2, height); ctx.stroke()
    }

    // Text label
    if (x2 - x1 > 30) {
      ctx.fillStyle = '#555'
      ctx.font = '11px sans-serif'
      ctx.save()
      ctx.beginPath()
      ctx.rect(Math.max(0, x1 + 2), 0, Math.min(x2, width) - Math.max(0, x1) - 4, height)
      ctx.clip()
      ctx.fillText(line.text, Math.max(0, x1) + 4, 14)
      ctx.restore()
    }
  })

  // Waveform
  if (peaks && peaks.length > 0) {
    const mid = height / 2
    const peakDuration = duration / peaks.length
    const startIdx = Math.max(0, Math.floor(viewStart / peakDuration))
    const endIdx = Math.min(peaks.length, Math.ceil(viewEnd / peakDuration))

    ctx.fillStyle = '#4a9eff'
    for (let i = startIdx; i < endIdx; i++) {
      const peakTime = i * peakDuration
      const x = timeToX(peakTime)
      const nextX = timeToX((i + 1) * peakDuration)
      const barW = Math.max(1, nextX - x - 0.3)
      const barH = peaks[i] * mid * 0.85
      ctx.fillRect(x, mid - barH, barW, barH * 2)
    }
  }

  // Progress overlay
  const progressX = timeToX(playbackStore.currentTime)
  if (progressX > 0) {
    ctx.fillStyle = 'rgba(29, 111, 219, 0.12)'
    ctx.fillRect(0, 0, Math.min(progressX, width), height)
  }

  // Playback cursor
  if (progressX >= 0 && progressX <= width) {
    ctx.strokeStyle = '#ff4444'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(progressX, 0)
    ctx.lineTo(progressX, height)
    ctx.stroke()
  }
}

function getTimeStep(viewDuration: number, width: number): number {
  const targetSteps = width / 80
  const rawStep = viewDuration / targetSteps
  const steps = [0.1, 0.2, 0.5, 1, 2, 5, 10, 15, 30, 60, 120, 300]
  for (const s of steps) {
    if (s >= rawStep) return s
  }
  return 600
}

function formatTimeShort(t: number): string {
  const m = Math.floor(t / 60)
  const s = (t % 60).toFixed(t < 10 ? 1 : 0)
  return m > 0 ? `${m}:${s.toString().padStart(t < 10 ? 3 : 2, '0')}` : `${s}s`
}

function startRenderLoop() {
  const loop = () => {
    if (isPlaying && audioContext) {
      const t = audioContext.currentTime - startedAt + pausedAt
      playbackStore.setTime(t)
      // Auto-scroll to follow playback
      if (zoom.value > 1) {
        const viewEnd = getViewEnd()
        const viewDuration = (playbackStore.duration || 1) / zoom.value
        if (t > viewEnd - viewDuration * 0.1) {
          scrollTime.value = t - viewDuration * 0.2
          clampScroll()
        }
      }
    }
    draw()
    animFrame = requestAnimationFrame(loop)
  }
  animFrame = requestAnimationFrame(loop)
}

// --- Playback ---
function togglePlay() { isPlaying ? pause() : play() }

function play() {
  if (!audioContext || !audioBuffer || !gainNode) return
  if (audioContext.state === 'suspended') audioContext.resume()
  sourceNode = audioContext.createBufferSource()
  sourceNode.buffer = audioBuffer
  sourceNode.connect(gainNode)
  sourceNode.onended = () => {
    if (isPlaying) {
      isPlaying = false
      playbackStore.setPlaying(false)
      pausedAt = 0
      playbackStore.setTime(0)
    }
  }
  startedAt = audioContext.currentTime
  sourceNode.start(0, pausedAt)
  isPlaying = true
  playbackStore.setPlaying(true)
}

function pause() {
  if (!audioContext || !isPlaying) return
  pausedAt = audioContext.currentTime - startedAt + pausedAt
  stopPlayback()
  isPlaying = false
  playbackStore.setPlaying(false)
}

function stop() {
  stopPlayback()
  pausedAt = 0
  isPlaying = false
  playbackStore.setTime(0)
  playbackStore.setPlaying(false)
}

function stopPlayback() {
  if (sourceNode) {
    try { sourceNode.stop() } catch {}
    sourceNode.disconnect()
    sourceNode = null
  }
}

function seekTo(time: number) {
  const wasPlaying = isPlaying
  if (isPlaying) stopPlayback()
  pausedAt = Math.max(0, Math.min(time, playbackStore.duration))
  playbackStore.setTime(pausedAt)
  isPlaying = false
  if (wasPlaying) play()
}

function onVolumeChange(val: number) {
  if (gainNode) gainNode.gain.value = val / 100
}

// --- Mouse interaction ---
function hitTestRegion(x: number): { lineId: number; edge: 'start' | 'end' | 'body' } | null {
  for (const line of subtitleStore.lines) {
    const x1 = timeToX(line.start_time)
    const x2 = timeToX(line.end_time)
    if (x >= x1 - 5 && x <= x1 + 5) return { lineId: line.id, edge: 'start' }
    if (x >= x2 - 5 && x <= x2 + 5) return { lineId: line.id, edge: 'end' }
    if (x > x1 + 5 && x < x2 - 5) return { lineId: line.id, edge: 'body' }
  }
  return null
}

function onCanvasMouseDown(e: MouseEvent) {
  const rect = canvasRef.value!.getBoundingClientRect()
  const x = e.clientX - rect.left
  const hit = hitTestRegion(x)

  if (hit) {
    const line = subtitleStore.lines.find(l => l.id === hit.lineId)!
    dragState = { ...hit, startX: e.clientX, origStart: line.start_time, origEnd: line.end_time }
    subtitleStore.select(hit.lineId)
  } else if (e.button === 1 || (e.button === 0 && e.shiftKey)) {
    // Middle-click or shift+click: pan
    panState = { startX: e.clientX, origScroll: scrollTime.value }
  } else {
    seekTo(xToTime(x))
  }
}

function onCanvasMouseMove(e: MouseEvent) {
  const canvas = canvasRef.value!
  const rect = canvas.getBoundingClientRect()
  const x = e.clientX - rect.left

  const hit = hitTestRegion(x)
  if (dragState) {
    canvas.style.cursor = dragState.edge === 'body' ? 'grabbing' : 'col-resize'
  } else if (panState) {
    canvas.style.cursor = 'move'
  } else if (hit) {
    canvas.style.cursor = hit.edge === 'body' ? 'grab' : 'col-resize'
  } else {
    canvas.style.cursor = 'crosshair'
  }
}

function onGlobalMouseMove(e: MouseEvent) {
  if (dragState) {
    const canvas = canvasRef.value!
    const duration = playbackStore.duration || 1
    const viewDuration = duration / zoom.value
    const dx = e.clientX - dragState.startX
    const dt = (dx / canvas.width) * viewDuration

    if (dragState.edge === 'start') {
      subtitleStore.updateLine(dragState.lineId, { start_time: Math.max(0, dragState.origStart + dt) })
    } else if (dragState.edge === 'end') {
      subtitleStore.updateLine(dragState.lineId, { end_time: Math.max(0, dragState.origEnd + dt) })
    } else {
      subtitleStore.updateLine(dragState.lineId, {
        start_time: Math.max(0, dragState.origStart + dt),
        end_time: Math.max(0, dragState.origEnd + dt),
      })
    }
  }

  if (panState) {
    const canvas = canvasRef.value!
    const duration = playbackStore.duration || 1
    const viewDuration = duration / zoom.value
    const dx = e.clientX - panState.startX
    scrollTime.value = panState.origScroll - (dx / canvas.width) * viewDuration
    clampScroll()
  }

  if (scrollbarDrag) {
    const container = containerRef.value!
    const barWidth = container.clientWidth
    const dx = e.clientX - scrollbarDrag.startX
    const duration = playbackStore.duration || 1
    scrollTime.value = scrollbarDrag.origScroll + (dx / barWidth) * duration
    clampScroll()
  }
}

function onGlobalMouseUp() {
  if (dragState) {
    const line = subtitleStore.lines.find(l => l.id === dragState!.lineId)
    if (line) {
      const projectId = Number(route.params.id)
      propagateAdjustment(projectId, line.id, line.start_time, line.end_time)
        .then(({ data }) => subtitleStore.setLines(data))
    }
    dragState = null
  }
  panState = null
  scrollbarDrag = null
}

function onCanvasMouseUp() {
  // handled by global
}

function onCanvasDblClick(e: MouseEvent) {
  const rect = canvasRef.value!.getBoundingClientRect()
  seekTo(xToTime(e.clientX - rect.left))
}

function onScrollbarDown(e: MouseEvent) {
  scrollbarDrag = { startX: e.clientX, origScroll: scrollTime.value }
}

// Seek when a subtitle is selected externally
watch(() => subtitleStore.selectedId, (id) => {
  if (id !== null) {
    const line = subtitleStore.lines.find(l => l.id === id)
    if (line) {
      seekTo(line.start_time)
      // Scroll to show the line if it's off-screen
      if (line.start_time < getViewStart() || line.start_time > getViewEnd()) {
        const viewDuration = (playbackStore.duration || 1) / zoom.value
        scrollTime.value = line.start_time - viewDuration * 0.1
        clampScroll()
      }
    }
  }
})

defineExpose({ seekTo })
</script>

<style scoped>
.waveform-player {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 4px 8px;
}
canvas {
  flex: 1;
  display: block;
  border-radius: 4px;
  min-height: 0;
}
.viewport-bar {
  height: 8px;
  background: #e8e8e8;
  border-radius: 4px;
  margin-top: 2px;
  position: relative;
  cursor: pointer;
  flex-shrink: 0;
}
.viewport-thumb {
  position: absolute;
  top: 0;
  height: 100%;
  background: #4a9eff;
  border-radius: 4px;
  opacity: 0.6;
  transition: opacity 0.1s;
}
.viewport-thumb:hover {
  opacity: 0.8;
}
.controls {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 4px;
  height: 32px;
  flex-shrink: 0;
}
.time-display {
  font-size: 12px;
  color: #666;
  font-family: monospace;
}
.zoom-controls {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
}
.zoom-label {
  font-size: 11px;
  color: #888;
  font-family: monospace;
  min-width: 32px;
  text-align: center;
}
</style>
