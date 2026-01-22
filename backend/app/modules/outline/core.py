from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...common.schemas import OutlineSlide, PPTOutline, TeachingRequest
from ...prompts.outline import OUTLINE_PLANNING_SYSTEM_PROMPT

# 预定义不需要图片的页面类型
SLIDE_TYPES_WITHOUT_IMAGES = {
    "title",      # 封面页通常不需要额外图片
    "objectives", # 教学目标页通常不需要图片
    "summary",    # 总结页通常不需要图片
    "qa",         # 问答页通常不需要图片
    "reference",  # 参考页通常不需要图片
}


# ============================================================================
# Assets后处理：生成图片描述和补充size/style字段
# ============================================================================

async def _generate_asset_description(
    asset: Dict[str, Any],
    slide: OutlineSlide,
    req: TeachingRequest,
    llm: Any,
    logger: Any,
    session_id: str,
) -> Dict[str, Any]:
    """为diagram或photo类型的asset生成详细的文字描述（用于后续图片生成的prompt）"""
    
    asset_type = asset.get("type", "").lower()
    
    # 只处理diagram和photo类型
    if asset_type not in ["diagram", "photo"]:
        return asset
    
    # 如果已经有description字段且不为空，直接返回
    if asset.get("description") and asset.get("description").strip():
        return asset
    
    # 构建上下文信息
    context = {
        "slide_title": slide.title,
        "slide_type": slide.slide_type,
        "bullets": slide.bullets,
        "subject": req.subject,
        "knowledge_points": req.kp_names,
        "teaching_scene": req.teaching_scene,
        "asset_type": asset_type,
        "theme": asset.get("theme", ""),
    }
    
    # 如果LLM可用，使用LLM生成描述
    if llm and llm.is_enabled():
        try:
            system_prompt = """你是PPT图片描述生成专家。你的任务是根据PPT页面的主题内容，为图片素材生成详细的文字描述，这个描述将用于后续AI图片生成的prompt。

## 任务要求
1. 根据页面标题、要点内容和知识点，理解这一页的教学主题
2. 结合asset的type（diagram或photo）和theme，生成详细的图片描述
3. 描述应该：
   - 具体明确，包含关键元素和场景细节
   - 适合作为AI图片生成的prompt
   - 体现教学内容的专业性和准确性
   - 如果是diagram，描述应该包含图表的结构、元素关系等
   - 如果是photo，描述应该包含场景、对象、环境等

## 输出格式
返回JSON格式：
{
  "description": "详细的图片描述文字，用于AI图片生成"
}

只输出JSON，不要解释。"""
            
            user_payload = json.dumps(context, ensure_ascii=False, indent=2)
            
            schema_hint = '{"description": "string"}'
            
            parsed, meta = await llm.chat_json(
                system_prompt,
                user_payload,
                schema_hint,
                temperature=0.7,
            )
            
            if parsed and parsed.get("description"):
                asset["description"] = parsed["description"]
                logger.emit(session_id, "3.3", "asset_description_generated", {
                    "slide_index": slide.index,
                    "asset_type": asset_type,
                    "description_length": len(parsed["description"])
                })
        except Exception as e:
            logger.emit(session_id, "3.3", "asset_description_error", {
                "slide_index": slide.index,
                "asset_type": asset_type,
                "error": str(e)
            })
            # 生成fallback描述
            asset["description"] = _generate_fallback_asset_description(asset, slide, context)
    else:
        # LLM不可用，生成fallback描述
        asset["description"] = _generate_fallback_asset_description(asset, slide, context)
    
    return asset


def _generate_fallback_asset_description(
    asset: Dict[str, Any],
    slide: OutlineSlide,
    context: Dict[str, Any],
) -> str:
    """生成fallback的asset描述（当LLM不可用时）"""
    asset_type = asset.get("type", "").lower()
    theme = asset.get("theme", "")
    slide_title = slide.title
    
    if asset_type == "diagram":
        # 图表类型：描述图表的结构和内容
        if theme:
            return f"关于{theme}的示意图，展示{slide_title}相关的结构、流程或关系"
        else:
            return f"展示{slide_title}相关内容的示意图，包含关键要素和关系"
    elif asset_type == "photo":
        # 照片类型：描述场景和对象
        if theme:
            return f"关于{theme}的实景照片，展示{slide_title}相关的实际应用场景"
        else:
            return f"展示{slide_title}相关内容的实景照片，体现实际应用场景"
    else:
        return f"与{slide_title}相关的图片素材"


def _ensure_asset_fields(asset: Dict[str, Any]) -> Dict[str, Any]:
    """确保asset包含size和style字段"""
    # 如果缺少size，设置默认值
    if "size" not in asset or not asset["size"]:
        asset["size"] = "16:9"  # 默认16:9比例
    
    # 如果缺少style，根据type设置默认值
    if "style" not in asset or not asset["style"]:
        asset_type = asset.get("type", "").lower()
        if asset_type == "diagram":
            asset["style"] = "schematic"  # 示意图风格
        elif asset_type == "photo":
            asset["style"] = "photo"  # 照片风格
        elif asset_type == "image":
            asset["style"] = "photo"  # 图片默认照片风格
        else:
            asset["style"] = "illustration"  # 其他类型默认插画风格
    
    return asset


def _post_process_outline_assets_sync(
    outline: PPTOutline,
) -> PPTOutline:
    """同步版本的assets后处理：只补充size/style字段，不生成描述（用于同步函数）"""
    for slide in outline.slides:
        # 判断该页面类型是否需要图片
        if slide.slide_type in SLIDE_TYPES_WITHOUT_IMAGES:
            # 如果页面类型不需要图片，跳过
            continue
        
        # 处理每个asset，确保包含size和style字段
        processed_assets = []
        for asset in slide.assets:
            asset = _ensure_asset_fields(asset.copy())
            processed_assets.append(asset)
        
        slide.assets = processed_assets
    
    return outline


async def _process_slide_assets(
    slide: OutlineSlide,
    req: TeachingRequest,
    llm: Any,
    logger: Any,
    session_id: str,
) -> OutlineSlide:
    """处理单个slide的assets：生成描述、补充字段、判断是否需要图片"""
    
    # 判断该页面类型是否需要图片
    if slide.slide_type in SLIDE_TYPES_WITHOUT_IMAGES:
        # 如果页面类型不需要图片，但已有assets，仍然处理它们（补充字段）
        # 如果没有assets，不添加新的
        if not slide.assets:
            return slide
        # 如果有assets，继续处理（但可能不生成描述，取决于LLM判断）
    
    # 处理每个asset
    processed_assets = []
    for asset in slide.assets:
        # 确保包含size和style字段
        asset = _ensure_asset_fields(asset.copy())
        
        # 为diagram和photo类型生成描述（即使页面类型在SLIDE_TYPES_WITHOUT_IMAGES中，如果已有asset也生成描述）
        asset = await _generate_asset_description(
            asset, slide, req, llm, logger, session_id
        )
        
        processed_assets.append(asset)
    
    slide.assets = processed_assets
    return slide


async def _post_process_outline_assets(
    outline: PPTOutline,
    req: TeachingRequest,
    llm: Any,
    logger: Any,
    session_id: str,
) -> PPTOutline:
    """后处理outline的所有slides的assets"""
    
    import asyncio
    
    # 并行处理所有slides的assets
    processed_slides = await asyncio.gather(*[
        _process_slide_assets(slide, req, llm, logger, session_id)
        for slide in outline.slides
    ])
    
    # 更新outline的slides
    outline.slides = list(processed_slides)
    
    logger.emit(session_id, "3.3", "assets_post_processed", {
        "total_slides": len(outline.slides),
        "slides_with_assets": len([s for s in outline.slides if s.assets])
    })
    
    return outline

# 加载slide_type定义
_SLIDE_TYPE_JSON_PATH = Path(__file__).parent / "slide_type.json"
_SLIDE_TYPES_DATA = None

def _load_slide_types() -> Dict[str, Any]:
    """加载slide_type.json数据"""
    global _SLIDE_TYPES_DATA
    if _SLIDE_TYPES_DATA is None:
        if _SLIDE_TYPE_JSON_PATH.exists():
            with open(_SLIDE_TYPE_JSON_PATH, 'r', encoding='utf-8') as f:
                _SLIDE_TYPES_DATA = json.load(f)
        else:
            _SLIDE_TYPES_DATA = {"slide_types": []}
    return _SLIDE_TYPES_DATA

def _get_slide_type_definitions() -> str:
    """获取slide_type定义的文本描述，用于LLM prompt"""
    data = _load_slide_types()
    definitions = []
    for st in data.get("slide_types", []):
        definitions.append(
            f"- **{st['slide_type']}**: {st['name']} - {st['description']}\n"
            f"  使用场景：{st['instruction']}"
        )
    return "\n".join(definitions)

def get_slide_types() -> Dict[str, Any]:
    """获取slide_type数据（供API使用）"""
    return _load_slide_types()


def _deck_title(req: TeachingRequest) -> str:
    """生成课件标题"""
    kps = req.kp_names
    if kps:
        if len(kps) == 1:
            return kps[0]
        return "、".join(kps)
    return "知识点课件"


