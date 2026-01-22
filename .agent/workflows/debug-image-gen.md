---
description: 如何排查图片生成问题
---

# 图片生成问题排查

## 快速诊断

运行以下命令直接测试 DashScope API：

```bash
cd backend
source .venv/bin/activate
// turbo
python -m app.modules.render.tests.test_image_api
```

## 成功时的输出
```
Status: 200
Code: None
Output: {"task_status": "SUCCEEDED", "results": [{"url": "https://..."}]}
```

## 常见问题

### 1. API Key 缺失
检查 `backend/.env` 文件：
```
DASHSCOPE_API_KEY=sk-xxx
```

### 2. 模型未开通
登录百炼控制台，开通 `qwen-image-plus` 模型

### 3. 日志追踪
`image_filler.py` 中已增强日志：
- `[IMG_GEN_START]` - 启动检查（API Key 状态）
- `[IMG_GEN_API]` - API 响应详情
- `[IMG_GEN_SUCCESS/ERROR]` - 结果状态

## 关键文件
- `backend/app/modules/render/image_filler.py` - 图片生成逻辑
- `backend/app/modules/render/tests/test_image_api.py` - 诊断脚本
