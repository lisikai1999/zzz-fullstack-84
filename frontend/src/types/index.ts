export interface Project {
  id: string
  name: string
  audio_path: string | null
  transcript: string | null
  language: string
  status: string
  created_at: string
}

export interface WordAlignment {
  char: string
  start: number
  end: number
  confidence: number
}

export interface AlignmentResult {
  id: string
  project_id: string
  status: string
  word_alignments: WordAlignment[] | null
  created_at: string
}

export interface SubtitleItem {
  id?: string
  index: number
  text: string
  start_time: number
  end_time: number
}

export interface AlignmentProgress {
  percent: number
  stage: string
  error?: string
}

export interface CorrectionRequest {
  mode: 'global_shift' | 'linear_scale' | 'single_cascade' | 'anchor_interpolation'
  offset_ms?: number
  scale_factor?: number
  scale_offset?: number
  anchor_index?: number
  new_start?: number
  anchors?: { subtitle_index: number; correct_start: number }[]
}

export interface WaveformData {
  metadata: {
    duration: number
    sample_rate: number
    channels: number
  }
  peaks: [number, number][]
}