def _get_current_semester() -> str:
    """获取当前学期（示例实现）"""
    import datetime
    now = datetime.datetime.now()
    year = now.year
    month = now.month
    if month >= 9:
        return f"{year}年秋季学期"
    elif month >= 3:
        return f"{year}年春季学期"
    else:
        return f"{year-1}年秋季学期"


def _get_tools_for_practice(kp: str, subject: str) -> str:
    """根据知识点和学科返回具体工具"""
    kp_lower = kp.lower()
    subject_lower = subject.lower() if subject else ""

    if "液压" in kp or "液压" in subject_lower:
        return "液压泵、液压缸、压力表、扳手、液压油、密封件"
    elif "plc" in kp_lower or "电气" in kp or "电气" in subject_lower:
        return "PLC编程器、万用表、螺丝刀、接线工具、继电器"
    elif "机械" in kp or "机械" in subject_lower or "车" in kp or "铣" in kp:
        return "车床/铣床、游标卡尺、千分尺、刀具、工件"
    elif "焊接" in kp or "焊" in subject_lower:
        return "焊机、焊条、防护面罩、焊接手套、角磨机"
    elif "汽车" in kp or "汽车" in subject_lower or "发动机" in kp:
        return "发动机、万用表、故障诊断仪、扳手套装、机油"
    elif "网络" in kp or "网络" in subject_lower or "路由" in kp:
        return "路由器、交换机、网线、测线仪、压线钳"
    elif "编程" in kp or "程序" in kp or "代码" in kp:
        return "计算机、开发环境、调试工具、代码编辑器"
    else:
        return "相关实训工具、安全防护用品、测量工具"


def _get_safety_check(kp: str, subject: str) -> str:
    """根据知识点返回安全检查内容"""
    kp_lower = kp.lower()
    subject_lower = subject.lower() if subject else ""

    if "液压" in kp or "液压" in subject_lower:
        return "检查油箱液位、确认管路无泄漏、穿戴防护眼镜"
    elif "plc" in kp_lower or "电气" in kp:
        return "确认断电状态、检查绝缘工具、穿戴绝缘手套"
    elif "机械" in kp or "车" in kp or "铣" in kp:
        return "检查机床安全防护装置、穿戴防护眼镜、固定工件"
    elif "焊接" in kp or "焊" in subject_lower:
        return "佩戴焊接面罩、穿戴防护服、确认通风良好"
    elif "汽车" in kp or "发动机" in kp:
        return "确认车辆稳固、关闭点火开关、准备灭火器"
    else:
        return "检查设备状态、穿戴防护用品、确认环境安全"


def _get_step_action(step_num: int, kp: str) -> str:
    """生成步骤的具体操作"""
    kp_lower = kp.lower()

    if step_num == 1:
        if "液压" in kp:
            return "操作要点：检查油箱液位在MIN-MAX之间，启动液压泵；质量要点：压力表读数稳定在额定范围"
        elif "plc" in kp_lower:
            return "操作要点：连接PLC与编程器，上传梯形图程序；质量要点：程序上传成功无报错"
        else:
            return "操作要点：按规范启动设备，观察运行状态；质量要点：设备运行平稳无异常"
    elif step_num == 2:
        if "液压" in kp:
            return "操作要点：调节溢流阀至8-10MPa，观察压力变化；质量要点：系统压力稳定"
        elif "plc" in kp_lower:
            return "操作要点：设置输入输出参数，运行调试程序；质量要点：输出信号正确响应"
        else:
            return "操作要点：按工艺要求调整参数，进行试运行；质量要点：参数在标准范围内"
    elif step_num == 3:
        if "液压" in kp:
            return "操作要点：测试液压缸动作，记录行程时间；质量要点：动作流畅，时间符合要求"
        elif "plc" in kp_lower:
            return "操作要点：进行联机测试，验证控制逻辑；质量要点：各环节动作准确"
        else:
            return "操作要点：完成标准操作流程，检查成品质量；质量要点：符合验收标准"
    else:
        return f"操作要点：完成第{step_num}步标准操作；质量要点：达到工艺要求"


def _get_risk_warning(kp: str, subject: str) -> str:
    """生成高风险点"""
    kp_lower = kp.lower()
    subject_lower = subject.lower() if subject else ""

    if "液压" in kp or "液压" in subject_lower:
        return "高压油喷出可能导致伤害，务必戴防护眼镜"
    elif "plc" in kp_lower or "电气" in kp:
        return "带电操作可能触电，必须确认断电后再接线"
    elif "焊接" in kp:
        return "焊接弧光伤眼，必须佩戴焊接面罩"
    elif "机械" in kp or "车" in kp:
        return "旋转部件易夹伤，禁止戴手套操作"
    else:
        return "操作不当可能导致设备损坏或人身伤害"


def _get_common_mistake(kp: str) -> str:
    """生成常见错误"""
    kp_lower = kp.lower()

    if "液压" in kp:
        return "忘记检查油位导致泵空转损坏"
    elif "plc" in kp_lower:
        return "接线错误导致输出信号不正确"
    elif "焊接" in kp:
        return "焊接电流过大导致焊穿"
    else:
        return "操作步骤顺序错误导致结果不准确"


def _get_correction_method(kp: str) -> str:
    """生成纠正方法"""
    kp_lower = kp.lower()

    if "液压" in kp:
        return "操作前必须按检查表逐项确认"
    elif "plc" in kp_lower:
        return "接线后先用万用表测试再通电"
    elif "焊接" in kp:
        return "根据板厚查表选择合适电流"
    else:
        return "严格按照操作规程逐步执行"


def _generate_exercise_question(kp: str, subject: str, q_num: int) -> str:
    """生成具体的练习题"""
    kp_lower = kp.lower()
    subject_lower = subject.lower() if subject else ""

    if q_num == 1:
        if "液压" in kp or "液压" in subject_lower:
            return "选择题：液压泵的主要作用是（ ） A.储存液压油 B.转换能量 C.控制压力 D.过滤杂质"
        elif "plc" in kp_lower:
            return "选择题：PLC的输入端子通常接（ ） A.执行器 B.传感器 C.电源 D.地线"
        elif "焊接" in kp:
            return "选择题：焊接电流过大会导致（ ） A.焊不透 B.焊穿 C.夹渣 D.气孔"
        else:
            return f"选择题：关于{kp}的基本概念，下列说法正确的是（ ）"
    elif q_num == 2:
        if "液压" in kp or "液压" in subject_lower:
            return f"填空题：液压系统的三大组成部分是动力元件、_____和辅助元件"
        elif "plc" in kp_lower:
            return "填空题：梯形图中，常开触点的符号是_____，常闭触点的符号是_____"
        else:
            return f"填空题：{kp}的核心要素包括_____、_____和_____"
    elif q_num == 3:
        if "液压" in kp or "液压" in subject_lower:
            return "简答题：说明液压缸推力不足的可能原因及排查方法"
        elif "plc" in kp_lower:
            return "简答题：说明PLC程序调试的基本步骤"
        else:
            return f"简答题：说明{kp}在实际应用中的注意事项"
    else:
        return f"题目{q_num}：请根据所学知识，分析{kp}的实际应用"


def _generate_key_points(kp: str, point_num: int) -> str:
    """生成知识点的要点"""
    if point_num == 1:
        return f"理解{kp}的基本定义和组成要素"
    elif point_num == 2:
        return f"掌握{kp}的工作原理和特点"
    elif point_num == 3:
        return f"能够分析{kp}在实际中的应用场景"
    else:
        return f"要点{point_num}：{kp}的相关知识"



