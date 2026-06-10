import { defineStore } from 'pinia'
import { ref } from 'vue'

export const usePlaybackStore = defineStore('playback', () => {
  const currentTime = ref(0)
  const duration = ref(0)
  const isPlaying = ref(false)

  function setTime(t: number) {
    currentTime.value = t
  }

  function setDuration(d: number) {
    duration.value = d
  }

  function setPlaying(playing: boolean) {
    isPlaying.value = playing
  }

  return { currentTime, duration, isPlaying, setTime, setDuration, setPlaying }
})
