<template>
  <div class="upload-panel">
    <el-form label-width="100px">
      <el-form-item label="音频/视频">
        <el-upload
          :auto-upload="false"
          :limit="1"
          :on-change="onFileChange"
          accept="audio/*,video/*"
          drag
        >
          <div class="upload-tip">
            <p>拖拽或点击上传音频/视频文件</p>
            <p class="hint">支持 mp3, wav, mp4, mkv 等格式</p>
          </div>
        </el-upload>
      </el-form-item>
      <el-form-item label="转录文本">
        <el-input
          v-model="transcript"
          type="textarea"
          :rows="6"
          placeholder="粘贴正确的转录文本内容..."
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleUpload" :loading="uploading">
          上传
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useProjectStore } from '@/stores/project'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ uploaded: [] }>()

const store = useProjectStore()
const audioFile = ref<File | null>(null)
const transcript = ref('')
const uploading = ref(false)

function onFileChange(file: any) {
  audioFile.value = file.raw
}

async function handleUpload() {
  if (!audioFile.value) {
    ElMessage.warning('请选择音频文件')
    return
  }
  if (!transcript.value.trim()) {
    ElMessage.warning('请输入转录文本')
    return
  }
  uploading.value = true
  try {
    await store.upload(props.projectId, audioFile.value, transcript.value)
    ElMessage.success('上传成功')
    emit('uploaded')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.upload-panel { max-width: 600px; }
.upload-tip { padding: 20px; text-align: center; }
.hint { color: #999; font-size: 12px; margin-top: 4px; }
</style>
