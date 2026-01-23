from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional, Tuple

from ...common.llm_client import LLMClient
from ...common.logger import WorkflowLogger
from ...common.schemas import PPTOutline, SlideDeckContent, SlideElement, SlidePage, StyleConfig, TeachingRequest


CONTENT_SYSTEM_PROMPT = """<protocol>
你是高职教学课件内容生成助手（Module 3.4: Content Expander）。

<critical_constraint priority="HIGHEST">
## 🚨 大纲是唯一真相来源 (Outline = Source of Truth)

你收到的 `outline.slides[].bullets` 是用户在 Module 3.3 确认的核心要点。

### 严格遵守规则:
1. **禁止添加**: 不要发明 outline.bullets 中不存在的新要点
2. **禁止删除**: outline 中的每个 bullet 必须在输出中体现
3. **1:1 映射**: 如果 outline 有 3 个 bullets，输出必须有 3 个 items

### 你的唯一任务:
- 为每个 bullet 生成扩展说明（1-2句话）
- 基于 bullet 内容建议视觉素材
- 生成演讲备注（speaker_notes）
</critical_constraint>

<design_philosophy>
- 教学效果驱动：优先考虑内容的教学效果
- 学生认知适配：根据高职学生的认知特点设计内容密度
- 实践应用导向：强调实用技能和实际操作能力
</design_philosophy>

<content_rules>
1. 精准表达：使用高职学生熟悉的语言和专业术语
2. 逻辑递进：遵循从基础到应用的认知规律
3. 视觉化支持：为抽象概念提供适当的可视化占位
</content_rules>

<visual_logic>
只在以下情况添加图片占位:
- slide_type 为 "concept", "steps", "comparison" 时添加示意图
- slide_type 为 "case" 时添加案例图片
- 其他类型默认不添加图片，除非 outline.assets 明确要求
</visual_logic>

<layout_guide aspect_ratio="16:9">
- 标题区：x=0.06, y=0.06, w=0.88, h=0.12
- 主内容区：x=0.06, y=0.20, w=0.60, h=0.72
- 右侧可视化区：x=0.70, y=0.20, w=0.24, h=0.72
- 页脚备注区：x=0.06, y=0.92, w=0.88, h=0.06
</layout_guide>

<fill_in_the_blank_rule priority="CRITICAL">
如果你看到 outline bullet 是一个填空题或占位符 (例如 "题目1: ____", "关键连接: ____", "图表: ____"):
1. **必须保留前缀**: 必须保留 "题目1:", "关键连接:" 等结构前缀
2. **填空逻辑**: 根据上下文生成具体内容填入空格 `____` 部分
3. **禁止替换**: 绝对不要把 "题目1: ____" 替换成 "理解PLC基本结构" 这种通用陈述
4. **一一对应**: 输入有几个 bullet，输出必须有几个 item，数量严格一致
</fill_in_the_blank_rule>

<slide_types>
cover=封面 | agenda=目录 | objectives=目标 | intro=导入 | concept=概念 | 
steps=步骤 | warning=注意 | exercises=练习 | summary=总结 | 
relations=联系 | bridge=过渡 | qa=问答 | case=案例 | comparison=对比
</slide_types>
</protocol>

<output_format>
输出严格JSON格式，符合SlideDeckContent schema。
页面数量必须与outline.slides数量完全一致。
</output_format>"""




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


async def refine_with_llm(
    session_id: str,
    llm: LLMClient,
    logger: WorkflowLogger,
    req: TeachingRequest,
    style: StyleConfig,
    outline: PPTOutline,
    base: SlideDeckContent,
) -> SlideDeckContent:
    """Refine base pages with LLM. Falls back to base if anything fails."""

    if not llm.is_enabled():
        return base

    schema_hint = SlideDeckContent.model_json_schema()

    # Keep prompts bounded: refine in batches.
    batch_size = 6 if len(base.pages) > 10 else len(base.pages)
    refined_pages: List[SlidePage] = []
    for batch in _chunk_pages(base.pages, batch_size):
        user_payload = {
            "teaching_request": req.model_dump(mode="json"),
            "style_config": style.model_dump(mode="json"),
            "outline": outline.model_dump(mode="json"),
            "base_pages": [p.model_dump(mode="json") for p in batch],
        }
        user_msg = json.dumps(user_payload, ensure_ascii=False)

        logger.emit(session_id, "3.4", "llm_prompt", {"system": CONTENT_SYSTEM_PROMPT, "user": user_payload, "schema_hint": schema_hint})

        try:
            parsed, meta = await llm.chat_json(CONTENT_SYSTEM_PROMPT, user_msg, json.dumps(schema_hint, ensure_ascii=False))
            logger.emit(session_id, "3.4", "llm_response", meta)
            deck = SlideDeckContent.model_validate(parsed)

            # Only take the refined pages that correspond to this batch indexes
            refined_pages.extend(deck.pages)
        except Exception as e:
            logger.emit(session_id, "3.4", "llm_error", {"error": str(e)})
            refined_pages.extend(batch)

    # Sort and validate alignment with outline
    refined_pages = sorted(refined_pages, key=lambda p: p.index)
    if len(refined_pages) != len(outline.slides):
        # If mismatch, keep base to be safe
        return base

    return SlideDeckContent(deck_title=outline.deck_title, pages=refined_pages)


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
