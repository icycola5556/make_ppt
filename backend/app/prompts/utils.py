"""
Prompt Engineering Utilities
借鉴 banana-slides 的 XML 上下文管理模式
"""
import json
from typing import Optional, Dict, Any, List


def format_context_xml(
    teaching_request: Optional[Dict[str, Any]] = None,
    style_config: Optional[Dict[str, Any]] = None,
    outline: Optional[List[Dict[str, Any]]] = None,
    additional_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    使用 XML 标签包装上下文，提升 LLM 解析准确性
    
    借鉴自 banana-slides 的 _format_reference_files_xml 模式
    
    Args:
        teaching_request: 教学需求对象
        style_config: 风格配置对象  
        outline: PPT大纲
        additional_context: 其他上下文信息
        
    Returns:
        XML 格式的上下文字符串
    """
    parts = ['<context>']
    
    if teaching_request:
        parts.append('  <teaching_request>')
        parts.append(f'    {json.dumps(teaching_request, ensure_ascii=False, indent=2)}')
        parts.append('  </teaching_request>')
    
    if style_config:
        parts.append('  <style_config>')
        parts.append(f'    {json.dumps(style_config, ensure_ascii=False, indent=2)}')
        parts.append('  </style_config>')
    
    if outline:
        parts.append('  <outline>')
        parts.append(f'    {json.dumps(outline, ensure_ascii=False, indent=2)}')
        parts.append('  </outline>')
    
    if additional_context:
        parts.append('  <additional>')
        parts.append(f'    {json.dumps(additional_context, ensure_ascii=False, indent=2)}')
        parts.append('  </additional>')
    
    parts.append('</context>')
    return '\n'.join(parts)


def get_language_instruction(language: str = 'zh') -> str:
    """
    获取语言限制指令文本
    
    借鉴自 banana-slides 的 get_language_instruction
    
    Args:
        language: 语言代码 ('zh', 'en', 'ja', 'auto')
        
    Returns:
        语言限制指令
    """
    LANGUAGE_CONFIG = {
        'zh': '请使用全中文输出。',
        'en': 'Please output all in English.',
        'ja': 'すべて日本語で出力してください。',
        'auto': ''  # 自动模式不添加语言限制
    }
    return LANGUAGE_CONFIG.get(language, LANGUAGE_CONFIG['zh'])


def wrap_user_input(user_text: str) -> str:
    """
    使用 XML 标签包装用户输入
    
    Args:
        user_text: 用户原始输入文本
        
    Returns:
        XML 包装后的用户输入
    """
    return f"""<user_input>
{user_text}
</user_input>"""


def build_json_constraint(return_only: bool = True) -> str:
    """
    构建 JSON 输出约束指令
    
    Args:
        return_only: 是否仅返回 JSON（无其他文字）
        
    Returns:
        约束指令字符串
    """
    if return_only:
        return "Return ONLY valid JSON, no explanation or other text."
    return "Output in valid JSON format."
