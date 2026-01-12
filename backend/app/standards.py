"""Course-standard defaults (minimal).

来自《AI生成PPT技术方案》中 3.1「需求校验与补全」：
- 优先通过交互提问引导教师补充缺失信息；
- 若用户选择自动补全，则按学科课程标准默认填充（理论课默认包含知识目标和素养目标；实训课默认包含能力目标）。

本文件提供一个“可运行”的最小默认库：
- 不依赖外部数据库；
- 便于你后续接入 MySQL/知识库（用 subject + scene 检索标准目标）。
"""

from __future__ import annotations

from typing import Dict, Optional


def default_goals(teaching_scene: str, subject: Optional[str] = None) -> Dict[str, str]:
    subj = subject or "本学科"

    # 实训课：默认强调能力目标
    if teaching_scene == "practice":
        return {
            "knowledge": f"掌握与{ subj }相关的关键概念，并能将其对应到操作步骤与注意事项。",
            "ability": "能够按照规范流程完成实训操作，并能自查关键风险点与质量要点。",
            "literacy": "形成安全意识、规范意识与团队协作意识，养成记录与复盘习惯。",
        }

    # 复习课：默认强调梳理与迁移
    if teaching_scene == "review":
        return {
            "knowledge": "回顾并串联核心知识点，形成清晰的知识结构框架。",
            "ability": "能够用典型题/情境完成知识迁移，并总结常见错误与解题策略。",
            "literacy": "培养反思与自我评估能力，形成持续改进的学习习惯。",
        }

    # 理论课（默认）：包含知识目标与素养目标（能力目标可选）
    return {
        "knowledge": f"理解{ subj }的定义、组成与关键原理，能够用规范表述解释核心概念。",
        "ability": "能够从简单情境中识别与应用该知识点，完成基础分析或推理。",
        "literacy": "形成严谨求实、规范表达与问题意识，能将知识与职业情境建立联系。",
    }
