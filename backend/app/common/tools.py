"""工具函数模块 - 支持模型自主调用外部工具（如联网搜索）"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx


# ============================================================================
# 工具定义
# ============================================================================

def get_web_search_tool_definition() -> Dict[str, Any]:
    """返回联网搜索工具的定义（OpenAI工具调用格式）"""
    return {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "在互联网上搜索相关信息。当需要获取最新的知识点信息、教学案例、专业术语解释、行业标准等内容时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询关键词，应包含核心概念和上下文信息。例如：'液压传动原理 高职教学'、'护理静脉输液操作步骤'"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "返回的最大结果数量，默认3",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        }
    }


async def execute_web_search(query: str, max_results: int = 3) -> Dict[str, Any]:
    """执行联网搜索
    
    Args:
        query: 搜索查询关键词
        max_results: 最大返回结果数
        
    Returns:
        包含搜索结果的字典，格式：
        {
            "success": bool,
            "results": [
                {"title": str, "url": str, "snippet": str},
                ...
            ],
            "error": str (如果失败)
        }
    
    Note:
        支持多种搜索后端：
        1. DuckDuckGo（推荐，免费，无需API密钥）- 需要安装 ddgs: pip install ddgs
        2. Google Custom Search API（需要API密钥）
        3. Bing Search API（需要API密钥）
    """
    try:
        # 尝试使用 ddgs 库（推荐的DuckDuckGo搜索库）
        try:
            from ddgs import DDGS
            
            results = []
            with DDGS() as ddgs:
                search_results = ddgs.text(
                    query,
                    max_results=min(max_results, 10),  # 限制最大结果数
                    region='cn-zh',  # 中文区域
                )
                for r in search_results:
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", "")[:200],  # 限制摘要长度
                    })
            
            return {
                "success": True,
                "results": results[:max_results],
            }
        except ImportError:
            # 如果没有安装 duckduckgo-search，使用备用方案
            # 可以使用其他搜索API或返回提示信息
            pass
        
        # 备用方案：使用公开的搜索API或返回提示
        # 这里提供一个基于HTTP的简化实现
        # 注意：实际生产环境建议使用专业的搜索API
        
        # 方案：使用DuckDuckGo Instant Answer API（JSON格式）
        instant_url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = await client.get(instant_url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

            results = []
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", query),
                    "url": data.get("AbstractURL", ""),
                    "snippet": data.get("AbstractText", "")[:200],
                })

            # 如果有RelatedTopics，也加入结果
            if data.get("RelatedTopics"):
                for topic in data["RelatedTopics"][:2]:  # 限制数量
                    if isinstance(topic, dict) and topic.get("Text"):
                        results.append({
                            "title": topic.get("FirstURL", "").split('/')[-1] or topic.get("Text", "")[:50],
                            "url": topic.get("FirstURL", ""),
                            "snippet": topic.get("Text", "")[:150],
                        })

            # 如果Instant Answer没有结果，返回提示信息
            if not results:
                return {
                    "success": True,
                    "results": [
                        {
                            "title": f"关于'{query}'的搜索",
                            "url": f"https://duckduckgo.com/?q={query}",
                            "snippet": f"建议安装 ddgs 库以获得完整搜索功能。当前查询：{query}",
                        }
                    ],
                    "note": "当前为简化实现。建议安装 ddgs: pip install ddgs",
                }
            
            return {
                "success": True,
                "results": results[:max_results],
            }
            
    except Exception as e:
        return {
            "success": False,
            "results": [],
            "error": str(e)
        }


# ============================================================================
# 工具执行器
# ============================================================================

class ToolExecutor:
    """工具执行器 - 根据工具名称执行对应的工具函数"""
    
    def __init__(self):
        self.tools: Dict[str, callable] = {
            "web_search": execute_web_search,
        }
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行指定的工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数（JSON格式）
            
        Returns:
            工具执行结果
        """
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"未知的工具: {tool_name}"
            }
        
        try:
            func = self.tools[tool_name]
            # 根据工具函数的签名调用
            if tool_name == "web_search":
                query = arguments.get("query", "")
                max_results = arguments.get("max_results", 3)
                result = await func(query, max_results)
            else:
                result = await func(**arguments)
            
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"工具执行失败: {str(e)}"
            }
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """返回所有可用工具的定义列表"""
        return [
            get_web_search_tool_definition(),
        ]

