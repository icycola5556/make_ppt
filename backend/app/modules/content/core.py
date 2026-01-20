from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional, Tuple

from ...common.llm_client import LLMClient
from ...common.logger import WorkflowLogger
from ...common.schemas import PPTOutline, OutlineSlide, SlideDeckContent, SlideElement, SlidePage, StyleConfig, TeachingRequest


# ============================================================================
# Per-Page Content Generation Prompt (方案B: 逐页生成)
# ============================================================================

PAGE_CONTENT_SYSTEM_PROMPT = """你是高职课程PPT内容生成助手。

任务：为PPT的**单个页面**生成详细内容。

你会收到：
1. **完整大纲** (full_outline)：整个PPT的结构，帮助你理解上下文
2. **当前页大纲** (current_page_outline)：这一页的标题、要点、类型
3. **教学需求** (teaching_request)：课程背景信息
4. **基础页面** (base_page)：布局参考（可选）

输出：这一页的完整 SlidePage（JSON格式）

---

🚨🚨🚨 **通用规则** 🚨🚨🚨

**current_page_outline.bullets 是你的内容来源！**
- 不要自己发明新内容
- 根据 slide_type 决定处理策略

---

## 📋 各页面类型处理规则

### 🔴 exercises / quiz（习题页）—— 特殊处理！

**输出 type="quiz" 元素，包含结构化的题目+答案：**

```json
{
  "type": "quiz",
  "content": {
    "questions": [
      {"question": "题目1原文", "answer": "该题目的参考答案"},
      {"question": "题目2原文", "answer": "该题目的参考答案"}
    ],
    "scoring": "评分标准原文（如有）"
  }
}
```

**规则**：
- `question` 字段：100% 保留大纲中的题目原文
- `answer` 字段：根据题目内容生成合理的参考答案
- `scoring` 字段：保留评分标准原文

---

### 🔴 其他必须保留的类型：

#### objectives / agenda（教学目标页）
- **100% 保留目标条目**，不要改写

#### summary（总结页）
- **保留原始总结要点**

#### warning（注意事项页）
- **保留所有警告/注意事项**

---

### 🟡 可以适度扩展的类型：

#### concept / theory（概念讲解页）
- 可扩展为更详细描述，每条 15-25 字
- 可添加右侧示意图

#### steps / practice（操作步骤页）
- **保留步骤编号和顺序**，可补充细节

---

## 📐 页面元素定位（16:9画布）

- 标题区：x=0.06, y=0.06, w=0.88, h=0.12
- 内容区：x=0.06, y=0.20, w=0.88, h=0.72

---

## 📝 exercises 完整示例

**输入**：
```json
{
  "slide_type": "exercises",
  "title": "习题巩固",
  "bullets": [
    "题目1：简述液压传动系统的工作原理，并说明帕斯卡定律的作用",
    "题目2：列出三种常见液压泵的类型并比较其适用场合",
    "评分标准：概念准确40%、逻辑清晰30%、术语规范30%"
  ]
}
```

**✅ 正确输出**：
```json
{
  "index": 12,
  "slide_type": "exercises",
  "title": "习题巩固",
  "layout": {"template": "one-column"},
  "elements": [
    {"id": "title-001", "type": "text", "x": 0.06, "y": 0.06, "w": 0.88, "h": 0.12, 
     "content": {"text": "习题巩固", "role": "title"}, "style": {"role": "title"}},
    {"id": "quiz-001", "type": "quiz", "x": 0.06, "y": 0.20, "w": 0.88, "h": 0.72,
     "content": {
       "questions": [
         {
           "question": "题目1：简述液压传动系统的工作原理，并说明帕斯卡定律的作用",
           "answer": "液压传动通过密闭容积内液体传递动力，将机械能转换为液压能再转换回机械能。帕斯卡定律指出静止液体中任一点的压强向各方向相等传递，使系统能够实现力的放大和远程传递。"
         },
         {
           "question": "题目2：列出三种常见液压泵的类型并比较其适用场合",
           "answer": "①齿轮泵：结构简单、价格低，适用于低压大流量场合；②叶片泵：输出流量平稳，适用于中压精密控制系统；③柱塞泵：压力高、效率高，适用于高压重载系统。"
         }
       ],
       "scoring": "概念准确40%、逻辑清晰30%、术语规范30%"
     }, "style": {"role": "body"}}
  ],
  "speaker_notes": "引导学生先独立思考，5分钟后点击显示答案进行讲解。"
}
```

只输出这一页的 SlidePage JSON，不要解释。"""


