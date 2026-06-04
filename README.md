# 会议纪要管理网站 Lite

一个适合新手阅读的轻量级全栈示例项目：

- 前端：Vue 3 + Vite + 原生 CSS
- 后端：FastAPI + SQLModel
- 数据库：SQLite
- 摘要生成：调用 OpenAI-compatible API

## 项目结构

```text
meeting_summary_lite/
├── backend/
│   ├── main.py
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.css
│       ├── App.vue
│       └── main.js
└── README.md
```

## 启动后端

进入后端目录：

```bash
cd backend
```

创建并激活虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

配置 API Key：

```bash
cp .env.example .env
```

打开 `backend/.env`，填入你的 OpenAI-compatible API 配置：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

如果你使用其他兼容 OpenAI 接口的服务商，把 `OPENAI_BASE_URL` 和 `OPENAI_MODEL` 改成对应值即可。

启动 FastAPI：

```bash
uvicorn main:app --reload
```

后端默认运行在：

```text
http://127.0.0.1:8000
```

API 文档地址：

```text
http://127.0.0.1:8000/docs
```

首次启动时会自动创建 SQLite 数据库文件：

```text
backend/meetings.db
```

## 启动前端

打开一个新的终端，进入前端目录：

```bash
cd frontend
```

安装依赖：

```bash
npm install
```

启动 Vite：

```bash
npm run dev
```

前端默认运行在：

```text
http://127.0.0.1:5173
```

## 主要功能

- 新建会议
- 输入会议标题和转录文本
- 点击按钮调用 OpenAI-compatible API 生成会议摘要、待办事项、关键词
- 查看历史会议列表
- 查看会议详情

## API

### 创建会议

```http
POST /meetings
```

请求体：

```json
{
  "title": "产品周会",
  "transcript": "这里是会议转录文本..."
}
```

返回完整会议对象，包含模型生成的 `summary`、`action_items`、`keywords`。

### 获取会议列表

```http
GET /meetings
```

返回历史会议列表，按创建时间倒序排列。

### 获取会议详情

```http
GET /meetings/{meeting_id}
```

返回指定会议的完整信息。
