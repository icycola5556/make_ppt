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
4. **特殊关注点** (special_focus)：例如 "incorporate_political_elements"（融入思政要点）
5. **基础页面** (base_page)：布局参考（可选）

输出：这一页的完整 SlidePage（JSON格式）

---

🚨🚨🚨 **核心规则** 🚨🚨🚨

### 1️⃣ 思政教育融入规则（仅当 special_focus 包含 "incorporate_political_elements" 时）

**当需要融入思政时，必须自然嵌入以下元素之一：**
- **工匠精神**：精益求精、严谨细致的职业态度
- **职业道德**：规范操作、诚信守法
- **社会责任感**：环保意识、公共安全意识
- **团队协作精神**：沟通协作、互助共赢

**融入方式**：
- 在 speaker_notes 中添加 1-2 句思政引导语（自然不生硬）
- 在适当的 bullet 中嵌入价值观引导（例如："操作步骤3：严格遵守操作规程（体现职业道德）"）
- 案例页中结合实际情境体现思政要素

**❌ 禁止**：
- 生硬说教（"我们要弘扬工匠精神"）
- 单独新增思政段落打断教学内容
- 思政内容与专业知识脱节

**✅ 正确示例**：
```json
{
  "speaker_notes": "强调：检修液压系统时必须严格遵守操作规程，体现机械工程师对设备安全和公共安全的职业责任感。"
}
```

---

### 2️⃣ 图片描述升级规则（适用于所有视觉元素）

**🚨 禁止简单描述！**

❌ **错误示例**（禁止）：
- "液压泵图片"
- "齿轮泵示意图"
- "教学图片"

✅ **正确格式**（模仿 Midjourney 提示词）：
```
Subject: [主体物]（例如：工业齿轮泵剖面结构）
Details: [关键细节]（例如：标注：齿轮、进油口、出油口、壳体）
Style: [视觉风格]（例如：工程制图风格，蓝白配色，清晰标注）
View: [视角]（例如：正剖视图）
```

**完整示例**：
```json
{
  "type": "image",
  "content": {
    "prompt": "Subject: 工业齿轮泵三维剖面结构 | Details: 清晰标注主动齿轮、从动齿轮、进油口、出油口、壳体、密封部件 | Style: 工程教学插图，蓝白色系，高对比度 | View: 立体剖视图，关键部件高亮显示"
  }
}
```

**适用于所有视觉类型**：
- `type="image"`：实物照片/示意图
- `type="diagram"`：流程图/结构图
- `type="chart"`：数据图表

---

### 3️⃣ 内容处理策略（根据 slide_type 分类）

#### 🔴 **必须 100% 保留原文的类型**

**exercises / quiz（习题页）**：
```json
{
  "type": "quiz",
  "content": {
    "questions": [
      {"question": "题目1原文（100%保留）", "answer": "生成合理的参考答案"},
      {"question": "题目2原文（100%保留）", "answer": "生成合理的参考答案"}
    ],
    "scoring": "评分标准原文（如有）"
  }
}
```

**objectives / agenda（教学目标）**：
- 目标条目 100% 保留，不要改写

**summary（课程总结）**：
- 总结要点 100% 保留

**warning / tips（注意事项）**：
- 所有警告/提示 100% 保留

---

#### 🟡 **可以适度扩展的类型**

**concept / theory（概念讲解）**：
- 可将简短要点扩展为 15-25 字的详细描述
- 可添加配图（使用升级版图片描述）

**steps / practice（操作步骤）**：
- 保留步骤编号和顺序
- 可补充操作细节（每步 20-30 字）

**case / case_study（案例分析）**：
- 保留案例核心信息
- 可补充分析角度

---

## 📐 页面元素定位（16:9 画布）

- 标题区：x=0.06, y=0.06, w=0.88, h=0.12
- 内容区：x=0.06, y=0.20, w=0.88, h=0.72
- 右侧配图：x=0.70, y=0.20, w=0.24, h=0.72

---

