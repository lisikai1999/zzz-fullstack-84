import { ref, watch, type Ref } from 'vue'
import type { SubtitleItem, WordAlignment } from '@/types'

export function useSubtitleSync(
  currentTime: Ref<number>,
  subtitles: Ref<SubtitleItem[]>,
  wordAlignments: Ref<WordAlignment[]>
) {
  const currentSubtitleIndex = ref(-1)
  const currentWordIndex = ref(-1)

  watch(currentTime, (time) => {
    currentSubtitleIndex.value = binarySearchSubtitle(subtitles.value, time)
    currentWordIndex.value = binarySearchWord(wordAlignments.value, time)
  })

  return { currentSubtitleIndex, currentWordIndex }
}

function binarySearchSubtitle(subtitles: SubtitleItem[], time: number): number {
  let lo = 0
  let hi = subtitles.length - 1
  while (lo <= hi) {
    const mid = (lo + hi) >> 1
    if (time < subtitles[mid].start_time) {
      hi = mid - 1
    } else if (time > subtitles[mid].end_time) {
      lo = mid + 1
    } else {
      return mid
    }
  }
  return -1
}

function binarySearchWord(words: WordAlignment[], time: number): number {
  let lo = 0
  let hi = words.length - 1
  while (lo <= hi) {
    const mid = (lo + hi) >> 1
    if (time < words[mid].start) {
      hi = mid - 1
    } else if (time > words[mid].end) {
      lo = mid + 1
    } else {
      return mid
    }
  }
  return -1
}
