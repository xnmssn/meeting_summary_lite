<script setup>
import { computed, onMounted, ref } from 'vue'

const API_BASE_URL = 'http://127.0.0.1:8000'

const meetings = ref([])
const selectedMeeting = ref(null)
const title = ref('')
const transcript = ref('')
const loading = ref(false)
const errorMessage = ref('')

const hasMeetings = computed(() => meetings.value.length > 0)

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json'
    },
    ...options
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || '请求失败，请稍后再试')
  }

  return response.json()
}

async function loadMeetings() {
  meetings.value = await request('/meetings')
}

async function createMeeting() {
  errorMessage.value = ''

  if (!title.value.trim()) {
    errorMessage.value = '请输入会议标题'
    return
  }

  if (!transcript.value.trim()) {
    errorMessage.value = '请输入会议转录文本'
    return
  }

  loading.value = true

  try {
    const meeting = await request('/meetings', {
      method: 'POST',
      body: JSON.stringify({
        title: title.value,
        transcript: transcript.value
      })
    })

    title.value = ''
    transcript.value = ''
    selectedMeeting.value = meeting
    await loadMeetings()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

async function selectMeeting(meetingId) {
  errorMessage.value = ''

  try {
    selectedMeeting.value = await request(`/meetings/${meetingId}`)
  } catch (error) {
    errorMessage.value = error.message
  }
}

function formatDate(value) {
  return new Date(value).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(async () => {
  try {
    await loadMeetings()
  } catch (error) {
    errorMessage.value = '无法连接后端服务，请先启动 FastAPI'
  }
})
</script>

<template>
  <main class="page">
    <section class="top-bar">
      <div>
        <p class="eyebrow">Meeting Summary Lite</p>
        <h1>会议纪要管理网站 Lite</h1>
      </div>
      <p class="status">{{ meetings.length }} 条历史会议</p>
    </section>

    <section class="layout">
      <div class="panel form-panel">
        <h2>新建会议</h2>

        <label for="title">会议标题</label>
        <input
          id="title"
          v-model="title"
          type="text"
          placeholder="例如：产品周会"
        />

        <label for="transcript">会议转录文本</label>
        <textarea
          id="transcript"
          v-model="transcript"
          rows="10"
          placeholder="粘贴会议录音转写后的文本..."
        ></textarea>

        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

        <button type="button" :disabled="loading" @click="createMeeting">
          {{ loading ? '生成中...' : '生成会议纪要' }}
        </button>
      </div>

      <div class="panel history-panel">
        <div class="panel-header">
          <h2>历史会议</h2>
          <button class="secondary-button" type="button" @click="loadMeetings">
            刷新
          </button>
        </div>

        <div v-if="!hasMeetings" class="empty">暂无历史会议</div>

        <button
          v-for="meeting in meetings"
          :key="meeting.id"
          type="button"
          class="meeting-item"
          :class="{ active: selectedMeeting?.id === meeting.id }"
          @click="selectMeeting(meeting.id)"
        >
          <span>{{ meeting.title }}</span>
          <small>{{ formatDate(meeting.created_at) }}</small>
        </button>
      </div>

      <div class="panel detail-panel">
        <template v-if="selectedMeeting">
          <div class="detail-header">
            <div>
              <p class="eyebrow">会议详情</p>
              <h2>{{ selectedMeeting.title }}</h2>
            </div>
            <time>{{ formatDate(selectedMeeting.created_at) }}</time>
          </div>

          <article>
            <h3>摘要</h3>
            <p>{{ selectedMeeting.summary }}</p>
          </article>

          <article>
            <h3>待办事项</h3>
            <p class="pre-line">{{ selectedMeeting.action_items }}</p>
          </article>

          <article>
            <h3>关键词</h3>
            <div class="keywords">
              <span
                v-for="keyword in selectedMeeting.keywords.split(',')"
                :key="keyword.trim()"
              >
                {{ keyword.trim() }}
              </span>
            </div>
          </article>

          <article>
            <h3>原始转录文本</h3>
            <p class="transcript">{{ selectedMeeting.transcript }}</p>
          </article>
        </template>

        <div v-else class="empty detail-empty">
          创建或选择一场会议后，这里会显示会议详情。
        </div>
      </div>
    </section>
  </main>
</template>