## 📝 完整示例

### 示例 1：习题页（包含思政融入）

**输入**：
```json
{
  "slide_type": "exercises",
  "title": "习题巩固",
  "bullets": [
    "题目1：简述液压传动系统的工作原理，并说明帕斯卡定律的作用",
    "题目2：列出三种常见液压泵的类型并比较其适用场合"
  ],
  "special_focus": ["incorporate_political_elements"]
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
       ]
     }, "style": {"role": "body"}}
  ],
  "speaker_notes": "引导学生独立思考5分钟后讲解答案。强调：设备选型不仅要考虑技术参数，更要体现工程师的严谨态度和对安全的责任感。"
}
```

---

### 示例 2：概念页（升级版图片描述）

**输入**：
```json
{
  "slide_type": "concept",
  "title": "齿轮泵的工作原理",
  "bullets": [
    "齿轮泵由主动齿轮和从动齿轮组成",
    "利用齿轮啮合形成密闭容积变化实现吸油和压油"
  ]
}
```

**❌ 错误输出**（禁止）：
```json
{
  "elements": [
    {"type": "image", "content": {"prompt": "齿轮泵图片"}}  // ❌ 过于简单
  ]
}
```

**✅ 正确输出**：
```json
{
  "index": 5,
  "slide_type": "concept",
  "title": "齿轮泵的工作原理",
  "layout": {"template": "two-column"},
  "elements": [
    {"id": "title-001", "type": "text", "x": 0.06, "y": 0.06, "w": 0.88, "h": 0.12,
     "content": {"text": "齿轮泵的工作原理", "role": "title"}, "style": {"role": "title"}},
    {"id": "bullets-001", "type": "bullets", "x": 0.06, "y": 0.20, "w": 0.60, "h": 0.72,
     "content": {"items": [
       "齿轮泵由主动齿轮和从动齿轮啮合组成，通过电机驱动主动齿轮旋转",
       "齿轮啮合处形成密闭容积，吸油侧容积增大产生负压吸油，压油侧容积减小将油液压出"
     ], "role": "body"}, "style": {"role": "body"}},
    {"id": "image-001", "type": "image", "x": 0.70, "y": 0.20, "w": 0.24, "h": 0.72,
     "content": {
       "prompt": "Subject: 齿轮泵工作原理动态示意图 | Details: 标注主动齿轮（蓝色）、从动齿轮（灰色）、吸油腔、压油腔、油液流动方向箭头 | Style: 工程教学插图，清晰配色，动态流程标注 | View: 正视剖面图，关键啮合区域放大显示"
     }, "style": {"role": "visual"}}
  ],
  "speaker_notes": "结合动画演示齿轮啮合过程，强调密闭容积变化是关键。"
}
```

---

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


