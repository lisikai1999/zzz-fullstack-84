import { ref, watch, onUnmounted } from 'vue'
import type { Ref } from 'vue'

export function useWebSocket(taskId: Ref<string | null>) {
  const progress = ref(0)
  const status = ref<'pending' | 'running' | 'completed' | 'failed'>('pending')
  let ws: WebSocket | null = null

  function connect(id: string) {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    ws = new WebSocket(`${protocol}//${location.host}/ws/progress/${id}`)
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      progress.value = data.progress
      status.value = data.status
    }
    ws.onclose = () => { ws = null }
  }

  function disconnect() {
    if (ws) {
      ws.close()
      ws = null
    }
  }

  watch(taskId, (id) => {
    disconnect()
    if (id) connect(id)
  }, { immediate: true })

  onUnmounted(disconnect)

  return { progress, status }
}
