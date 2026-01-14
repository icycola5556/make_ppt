# AI生成PPT系统

> 基于 LLM + 多模块协作的智能课件生成工作流

本项目实现《AI生成PPT技术方案》中的 **3.1-3.7 模块**，提供从意图理解到 PPTX 导出的完整工作流。

---

## 核心功能

| 模块 | 功能 | 状态 |
|------|------|------|
| **3.1 意图理解** | 解析用户输入、提取教学需求、交互补全 | ✅ 已实现 |
| **3.2 风格设计** | 场景驱动风格匹配、专业配色适配 | ✅ 已实现 |
| **3.3 大纲生成** | 智能页面规划、教学逻辑编排 | ✅ 已实现 |
| **3.4 内容生成** | 逐页内容生成、LLM优化 | ✅ 已实现 |
| **3.5 网页渲染** | HTML/reveal.js 渲染 | 🚧 规划中 |
| **3.6 素材匹配** | 知识库检索、AI素材生成 | 🚧 规划中 |
| **3.7 PPTX导出** | 格式转换、样式保持 | 🚧 规划中 |

---

## 项目结构

```
pptgen_workflow/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI 入口
│   │   │
│   │   ├── common/                 # 公共模块
│   │   │   ├── schemas.py          # 共享数据结构
│   │   │   ├── llm_client.py       # LLM 调用封装
│   │   │   ├── logger.py           # 日志工具
│   │   │   ├── store.py            # 会话存储
│   │   │   └── tools.py            # 工具定义
│   │   │
│   │   ├── modules/                # 业务模块
│   │   │   ├── intent/             # 3.1 意图理解
│   │   │   ├── style/              # 3.2 风格设计
│   │   │   ├── outline/            # 3.3 大纲生成
│   │   │   ├── content/            # 3.4 内容生成
│   │   │   ├── render/             # 3.5 网页渲染
│   │   │   ├── asset/              # 3.6 素材匹配
│   │   │   └── export/             # 3.7 PPTX导出
│   │   │
│   │   └── orchestrator/           # 工作流编排
│   │       ├── engine.py           # WorkflowEngine
│   │       └── prompts.py          # Prompt 模板
│   │
│   ├── data/                       # 会话数据/日志
│   └── requirements.txt
│
├── frontend/                       # Vue 3 + Vite 前端
├── docs/                           # 技术文档
└── README.md
```

---

## 快速开始

### 1. 后端启动

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Mock 模式（无需 LLM）
uvicorn app.main:app --reload --port 8000

# 或 LLM 模式（需配置 .env）
```

### 2. 前端启动（开发模式）

```bash
cd frontend
npm install
npm run dev
```

访问：http://localhost:5173

### 3. 配置 LLM（可选）

在 `backend/.env` 中配置：

```env
LLM_MODE=openai
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

---

## API 接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/session` | POST | 创建会话 |
| `/api/workflow/run` | POST | 运行工作流 |
| `/api/session/{session_id}` | GET | 获取会话状态 |
| `/api/logs/{session_id}` | GET | 下载日志 |

---

## 工作流说明

### 模块 3.1：意图理解

- LLM/启发式解析用户输入
- 校验必填项（学科/知识点/教学场景）
- 交互式问题补全

### 模块 3.2：风格设计

- 基于教学场景选择模板（理论/实训/复习）
- 17 套专业配色方案
- 生成风格样例页预览

### 模块 3.3：大纲生成

- 智能页面分配算法
- 12 种页面类型支持
- LLM 智能规划优化

### 模块 3.4：内容生成

- 逐页内容生成
- 8 种元素类型支持
- LLM 内容优化

---

## 技术栈

- **后端**: Python 3.11+ / FastAPI / Pydantic
- **前端**: Vue 3 / Vite
- **LLM**: OpenAI 兼容接口
- **文档**: Markdown

---

## 日志

- 路径: `backend/data/logs/<session>.jsonl`
- 格式: JSONL（每行一个事件）
- 内容: 各阶段输入/输出、LLM 提示词/回复

---

## 开发指南

### 模块开发

每个模块在 `modules/` 下独立目录，通过 `__init__.py` 导出公开接口：

```python
# modules/style/__init__.py
from .core import choose_style, build_style_samples

__all__ = ["choose_style", "build_style_samples"]
```

### 新增模块

1. 在 `modules/` 下创建目录
2. 实现核心逻辑
3. 在 `__init__.py` 导出公开函数
4. 在 `orchestrator/engine.py` 中集成

---

## 许可证

MIT License
