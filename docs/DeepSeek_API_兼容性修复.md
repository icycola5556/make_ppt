# DeepSeek API 兼容性修复说明

## 问题描述

在使用工具调用功能时，DeepSeek API 返回了 `400 Bad Request` 错误。

## 问题原因

1. **thinking 参数兼容性**：DeepSeek API 在使用工具调用（`tools` 参数）时，可能不支持 `thinking` 参数
2. **错误信息不够详细**：原始错误信息没有提供足够的调试信息

## 修复内容

### 1. 工具调用时禁用 thinking 参数

在 `backend/app/llm.py` 的 `chat_with_tools` 方法中：

```python
# 注意：某些API（如DeepSeek）在使用工具调用时可能不支持thinking参数
# 为了兼容性，工具调用时暂时不添加thinking参数
if thinking in ("enabled", "disabled") and not tools:
    payload["thinking"] = {"type": thinking}
```

### 2. 改进错误处理

添加了详细的错误信息，包括：
- HTTP 状态码
- 请求URL
- 响应内容预览
- 请求payload的关键信息

### 3. 改进JSON解析

在 `backend/app/workflow.py` 中，改进了工具调用后的JSON解析逻辑：
- 支持字典类型的响应
- 支持字符串类型的JSON响应
- 支持从混合文本中提取JSON
- 提供更详细的错误日志

### 4. 明确要求JSON格式

在工具调用循环的最后一次迭代时，明确要求模型返回JSON格式。

## 使用建议

### 对于DeepSeek API

1. **确保使用支持工具调用的模型**：
   - DeepSeek Chat 模型应该支持工具调用
   - 如果遇到问题，检查模型名称是否正确

2. **环境变量配置**：
   ```env
   LLM_MODE=openai
   OPENAI_BASE_URL=https://api.deepseek.com/v1
   OPENAI_API_KEY=your_deepseek_api_key
   OPENAI_MODEL=deepseek-chat  # 或其他支持工具调用的模型
   ```

3. **如果仍然遇到400错误**：
   - 检查API密钥是否有效
   - 检查模型名称是否正确
   - 查看日志中的详细错误信息
   - 可以尝试禁用工具调用功能进行测试

### 禁用工具调用进行测试

如果工具调用功能有问题，可以临时禁用：

```python
# 在 workflow.py 的 _parse_intent 方法中
req = await self._parse_intent(session_id, user_text, use_tools=False)
```

## 测试步骤

1. **测试基本功能**（不使用工具调用）：
   ```bash
   # 确保环境变量配置正确
   # 运行系统，输入测试请求
   # 检查是否正常工作
   ```

2. **测试工具调用功能**：
   ```bash
   # 确保安装了 duckduckgo-search（可选）
   pip install duckduckgo-search
   
   # 运行系统，输入包含不熟悉知识点的请求
   # 例如："给我一个关于量子计算的理论课课件"
   # 检查日志中是否有工具调用记录
   ```

3. **检查日志**：
   ```bash
   # 查看日志文件
   cat backend/data/logs/{session_id}.jsonl
   
   # 查找以下关键事件：
   # - llm_prompt: 检查 tools_enabled 是否为 true
   # - tool_calls: 检查工具调用是否成功
   # - llm_error: 检查是否有错误信息
   ```

## 常见问题

### Q: 为什么工具调用时返回400错误？

A: 可能的原因：
1. API不支持工具调用功能（检查模型是否支持）
2. 请求格式不正确（已修复）
3. API密钥或配置问题

### Q: 如何确认DeepSeek API是否支持工具调用？

A: 
1. 查看DeepSeek官方文档
2. 尝试使用简单的工具调用测试
3. 检查API响应中的错误信息

### Q: 如果DeepSeek不支持工具调用怎么办？

A: 
1. 可以禁用工具调用功能（`use_tools=False`）
2. 使用其他支持工具调用的API（如OpenAI GPT-4）
3. 等待DeepSeek更新支持工具调用

## 后续优化建议

1. **API兼容性检测**：可以添加API兼容性检测功能，自动判断是否支持工具调用
2. **降级策略**：如果工具调用失败，自动降级到不使用工具的模式
3. **错误重试**：对于临时性错误，可以添加重试机制

## 相关文件

- `backend/app/llm.py`: LLM客户端，包含工具调用逻辑
- `backend/app/workflow.py`: 工作流引擎，包含意图理解逻辑
- `backend/app/tools.py`: 工具定义和执行器

