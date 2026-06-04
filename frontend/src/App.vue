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
const transcriptLength = computed(() => transcript.value.trim().length)
const selectedKeywords = computed(() => {
  if (!selectedMeeting.value?.keywords) {
    return []
  }

  return selectedMeeting.value.keywords
    .split(',')
    .map((keyword) => keyword.trim())
    .filter(Boolean)
})

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
    <nav class="site-nav" aria-label="主导航">
      <a class="brand" href="#">
        <span class="brand-mark">AI</span>
        <span>
          <strong>Meeting Summary Lite</strong>
          <small>智能会议纪要</small>
        </span>
      </a>

      <div class="nav-links">
        <a href="#workspace">工作台</a>
        <a href="#history">历史</a>
        <a href="#result">结果</a>
      </div>

      <button class="nav-button" type="button" @click="loadMeetings">
        同步数据
      </button>
    </nav>

    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">AI Copilot</p>
        <h1>会议纪要，一键生成</h1>
        <p class="hero-text">
          粘贴转录文本，快速整理摘要、待办和关键词。
        </p>

        <div class="hero-actions">
          <a class="primary-link" href="#workspace">开始生成</a>
          <a class="ghost-link" href="#history">查看历史</a>
        </div>
      </div>

      <div class="hero-card" aria-label="数据概览">
        <div class="metric">
          <span>{{ meetings.length }}</span>
          <small>历史会议</small>
        </div>
        <div class="metric">
          <span>{{ transcriptLength }}</span>
          <small>当前字数</small>
        </div>
        <div class="metric">
          <span>{{ selectedMeeting ? '已就绪' : '待生成' }}</span>
          <small>纪要状态</small>
        </div>
      </div>
    </section>

    <section id="workspace" class="layout">
      <div class="tool-card form-panel">
        <div class="section-heading">
          <p class="eyebrow">Create</p>
          <h2>新建会议</h2>
        </div>

        <div class="field">
          <label for="title">会议标题</label>
          <input
            id="title"
            v-model="title"
            type="text"
            placeholder="例如：产品周会"
          />
        </div>

        <div class="field">
          <div class="field-top">
            <label for="transcript">会议转录文本</label>
            <span>{{ transcriptLength }} 字</span>
          </div>
          <textarea
            id="transcript"
            v-model="transcript"
            rows="12"
            placeholder="粘贴会议录音转写后的文本..."
          ></textarea>
        </div>

        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

        <button
          class="primary-button"
          type="button"
          :disabled="loading"
          @click="createMeeting"
        >
          {{ loading ? '生成中...' : '生成会议纪要' }}
        </button>
      </div>

      <div id="history" class="tool-card history-panel">
        <div class="panel-header">
          <div>
            <p class="eyebrow">History</p>
            <h2>历史会议</h2>
          </div>
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
          <span class="meeting-title">{{ meeting.title }}</span>
          <span class="meeting-date">{{ formatDate(meeting.created_at) }}</span>
        </button>
      </div>

      <div id="result" class="tool-card detail-panel">
        <template v-if="selectedMeeting">
          <div class="detail-header">
            <div>
              <p class="eyebrow">Result</p>
              <h2>{{ selectedMeeting.title }}</h2>
            </div>
            <time>{{ formatDate(selectedMeeting.created_at) }}</time>
          </div>

          <div class="result-grid">
            <article class="result-card summary-card">
              <h3>摘要</h3>
              <p>{{ selectedMeeting.summary }}</p>
            </article>

            <article class="result-card">
              <h3>待办事项</h3>
              <p class="pre-line">{{ selectedMeeting.action_items }}</p>
            </article>

            <article class="result-card">
              <h3>关键词</h3>
              <div class="keywords">
                <span v-for="keyword in selectedKeywords" :key="keyword">
                  {{ keyword }}
                </span>
              </div>
            </article>

            <article class="result-card transcript-card">
              <h3>原始转录文本</h3>
              <p class="transcript">{{ selectedMeeting.transcript }}</p>
            </article>
          </div>
        </template>

        <div v-else class="empty detail-empty">
          <span>AI 输出区</span>
          <strong>创建或选择一场会议后，这里会显示会议详情。</strong>
        </div>
      </div>
    </section>
  </main>
</template>
