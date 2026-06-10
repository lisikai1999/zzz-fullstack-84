export interface Project {
  id: number
  name: string
  audio_path: string | null
  transcript_path: string | null
  status: string
  created_at: string
  updated_at: string
}

export interface WordTimestamp {
  word: string
  start: number
  end: number
}

export interface SubtitleLine {
  id: number
  project_id: number
  index: number
  text: string
  start_time: number
  end_time: number
  words: WordTimestamp[] | null
}

export interface AlignmentTask {
  id: string
  project_id: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  error_message: string | null
  created_at: string
  completed_at: string | null
}
