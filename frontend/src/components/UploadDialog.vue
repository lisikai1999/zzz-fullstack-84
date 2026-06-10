<template>
  <el-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" title="上传文件" width="500px">
    <div class="upload-section">
      <h4>音频/视频文件</h4>
      <el-upload
        :action="`/api/projects/${projectId}/upload/audio`"
        :show-file-list="true"
        :limit="1"
        :on-success="onAudioSuccess"
        accept=".mp3,.wav,.mp4,.mkv,.flac,.m4a,.ogg"
      >
        <el-button>选择音频文件</el-button>
        <template #tip>
          <div class="el-upload__tip">支持 mp3, wav, mp4, mkv, flac, m4a, ogg</div>
        </template>
      </el-upload>
    </div>
    <div class="upload-section">
      <h4>转录文本</h4>
      <el-upload
        :action="`/api/projects/${projectId}/upload/transcript`"
        :show-file-list="true"
        :limit="1"
        :on-success="onTranscriptSuccess"
        accept=".txt,.srt,.ass"
      >
        <el-button>选择文本文件</el-button>
        <template #tip>
          <div class="el-upload__tip">支持 txt (纯文本), srt, ass</div>
        </template>
      </el-upload>
    </div>
    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'

defineProps<{ modelValue: boolean; projectId: number }>()
const emit = defineEmits<{ 'update:modelValue': [val: boolean]; done: [] }>()

function onAudioSuccess() {
  ElMessage.success('音频上传成功')
  emit('done')
}

function onTranscriptSuccess() {
  ElMessage.success('文本上传成功')
  emit('done')
}
</script>

<style scoped>
.upload-section {
  margin-bottom: 20px;
}
h4 {
  margin: 0 0 8px;
  font-size: 14px;
}
</style>