def _build_outline_planning_prompt() -> str:
    """构建大纲规划系统提示词，动态包含slide_type定义"""
    slide_type_defs = _get_slide_type_definitions()
    
    return f"""你是高职课程PPT大纲智能规划专家，负责根据教学需求生成结构化的课件大纲。

## 核心职责
1. **智能页面规划**：根据知识点数量、难度、教学场景，合理分配页面数量和类型
2. **教学逻辑编排**：按照"封面→目标→导入→讲解→案例→练习→总结"的逻辑顺序组织内容
3. **素材占位定义**：为每页预定义图片、图表等素材需求
4. **互动设计优化**：根据教学场景和知识点特点，设计合适的互动环节
5. **准确类型判断**：根据每页的实际内容和教学目的，准确选择最合适的slide_type

## 页面类型体系
系统支持以下页面类型（slide_type），请根据每页的实际内容和教学目的，选择最合适的类型：

{slide_type_defs}

## 类型选择原则
- 仔细分析每页的title、bullets和教学目的
- 选择最能准确描述该页功能和内容特点的slide_type
- 如果内容同时符合多个类型，选择最核心、最主要的类型
- 封面页必须使用"title"类型，教学目标页使用"objectives"类型

## 页面分配原则

### 固定页面（必须包含）
- 封面(title): 1页
- 目标(objectives): 1页  
- 总结(summary): 1页

### 知识点内容页分配
- **简单知识点(easy)**: 1-2页（概念定义 + 要点解析）
- **中等知识点(medium)**: 2-3页（导入 + 概念定义 + 要点解析）
- **困难知识点(hard)**: 3-4页（导入 + 概念定义 + 要点解析 + 深入讲解）

### 场景特定页面
- **理论课(theory)**: 导入页、概念页、要点解析页、案例页（可选）、练习页（可选）
- **实训课(practice)**: 任务映射页、准备页、步骤页（多个）、注意事项页、巩固页
- **复习课(review)**: 复习路线页、知识框架页、知识点回顾页、易错点页、典型题页

### 特殊需求页面
- **案例页**: 根据 special_requirements.cases.count 决定（最多3页）
- **练习页**: 根据 special_requirements.exercises.total_count 决定（每页约3道题）
- **互动页**: 根据 special_requirements.interaction.types 决定（每类型1页，最多2页）

## 素材占位定义规范
每页的assets字段应包含素材占位信息：
```json
{{
  "type": "image|diagram|chart|icon",
  "theme": "素材主题描述（如'液压系统原理图'）",
  "size": "small|medium|large|16:9|4:3|1:1",
  "style": "photo|illustration|schematic|mindmap|flow"
}}
```

## 互动设计规范
interactions字段应包含具体的互动设计：
- 理论课：提问、案例分析、小组讨论
- 实训课：操作演示、随堂提问、学员提交
- 复习课：投票、抢答、现场作答

## 输出要求
1. 严格按照JSON Schema输出，确保所有字段完整
2. 页面序号从1开始（index字段）
3. 每页的bullets应包含3-5个核心要点
4. 标题应具体明确，体现教学重点
5. 确保页面数量符合target_count要求（如果指定）
6. **重要**：每页的slide_type必须从上述页面类型体系中选择，确保类型准确匹配页面内容

只输出JSON对象，不要解释。"""

# 为了向后兼容，保留原来的OUTLINE_PLANNING_SYSTEM_PROMPT变量
OUTLINE_PLANNING_SYSTEM_PROMPT = _build_outline_planning_prompt()



# ============================================================================
# 基于3.1预估分布的页面生成
# ============================================================================

def _has_valid_distribution(dist) -> bool:
    """检查预估分布是否有效（总页数大于基础页数）"""
    if dist is None:
        return False
    total = (
        dist.cover + dist.objectives + dist.introduction +
        dist.concept_definition + dist.explanation + dist.case_study +
        dist.exercises + dist.interaction + dist.summary
    )
    return total > 3  # 至少包含封面+目标+总结以外的内容


def _generate_fallback_bullets(slide_type: str, title: str, context: Dict[str, Any]) -> List[str]:
    """根据页面类型生成有意义的 fallback bullets（通用辅助函数）"""
    subject = context.get("subject", "本课程")
    scene = context.get("scene", "theory")
    
    # 根据页面类型生成专属内容
    fallback_map = {
        "title": [
            f"课程：{subject}",
            "授课人：待编辑",
            f"教学场景：{scene}",
        ],
        "cover": [
            f"课程：{subject}",
            "授课人：待编辑",
            f"教学场景：{scene}",
        ],
        "objectives": [
            f"知识目标：掌握{title}的核心概念",
            f"能力目标：能够运用所学知识解决实际问题",
            "素养目标：培养专业精神和规范意识",
        ],
        "intro": [
            f"场景导入：{title}在实际工作中的应用",
            "问题驱动：今天我们要解决什么问题？",
            "学习路径：本节课的核心内容预览",
        ],
        "concept": [
            f"{title}的定义与内涵",
            f"{title}的组成要素",
            f"{title}的关键特征",
        ],
        "content": [
            f"{title}的基本原理",
            f"{title}的应用条件",
            f"{title}的实际操作要点",
        ],
        "steps": [
            "操作步骤一：准备工作与环境检查",
            "操作步骤二：执行核心操作流程",
            "操作步骤三：结果验证与记录",
        ],
        "case": [
            f"案例背景：{title}的实际应用情景",
            "分析过程：如何运用所学知识解决问题",
            "案例结论：经验总结与启示",
        ],
        "exercise": [
            "练习题目：请根据所学内容回答以下问题",
            "评分要点：准确性、完整性、规范性",
            "参考答案：详见讲师备注",
        ],
        "discussion": [
            "讨论话题：如何将所学知识应用到实际工作中？",
            "引导问题：你认为最重要的知识点是什么？",
            "拓展思考：还有哪些相关问题值得探讨？",
        ],
        "summary": [
            f"本节核心收获：掌握{title}的关键要点",
            "重点回顾：需要牢记的核心概念",
            "下节预告：深入学习相关拓展知识",
        ],
        "warning": [
            "安全警示：操作前必须检查设备状态",
            "常见错误：避免以下操作失误",
            "正确方法：规范操作的关键步骤",
        ],
    }
    
    # 使用映射获取fallback，如果没有则使用通用模板
    return fallback_map.get(slide_type, [
        f"{title}的核心内容",
        f"{title}的重要知识点",
        f"{title}的实践应用",
    ])


def _build_slides_from_distribution(req: TeachingRequest) -> List[OutlineSlide]:
    """
    根据 estimated_page_distribution 精确构建页面框架。
    
    返回按以下顺序组织的页面列表：
    - cover (封面) x1
    - objectives (目标) x1 
    - introduction (导入) x dist.introduction
    - concept_definition (定义) x dist.concept_definition
    - explanation (讲解) x dist.explanation
    - case_study (案例) x dist.case_study
    - exercises (习题) x dist.exercises
    - interaction (互动) x dist.interaction
    - summary (总结) x1
    """
    dist = req.estimated_page_distribution
    subj = req.subject or "未指定学科"
    kps = req.kp_names or ["未指定知识点"]
    first_kp = kps[0] if kps else "本知识点"
    
    slides: List[OutlineSlide] = []
    
    def add(slide_type: str, title: str, bullets: List[str], notes: str | None = None,
            assets: List[Dict[str, Any]] | None = None, interactions: List[str] | None = None):
        slides.append(
            OutlineSlide(
                index=len(slides) + 1,
                slide_type=slide_type,
                title=title,
                bullets=bullets,
                notes=notes,
                assets=assets or [],
                interactions=interactions or [],
            )
        )
    
    # === 1. 封面页 (cover) ===
    add(
        "title",
        f"{subj}：{_deck_title(req)}",
        [
            "授课人：待编辑（可在前端修改）",
            f"时间：{_get_current_semester()}",
            f"教学场景：{req.teaching_scene}",
        ],
        notes="封面信息可在前端编辑区直接改。",
    )
    
    # === 2. 教学目标页 (objectives) ===
    goals = req.teaching_objectives
    goal_bullets = []
    if goals.knowledge:
        goal_bullets.append(f"知识目标：{'；'.join(goals.knowledge)}")
    if goals.ability:
        goal_bullets.append(f"能力目标：{'；'.join(goals.ability)}")
    if goals.literacy:
        goal_bullets.append(f"素养目标：{'；'.join(goals.literacy)}")
    add("objectives", "教学目标", goal_bullets or ["（待补充）"], notes="可根据班级学情进一步细化。")
    
    # === 3. 导入页 (introduction) ===
    for i in range(dist.introduction):
        add(
            "intro",
            f"课堂导入：{first_kp}的实际应用" if i == 0 else f"导入延伸 {i+1}",
            [
                f"场景引入：{first_kp}在实际工作中的应用场景",
                "问题驱动：今天我们要解决什么问题？",
                "学习路径：本节课的核心内容预览",
            ],
            assets=[{"type": "image", "theme": "scene_intro", "size": "16:9", "style": "photo"}],
            interactions=["提问：你在哪些场景见过它？"] if req.include_interaction else [],
        )
    
    # === 4. 概念定义页 (concept_definition) ===
    kp_index = 0
    for i in range(dist.concept_definition):
        kp = kps[kp_index % len(kps)] if kps else first_kp
        add(
            "concept",
            f"核心概念：{kp}",
            [
                f"{kp}的定义与内涵",
                f"{kp}的组成要素与关键特征",
                f"{kp}相关术语解释",
            ],
            assets=[{"type": "diagram", "theme": f"{kp}_definition", "size": "4:3", "style": "schematic"}],
        )
        kp_index += 1
    
    # === 5. 讲解页 (explanation) ===
    kp_index = 0
    for i in range(dist.explanation):
        kp = kps[kp_index % len(kps)] if kps else first_kp
        page_num = (i % 3) + 1
        
        if page_num == 1:
            title = f"原理解析：{kp}的工作机制"
            bullets = [
                f"{kp}的基本工作原理",
                f"{kp}的核心公式/逻辑",
                f"{kp}的应用条件",
            ]
        elif page_num == 2:
            title = f"深入讲解：{kp}的关键要点"
            bullets = [
                _generate_key_points(kp, 1),
                _generate_key_points(kp, 2),
                _generate_key_points(kp, 3),
            ]
        else:
            title = f"拓展分析：{kp}的进阶内容"
            bullets = [
                f"{kp}的常见变体与应用场景",
                f"{kp}与其他知识点的关联",
                f"{kp}在实际中的注意事项",
            ]
            kp_index += 1
        
        add(
            "content",
            title,
            bullets,
            assets=[{"type": "diagram", "theme": f"{kp}_explanation_{page_num}", "size": "16:9"}],
        )
    
    # === 6. 案例页 (case_study) ===
    for i in range(dist.case_study):
        add(
            "case",
            f"案例分析 {i+1}：{first_kp}的实际应用",
            [
                f"案例背景：{first_kp}在实际工作中的应用实例",
                f"案例分析：如何运用{first_kp}的原理解决问题",
                "案例结论：掌握理论与实践的结合方法",
            ],
            assets=[{"type": "image", "theme": f"case_image_{i+1}", "size": "16:9", "style": "photo"}],
        )
    
    # === 7. 习题页 (exercises) ===
    for i in range(dist.exercises):
        add(
            "exercise",
            f"习题巩固 {i+1}" if dist.exercises > 1 else "习题巩固",
            [
                _generate_exercise_question(first_kp, req.subject or "", i * 3 + 1),
                _generate_exercise_question(first_kp, req.subject or "", i * 3 + 2),
                "参考答案/解析：详见讲师备注",
            ],
            interactions=["现场作答区"] if req.include_interaction else [],
        )
    
    # === 8. 互动页 (interaction) ===
    interaction_titles = ["课堂讨论", "小组活动", "问答环节"]
    for i in range(dist.interaction):
        title = interaction_titles[i % len(interaction_titles)]
        add(
            "discussion",
            title,
            [
                f"讨论话题：{first_kp}在你的专业领域如何应用？",
                "引导问题：你认为最重要的知识点是什么？",
                "思考延伸：如何将今天所学应用到实际工作中？",
            ],
            interactions=["举手发言", "小组讨论", "弹幕互动"],
        )
    
    # === 9. 总结页 (summary) ===
    add(
        "summary",
        "课堂总结",
        [
            f"本节课你应该会：掌握{first_kp}的核心概念和应用",
            f"关键记忆点：{first_kp}的定义、特点和使用场景",
            "下节课预告：深入学习相关拓展知识",
        ],
        notes="可追加作业或拓展练习。",
    )
    
    return slides


