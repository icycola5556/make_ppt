---
description: 项目架构与模块职责说明
---

# PPT 生成工作流架构

## 模块流水线

```
3.1 意图理解 → 3.2 风格设计 → 3.3 大纲生成 → 3.4 内容生成 → 3.5 HTML 渲染
```

## 各模块关键文件

### 模块 3.1 - 意图理解
- `backend/app/prompts/intent.py` - 意图提取提示词
- `backend/app/common/schemas.py` - TeachingRequest 数据结构

### 模块 3.2 - 风格设计  
- `backend/app/modules/style/` - 风格选择逻辑
- 无 LLM 提示词（基于规则匹配）

### 模块 3.3 - 大纲生成
- `backend/app/prompts/outline.py` - 大纲生成提示词
- `backend/app/common/schemas.py` - PPTOutline 数据结构

### 模块 3.4 - 内容生成
- `backend/app/modules/content/core.py` - 内容生成 + 内置审核
- `PAGE_CONTENT_SYSTEM_PROMPT` - 逐页生成提示词

### 模块 3.5 - HTML 渲染
- `backend/app/modules/render/html_renderer.py` - Jinja2 模板渲染
- `backend/app/modules/render/layout_engine.py` - 布局选择（含防重复）
- `backend/app/modules/render/layout_configs.py` - 10 种布局定义
- `backend/app/modules/render/image_filler.py` - DashScope 图片生成
- `backend/app/prompts/render.py` - Layout Agent 提示词

## 流程编排
- `backend/app/orchestrator/engine.py` - WorkflowEngine（主引擎）
- `backend/scripts/graph_langgraph.py` - LangGraph 版本

## 数据结构
所有 Pydantic 模型定义在 `backend/app/common/schemas.py`：
- TeachingRequest, StyleConfig, PPTOutline, SlideDeckContent, SlidePage, SlideElement
