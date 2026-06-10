<template>
  <div class="subtitle-timeline" ref="containerRef">
    <canvas ref="canvasRef" @mousedown="onMouseDown" @mousemove="onMouseMove" @mouseup="onMouseUp" @wheel="onWheel"></canvas>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useSubtitleStore } from '../stores/subtitle'
import { usePlaybackStore } from '../stores/playback'
import { propagateAdjustment } from '../api/subtitles'
import { useRoute } from 'vue-router'

const route = useRoute()
const subtitleStore = useSubtitleStore()
const playbackStore = usePlaybackStore()
const containerRef = ref<HTMLElement>()
const canvasRef = ref<HTMLCanvasElement>()

const zoom = ref(1)
const scrollOffset = ref(0)
let dragging: { lineId: number; edge: 'start' | 'end' | 'body'; startX: number; origStart: number; origEnd: number } | null = null
let animFrame = 0

function draw() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')!
  const { width, height } = canvas

  ctx.clearRect(0, 0, width, height)

  const duration = playbackStore.duration || 60
  const pxPerSec = (width * zoom.value) / duration
  const offset = scrollOffset.value

  ctx.fillStyle = '#f5f7fa'
  ctx.fillRect(0, 0, width, height)

  ctx.strokeStyle = '#ddd'
  ctx.fillStyle = '#999'
  ctx.font = '10px monospace'
  const step = Math.max(1, Math.round(60 / zoom.value))
  for (let t = 0; t <= duration; t += step) {
    const x = (t - offset) * pxPerSec
    if (x < 0 || x > width) continue
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, height)
    ctx.stroke()
    const m = Math.floor(t / 60)
    const s = Math.floor(t % 60)
    ctx.fillText(`${m}:${s.toString().padStart(2, '0')}`, x + 2, 12)
  }

  subtitleStore.lines.forEach((line, i) => {
    const x1 = (line.start_time - offset) * pxPerSec
    const x2 = (line.end_time - offset) * pxPerSec
    if (x2 < 0 || x1 > width) return

    const selected = line.id === subtitleStore.selectedId
    const hue = (i * 37) % 360
    ctx.fillStyle = selected ? `hsla(${hue}, 80%, 55%, 0.6)` : `hsla(${hue}, 70%, 60%, 0.4)`
    ctx.fillRect(x1, 18, x2 - x1, height - 22)

    ctx.fillStyle = '#333'
    ctx.font = '11px sans-serif'
    const maxW = x2 - x1 - 4
    if (maxW > 10) {
      ctx.save()
      ctx.beginPath()
      ctx.rect(x1, 18, x2 - x1, height - 22)
      ctx.clip()
      ctx.fillText(line.text, x1 + 2, 34)
      ctx.restore()
    }
  })

  const cx = (playbackStore.currentTime - offset) * pxPerSec
  ctx.strokeStyle = '#ff4444'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(cx, 0)
  ctx.lineTo(cx, height)
  ctx.stroke()
  ctx.lineWidth = 1
}

function resize() {
  const canvas = canvasRef.value
  const container = containerRef.value
  if (!canvas || !container) return
  canvas.width = container.clientWidth
  canvas.height = container.clientHeight
  draw()
}

function onWheel(e: WheelEvent) {
  e.preventDefault()
  if (e.ctrlKey) {
    zoom.value = Math.max(0.5, Math.min(20, zoom.value * (1 - e.deltaY * 0.002)))
  } else {
    const duration = playbackStore.duration || 60
    scrollOffset.value = Math.max(0, Math.min(duration, scrollOffset.value + e.deltaX * 0.05))
  }
  draw()
}

function hitTest(x: number): { lineId: number; edge: 'start' | 'end' | 'body' } | null {
  const canvas = canvasRef.value!
  const duration = playbackStore.duration || 60
  const pxPerSec = (canvas.width * zoom.value) / duration
  const t = x / pxPerSec + scrollOffset.value

  for (const line of subtitleStore.lines) {
    const x1 = (line.start_time - scrollOffset.value) * pxPerSec
    const x2 = (line.end_time - scrollOffset.value) * pxPerSec
    if (x >= x1 - 4 && x <= x1 + 4) return { lineId: line.id, edge: 'start' }
    if (x >= x2 - 4 && x <= x2 + 4) return { lineId: line.id, edge: 'end' }
    if (x >= x1 && x <= x2) return { lineId: line.id, edge: 'body' }
  }
  return null
}

function onMouseDown(e: MouseEvent) {
  const rect = canvasRef.value!.getBoundingClientRect()
  const x = e.clientX - rect.left
  const hit = hitTest(x)
  if (hit) {
    const line = subtitleStore.lines.find(l => l.id === hit.lineId)!
    dragging = { ...hit, startX: x, origStart: line.start_time, origEnd: line.end_time }
    subtitleStore.select(hit.lineId)
  }
}

function onMouseMove(e: MouseEvent) {
  if (!dragging) return
  const canvas = canvasRef.value!
  const rect = canvas.getBoundingClientRect()
  const x = e.clientX - rect.left
  const duration = playbackStore.duration || 60
  const pxPerSec = (canvas.width * zoom.value) / duration
  const dt = (x - dragging.startX) / pxPerSec

  if (dragging.edge === 'start') {
    subtitleStore.updateLine(dragging.lineId, { start_time: Math.max(0, dragging.origStart + dt) })
  } else if (dragging.edge === 'end') {
    subtitleStore.updateLine(dragging.lineId, { end_time: Math.max(0, dragging.origEnd + dt) })
  } else {
    subtitleStore.updateLine(dragging.lineId, {
      start_time: Math.max(0, dragging.origStart + dt),
      end_time: Math.max(0, dragging.origEnd + dt),
    })
  }
  draw()
}

function onMouseUp() {
  if (dragging) {
    const line = subtitleStore.lines.find(l => l.id === dragging!.lineId)
    if (line) {
      const projectId = Number(route.params.id)
      propagateAdjustment(projectId, line.id, line.start_time, line.end_time)
        .then(({ data }) => subtitleStore.setLines(data))
    }
    dragging = null
  }
}

function startAnimLoop() {
  const loop = () => {
    draw()
    animFrame = requestAnimationFrame(loop)
  }
  animFrame = requestAnimationFrame(loop)
}

onMounted(() => {
  resize()
  window.addEventListener('resize', resize)
  startAnimLoop()
})

onUnmounted(() => {
  window.removeEventListener('resize', resize)
  cancelAnimationFrame(animFrame)
})
</script>

<style scoped>
.subtitle-timeline {
  width: 100%;
  height: 100%;
  overflow: hidden;
}
canvas {
  display: block;
  width: 100%;
  height: 100%;
  cursor: default;
}
</style>