def generate_outline(req: TeachingRequest, style_name: str | None = None) -> PPTOutline:
    """Generate a slide-level outline following 方案 3.3.
    
    This is a deterministic baseline. If LLM is enabled, the workflow may
    ask LLM to rewrite titles/bullets, but the structure is controlled here.
    
    优化：如果存在有效的预估分布，优先使用 _build_slides_from_distribution 生成。
    """
    
    # 优先使用3.1模块的预估分布生成页面结构
    if _has_valid_distribution(req.estimated_page_distribution):
        slides = _build_slides_from_distribution(req)
        
        # 重新索引
        for idx, s in enumerate(slides, start=1):
            s.index = idx
        
        outline = PPTOutline(
            deck_title=f"{req.subject or '未指定学科'}：{_deck_title(req)}",
            subject=req.subject or "未指定学科",
            knowledge_points=req.kp_names or ["未指定知识点"],
            teaching_scene=req.teaching_scene,
            slides=slides,
        )
        
        # 同步后处理assets：补充size/style字段（同步函数，不生成描述）
        outline = _post_process_outline_assets_sync(outline)
        
        return outline
    
    # Fallback: 原有的确定性逻辑
    title = _deck_title(req)
    subj = req.subject or "未指定学科"
    kps = req.kp_names or ["未指定知识点"]

    slides: List[OutlineSlide] = []


    def add(slide_type: str, title: str, bullets: List[str], notes: str | None = None, 
            assets: List[Dict[str, Any]] | None = None, interactions: List[str] | None = None):
        slides.append(
            OutlineSlide(
                index=len(slides) + 1,
                slide_type=slide_type,
                title=title,
                bullets=bullets,
                notes=notes,
                assets=assets or [],
                interactions=interactions or [],
            )
        )

    # --- Common slides ---
    add(
        "title",  # 使用slide_type.json中定义的"title"类型
        f"{subj}：{title}",
        [
            "授课人：待编辑（可在前端修改）",
            f"时间：{_get_current_semester()}",
            f"教学场景：{req.teaching_scene}",
        ],
        notes="封面信息可在前端编辑区直接改。",
    )

    # Objectives
    goals = req.teaching_objectives
    goal_bullets = []
    if goals.knowledge:
        goal_bullets.append(f"知识目标：{'；'.join(goals.knowledge)}")
    if goals.ability:
        goal_bullets.append(f"能力目标：{'；'.join(goals.ability)}")
    if goals.literacy:
        goal_bullets.append(f"素养目标：{'；'.join(goals.literacy)}")

    add("objectives", "教学目标", goal_bullets or ["（待补充）"], notes="可根据班级学情进一步细化。")

    # Scene-specific templates
    if req.teaching_scene == "practice":
        first_kp = kps[0] if kps else "本知识点"
        add(
            "mapping",
            "知识点与实训任务对应",
            [
                f"本次实训任务：{first_kp}的实训操作与检测",
                "对应知识点：" + "、".join(kps),
                "达标标准：能够独立完成操作，结果符合工艺要求",
            ],
            assets=[{"type": "diagram", "theme": "knowledge_to_task_mapping", "size": "16:9"}],
        )
        add(
            "prep",
            "实训准备",
            [
                f"工具/材料：{_get_tools_for_practice(first_kp, req.subject or '')}",
                f"安全检查：{_get_safety_check(first_kp, req.subject or '')}",
                "环境要求：通风良好、照明充足、工位整洁",
            ],
            assets=[{"type": "icon", "theme": "tools_and_safety", "size": "1:1"}],
        )
        # Steps
        step_count = 3
        for i in range(1, step_count + 1):
            add(
                "steps",
                f"实训步骤 {i}",
                [
                    _get_step_action(i, first_kp),
                    f"对应知识点：{first_kp}",
                ],
                assets=[{"type": "image", "theme": f"practice_step_{i}", "size": "16:9"}],
            )

        warn_title = "注意事项 / 警示" if req.warning_mark else "注意事项"
        warn_bullets = [
            f"高风险点：{_get_risk_warning(first_kp, req.subject or '')}",
            f"常见错误：{_get_common_mistake(first_kp)}",
            f"纠正方法：{_get_correction_method(first_kp)}",
        ]
        interactions = ["随堂提问：你认为最容易出错的步骤是？"] if req.include_interaction else []
        add(
            "warning",
            warn_title,
            warn_bullets,
            assets=[{"type": "icon", "theme": "warning", "size": "1:1"}],
            interactions=interactions,
        )

        if req.include_exercises:
            add(
                "exercises",
                "实训巩固 / 自测",
                [
                    _generate_exercise_question(first_kp, req.subject or "", 1),
                    _generate_exercise_question(first_kp, req.subject or "", 2),
                    f"评分要点：操作规范性、结果准确性、安全意识",
                ],
                interactions=["学员提交：拍照/勾选完成情况"] if req.include_interaction else [],
            )

        add("summary", "实训总结", ["本次实训关键点回顾", "常见问题与改进建议", f"拓展任务：尝试{first_kp}的变式操作"], notes="可追加作业或拓展练习。")

    elif req.teaching_scene == "review":
        first_kp = kps[0] if kps else "本知识点"
        add(
            "agenda",
            "复习路线",
            [
                "知识结构梳理",
                "典型题与方法总结",
                "易错点与纠错",
            ],
        )
        add(
            "relations",
            "知识结构框架",
            [f"主干：{first_kp}的核心理论", f"分支：{'、'.join(kps)}" if len(kps) > 1 else "相关应用领域", "关键关系：理论与实践的结合"],
            assets=[{"type": "diagram", "theme": "knowledge_framework", "size": "16:9", "style": "mindmap"}],
        )
        for kp in kps:
            add(
                "concept",
                f"知识点回顾：{kp}",
                ["定义/结论", "关键条件", "典型应用"],
            )

        add(
            "warning",
            "易错点清单",
            [f"易错点1：{_get_common_mistake(first_kp)}", f"易错点2：概念理解不透彻导致应用错误", f"纠错方法：{_get_correction_method(first_kp)}"],
            interactions=["投票：你最不确定的是哪一类题？"] if req.include_interaction else [],
        )

        add(
            "exercises",
            "典型题讲解",
            [_generate_exercise_question(first_kp, req.subject or "", 1), f"思路：从基本概念出发，结合题目条件分析", f"答案：详见讲解（可在讲师备注中补充）"],
        )

        if req.include_exercises:
            add(
                "exercises",
                "随堂练习",
                [_generate_exercise_question(first_kp, req.subject or "", 2), _generate_exercise_question(first_kp, req.subject or "", 3), "参考答案：见讲师备注"],
                interactions=["现场作答区"] if req.include_interaction else [],
            )

        add("summary", "复习小结", ["结构回顾", "方法总结", "考前提醒/建议"], notes="可加入时间分配与复盘提示。")

    else:
        # theory (default)
        first_kp = kps[0] if kps else "本知识点"
        add(
            "intro",
            "导入：为什么要学这个知识点？",
            [
                "真实场景/岗位任务引入",
                "本节课解决什么问题",
                "与后续知识/技能的联系",
            ],
            assets=[{"type": "image", "theme": "scene_intro", "size": "16:9", "style": "photo"}],
            interactions=["提问：你在哪些场景见过它？"] if req.include_interaction else [],
        )

        if len(kps) >= 2:
            add(
                "relations",
                "知识点关联框架",
                ["知识点之间的先后/并列关系", f"关键连接：{kps[0]}为基础，{kps[1]}为应用", f"学习路径：理论→原理→应用"],
                assets=[{"type": "diagram", "theme": "knowledge_relations", "size": "16:9", "style": "flow"}],
            )

        for kp in kps:
            add(
                "concept",
                f"核心概念：{kp}",
                ["定义", "组成/特征", "关键术语解释"],
                assets=[{"type": "diagram", "theme": f"{kp}_definition", "size": "4:3", "style": "schematic"}],
            )
            add(
                "concept",
                f"要点解析：{kp}",
                [_generate_key_points(kp, 1), _generate_key_points(kp, 2), _generate_key_points(kp, 3)],
            )

        if req.include_cases:
            add(
                "exercises",
                "案例应用",
                [f"案例背景：{first_kp}在实际工作中的应用实例", f"分析：如何运用{first_kp}的原理解决问题", "结论：掌握理论与实践的结合方法"],
                assets=[{"type": "image", "theme": "case_image", "size": "16:9", "style": "photo"}],
            )

        if req.include_exercises:
            add(
                "exercises",
                "习题巩固",
                [_generate_exercise_question(first_kp, req.subject or "", 1), _generate_exercise_question(first_kp, req.subject or "", 2), "参考答案/解析：详见讲师备注"],
                interactions=["现场作答区"] if req.include_interaction else [],
            )

        add(
            "summary",
            "总结",
            [f"本节课你应该会：掌握{first_kp}的核心概念和应用", f"关键记忆点：{first_kp}的定义、特点和使用场景", "下节课预告：深入学习相关拓展知识"],
        )

    # Adjust to slide_count (simple): trim optional slides or pad with Q&A
    target = req.slide_count or len(slides)
    if len(slides) > target:
        # Remove optional types in this order
        removable = {"agenda", "relations", "warning", "exercises"}
        i = len(slides) - 1
        while len(slides) > target and i >= 0:
            if slides[i].slide_type in removable:
                slides.pop(i)
            i -= 1
        # If still too long, truncate from the end but keep cover/objectives
        while len(slides) > target and len(slides) > 2:
            slides.pop()

    # Padding templates for unique Q&A pages
    qa_templates: List[Dict[str, Any]] = [
        {
            "title": "课堂互动 / Q&A",
            "bullets": [f"讨论问题：{first_kp}在实际工作中有哪些典型应用？", "思考题：结合所学知识，分析一个实际案例"],
        },
        {
            "title": "拓展思考",
            "bullets": [f"延伸问题：{first_kp}与其他知识点有什么关联？", f"预习提示：下节课将学习{first_kp}的进阶内容"],
        },
        {
            "title": "知识回顾",
            "bullets": [f"核心概念回顾：{first_kp}的定义和特点", "关键要点总结：本节课的重点难点"],
        },
    ]
    
    qa_index = 0
    max_qa_pages = 2  # Limit padding to avoid too many filler pages
    
    while len(slides) < target and qa_index < max_qa_pages:
        template = qa_templates[qa_index % len(qa_templates)]
        add(
            "qa",
            template["title"],
            template["bullets"],
            interactions=["举手/弹幕提问"] if req.include_interaction else [],
        )
        qa_index += 1

    # re-index
    for idx, s in enumerate(slides, start=1):
        s.index = idx

    outline = PPTOutline(
        deck_title=f"{subj}：{title}",
        subject=subj,
        knowledge_points=kps,
        teaching_scene=req.teaching_scene,
        slides=slides,
    )
    
    # 同步后处理assets：补充size/style字段（同步函数，不生成描述）
    outline = _post_process_outline_assets_sync(outline)
    
    return outline