# Legacy batch prompt (kept for reference, not used in new implementation)
CONTENT_SYSTEM_PROMPT = PAGE_CONTENT_SYSTEM_PROMPT




def _title_el(title: str) -> SlideElement:
    return SlideElement(
        id=str(uuid.uuid4()),
        type="text",
        x=0.06,
        y=0.06,
        w=0.88,
        h=0.12,
        content={"text": title, "role": "title"},
        style={"role": "title"},
    )


def _bullets_el(bullets: List[str]) -> SlideElement:
    return SlideElement(
        id=str(uuid.uuid4()),
        type="bullets",
        x=0.06,
        y=0.20,
        w=0.60,
        h=0.72,
        content={"items": bullets, "role": "body"},
        style={"role": "body"},
    )


def _right_placeholder(kind: str, theme: str) -> SlideElement:
    # Generic placeholder for images/diagrams/charts. Module 3.5 will render this block.
    return SlideElement(
        id=str(uuid.uuid4()),
        type="image" if kind == "image" else ("diagram" if kind == "diagram" else "chart"),
        x=0.70,
        y=0.20,
        w=0.24,
        h=0.72,
        content={
            "placeholder": True,
            "kind": kind,
            "theme": theme,
            "prompt": f"{theme}（教学示意图/结构图/流程图，风格简洁清晰）",
        },
        style={"role": "visual"},
    )


def build_base_deck(req: TeachingRequest, style: StyleConfig, outline: PPTOutline) -> SlideDeckContent:
    """Deterministic base pages for Module 3.4 (works even without LLM)."""
    pages: List[SlidePage] = []
    for s in outline.slides:
        els: List[SlideElement] = [_title_el(s.title)]

        # Base mapping by slide_type
        st = (s.slide_type or "").lower()

        if st == "cover":
            # Cover: title + meta lines
            els.append(
                SlideElement(
                    id=str(uuid.uuid4()),
                    type="text",
                    x=0.06,
                    y=0.22,
                    w=0.88,
                    h=0.20,
                    content={
                        "text": f"学科：{req.subject or outline.subject or '_____'}\n知识点：{', '.join(outline.knowledge_points) if outline.knowledge_points else '_____'}\n课时：{req.lesson_duration_min or '____'} 分钟",
                        "role": "subtitle",
                    },
                    style={"role": "subtitle"},
                )
            )
        elif st in ("agenda", "objectives"):
            els.append(_bullets_el(s.bullets or ["_____"]))
        elif st in ("steps", "warning"):
            # steps: left steps bullets + right visual placeholder
            els.append(_bullets_el(s.bullets or ["步骤1：_____", "步骤2：_____", "步骤3：_____"]))
            els.append(_right_placeholder("diagram", theme=s.title))
        elif st in ("relations", "bridge"):
            els.append(_bullets_el(s.bullets or ["关联点A—关联点B：_____", "关键联系：_____"]))
            els.append(_right_placeholder("diagram", theme="知识点关联框架"))
        elif st in ("exercises", "quiz"):
            els.append(
                SlideElement(
                    id=str(uuid.uuid4()),
                    type="quiz",
                    x=0.06,
                    y=0.20,
                    w=0.88,
                    h=0.72,
                    content={
                        "questions": s.bullets or ["题目1：_____", "题目2：_____"],
                        "answer_key": "参考答案：_____（可在讲师备注补充）",
                    },
                    style={"role": "body"},
                )
            )
        else:
            # default: bullets + optional visual placeholder if outline asks assets
            els.append(_bullets_el(s.bullets or ["_____"]))
            if s.assets:
                # choose the first asset as a placeholder
                a0 = s.assets[0]
                kind = a0.get("type", "image")
                theme = a0.get("theme", s.title)
                els.append(_right_placeholder("image" if kind == "image" else "diagram", theme=theme))

        pages.append(
            SlidePage(
                index=s.index,
                slide_type=s.slide_type,
                title=s.title,
                layout={"template": "two-column" if any(e.x > 0.65 for e in els) else "one-column"},
                elements=els,
                speaker_notes=s.notes,
            )
        )

    return SlideDeckContent(deck_title=outline.deck_title, pages=pages)


