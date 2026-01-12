# AI生成PPT（模块3.1–3.3）闭环工作流 Demo

> 目标：严格对齐《AI生成PPT技术方案》中的 **3.1 意图理解**、**3.2 风格设计**、**3.3 大纲生成**，并实现“交互补全优先、LLM可审校、全链路日志输出”的可运行系统。

本Demo提供：
- **后端**：FastAPI +（可选）OpenAI兼容LLM调用 + 结构化日志JSONL
- **前端**：Vue 3 + Vite（可交互），支持 build 后由后端静态托管
- **输出**：生成的标准化 TeachingRequest、StyleConfig、PPTOutline（逐页大纲）
- **日志**：每一步输入/输出、LLM提示词/回复（元信息）都会写入 `backend/data/logs/<session>.jsonl`

> 说明：本仓库只实现到 3.3（大纲），后续 3.4+ 的页面内容生成、网页渲染、素材适配、pptx导出不包含在本Demo里。

---

## 目录结构

```
pptgen_workflow/
  backend/
    app/                 # FastAPI源码
    data/                # sessions/ logs/
    requirements.txt
  frontend/              # 静态前端（后端会直接托管）
  README.md
```

---

## 快速开始

### 1) 运行（Mock模式，不需要LLM）

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000
```

浏览器打开：
- http://localhost:8000

> Mock模式下会用启发式解析 + 模板化生成，确保可运行。

### 2) 运行（OpenAI兼容LLM模式）

在 `backend/` 下创建 `.env`：

```env
LLM_MODE=openai
OPENAI_API_KEY=你的key
# 如果你是第三方网关（如公司代理/自建兼容接口），填自己的base_url
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

然后同样启动 uvicorn。

---

## 工作流说明（严格对齐方案 3.1–3.3）

### 模块 3.1：意图理解 + 需求校验与补全
- 先用 LLM（或启发式）抽取 TeachingRequest
- 校验必填项（学科/知识点/教学场景）
- **优先交互提问**：前端会展示问题表单
- 用户也可点击“使用默认补全并继续”（按方案：理论课默认含知识/素养，实训课默认含能力）

### 模块 3.2：整体风格设计
- 根据教学场景选择风格模板（理论/实训/复习）
- 产出 StyleConfig + 3页样例（封面/内容/步骤）
- 若开启LLM，可对 StyleConfig 做一次审校/微调

### 模块 3.3：生成PPT大纲
- 根据场景模板生成 slide-by-slide outline（含类型、标题、要点、互动、素材占位符）
- 若开启LLM，可在 **不改变 slide 数量、不改变 slide_type** 的前提下优化表达

---

## 日志

- 访问：`GET /api/logs/{session_id}`
- 内容：JSONL，一行一个事件（含 stage/kind/payload）
- 重点事件类型：
  - `3.1/llm_prompt`, `3.1/llm_response`, `3.1/heuristic_parse`, `3.1/user_answers`, `3.1/autofill_defaults`
  - `3.2/style_base`, `3.2/llm_prompt`, `3.2/llm_response`
  - `3.3/outline_base`, `3.3/llm_prompt`, `3.3/llm_response`

---

## API一览

- `POST /api/session` → 创建会话
- `POST /api/workflow/run` → 运行工作流（可能返回 need_user_input）
- `GET /api/session/{session_id}` → 获取当前状态
- `GET /api/logs/{session_id}` → 下载日志

---

## 下一步（你后续要扩展的点）

1. **接入模板解析/数据库**：将 TeachingRequest、StyleConfig、Outline 存入 MySQL；
2. **3.4 内容生成**：按大纲逐页生成正文 + 图表配置 + 布局树；
3. **3.5 网页渲染**：将布局树渲染为 reveal.js / PPTXJS 的 DOM；
4. **3.6 素材适配**：接入 MinIO 素材库 + 图像生成；
5. **3.7 导出pptx**：DOM→PPT元素映射，或直接用 PptxGenJS 生成。

---

## 可选：用 LangGraph 编排

见 `backend/app/graph_langgraph.py`：
- 提供 `build_graph()` 示例，把 3.1–3.3 映射为 LangGraph 节点与条件边。
- 你可以在 `workflow.py` 中将现有节点函数（parse/validate/style/outline）包装后接入 LangGraph。
---

## 前端运行（Vue）

### 开发模式（推荐用于二次开发）
```bash
cd frontend
npm install
npm run dev
```
然后访问：
- http://localhost:5173

> 默认后端地址为 `http://localhost:8000`。如需修改，可在 `frontend/.env` 设置 `VITE_API_BASE`。

### 生产模式（后端托管 dist）
```bash
cd frontend
npm install
npm run build
```
生成 `frontend/dist` 后，直接启动后端：
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
访问：
- http://localhost:8000