# ============================================================================
# 基于分布的LLM智能优化生成
# ============================================================================

# 页面类型专属优化prompts
SLIDE_OPTIMIZATION_PROMPTS = {
    "title": """你是课件标题设计师。请为封面页生成专业的副标题和授课信息。
要求：
1. 副标题简洁有力，突出课程特色
2. 信息完整但不冗余
3. 体现职业教育特点""",
    
    "objectives": """你是教学目标设计师。请根据知识点生成清晰的三维教学目标。
要求：
1. 知识目标：可测量、可验证
2. 能力目标：突出职业技能
3. 素养目标：体现职业精神""",
    
    "intro": """你是课堂导入设计师。请生成引人入胜的课堂导入内容。
要求：
1. 联系实际工作场景
2. 提出驱动问题激发兴趣
3. 建立与已学知识的联系""",
    
    "concept": """你是知识讲解专家。请为概念页生成专业定义和关键特征。
要求：
1. 定义准确、表述专业
2. 突出核心特征
3. 配合示例说明""",
    
    "content": """你是课程内容设计师。请为讲解页生成详细的内容要点。
要求：
1. 逻辑清晰、层次分明
2. 理论联系实践
3. 突出重点难点""",
    
    "case": """你是案例教学专家。请为案例页生成具体的案例分析。
要求：
1. 案例真实、贴近工作实际
2. 分析过程完整
3. 结论有指导意义""",
    
    "exercise": """你是习题设计专家。请为习题页生成适合难度的练习题。
要求：
1. 题目类型多样（选择/填空/简答）
2. 难度适中，体现知识应用
3. 提供评分要点""",
    
    "discussion": """你是课堂互动设计师。请为互动页生成讨论话题和引导问题。
要求：
1. 问题开放性强
2. 能引发思考和讨论
3. 联系实际工作场景""",
    
    "summary": """你是课程总结专家。请为总结页生成核心知识点回顾。
要求：
1. 突出核心收获
2. 强调重点难点
3. 预告后续学习内容""",
}


async def generate_outline_from_distribution(
    req: TeachingRequest,
    llm: Any,
    logger: Any,
    session_id: str,
    style_name: Optional[str] = None,
) -> PPTOutline:
    """
    根据3.1模块的预估页面分布，结合LLM智能优化，生成PPT大纲。
    
    流程：
    1. 根据 req.estimated_page_distribution 确定性生成页面结构框架
    2. 对每个页面调用LLM优化内容（bullets, assets, interactions）
    3. 返回最终大纲
    
    Args:
        req: 教学需求
        llm: LLM客户端
        logger: 日志记录器
        session_id: 会话ID
        style_name: 可选的样式名称
        
    Returns:
        优化后的PPTOutline
    """
    import asyncio
    
    # 1. 检查预估分布是否有效
    if not _has_valid_distribution(req.estimated_page_distribution):
        logger.emit(session_id, "3.3", "distribution_invalid", {
            "message": "预估分布无效，使用原有逻辑"
        })
        # 降级到原有的LLM生成或确定性生成
        if llm.is_enabled():
            return await generate_outline_with_llm(req, style_name, llm, logger, session_id)
        return generate_outline(req, style_name)
    
    # 2. 根据预估分布生成页面框架
    logger.emit(session_id, "3.3", "building_from_distribution", {
        "distribution": req.estimated_page_distribution.model_dump()
    })
    slides = _build_slides_from_distribution(req)
    
    # 3. 如果LLM可用，优化每个页面的内容
    if llm.is_enabled():
        logger.emit(session_id, "3.3", "llm_optimization_start", {
            "slide_count": len(slides)
        })
        
        # 构建上下文信息
        deck_context = {
            "subject": req.subject,
            "teaching_scene": req.teaching_scene,
            "knowledge_points": req.kp_names,
            "objectives": {
                "knowledge": req.teaching_objectives.knowledge,
                "ability": req.teaching_objectives.ability,
                "literacy": req.teaching_objectives.literacy,
            },
            "total_slides": len(slides),
        }
        
        # 并行优化所有页面
        async def optimize_slide(slide: OutlineSlide) -> OutlineSlide:
            """优化单个页面的内容"""
            # 确定页面类型对应的prompt
            slide_type_key = slide.slide_type
            if slide_type_key not in SLIDE_OPTIMIZATION_PROMPTS:
                # 根据页面类型映射到通用类型
                type_mapping = {
                    "title": "title",
                    "objectives": "objectives",
                    "intro": "intro",
                    "concept": "concept",
                    "principle": "content",
                    "content": "content",
                    "case": "case",
                    "case_compare": "case",
                    "exercise": "exercise",
                    "exercises": "exercise",
                    "discussion": "discussion",
                    "qa": "discussion",
                    "summary": "summary",
                }
                slide_type_key = type_mapping.get(slide.slide_type, "content")
            
            optimization_prompt = SLIDE_OPTIMIZATION_PROMPTS.get(slide_type_key, SLIDE_OPTIMIZATION_PROMPTS["content"])
            
            system_prompt = f"""{optimization_prompt}

## 上下文
- 学科：{deck_context['subject']}
- 教学场景：{deck_context['teaching_scene']}
- 知识点：{', '.join(deck_context['knowledge_points'])}

## 输出格式
返回JSON格式：
{{
  "bullets": ["要点1", "要点2", "要点3"],
  "assets": [{{"type": "image|diagram|chart", "theme": "描述主题"}}],
  "interactions": ["互动设计（如有）"]
}}

只输出JSON，不要解释。"""
            
            user_payload = {
                "slide_index": slide.index,
                "slide_type": slide.slide_type,
                "title": slide.title,
                "current_bullets": slide.bullets,
            }
            
            try:
                parsed, meta = await llm.chat_json(
                    system_prompt,
                    json.dumps(user_payload, ensure_ascii=False),
                    '{"bullets": ["string"], "assets": [{"type": "string", "theme": "string"}], "interactions": ["string"]}',
                    temperature=0.5,
                )
                
                # 更新页面内容
                if parsed:
                    if parsed.get("bullets") and len(parsed["bullets"]) >= 2:
                        slide.bullets = parsed["bullets"]
                    if parsed.get("assets"):
                        slide.assets = parsed["assets"]
                    if parsed.get("interactions"):
                        slide.interactions = parsed["interactions"]
                
                return slide
                
            except Exception as e:
                logger.emit(session_id, "3.3", "slide_optimization_error", {
                    "slide_index": slide.index,
                    "error": str(e)
                })
                return slide  # 保持原有内容
        
        # 并行优化所有页面
        optimized_slides = await asyncio.gather(*[optimize_slide(s) for s in slides])
        slides = list(optimized_slides)
        
        logger.emit(session_id, "3.3", "llm_optimization_complete", {
            "optimized_count": len(slides)
        })
    
    # 4. 重新索引并返回
    for idx, s in enumerate(slides, start=1):
        s.index = idx
    
    outline = PPTOutline(
        deck_title=f"{req.subject or '未指定学科'}：{_deck_title(req)}",
        subject=req.subject or "未指定学科",
        knowledge_points=req.kp_names or ["未指定知识点"],
        teaching_scene=req.teaching_scene,
        slides=slides,
    )
    
    logger.emit(session_id, "3.3", "outline_from_distribution_complete", {
        "total_slides": len(slides),
        "distribution_used": req.estimated_page_distribution.model_dump()
    })
    
    # 后处理assets：生成描述、补充size/style字段
    outline = await _post_process_outline_assets(outline, req, llm, logger, session_id)
    
    return outline