def _chunk_pages(pages: List[SlidePage], size: int) -> List[List[SlidePage]]:
    """Legacy helper - kept for backward compatibility."""
    out: List[List[SlidePage]] = []
    buf: List[SlidePage] = []
    for p in pages:
        buf.append(p)
        if len(buf) >= size:
            out.append(buf)
            buf = []
    if buf:
        out.append(buf)
    return out


# ============================================================================
# Per-Page Content Generation (方案B核心实现)
# ============================================================================

async def _generate_single_page(
    session_id: str,
    llm: LLMClient,
    logger: WorkflowLogger,
    req: TeachingRequest,
    style: StyleConfig,
    full_outline: PPTOutline,
    page_outline: OutlineSlide,
    base_page: SlidePage,
    page_index: int,
    total_pages: int,
) -> SlidePage:
    """Generate content for a single page with full outline context.
    
    This is the core of Plan B: each page receives:
    1. full_outline: The complete PPT outline for context
    2. page_outline: The specific page's outline (title, bullets, type)
    3. base_page: Layout reference (optional)
    """
    
    # 🚨 Special handling for exercises/quiz pages
    # Skip LLM and preserve original questions to prevent rewriting
    if page_outline.slide_type in ("exercises", "quiz") and page_outline.bullets:
        print(f"[DEBUG] 3.4 generate_page {page_index}: SKIPPING LLM for exercises (preserving {len(page_outline.bullets)} questions)")
        
        # Build page directly from outline bullets
        elements = [
            {
                "id": "title-001",
                "type": "text",
                "x": 0.06, "y": 0.06, "w": 0.88, "h": 0.12,
                "content": {"text": page_outline.title, "role": "title"},
                "style": {"role": "title"}
            },
            {
                "id": "bullets-001",
                "type": "bullets",
                "x": 0.06, "y": 0.20, "w": 0.88, "h": 0.72,
                "content": {"items": page_outline.bullets},
                "style": {"role": "body"}
            }
        ]
        
        return SlidePage(
            index=page_index,
            slide_type=page_outline.slide_type,
            title=page_outline.title,
            layout={"template": "one-column"},
            elements=elements,
            speaker_notes=f"习题页：请学生先独立完成后再讲解答案。"
        )
    
    schema_hint = SlidePage.model_json_schema()
    
    # Build context-rich user message
    user_payload = {
        "teaching_request": {
            "subject": req.subject,
            "professional_category": req.professional_category,
            "teaching_scene": req.teaching_scene,
            "knowledge_points": req.kp_names,
        },
        "full_outline": {
            "deck_title": full_outline.deck_title,
            "total_pages": total_pages,
            "slides_summary": [
                {"index": s.index, "title": s.title, "type": s.slide_type}
                for s in full_outline.slides
            ],
        },
        "current_page": {
            "index": page_index,
            "position": f"第 {page_index} 页 / 共 {total_pages} 页",
        },
        "current_page_outline": page_outline.model_dump(mode="json"),
        "base_page": base_page.model_dump(mode="json"),
        "style_theme": style.style_name,
    }
    
    user_msg = json.dumps(user_payload, ensure_ascii=False)
    
    logger.emit(session_id, "3.4", "llm_page_prompt", {
        "page_index": page_index,
        "slide_type": page_outline.slide_type,
        "title": page_outline.title,
    })
    
    try:
        parsed, meta = await llm.chat_json(
            PAGE_CONTENT_SYSTEM_PROMPT,
            user_msg,
            json.dumps(schema_hint, ensure_ascii=False)
        )
        logger.emit(session_id, "3.4", "llm_page_response", {
            "page_index": page_index,
            **meta
        })
        
        # Debug: Log LLM response for exercises pages
        if page_outline.slide_type in ("exercises", "quiz"):
            print(f"\n=== DEBUG: LLM 响应 (index={page_index}) ===")
            elements = parsed.get("elements", [])
            for el in elements:
                if el.get("type") in ("quiz", "bullets"):
                    print(f"Element type: {el.get('type')}")
                    print(f"Content: {el.get('content')}")
            print("=" * 50)
        
        refined_page = SlidePage.model_validate(parsed)
        
        # Ensure index is preserved
        refined_page.index = page_index
        return refined_page
        
    except Exception as e:
        logger.emit(session_id, "3.4", "llm_page_error", {
            "page_index": page_index,
            "error": str(e)
        })
        # Fallback to base page
        return base_page


