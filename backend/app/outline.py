from __future__ import annotations

from typing import Any, Dict, List

from .schemas import OutlineSlide, PPTOutline, TeachingRequest


def _deck_title(req: TeachingRequest) -> str:
    kps = req.kp_names
    if kps:
        if len(kps) == 1:
            return kps[0]
        return "、".join(kps)
    return "知识点课件"


def generate_outline(req: TeachingRequest, style_name: str | None = None) -> PPTOutline:
    """Generate a slide-level outline following 方案 3.3.

    This is a deterministic baseline. If LLM is enabled, the workflow may
    ask LLM to rewrite titles/bullets, but the structure is controlled here.
    """

    title = _deck_title(req)
    subj = req.subject or "未指定学科"
    kps = req.kp_names or ["未指定知识点"]

    slides: List[OutlineSlide] = []

    def add(slide_type: str, title: str, bullets: List[str], notes: str | None = None, assets: List[Dict[str, Any]] | None = None, interactions: List[str] | None = None):
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
        "cover",
        f"{subj}：{title}",
        [
            "授课人：_____",
            "时间：_____",
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
        add(
            "mapping",
            "知识点与实训任务对应",
            [
                "本次实训任务：_____",
                "对应知识点：" + "、".join(kps),
                "达标标准：_____",
            ],
            assets=[{"type": "diagram", "theme": "knowledge_to_task_mapping", "size": "16:9"}],
        )
        add(
            "prep",
            "实训准备",
            [
                "工具/材料：_____",
                "安全检查：_____",
                "环境要求：_____",
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
                    f"操作要点：步骤{i}的关键动作/顺序",
                    "质量要点：如何判断做对了",
                    "对应知识点：_____",
                ],
                assets=[{"type": "image", "theme": f"practice_step_{i}", "size": "16:9"}],
            )

        warn_title = "注意事项 / 警示" if req.warning_mark else "注意事项"
        warn_bullets = [
            "高风险点：_____",
            "常见错误：_____",
            "纠正方法：_____",
        ]
        interactions = ["随堂提问：你认为最容易出错的步骤是？"] if req.include_interaction else []
        add(
            "warnings",
            warn_title,
            warn_bullets,
            assets=[{"type": "icon", "theme": "warning", "size": "1:1"}],
            interactions=interactions,
        )

        if req.include_exercises:
            add(
                "practice_check",
                "实训巩固 / 自测",
                [
                    "自测题1：_____",
                    "自测题2：_____",
                    "评分要点：_____",
                ],
                interactions=["学员提交：拍照/勾选完成情况"] if req.include_interaction else [],
            )

        add("summary", "实训总结", ["本次实训关键点回顾", "常见问题与改进建议", "拓展任务：_____"], notes="可追加作业或拓展练习。")

    elif req.teaching_scene == "review":
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
            "framework",
            "知识结构框架",
            ["主干：____", "分支：____", "关键关系：____"],
            assets=[{"type": "mindmap", "theme": "knowledge_framework", "size": "16:9"}],
        )
        for kp in kps:
            add(
                "recap",
                f"知识点回顾：{kp}",
                ["定义/结论", "关键条件", "典型应用"],
            )

        add(
            "mistakes",
            "易错点清单",
            ["易错点1：____", "易错点2：____", "纠错方法：____"],
            interactions=["投票：你最不确定的是哪一类题？"] if req.include_interaction else [],
        )

        add(
            "typical",
            "典型题讲解",
            ["题目：____", "思路：____", "答案：____"],
        )

        if req.include_exercises:
            add(
                "exercises",
                "随堂练习",
                ["练习1：____", "练习2：____", "参考答案：____"],
                interactions=["现场作答区"] if req.include_interaction else [],
            )

        add("summary", "复习小结", ["结构回顾", "方法总结", "考前提醒/建议"], notes="可加入时间分配与复盘提示。")

    else:
        # theory (default)
        add(
            "intro",
            "导入：为什么要学这个知识点？",
            [
                "真实场景/岗位任务引入",
                "本节课解决什么问题",
                "与后续知识/技能的联系",
            ],
            assets=[{"type": "image", "theme": "scene_intro", "size": "16:9"}],
            interactions=["提问：你在哪些场景见过它？"] if req.include_interaction else [],
        )

        if len(kps) >= 2:
            add(
                "framework",
                "知识点关联框架",
                ["知识点之间的先后/并列关系", "关键连接：____", "学习路径：____"],
                assets=[{"type": "diagram", "theme": "knowledge_relations", "size": "16:9"}],
            )

        for kp in kps:
            add(
                "concept",
                f"核心概念：{kp}",
                ["定义", "组成/特征", "关键术语解释"],
                assets=[{"type": "diagram", "theme": f"{kp}_definition", "size": "4:3"}],
            )
            add(
                "keypoints",
                f"要点解析：{kp}",
                ["要点1：____", "要点2：____", "要点3：____"],
            )

        if req.include_cases:
            add(
                "case",
                "案例应用",
                ["案例背景：____", "分析：____", "结论：____"],
                assets=[{"type": "image", "theme": "case_image", "size": "16:9"}],
            )

        if req.include_exercises:
            add(
                "exercises",
                "习题巩固",
                ["题目1：____", "题目2：____", "参考答案/解析：____"],
                interactions=["现场作答区"] if req.include_interaction else [],
            )

        add(
            "summary",
            "总结",
            ["本节课你应该会：____", "关键记忆点：____", "下节课预告：____"],
        )

    # Adjust to slide_count (simple): trim optional slides or pad with Q&A
    target = req.slide_count or len(slides)
    if len(slides) > target:
        # Remove optional types in this order
        removable = {"agenda", "framework", "mistakes", "typical", "case", "exercises", "practice_check"}
        i = len(slides) - 1
        while len(slides) > target and i >= 0:
            if slides[i].slide_type in removable:
                slides.pop(i)
            i -= 1
        # If still too long, truncate from the end but keep cover/objectives
        while len(slides) > target and len(slides) > 2:
            slides.pop()

    while len(slides) < target:
        add(
            "qa",
            "课堂互动 / Q&A",
            ["问题1：____", "问题2：____"],
            interactions=["举手/弹幕提问"] if req.include_interaction else [],
        )

    # re-index
    for idx, s in enumerate(slides, start=1):
        s.index = idx

    return PPTOutline(
        deck_title=f"{subj}：{title}",
        subject=subj,
        knowledge_points=kps,
        teaching_scene=req.teaching_scene,
        slides=slides,
    )