# ============================================================================
# LLM智能规划生成 (Split Workflow)
# ============================================================================

async def generate_outline_structure(
    req: TeachingRequest,
    style_name: Optional[str],
    llm: Any,
    logger: Any,
    session_id: str,
) -> PPTOutline:
    """Step 1: 快速生成大纲结构（仅包含 index, type, title, brief_intent）"""
    
    if not llm.is_enabled():
        # Fallback to deterministic
        return generate_outline(req, style_name)

    # 1. Prepare Prompt - Use dynamic target_count from request
    target_count = req.slide_requirements.target_count or 12
    min_count = req.slide_requirements.min_count or max(8, target_count - 2)
    max_count = req.slide_requirements.max_count or (target_count + 2)
    
    system_prompt = _get_slide_type_definitions() + "\n\n" + f"""
    你是高职课程PPT大纲规划师。请根据教学需求，快速规划PPT的页面结构。
    
    任务：
    1. 规划 {target_count} 页 PPT（范围 {min_count}-{max_count} 页，严格遵守目标页数）
    2. 确定每页的 slide_type (必须准确)
    3. 确定每页的 title (简短明确)
    4. 简要说明每页的设计意图 (brief_intent)
    
    页面分配原则：
    - 封面(title) -> 目标(objectives) -> 导入(intro) -> 讲解(concept/content) ... -> 总结(summary)
    
    输出 JSON 格式:
    {{
      "slides": [
        {{"index": 1, "slide_type": "title", "title": "...", "brief_intent": "..."}},
        ...
      ]
    }}
    """
    
    user_payload = {
        "subject": req.subject,
        "scene": req.teaching_scene,
        "kps": req.kp_names,
        "objectives": req.teaching_objectives.knowledge,
        "target_count": req.slide_requirements.target_count
    }
    user_msg = json.dumps(user_payload, ensure_ascii=False)
    
    schema_hint = """{
      "slides": [
        {"index": "int", "slide_type": "string", "title": "string", "brief_intent": "string"}
      ]
    }"""

    # 2. Call LLM
    try:
        parsed, meta = await llm.chat_json(
            system_prompt, user_msg, schema_hint, temperature=0.3
        )
        logger.emit(session_id, "3.3", "structure_generated", meta)
        
        # 3. Construct PPTOutline (with placeholder bullets to satisfy min_length=2 validation)
        slides_data = parsed.get("slides", [])
        slides = []
        
        # 构建上下文供 fallback 使用
        deck_context = {
            "subject": req.subject,
            "scene": req.teaching_scene,
            "objectives": req.teaching_objectives.knowledge,
        }
        
        for i, s in enumerate(slides_data, 1):
            slide_title = s.get("title", f"Page {i}")
            slide_type = s.get("slide_type", "content")
            # 使用有意义的 fallback bullets (会被 expand_slide_details 覆盖)
            placeholder_bullets = _generate_fallback_bullets(slide_type, slide_title, deck_context)
            slides.append(OutlineSlide(
                index=i,
                slide_type=slide_type,
                title=slide_title,
                bullets=placeholder_bullets,  # Placeholder to pass validation
                notes=s.get("brief_intent", ""),
                assets=[],
                interactions=[]
            ))

            
        outline = PPTOutline(
            deck_title=req.subject, # Simple default
            subject=req.subject,
            knowledge_points=req.kp_names,
            teaching_scene=req.teaching_scene,
            slides=slides
        )
        
        # Adjust count to match target (important for user-specified page counts)
        outline = _adjust_outline_to_target_count(outline, req.slide_requirements.target_count)
        
        # 后处理assets：生成描述、补充size/style字段
        outline = await _post_process_outline_assets(outline, req, llm, logger, session_id)
        
        return outline
        
    except Exception as e:
        logger.emit(session_id, "3.3", "structure_error", {"error": str(e)})
        return generate_outline(req, style_name)


async def expand_slide_details(
    slide: OutlineSlide,
    req: TeachingRequest,
    deck_context: Dict[str, Any],
    llm: Any,
) -> OutlineSlide:
    """Step 2: 并行扩展单页详细内容 (Bullets, Assets, Interactions)
    
    优化策略：如果页面已有有效内容，跳过 LLM 调用以节省 token
    """
    
    # Check if slide already has valid bullets (not placeholders)
    # For exercises pages, don't check for ____ since fill-in-the-blank questions use underscores
    is_exercises_page = slide.slide_type in ("exercises", "quiz")
    
    if is_exercises_page:
        # Exercises pages: just check for 2+ bullets (allow _____ for fill-in-the-blank)
        has_valid_bullets = slide.bullets and len(slide.bullets) >= 2
    else:
        # Other pages: check for placeholders
        has_valid_bullets = (
            slide.bullets 
            and len(slide.bullets) >= 2 
            and not any("____" in b or "待填充" in b or "待补充" in b for b in slide.bullets)
        )
    
    if has_valid_bullets:
        print(f"[DEBUG] expand_slide {slide.index}: SKIPPING (already has {len(slide.bullets)} valid bullets)")
        # Keep original bullets, just ensure assets/interactions exist
        if not slide.assets:
            slide.assets = [{"type": "diagram", "theme": f"{slide.title}相关示意图"}]
        if not slide.interactions:
            slide.interactions = []
        return slide
    
    if not llm.is_enabled():
        slide.bullets = ["(Mock) Point 1", "(Mock) Point 2"]
        return slide
        
    system_prompt = """<protocol>
你是高职课程内容设计师（Module 3.3: Slide Expander）。

<zero_empty_slides_policy priority="HIGHEST">
## 🚨 零空页策略 (Zero Empty Slides)

每个slide的bullets必须至少包含2个要点，绝不允许空列表。

### 页面类型专属填充规则:

| slide_type | 必须包含的内容 |
|------------|----------------|
| title, cover | 课程名称、授课人、日期/学期、目标受众 |
| subtitle, objectives | 本节目标、关键知识点、预计时长 |
| summary | 核心收获、重点回顾、下节预告 |
| qa, discussion | 讨论问题、复习要点、拓展思考 |
| reference | 教材名称、参考资料、学习链接 |
| concept, principle | 3-6个专业知识要点 |
| steps, process | 3-5个操作步骤 |
| case, comparison | 案例背景、分析要点、结论 |
| warning | 注意事项、常见错误、安全提示 |
| exercise | 练习题目、评分标准、答案要点 |

### 示例输出:
**封面页**: ["课程：液压传动原理", "授课：AI助教", "2024年秋季", "面向：机电专业"]
**章节页**: ["本节目标：理解泵的原理", "重点概念：齿轮泵vs叶片泵", "预计时长：15分钟"]
**问答页**: ["复习：什么是帕斯卡定律?", "讨论：实际失效案例", "预告：回路设计"]
</zero_empty_slides_policy>

<output_format>
{
  "bullets": ["要点1", "要点2", ...],  // 最少2个，禁止空数组
  "assets": [{"type": "image|diagram|chart", "theme": "描述主题"}],
  "interactions": ["互动设计"]
}
</output_format>
</protocol>"""


    
    user_payload = {
        "context": deck_context,
        "slide": {
            "type": slide.slide_type,
            "title": slide.title,
            "intent": slide.notes
        }
    }
    
    try:
        parsed, meta = await llm.chat_json(
            system_prompt, 
            json.dumps(user_payload, ensure_ascii=False),
            '{"bullets": ["string"], "assets": [{"type": "string", "theme": "string"}], "interactions": ["string"]}'
        )
        
        # Debug logging
        print(f"[DEBUG] expand_slide {slide.index}: parsed = {parsed}")
        
        # Extract bullets with fallback
        bullets = parsed.get("bullets") if parsed else None
        if bullets and isinstance(bullets, list) and len(bullets) > 0:
            slide.bullets = bullets
        else:
            # Generate fallback bullets based on slide type and title (使用更有意义的内容)
            slide.bullets = _generate_fallback_bullets(slide.slide_type, slide.title, deck_context)
            print(f"[DEBUG] expand_slide {slide.index}: using fallback bullets (parsed was empty)")
        
        slide.assets = parsed.get("assets", slide.assets) if parsed else slide.assets
        slide.interactions = parsed.get("interactions", slide.interactions) if parsed else slide.interactions
        
        # 确保assets包含size和style字段，并为diagram/photo生成描述
        processed_assets = []
        for asset in slide.assets:
            asset = _ensure_asset_fields(asset.copy())
            # 为diagram和photo类型生成描述（如果LLM可用）
            if llm and llm.is_enabled():
                # 需要logger和session_id，但expand_slide_details没有这些参数
                # 暂时只补充字段，描述生成在后续统一处理
                pass
            processed_assets.append(asset)
        slide.assets = processed_assets
        
        return slide
        
    except Exception as e:
        print(f"[ERROR] expand_slide {slide.index}: {e}")
        # Provide fallback bullets on error (使用更有意义的内容)
        slide.bullets = _generate_fallback_bullets(slide.slide_type, slide.title, deck_context)
        
        # 确保assets包含size和style字段
        processed_assets = []
        for asset in slide.assets:
            asset = _ensure_asset_fields(asset.copy())
            processed_assets.append(asset)
        slide.assets = processed_assets
        
        return slide


