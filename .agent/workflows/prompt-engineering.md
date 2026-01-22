---
description: 如何修改提示词并测试生成质量
---

# 提示词工程指南

## 提示词文件位置

| 模块 | 文件 | 变量名 |
|------|------|--------|
| 3.1 意图 | `backend/app/prompts/intent.py` | `INTENT_SYSTEM_PROMPT` |
| 3.3 大纲 | `backend/app/prompts/outline.py` | `OUTLINE_PLANNING_SYSTEM_PROMPT` |
| 3.4 内容 | `backend/app/modules/content/core.py` | `PAGE_CONTENT_SYSTEM_PROMPT` |
| 3.5 布局 | `backend/app/prompts/render.py` | `LAYOUT_AGENT_SYSTEM_PROMPT` |

## 提示词设计原则

### 1. 使用 XML 标签结构化
```
<task>任务描述</task>
<rules>规则约束</rules>
<examples>示例</examples>
```

### 2. 防占位符规则
始终包含明确的禁止规则：
```
❌ 错误示例（禁止）：
"bullets": ["要点1：____", "内容待填充"]
```

### 3. 示例驱动（Few-Shot）
为每种页面类型提供 2-3 个具体示例。

## 测试提示词

1. 修改提示词文件
2. 重启后端：`uvicorn app.main:app --reload`
3. 通过前端或 API 创建测试会话
4. 在终端查看 LLM 响应日志

## 内容审核

已内置于模块 3.4（`_review_and_fix_page` 函数）：
- 检查要点数量（2-6 个）
- 检测占位符残留
- 警告信息写入 `speaker_notes`
