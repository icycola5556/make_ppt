---
description: 如何启动 PPT 生成工作流项目
---

# 启动项目

## 前置条件
- Python 3.9+ 并配置 venv
- Node.js 18+
- DashScope API Key（配置在 `backend/.env`）

## 后端

```bash
cd backend
source .venv/bin/activate
// turbo
uvicorn app.main:app --reload --port 8000
```

## 前端

```bash
cd frontend
// turbo
npm run dev
```

## 关键环境变量

后端 `.env` 文件：
```
DASHSCOPE_API_KEY=sk-xxx
LLM_MODE=openai_compatible
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

## 健康检查
```bash
// turbo
curl http://localhost:8000/api/health
```