# Keep original monolithic function for backward compatibility or direct fallback
async def generate_outline_with_llm(
    req: TeachingRequest,
    style_name: Optional[str],
    llm: Any,  # LLMClient
    logger: Any,  # WorkflowLogger
    session_id: str,
) -> PPTOutline:
    """使用LLM进行智能规划生成PPT大纲 (Monolithic Strategy)。"""
    
    if not llm.is_enabled():
        return generate_outline(req, style_name)
    
    # 构建用户输入消息
    user_payload = {
        "teaching_request": {
            "subject": req.subject,
            "professional_category": req.professional_category,
            "teaching_scene": req.teaching_scene,
            "knowledge_points": [
                {
                    "name": kp.name,
                    "type": kp.type,
                    "difficulty_level": kp.difficulty_level,
                    "is_core": getattr(kp, "is_core", True),
                    "estimated_teaching_time_min": getattr(kp, "estimated_teaching_time_min", None),
                }
                for kp in req.knowledge_points
            ],
            "teaching_objectives": {
                "knowledge": req.teaching_objectives.knowledge,
                "ability": req.teaching_objectives.ability,
                "literacy": req.teaching_objectives.literacy,
            },
            "slide_requirements": {
                "target_count": req.slide_requirements.target_count,
                "min_count": req.slide_requirements.min_count,
                "max_count": req.slide_requirements.max_count,
                "lesson_duration_min": req.slide_requirements.lesson_duration_min,
            },
            "special_requirements": {
                "cases": {
                    "enabled": req.special_requirements.cases.enabled,
                    "count": req.special_requirements.cases.count,
                    "case_type": getattr(req.special_requirements.cases, "case_type", None),
                },
                "exercises": {
                    "enabled": req.special_requirements.exercises.enabled,
                    "total_count": req.special_requirements.exercises.total_count,
                },
                "interaction": {
                    "enabled": req.special_requirements.interaction.enabled,
                    "types": req.special_requirements.interaction.types,
                },
                "warnings": {
                    "enabled": req.special_requirements.warnings.enabled,
                },
            },
            "estimated_page_distribution": req.estimated_page_distribution.model_dump() if req.estimated_page_distribution else None,
        },
        "style_name": style_name,
    }
    
    user_msg = json.dumps(user_payload, ensure_ascii=False, indent=2)
    
    # 获取JSON Schema
    schema_hint = PPTOutline.model_json_schema()
    schema_str = json.dumps(schema_hint, ensure_ascii=False, indent=2)
    
    # 使用动态生成的prompt
    system_prompt = _build_outline_planning_prompt()
    
    # 记录日志
    logger.emit(session_id, "3.3", "llm_planning_prompt", {
        "system": system_prompt,
        "user": user_payload,
        "schema_hint": schema_hint,
    })
    
    try:
        # 调用LLM进行智能规划
        parsed, meta = await llm.chat_json(
            system_prompt,
            user_msg,
            schema_str,
            temperature=0.3,  # 稍高的温度以获得更多创意
        )
        
        logger.emit(session_id, "3.3", "llm_planning_response", meta)
        
        # 验证并返回结果
        outline = PPTOutline.model_validate(parsed)
        
        # 后处理：确保页面数量符合要求
        outline = _adjust_outline_to_target_count(outline, req.slide_requirements.target_count)
        
        # 后处理：使用LLM更准确地判断每页的slide_type
        outline = await _refine_slide_types(outline, llm, logger, session_id)
        
        # 后处理assets：生成描述、补充size/style字段
        outline = await _post_process_outline_assets(outline, req, llm, logger, session_id)
        
        return outline
        
    except Exception as e:
        # LLM调用失败，降级到确定性生成
        logger.emit(session_id, "3.3", "llm_planning_error", {
            "error": str(e),
            "fallback_to_deterministic": True,
        })
        return generate_outline(req, style_name)


async def _refine_slide_types(
    outline: PPTOutline,
    llm: Any,  # LLMClient
    logger: Any,  # WorkflowLogger
    session_id: str,
) -> PPTOutline:
    """使用LLM更准确地判断每页的slide_type"""
    if not llm.is_enabled():
        return outline
    
    slide_type_data = _load_slide_types()
    available_types = [st["slide_type"] for st in slide_type_data.get("slide_types", [])]
    
    type_refinement_prompt = f"""你是PPT页面类型判断专家。请根据每页的实际内容（title和bullets），从以下页面类型中选择最准确的一个：

{_get_slide_type_definitions()}

## 判断规则
1. 仔细分析每页的title和bullets内容
2. 选择最能准确描述该页功能和内容特点的slide_type
3. 如果内容同时符合多个类型，选择最核心、最主要的类型
4. 封面页必须使用"title"类型
5. 教学目标页必须使用"objectives"类型

## 输入格式
你将收到一个包含slides数组的JSON对象

## 输出要求
返回完整的PPTOutline JSON对象，只修改slides数组中每页的slide_type字段

只输出JSON对象，不要解释。"""
    
    outline_data = outline.model_dump(mode="json")
    user_msg = json.dumps({
        "outline": outline_data,
        "instruction": "请为每页选择最准确的slide_type，确保类型准确匹配页面内容。"
    }, ensure_ascii=False, indent=2)
    
    schema_hint = PPTOutline.model_json_schema()
    schema_str = json.dumps(schema_hint, ensure_ascii=False, indent=2)
    
    try:
        logger.emit(session_id, "3.3", "slide_type_refinement_prompt", {
            "system": type_refinement_prompt,
            "user": outline_data
        })
        
        parsed, meta = await llm.chat_json(
            type_refinement_prompt,
            user_msg,
            schema_str,
            temperature=0.1,
        )
        
        logger.emit(session_id, "3.3", "slide_type_refinement_response", meta)
        
        if isinstance(parsed, dict) and "outline" in parsed and len(parsed) == 1:
            parsed = parsed["outline"]
        elif isinstance(parsed, dict) and "outline" in parsed:
            parsed = parsed["outline"]
        
        refined_outline = PPTOutline.model_validate(parsed)
        
        for slide in refined_outline.slides:
            if slide.slide_type not in available_types:
                logger.emit(session_id, "3.3", "slide_type_warning", {
                    "slide_index": slide.index,
                    "invalid_type": slide.slide_type,
                    "fallback_to_original": True,
                })
                original_slide = next((s for s in outline.slides if s.index == slide.index), None)
                if original_slide:
                    slide.slide_type = original_slide.slide_type
        
        return refined_outline
        
    except Exception as e:
        logger.emit(session_id, "3.3", "slide_type_refinement_error", {
            "error": str(e),
            "fallback_to_original": True,
        })
        return outline