def _right_placeholder(kind: str, theme: str, description: str = None) -> SlideElement:
    # Generic placeholder for images/diagrams/charts. Module 3.5 will render this block.
    content = {
        "placeholder": True,
        "kind": kind,
        "theme": theme,
    }

    # 关键修改：如果有 description，直接写入 content，不再生成硬编码 prompt
    if description:
        content["description"] = description
    else:
        # Fallback (只有没描述时才用这个)
        content["prompt"] = f"{theme}（教学示意图/结构图/流程图，风格简洁清晰）"

    return SlideElement(
        id=str(uuid.uuid4()),
        type="image" if kind == "image" else ("diagram" if kind == "diagram" else "chart"),
        x=0.70,
        y=0.20,
        w=0.24,
        h=0.72,
        content=content,
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
                        "text": f"学科：{req.subject_info.subject_name if req.subject_info else (outline.subject or '_____')}\n知识点：{', '.join(outline.knowledge_points) if outline.knowledge_points else '_____'}\n课时：{req.slide_requirements.lesson_duration_min if req.slide_requirements else '____'} 分钟",
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
            # 尝试从 assets 获取 description
            desc = s.assets[0].get("description") if s.assets else None
            els.append(_right_placeholder("diagram", theme=s.title, description=desc))
        elif st in ("relations", "bridge"):
            els.append(_bullets_el(s.bullets or ["关联点A—关联点B：_____", "关键联系：_____"]))
            # 尝试从 assets 获取 description
            desc = s.assets[0].get("description") if s.assets else None
            els.append(_right_placeholder("diagram", theme="知识点关联框架", description=desc))
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
                # ✅ 获取 description (这是我们在 Phase 3 同步进去的高质量 Prompt)
                desc = a0.get("description")

                # 传递给 placeholder 生成器
                els.append(_right_placeholder(
                    "image" if kind == "image" else "diagram",
                    theme=theme,
                    description=desc  # <--- 关键传参
                ))

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
# 内容审核 (P2: 内化到 3.4 模块)
# ============================================================================

def _review_and_fix_page(
    page: SlidePage,
    outline: OutlineSlide,
    req: TeachingRequest
) -> SlidePage:
    """
    内置内容审核 - 生成时自动检查质量问题
    
    检查项：
    1. 要点数量 (2-6个)
    2. 占位符残留
    3. 内容长度
    
    问题会写入 speaker_notes 供教师查看
    """
    issues = []
    
    # 1. 检查要点数量
    for elem in page.elements:
        if elem.type == "bullets" and isinstance(elem.content, dict):
            items = elem.content.get("items", [])
            if len(items) < 2 and page.slide_type not in ("title", "cover", "bridge"):
                issues.append(f"要点数量不足 ({len(items)}个，建议2-6个)")
            if len(items) > 6:
                issues.append(f"要点过多 ({len(items)}个，建议精简至6个以内)")
    
    # 2. 检查占位符残留
    placeholder_patterns = ["____", "TODO", "待填充", "___", "[待定]"]
    for elem in page.elements:
        content_str = str(elem.content)
        for pattern in placeholder_patterns:
            if pattern in content_str:
                issues.append(f"发现未填充占位符: '{pattern}'")
                break
    
    # 3. 检查内容与大纲匹配度
    if outline.bullets:
        outline_bullet_count = len(outline.bullets)
        page_bullets = []
        for elem in page.elements:
            if elem.type == "bullets" and isinstance(elem.content, dict):
                page_bullets.extend(elem.content.get("items", []))
        
        if len(page_bullets) < outline_bullet_count - 1:
            issues.append(f"内容要点少于大纲 ({len(page_bullets)} vs {outline_bullet_count})")
    
    # 写入审核结果
    if issues:
        warning_text = "⚠️ 内容审核: " + "; ".join(issues)
        if page.speaker_notes:
            page.speaker_notes = warning_text + "\n---\n" + page.speaker_notes
        else:
            page.speaker_notes = warning_text
    
    return page


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
            SlideElement(
                id="title-001",
                type="text",
                x=0.06, y=0.06, w=0.88, h=0.12,
                content={"text": page_outline.title, "role": "title"},
                style={"role": "title"}
            ),
            SlideElement(
                id="bullets-001",
                type="bullets",
                x=0.06, y=0.20, w=0.88, h=0.72,
                content={"items": page_outline.bullets},
                style={"role": "body"}
            )
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

    # Add special_focus if ideological education is enabled
    special_focus = []
    if req.special_requirements.ideological_education.enabled:
        special_focus.append("incorporate_political_elements")
    if special_focus:
        user_payload["special_focus"] = special_focus
    
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
            parsed_elements = parsed.get("elements", [])
            for el in parsed_elements:
                if isinstance(el, dict) and el.get("type") in ("quiz", "bullets"):
                    print(f"Element type: {el.get('type')}")
                    print(f"Content: {el.get('content')}")
            print("=" * 50)
        
        refined_page = SlidePage.model_validate(parsed)
        
        # Ensure index is preserved
        refined_page.index = page_index
        
        # 🆕 内置内容审核
        refined_page = _review_and_fix_page(refined_page, page_outline, req)
        
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
