from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

import httpx


def env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    if v is None or v == "":
        return default
    return v


class LLMClient:
    """OpenAI-compatible Chat Completions client.

    Env:
      - LLM_MODE: "openai" or "mock" (default: mock)
      - OPENAI_API_KEY
      - OPENAI_BASE_URL (default: https://api.openai.com/v1)
      - OPENAI_MODEL (default: gpt-4o-mini)

    Notes:
      - Works with OpenAI and any compatible gateway.
      - In mock mode, no network calls are made.
    """

    def __init__(self):
        self.mode = env("LLM_MODE", "mock")
        self.base_url = env("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.api_key = env("OPENAI_API_KEY", "")
        self.model = env("OPENAI_MODEL", "gpt-4o-mini")

    def is_enabled(self) -> bool:
        return self.mode != "mock" and bool(self.api_key)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        thinking: Optional[str] = "enabled",
    ) -> str:
        """Standard chat completion returning text string."""
        if not self.is_enabled():
            raise RuntimeError("LLM disabled")

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if thinking in ("enabled", "disabled"):
            payload["thinking"] = {"type": thinking}

        async with httpx.AsyncClient(timeout=180.0, proxy=None) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()

        return data["choices"][0]["message"].get("content") or ""

    async def chat_json(
        self,
        system: str,
        user: str,
        json_schema_hint: str,
        temperature: float = 0.2,
        thinking: Optional[str] = "enabled",  # "enabled" | "disabled" | None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Return (parsed_json, raw_response_meta)."""

        if not self.is_enabled():
            # Caller should fall back to heuristic.
            raise RuntimeError("LLM disabled (mock mode or missing OPENAI_API_KEY).")

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        # DeepSeek JSON mode：prompt 里必须明确要求输出 json（官方建议）:contentReference[oaicite:5]{index=5}
        system2 = system.strip() + "\n\nYou MUST output valid JSON only."
        user2 = (
                user
                + "\n\nReturn JSON only. JSON schema hint:\n"
                + json_schema_hint
        )
        payload = {
            "model": self.model,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system2},
                {"role": "user", "content": user2 + "\n\nJSON schema hint:\n" + json_schema_hint},
            ],
        }
        # DeepSeek thinking mode（两种方式：reasoner模型 or thinking参数）:contentReference[oaicite:6]{index=6}
        # 这里给你一个“可控开关”：即使不是 reasoner，也可以显式开/关
        if thinking in ("enabled", "disabled"):
            payload["thinking"] = {"type": thinking}

        async with httpx.AsyncClient(timeout=180.0) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()

        msg = data["choices"][0]["message"]
        content = msg.get("content") or ""
        reasoning_content = msg.get(
            "reasoning_content")  # reasoner模型会带这个字段（用于日志回放）:contentReference[oaicite:7]{index=7}

        #解析 JSON
        try:
            parsed = json.loads(content)
        except Exception as e:
            raise RuntimeError(f"LLM returned non-JSON content: {content[:200]}... ({e})")

        meta = {
            "model": data.get("model"),
            "id": data.get("id"),
            "usage": data.get("usage"),
            "raw_content": content,
            "reasoning_content": reasoning_content,  # ✅写日志用
            "thinking": payload.get("thinking"),
        }
        return parsed, meta

    async def chat_with_tools(
        self,
        system: str,
        user: str,
        tools: List[Dict[str, Any]],
        tool_executor: Optional[Any] = None,
        max_iterations: int = 5,
        temperature: float = 0.2,
        thinking: Optional[str] = "enabled",
    ) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
        """支持工具调用的对话方法
        
        Args:
            system: 系统提示词
            user: 用户输入
            tools: 工具定义列表（OpenAI工具调用格式）
            tool_executor: 工具执行器实例
            max_iterations: 最大迭代次数（防止无限循环）
            temperature: 温度参数
            thinking: 思考模式
            
        Returns:
            (final_response, meta, tool_calls_history)
            - final_response: 最终响应内容（可能是JSON或文本）
            - meta: 元数据
            - tool_calls_history: 工具调用历史记录
        """
        if not self.is_enabled():
            raise RuntimeError("LLM disabled (mock mode or missing OPENAI_API_KEY).")
        
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        
        tool_calls_history: List[Dict[str, Any]] = []
        iteration = 0
        
        while iteration < max_iterations:
            payload = {
                "model": self.model,
                "temperature": temperature,
                "messages": messages,
            }
            
            # 只有在有工具时才添加tools参数
            if tools:
                payload["tools"] = tools
            
            # 注意：某些API（如DeepSeek）在使用工具调用时可能不支持thinking参数
            # 这里只在非工具调用场景下添加thinking参数，或者根据API类型判断
            # 为了兼容性，工具调用时暂时不添加thinking参数
            if thinking in ("enabled", "disabled") and not tools:
                payload["thinking"] = {"type": thinking}
            
            async with httpx.AsyncClient(timeout=180.0, proxy=None) as client:
                try:
                    r = await client.post(url, headers=headers, json=payload)
                    r.raise_for_status()
                    data = r.json()
                except httpx.HTTPStatusError as e:
                    # 记录详细的错误信息以便调试
                    error_detail = {
                        "status_code": e.response.status_code,
                        "url": str(e.request.url),
                        "response_text": e.response.text[:500] if e.response.text else None,
                        "payload_keys": list(payload.keys()),
                        "has_tools": bool(tools),
                        "tools_count": len(tools) if tools else 0,
                    }
                    raise RuntimeError(
                        f"API请求失败 (HTTP {e.response.status_code}): {e.response.text[:200] if e.response.text else '无响应内容'}\n"
                        f"详细信息: {error_detail}"
                    ) from e
            
            msg = data["choices"][0]["message"]
            content = msg.get("content") or ""
            tool_calls = msg.get("tool_calls")
            reasoning_content = msg.get("reasoning_content")
            
            # 将助手的响应添加到消息历史
            assistant_msg: Dict[str, Any] = {"role": "assistant", "content": content}
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            messages.append(assistant_msg)
            
            # 如果没有工具调用，返回最终响应
            if not tool_calls:
                meta = {
                    "model": data.get("model"),
                    "id": data.get("id"),
                    "usage": data.get("usage"),
                    "raw_content": content,
                    "reasoning_content": reasoning_content,
                    "thinking": payload.get("thinking"),
                    "iterations": iteration + 1,
                }
                return content, meta, tool_calls_history
            
            # 执行工具调用
            if not tool_executor:
                raise RuntimeError("工具调用需要提供 tool_executor 参数")
            
            for tool_call in tool_calls:
                tool_id = tool_call.get("id")
                tool_name = tool_call["function"]["name"]
                tool_args_str = tool_call["function"]["arguments"]
                
                try:
                    tool_args = json.loads(tool_args_str)
                except json.JSONDecodeError:
                    tool_args = {}
                
                # 执行工具
                tool_result = await tool_executor.execute(tool_name, tool_args)
                
                # 记录工具调用历史
                tool_calls_history.append({
                    "tool_name": tool_name,
                    "arguments": tool_args,
                    "result": tool_result,
                })
                
                # 将工具结果添加到消息历史
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                })
            
            # 在最后一次迭代时，明确要求返回JSON格式
            if iteration == max_iterations - 1:
                messages.append({
                    "role": "user",
                    "content": "请根据以上信息，返回符合schema的JSON对象。只返回JSON，不要包含任何解释。"
                })
            
            iteration += 1
        
        # 如果达到最大迭代次数，返回最后一次响应
        meta = {
            "model": data.get("model"),
            "id": data.get("id"),
            "usage": data.get("usage"),
            "raw_content": content,
            "reasoning_content": reasoning_content,
            "thinking": payload.get("thinking"),
            "iterations": iteration,
            "warning": f"达到最大迭代次数 {max_iterations}",
        }
        return content, meta, tool_calls_history