def _adjust_outline_to_target_count(outline: PPTOutline, target_count: Optional[int]) -> PPTOutline:
    """调整大纲页面数量以符合目标页数要求（智能合并精简策略）。
    
    实现三级优先级策略：
    1. 优先级1: 移除非教学必需页面（agenda, warning, qa）
    2. 优先级2: 合并同主题内容页（intro+concept, 案例页, 练习页）
    3. 优先级3: 精简内容（最后手段，确保不删除核心知识点页面）
    """
    if target_count is None:
        return outline
    
    slides = outline.slides.copy()
    current_count = len(slides)
    
    if current_count > target_count:
        # 优先级1: 移除非教学必需页面
        slides = _remove_non_essential_slides(slides, target_count)
        
        # 如果还不够，进行优先级2: 合并同主题内容页
        if len(slides) > target_count:
            slides = _merge_similar_slides(slides, target_count)
        
        # 如果还不够，进行优先级3: 精简内容（最后手段）
        if len(slides) > target_count:
            slides = _simplify_content_slides(slides, target_count)
    
    elif current_count < target_count:
        # 添加Q&A页面
        first_kp = outline.knowledge_points[0] if outline.knowledge_points else "本知识点"
        while len(slides) < target_count:
            qa_slide = OutlineSlide(
                index=len(slides) + 1,
                slide_type="qa",
                title="课堂互动 / Q&A",
                bullets=[f"讨论问题：{first_kp}在实际中有哪些应用？", "思考题：如何将今天所学应用到实际工作中？"],
                interactions=["举手/弹幕提问"],
            )
            slides.append(qa_slide)
    
    # 重新索引
    for idx, slide in enumerate(slides, start=1):
        slide.index = idx
    
    # 创建新的大纲对象
    return PPTOutline(
        deck_title=outline.deck_title,
        subject=outline.subject,
        knowledge_points=outline.knowledge_points,
        teaching_scene=outline.teaching_scene,
        slides=slides,
    )


def _remove_non_essential_slides(slides: List[OutlineSlide], target_count: int) -> List[OutlineSlide]:
    """优先级1: 移除非教学必需页面。
    
    移除顺序：
    1. agenda（目录页）：内容可精简为封面页下方小字或并入objectives
    2. warning（注意页）：将易错点、安全警示嵌入对应steps或concept的bullets
    3. qa（问答页）：将互动问答内容并入summary作为"课后答疑"板块
    """
    result = []
    removed_count = 0
    target_removal = len(slides) - target_count
    
    # 按优先级移除
    removable_priority = ["agenda", "qa", "warning"]  # agenda优先级最高
    
    for slide in slides:
        if removed_count < target_removal and slide.slide_type in removable_priority:
            # 尝试将内容嵌入到相关页面
            if slide.slide_type == "warning":
                # 将warning内容嵌入到前面的concept或steps页面
                _embed_warning_content(result, slide)
            elif slide.slide_type == "qa":
                # 将qa内容嵌入到summary页面
                _embed_qa_content(result, slide)
            # agenda直接移除，不需要嵌入
            removed_count += 1
        else:
            result.append(slide)
    
    return result


def _merge_similar_slides(slides: List[OutlineSlide], target_count: int) -> List[OutlineSlide]:
    """优先级2: 合并同主题内容页。
    
    合并策略：
    1. 知识点导入+概念合并：将同一知识点的intro和concept合并为1页
    2. 多案例页合并：将相似案例合并为1页"典型案例对比分析"
    3. 练习页整合：将多个小题的exercises页合并为1页"综合巩固练习"
    """
    result = []
    i = 0
    
    while i < len(slides):
        current = slides[i]
        
        # 尝试合并intro和concept
        if current.slide_type == "intro" and i + 1 < len(slides):
            next_slide = slides[i + 1]
            if next_slide.slide_type == "concept":
                merged = _merge_intro_and_concept(current, next_slide)
                result.append(merged)
                i += 2
                continue
        
        # 尝试合并多个案例页
        if current.slide_type in ["exercises", "case_study"] and current.title.startswith("案例"):
            case_slides = [current]
            j = i + 1
            while j < len(slides) and slides[j].slide_type == current.slide_type:
                case_slides.append(slides[j])
                j += 1
            if len(case_slides) > 1:
                merged = _merge_case_slides(case_slides)
                result.append(merged)
                i = j
                continue
        
        # 尝试合并多个练习页
        if current.slide_type == "exercises":
            exercise_slides = [current]
            j = i + 1
            while j < len(slides) and slides[j].slide_type == "exercises":
                exercise_slides.append(slides[j])
                j += 1
            if len(exercise_slides) > 1:
                merged = _merge_exercise_slides(exercise_slides)
                result.append(merged)
                i = j
                continue
        
        result.append(current)
        i += 1
    
    # 如果合并后仍然超过目标，继续移除
    if len(result) > target_count:
        # 移除bridge、relations等过渡页
        result = [s for s in result if s.slide_type not in ["bridge", "relations"]]
    
    return result


def _simplify_content_slides(slides: List[OutlineSlide], target_count: int) -> List[OutlineSlide]:
    """优先级3: 精简内容（最后手段）。
    
    确保不删除核心知识点页面（cover, objectives, concept, summary）。
    优先精简非核心内容页。
    """
    result = []
    core_types = {"cover", "objectives", "concept", "summary"}
    removable_types = {"bridge", "relations", "intro"}
    
    # 先移除可移除类型
    for slide in slides:
        if len(result) >= target_count and slide.slide_type in removable_types:
            continue
        result.append(slide)
    
    # 如果还不够，从末尾移除非核心页面（但保留封面和目标）
    while len(result) > target_count and len(result) > 2:
        if result[-1].slide_type not in core_types:
            result.pop()
        else:
            break
    
    return result


def _merge_intro_and_concept(intro: OutlineSlide, concept: OutlineSlide) -> OutlineSlide:
    """合并知识点的导入和概念页。"""
    merged_title = f"{concept.title}——从案例看核心概念"
    merged_bullets = intro.bullets[:2] + concept.bullets[:3]  # 合并要点，限制数量
    merged_assets = (intro.assets or []) + (concept.assets or [])
    merged_interactions = (intro.interactions or []) + (concept.interactions or [])
    
    return OutlineSlide(
        index=intro.index,
        slide_type="concept",
        title=merged_title,
        bullets=merged_bullets,
        notes=concept.notes or intro.notes,
        assets=merged_assets[:3],  # 限制素材数量
        interactions=merged_interactions[:2],  # 限制互动数量
    )


def _merge_case_slides(case_slides: List[OutlineSlide]) -> OutlineSlide:
    """合并案例页。"""
    merged_title = "典型案例对比分析"
    merged_bullets = []
    for i, slide in enumerate(case_slides[:3], 1):  # 最多合并3个案例
        merged_bullets.append(f"案例{i}：{slide.title}")
        merged_bullets.extend(slide.bullets[:2])  # 每个案例取前2个要点
    
    merged_assets = []
    for slide in case_slides[:3]:
        merged_assets.extend(slide.assets or [])
    
    return OutlineSlide(
        index=case_slides[0].index,
        slide_type="case_study",
        title=merged_title,
        bullets=merged_bullets[:8],  # 限制总要点数
        notes="通过对比分析多个典型案例，加深理解",
        assets=merged_assets[:2],  # 限制素材数量
        interactions=case_slides[0].interactions or [],
    )


def _merge_exercise_slides(exercise_slides: List[OutlineSlide]) -> OutlineSlide:
    """合并练习页。"""
    merged_title = "综合巩固练习"
    merged_bullets = []
    for i, slide in enumerate(exercise_slides, 1):
        merged_bullets.append(f"【题型{i}】{slide.title}")
        merged_bullets.extend(slide.bullets[:2])  # 每个练习取前2个要点
    
    return OutlineSlide(
        index=exercise_slides[0].index,
        slide_type="exercises",
        title=merged_title,
        bullets=merged_bullets[:10],  # 限制总要点数
        notes="按题型分块展示，便于系统练习",
        assets=exercise_slides[0].assets or [],
        interactions=exercise_slides[0].interactions or [],
    )


def _embed_warning_content(slides: List[OutlineSlide], warning_slide: OutlineSlide) -> None:
    """将warning内容嵌入到相关页面。"""
    if not slides:
        return
    
    # 找到最近的concept或steps页面
    for slide in reversed(slides):
        if slide.slide_type in ["concept", "steps"]:
            # 将warning的要点添加到该页面的bullets
            warning_bullets = [f"⚠️ {b}" for b in warning_slide.bullets[:2]]
            slide.bullets.extend(warning_bullets)
            break


def _embed_qa_content(slides: List[OutlineSlide], qa_slide: OutlineSlide) -> None:
    """将qa内容嵌入到summary页面。"""
    # 找到summary页面
    for slide in reversed(slides):
        if slide.slide_type == "summary":
            # 将qa内容添加到summary作为"课后答疑"板块
            qa_section = ["课后答疑："]
            qa_section.extend(qa_slide.bullets[:3])
            slide.bullets.extend(qa_section)
            break
