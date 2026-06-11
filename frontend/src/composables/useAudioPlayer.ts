import { ref, onBeforeUnmount, type Ref } from 'vue'
import WaveSurfer from 'wavesurfer.js'
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.js'
import type { SubtitleItem } from '@/types'

export interface RegionUpdateEvent {
  subtitleIndex: number
  start: number
  end: number
}

export function useAudioPlayer(containerRef: Ref<HTMLElement | null>) {
  const wavesurfer = ref<WaveSurfer | null>(null)
  const regionsPlugin = ref<RegionsPlugin | null>(null)
  const isPlaying = ref(false)
  const currentTime = ref(0)
  const duration = ref(0)

  const onRegionUpdate = ref<((event: RegionUpdateEvent) => void) | null>(null)

  function init(audioUrl: string) {
    if (!containerRef.value) return
    if (wavesurfer.value) {
      wavesurfer.value.destroy()
    }

    const regions = RegionsPlugin.create()
    regionsPlugin.value = regions

    wavesurfer.value = WaveSurfer.create({
      container: containerRef.value,
      waveColor: '#4a9eff',
      progressColor: '#1a6ed8',
      cursorColor: '#ff4444',
      cursorWidth: 2,
      height: 128,
      normalize: true,
      minPxPerSec: 50,
      fillParent: true,
      scrollParent: true,
      plugins: [regions],
    })

    wavesurfer.value.load(audioUrl)

    wavesurfer.value.on('ready', () => {
      duration.value = wavesurfer.value!.getDuration()
    })

    wavesurfer.value.on('audioprocess', () => {
      currentTime.value = wavesurfer.value!.getCurrentTime()
    })

    wavesurfer.value.on('play', () => { isPlaying.value = true })
    wavesurfer.value.on('pause', () => { isPlaying.value = false })
    wavesurfer.value.on('seeking', () => {
      currentTime.value = wavesurfer.value!.getCurrentTime()
    })

    regions.on('region-updated', (region: any) => {
      const idx = parseInt(region.id.replace('sub-', ''))
      if (!isNaN(idx) && onRegionUpdate.value) {
        onRegionUpdate.value({
          subtitleIndex: idx,
          start: region.start,
          end: region.end,
        })
      }
    })
  }

  function renderSubtitleRegions(subtitles: SubtitleItem[]) {
    if (!regionsPlugin.value) return
    regionsPlugin.value.clearRegions()

    const colors = [
      'rgba(64, 158, 255, 0.25)',
      'rgba(103, 194, 58, 0.25)',
      'rgba(230, 162, 60, 0.25)',
      'rgba(144, 147, 153, 0.25)',
    ]

    subtitles.forEach((sub, idx) => {
      regionsPlugin.value!.addRegion({
        id: `sub-${idx}`,
        start: sub.start_time,
        end: sub.end_time,
        content: sub.text.slice(0, 8),
        color: colors[idx % colors.length],
        drag: true,
        resize: true,
      })
    })
  }

  function highlightRegion(index: number) {
    if (!regionsPlugin.value) return
    const regions = regionsPlugin.value.getRegions()
    regions.forEach((r: any) => {
      const el = r.element as HTMLElement
      if (!el) return
      if (r.id === `sub-${index}`) {
        el.style.borderTop = '3px solid #409eff'
      } else {
        el.style.borderTop = ''
      }
    })
  }

  function play() { wavesurfer.value?.play() }
  function pause() { wavesurfer.value?.pause() }
  function toggle() { wavesurfer.value?.playPause() }
  function seekTo(time: number) {
    if (wavesurfer.value && duration.value > 0) {
      wavesurfer.value.seekTo(time / duration.value)
    }
  }
  function setPlaybackRate(rate: number) { wavesurfer.value?.setPlaybackRate(rate) }
  function zoom(pxPerSec: number) { wavesurfer.value?.zoom(pxPerSec) }

  function destroy() {
    wavesurfer.value?.destroy()
    wavesurfer.value = null
    regionsPlugin.value = null
  }

  onBeforeUnmount(destroy)

  return {
    wavesurfer, isPlaying, currentTime, duration,
    init, play, pause, toggle, seekTo, setPlaybackRate, zoom, destroy,
    renderSubtitleRegions, highlightRegion, onRegionUpdate,
  }
}