async def refine_with_llm(
    session_id: str,
    llm: LLMClient,
    logger: WorkflowLogger,
    req: TeachingRequest,
    style: StyleConfig,
    outline: PPTOutline,
    base: SlideDeckContent,
) -> SlideDeckContent:
    """Refine base pages with LLM using per-page generation (Plan B).
    
    Each page is generated independently with full outline context,
    enabling better contextual understanding and proper handling of
    special page types like exercises, steps, and quizzes.
    
    Falls back to base if anything fails.
    """
    if not llm.is_enabled():
        return base

    total_pages = len(outline.slides)
    logger.emit(session_id, "3.4", "per_page_start", {
        "total_pages": total_pages,
        "generation_mode": "per-page-parallel"
    })
    
    # Create tasks for parallel generation
    tasks = []
    for slide_outline, base_page in zip(outline.slides, base.pages):
        task = _generate_single_page(
            session_id=session_id,
            llm=llm,
            logger=logger,
            req=req,
            style=style,
            full_outline=outline,
            page_outline=slide_outline,
            base_page=base_page,
            page_index=slide_outline.index,
            total_pages=total_pages,
        )
        tasks.append(task)
    
    # Run all pages in parallel
    refined_pages = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle any exceptions - replace with base pages
    final_pages: List[SlidePage] = []
    for i, result in enumerate(refined_pages):
        if isinstance(result, BaseException):
            logger.emit(session_id, "3.4", "page_fallback", {
                "page_index": i + 1,
                "reason": str(result)
            })
            final_pages.append(base.pages[i])
        else:
            # Result is SlidePage
            final_pages.append(result)
    
    # Sort by index and validate
    final_pages = sorted(final_pages, key=lambda p: p.index)
    
    if len(final_pages) != len(outline.slides):
        logger.emit(session_id, "3.4", "validation_failed", {
            "expected": len(outline.slides),
            "got": len(final_pages)
        })
        return base
    
    logger.emit(session_id, "3.4", "per_page_complete", {
        "total_pages": len(final_pages)
    })
    
    return SlideDeckContent(deck_title=outline.deck_title, pages=final_pages)


def validate_deck(outline: PPTOutline, deck: SlideDeckContent) -> Tuple[bool, List[str]]:
    """Lightweight validation for Module 3.4 output."""
    errs: List[str] = []
    if len(deck.pages) != len(outline.slides):
        errs.append(f"pages count mismatch: {len(deck.pages)} vs outline {len(outline.slides)}")

    outline_idx = [s.index for s in outline.slides]
    deck_idx = [p.index for p in deck.pages]
    if outline_idx != deck_idx:
        errs.append("page indices do not align with outline indices")

    for p in deck.pages:
        if not p.title or not p.elements:
            errs.append(f"page {p.index} missing title/elements")
        # Must contain a title element
        if not any(e.type == "text" and (e.content or {}).get("role") in ("title", "cover_title") for e in p.elements):
            errs.append(f"page {p.index} missing title text element")

    return (len(errs) == 0), errs
