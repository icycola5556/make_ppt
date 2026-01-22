"""
Module 3.5: 完整的 Mock 数据（3.1-3.4 输出）

基于真实日志和代码结构构建的完整Mock数据，
可直接用于测试3.5模块的渲染功能。

数据来源参考：
- 3.1 TeachingRequest 结构
- 3.2 StyleConfig 结构
- 3.3 PPTOutline 结构
- 3.4 SlideDeckContent 结构
"""

from typing import Any, Dict, List
from datetime import datetime


# ============================================================================
# 3.1 TeachingRequest 完整输出
# ============================================================================

MOCK_TEACHING_REQUEST: Dict[str, Any] = {
    "request_id": "mock_request_001",
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "subject_info": {
        "subject_name": "机械制造",
        "subject_category": "engineering",
        "sub_field": "液压传动",
    },
    "knowledge_points": [
        {
            "id": "kp1",
            "name": "液压系统的基本组成",
            "type": "theory",
            "is_core": True,
            "difficulty_level": "medium",
            "estimated_teaching_time_min": 10,
        },
        {
            "id": "kp2",
            "name": "帕斯卡定律与液压传动原理",
            "type": "mixed",
            "is_core": True,
            "difficulty_level": "hard",
            "estimated_teaching_time_min": 15,
        },
        {
            "id": "kp3",
            "name": "液压泵的结构与工作原理",
            "type": "practice",
            "is_core": True,
            "difficulty_level": "medium",
            "estimated_teaching_time_min": 12,
        },
        {
            "id": "kp4",
            "name": "液压缸的类型与选用",
            "type": "practice",
            "is_core": False,
            "difficulty_level": "easy",
            "estimated_teaching_time_min": 8,
        },
    ],
    "knowledge_structure": {
        "total_count": 4,
        "relation_type": "progressive",
        "relation_description": "从基础概念到实际应用的递进关系",
        "relation_graph": None,
    },
    "teaching_scenario": {
        "scene_type": "practice",
        "scene_label": "实操教学",
        "sub_type": "实训操作",
    },
    "teaching_objectives": {
        "knowledge": [
            "理解液压系统的基本组成和工作原理",
            "掌握帕斯卡定律在液压传动中的应用",
            "了解液压泵和液压缸的结构特点",
        ],
        "ability": [
            "能够识别液压系统的主要部件",
            "能够正确选用液压元件",
            "能够进行简单的液压系统故障诊断",
        ],
        "literacy": ["培养安全操作意识和规范操作习惯", "增强工程实践能力和创新思维"],
        "auto_generated": False,
    },
    "slide_requirements": {
        "target_count": 8,
        "min_count": 6,
        "max_count": 10,
        "flexibility": "adjustable",
        "lesson_duration_min": 45,
        "llm_recommended_count": None,
        "page_conflict_resolution": None,
    },
    "special_requirements": {
        "cases": {
            "enabled": True,
            "count": 1,
            "case_type": "practical_application",
            "description": "液压系统在挖掘机中的应用",
        },
        "exercises": {
            "enabled": True,
            "total_count": 3,
            "per_knowledge_point": 0,
            "types": ["multiple_choice", "fill_blank"],
        },
        "interaction": {"enabled": True, "types": ["qa", "discussion"]},
        "warnings": {"enabled": True, "color": "#e74c3c"},
        "animations": {"enabled": False},
    },
    "estimated_page_distribution": {
        "cover": 1,
        "objectives": 1,
        "introduction": 0,
        "concept_definition": 2,
        "explanation": 2,
        "case_study": 1,
        "exercises": 1,
        "interaction": 0,
        "summary": 1,
    },
    "parsing_metadata": {
        "raw_input": "我想制作一个关于液压系统工作原理的教学课件，时长45分钟，面向机械制造专业学生，实操教学场景，需要包含液压泵、液压缸等核心部件的讲解，以及帕斯卡定律的原理说明。",
        "input_source": "text",
        "parsing_method": "llm_extraction",
        "request_id": "mock_001",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    },
    "internal_interaction_stage": "confirmed",
    "display_summary": None,
    "interaction_metadata": {},
}


# ============================================================================
# 3.2 StyleConfig 完整输出
# ============================================================================

MOCK_STYLE_CONFIG: Dict[str, Any] = {
    "style_name": "practice_steps",
    "color": {
        "primary": "#2c3e50",
        "secondary": "#34495e",
        "accent": "#3498db",
        "text": "#2c3e50",
        "muted": "#ecf0f1",
        "background": "#ffffff",
        "warning": "#e74c3c",
    },
    "font": {
        "title_family": "Microsoft YaHei",
        "heading_family": "Microsoft YaHei",
        "body_family": "Microsoft YaHei",
        "title_size": 48,
        "heading_size": 36,
        "body_size": 24,
        "line_height": 1.5,
    },
    "layout": {
        "width": 1920,
        "height": 1080,
        "padding": 60,
        "content_margin": 40,
        "grid_columns": 12,
        "grid_rows": 8,
    },
    "imagery": {
        "image_style": "photo",
        "icon_style": "flat",
        "chart_preference": ["bar_chart", "pie_chart"],
    },
    "animation": {"type": "fade", "duration": 500, "direction": "horizontal"},
}


# ============================================================================
# 3.3 PPTOutline 完整输出
# ============================================================================

MOCK_PPT_OUTLINE: Dict[str, Any] = {
    "deck_title": "液压系统工作原理",
    "subject": "机械制造",
    "knowledge_points": [
        "液压系统的基本组成",
        "帕斯卡定律与液压传动原理",
        "液压泵的结构与工作原理",
        "液压缸的类型与选用",
    ],
    "teaching_scene": "practice",
    "slides": [
        {
            "index": 1,
            "slide_type": "title",
            "title": "液压系统工作原理",
            "bullets": ["主讲教师", "课程时长", "教学目标"],
            "notes": "封面页，展示课程主题",
            "interactions": [],
            "assets": [],
        },
        {
            "index": 2,
            "slide_type": "objectives",
            "title": "本次课程目标",
            "bullets": [
                "理解液压系统的基本组成和工作原理",
                "掌握帕斯卡定律在液压传动中的应用",
                "了解液压泵和液压缸的结构特点",
            ],
            "notes": "教学目标页",
            "interactions": [],
            "assets": [],
        },
        {
            "index": 3,
            "slide_type": "concept",
            "title": "液压系统的五大组成部分",
            "bullets": [
                "动力元件：液压泵（机械能→液压能）",
                "执行元件：液压缸/马达（液压能→机械能）",
                "控制元件：各种阀门（控制压力、流量、方向）",
                "辅助元件：油箱、滤油器、管路",
                "工作介质：液压油",
            ],
            "notes": "概念讲解页",
            "interactions": ["提问：液压系统的核心是什么？"],
            "assets": [
                {"type": "diagram", "theme": "液压系统五大组成全景图", "size": "large"}
            ],
        },
        {
            "index": 4,
            "slide_type": "content",
            "title": "核心动力：液压泵",
            "bullets": [
                "作用：为系统提供压力油，是心脏部件",
                "常用类型：齿轮泵、叶片泵、柱塞泵",
                "特点：齿轮泵结构简单但噪音大，柱塞泵压力高效率高",
                "维护重点：防止吸空，定期更换密封件",
            ],
            "notes": "内容讲解页",
            "interactions": [],
            "assets": [
                {
                    "type": "photo",
                    "theme": "工业齿轮泵内部精密结构特写",
                    "size": "medium",
                }
            ],
        },
        {
            "index": 5,
            "slide_type": "content",
            "title": "执行机构：液压缸",
            "bullets": [
                "作用：将液压能转换为直线运动的机械能",
                "分类：单作用式（靠外力回程）、双作用式（靠油压回程）",
                "关键参数：缸径（决定推力）、行程（决定距离）",
                "应用：挖掘机动臂、注塑机合模机构",
            ],
            "notes": "内容讲解页",
            "interactions": [],
            "assets": [
                {"type": "photo", "theme": "挖掘机液压缸工作特写", "size": "medium"}
            ],
        },
        {
            "index": 6,
            "slide_type": "concept",
            "title": "基本原理：帕斯卡定律",
            "bullets": [
                "定义：密闭液体上的压强向各个方向传递不变",
                "公式：F = P × A（力=压强×面积）",
                "应用：千斤顶原理（大力举小重物）",
                "优势：可以实现力的放大和远距离传递",
            ],
            "notes": "原理讲解页",
            "interactions": [],
            "assets": [
                {
                    "type": "diagram",
                    "theme": "帕斯卡定律千斤顶原理示意图",
                    "size": "medium",
                }
            ],
        },
        {
            "index": 7,
            "slide_type": "steps",
            "title": "液压系统标准启动流程",
            "bullets": [
                "检查油箱液位是否在标准刻度线以上",
                "确认所有换向阀处于中位，卸荷启动",
                "点动电机，检查旋转方向是否正确",
                "空载运行5-10分钟，进行排气",
                "逐步加载，观察压力表读数是否稳定",
            ],
            "notes": "操作步骤页",
            "interactions": [],
            "assets": [
                {"type": "photo", "theme": "液压站控制面板操作", "size": "large"}
            ],
        },
        {
            "index": 8,
            "slide_type": "summary",
            "title": "课程总结",
            "bullets": [
                "液压系统通过液压油传递动力，遵循帕斯卡定律",
                "五大组成部分各司其职，缺一不可",
                "正确的启动和维护流程能延长系统寿命",
                "油液清洁度是液压系统的生命线",
            ],
            "notes": "总结页",
            "interactions": ["课后作业：绘制液压系统原理图"],
            "assets": [],
        },
    ],
}


# ============================================================================
# 3.4 SlideDeckContent 完整输出
# ============================================================================

MOCK_SLIDE_DECK_CONTENT: Dict[str, Any] = {
    "deck_title": "液压系统工作原理",
    "pages": [
        {
            "index": 1,
            "slide_type": "title",
            "title": "液压系统工作原理",
            "layout": {"template": "title_only"},
            "elements": [],
            "speaker_notes": "开场介绍课程主题",
        },
        {
            "index": 2,
            "slide_type": "objectives",
            "title": "本次课程目标",
            "layout": {"template": "title_bullets"},
            "elements": [
                {
                    "id": "el_1",
                    "type": "bullets",
                    "x": 0.1,
                    "y": 0.2,
                    "w": 0.8,
                    "h": 0.7,
                    "content": {
                        "items": [
                            "理解液压系统的基本组成和工作原理",
                            "掌握帕斯卡定律在液压传动中的应用",
                            "了解液压泵和液压缸的结构特点",
                        ]
                    },
                    "style": {"role": "body"},
                }
            ],
            "speaker_notes": "明确教学目标",
        },
        {
            "index": 3,
            "slide_type": "concept",
            "title": "液压系统的五大组成部分",
            "layout": {"template": "title_bullets_right_img"},
            "elements": [
                {
                    "id": "el_1",
                    "type": "bullets",
                    "x": 0.05,
                    "y": 0.2,
                    "w": 0.45,
                    "h": 0.7,
                    "content": {
                        "items": [
                            "动力元件：液压泵（机械能→液压能）",
                            "执行元件：液压缸/马达（液压能→机械能）",
                            "控制元件：各种阀门（控制压力、流量、方向）",
                            "辅助元件：油箱、滤油器、管路",
                            "工作介质：液压油",
                        ]
                    },
                    "style": {"role": "body"},
                },
                {
                    "id": "el_2",
                    "type": "image",
                    "x": 0.55,
                    "y": 0.2,
                    "w": 0.4,
                    "h": 0.6,
                    "content": {
                        "kind": "diagram",
                        "theme": "液压系统五大组成全景图，包含油泵、油缸、阀门、油箱、管路，工程示意图",
                        "placeholder": True,
                    },
                    "style": {"role": "visual"},
                },
            ],
            "speaker_notes": "介绍液压系统的基本组成",
        },
        {
            "index": 4,
            "slide_type": "content",
            "title": "核心动力：液压泵",
            "layout": {"template": "title_bullets_right_img"},
            "elements": [
                {
                    "id": "el_1",
                    "type": "bullets",
                    "x": 0.05,
                    "y": 0.2,
                    "w": 0.45,
                    "h": 0.7,
                    "content": {
                        "items": [
                            "作用：为系统提供压力油，是心脏部件",
                            "常用类型：齿轮泵、叶片泵、柱塞泵",
                            "特点：齿轮泵结构简单但噪音大，柱塞泵压力高效率高",
                            "维护重点：防止吸空，定期更换密封件",
                        ]
                    },
                    "style": {"role": "body"},
                },
                {
                    "id": "el_2",
                    "type": "image",
                    "x": 0.55,
                    "y": 0.2,
                    "w": 0.4,
                    "h": 0.5,
                    "content": {
                        "kind": "photo",
                        "theme": "工业齿轮泵内部精密结构特写，金属齿轮咬合，机械剖视图，高精度渲染",
                        "placeholder": True,
                    },
                    "style": {"role": "visual"},
                },
            ],
            "speaker_notes": "讲解液压泵的结构和工作原理",
        },
        {
            "index": 5,
            "slide_type": "content",
            "title": "执行机构：液压缸",
            "layout": {"template": "title_bullets_right_img"},
            "elements": [
                {
                    "id": "el_1",
                    "type": "bullets",
                    "x": 0.05,
                    "y": 0.2,
                    "w": 0.45,
                    "h": 0.7,
                    "content": {
                        "items": [
                            "作用：将液压能转换为直线运动的机械能",
                            "分类：单作用式（靠外力回程）、双作用式（靠油压回程）",
                            "关键参数：缸径（决定推力）、行程（决定距离）",
                            "应用：挖掘机动臂、注塑机合模机构",
                        ]
                    },
                    "style": {"role": "body"},
                },
                {
                    "id": "el_2",
                    "type": "image",
                    "x": 0.55,
                    "y": 0.2,
                    "w": 0.4,
                    "h": 0.5,
                    "content": {
                        "kind": "photo",
                        "theme": "挖掘机液压缸工作特写，展示活塞杆伸缩过程",
                        "placeholder": True,
                    },
                    "style": {"role": "visual"},
                },
            ],
            "speaker_notes": "讲解液压缸的类型和选用",
        },
        {
            "index": 6,
            "slide_type": "concept",
            "title": "基本原理：帕斯卡定律",
            "layout": {"template": "title_bullets_right_img"},
            "elements": [
                {
                    "id": "el_1",
                    "type": "bullets",
                    "x": 0.05,
                    "y": 0.2,
                    "w": 0.45,
                    "h": 0.7,
                    "content": {
                        "items": [
                            "定义：密闭液体上的压强向各个方向传递不变",
                            "公式：F = P × A（力=压强×面积）",
                            "应用：千斤顶原理（小力举起大重物）",
                            "优势：可以实现力的放大和远距离传递",
                        ]
                    },
                    "style": {"role": "body"},
                },
                {
                    "id": "el_2",
                    "type": "image",
                    "x": 0.55,
                    "y": 0.2,
                    "w": 0.4,
                    "h": 0.5,
                    "content": {
                        "kind": "diagram",
                        "theme": "帕斯卡定律千斤顶原理示意图，展示大小活塞和压力传递",
                        "placeholder": True,
                    },
                    "style": {"role": "visual"},
                },
            ],
            "speaker_notes": "讲解帕斯卡定律及其应用",
        },
        {
            "index": 7,
            "slide_type": "steps",
            "title": "液压系统标准启动流程",
            "layout": {"template": "operation_steps"},
            "elements": [
                {
                    "id": "el_1",
                    "type": "image",
                    "x": 0.05,
                    "y": 0.15,
                    "w": 0.35,
                    "h": 0.7,
                    "content": {
                        "kind": "photo",
                        "theme": "液压站控制面板特写，显示压力表和操作按钮",
                        "placeholder": True,
                    },
                    "style": {"role": "visual"},
                },
                {
                    "id": "el_2",
                    "type": "bullets",
                    "x": 0.45,
                    "y": 0.15,
                    "w": 0.5,
                    "h": 0.7,
                    "content": {
                        "items": [
                            "1. 检查油箱液位是否在标准刻度线以上",
                            "2. 确认所有换向阀处于中位，卸荷启动",
                            "3. 点动电机，检查旋转方向是否正确",
                            "4. 空载运行5-10分钟，进行排气",
                            "5. 逐步加载，观察压力表读数是否稳定",
                        ]
                    },
                    "style": {"role": "body"},
                },
            ],
            "speaker_notes": "演示液压系统的标准启动流程",
        },
        {
            "index": 8,
            "slide_type": "summary",
            "title": "课程总结",
            "layout": {"template": "title_bullets"},
            "elements": [
                {
                    "id": "el_1",
                    "type": "bullets",
                    "x": 0.1,
                    "y": 0.2,
                    "w": 0.8,
                    "h": 0.7,
                    "content": {
                        "items": [
                            "液压系统通过液压油传递动力，遵循帕斯卡定律",
                            "五大组成部分各司其职，缺一不可",
                            "正确的启动和维护流程能延长系统寿命",
                            "油液清洁度是液压系统的生命线",
                        ]
                    },
                    "style": {"role": "body"},
                }
            ],
            "speaker_notes": "总结课程要点",
        },
    ],
}


# ============================================================================
# 完整的3.5渲染输入数据（组合3.1-3.4）
# ============================================================================

MOCK_FULL_INPUT: Dict[str, Any] = {
    "session_id": "mock_full_session_001",
    "teaching_request": MOCK_TEACHING_REQUEST,
    "style_config": MOCK_STYLE_CONFIG,
    "outline": MOCK_PPT_OUTLINE,
    "deck_content": MOCK_SLIDE_DECK_CONTENT,
}


# ============================================================================
# 化学课程 Mock 数据（另一个学科示例）
# ============================================================================

MOCK_TEACHING_REQUEST_CHEMISTRY: Dict[str, Any] = {
    "request_id": "mock_chem_001",
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "subject_info": {
        "subject_name": "化学",
        "subject_category": "science",
        "sub_field": "无机化学",
    },
    "knowledge_points": [
        {
            "id": "chem1",
            "name": "氢氧化钠与盐酸中和反应",
            "type": "practice",
            "is_core": True,
            "difficulty_level": "easy",
            "estimated_teaching_time_min": 10,
        },
        {
            "id": "chem2",
            "name": "离子方程式书写",
            "type": "theory",
            "is_core": True,
            "difficulty_level": "medium",
            "estimated_teaching_time_min": 15,
        },
    ],
    "knowledge_structure": {
        "total_count": 2,
        "relation_type": "causal",
        "relation_description": "先讲解反应原理，再学习离子方程式",
        "relation_graph": None,
    },
    "teaching_scenario": {
        "scene_type": "practice",
        "scene_label": "实验教学",
        "sub_type": "化学实验",
    },
    "teaching_objectives": {
        "knowledge": ["理解中和反应的本质", "掌握离子方程式书写方法"],
        "ability": ["能够正确书写常见中和反应方程式", "能够判断离子方程式正误"],
        "literacy": ["培养实验安全意识", "增强化学实验操作能力"],
        "auto_generated": False,
    },
    "slide_requirements": {
        "target_count": 5,
        "min_count": 4,
        "max_count": 6,
        "flexibility": "adjustable",
        "lesson_duration_min": 30,
        "llm_recommended_count": None,
        "page_conflict_resolution": None,
    },
    "special_requirements": {
        "cases": {"enabled": False, "count": 0, "case_type": None, "description": None},
        "exercises": {
            "enabled": True,
            "total_count": 2,
            "per_knowledge_point": 0,
            "types": ["fill_blank"],
        },
        "interaction": {"enabled": True, "types": ["qa"]},
        "warnings": {"enabled": True, "color": "#e74c3c"},
        "animations": {"enabled": False},
    },
    "estimated_page_distribution": {
        "cover": 1,
        "objectives": 1,
        "introduction": 0,
        "concept_definition": 1,
        "explanation": 1,
        "case_study": 0,
        "exercises": 1,
        "interaction": 0,
        "summary": 1,
    },
    "parsing_metadata": {
        "raw_input": "制作一个关于中和反应的化学课件，时长30分钟，面向高中化学实验班",
        "input_source": "text",
        "parsing_method": "llm_extraction",
        "request_id": "mock_chem_001",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    },
    "internal_interaction_stage": "confirmed",
    "display_summary": None,
    "interaction_metadata": {},
}


MOCK_STYLE_CONFIG_CHEMISTRY: Dict[str, Any] = {
    "style_name": "theory_clean",
    "color": {
        "primary": "#27ae60",
        "secondary": "#2ecc71",
        "accent": "#f39c12",
        "text": "#2c3e50",
        "muted": "#ecf0f1",
        "background": "#ffffff",
        "warning": "#e74c3c",
    },
    "font": {
        "title_family": "Microsoft YaHei",
        "heading_family": "Microsoft YaHei",
        "body_family": "Microsoft YaHei",
        "title_size": 48,
        "heading_size": 36,
        "body_size": 24,
        "line_height": 1.5,
    },
    "layout": {
        "width": 1920,
        "height": 1080,
        "padding": 60,
        "content_margin": 40,
        "grid_columns": 12,
        "grid_rows": 8,
    },
    "imagery": {
        "image_style": "schematic",
        "icon_style": "flat",
        "chart_preference": [],
    },
    "animation": {"type": "fade", "duration": 500, "direction": "horizontal"},
}


MOCK_DECK_CHEMISTRY: Dict[str, Any] = {
    "deck_title": "中和反应与离子方程式",
    "pages": [
        {
            "index": 1,
            "slide_type": "title",
            "title": "中和反应与离子方程式",
            "layout": {"template": "title_only"},
            "elements": [],
            "speaker_notes": "封面",
        },
        {
            "index": 2,
            "slide_type": "objectives",
            "title": "学习目标",
            "layout": {"template": "title_bullets"},
            "elements": [
                {
                    "id": "obj1",
                    "type": "bullets",
                    "x": 0.1,
                    "y": 0.2,
                    "w": 0.8,
                    "h": 0.7,
                    "content": {
                        "items": ["理解中和反应的本质", "掌握离子方程式书写方法"]
                    },
                    "style": {"role": "body"},
                }
            ],
            "speaker_notes": "明确学习目标",
        },
        {
            "index": 3,
            "slide_type": "concept",
            "title": "中和反应的本质",
            "layout": {"template": "title_bullets_right_img"},
            "elements": [
                {
                    "id": "concept1",
                    "type": "bullets",
                    "x": 0.05,
                    "y": 0.2,
                    "w": 0.45,
                    "h": 0.7,
                    "content": {
                        "items": [
                            "中和反应：酸 + 碱 → 盐 + 水",
                            "本质：H⁺ + OH⁻ = H₂O",
                            "放热反应",
                            "常用指示剂：酚酞、石蕊",
                        ]
                    },
                    "style": {"role": "body"},
                },
                {
                    "id": "img1",
                    "type": "image",
                    "x": 0.55,
                    "y": 0.2,
                    "w": 0.4,
                    "h": 0.5,
                    "content": {
                        "kind": "diagram",
                        "theme": "HCl与NaOH中和反应示意图，H+与OH-结合生成水分子",
                        "placeholder": True,
                    },
                    "style": {"role": "visual"},
                },
            ],
            "speaker_notes": "讲解中和反应本质",
        },
    ],
}


# 导出函数：获取完整的Mock输入
def get_mock_full_input(subject: str = "mechanical") -> Dict[str, Any]:
    """
    获取完整的Mock输入数据

    Args:
        subject: 学科主题，可选 'mechanical' 或 'chemistry'

    Returns:
        包含 teaching_request, style_config, outline, deck_content 的字典
    """
    if subject == "chemistry":
        return {
            "session_id": f"mock_chem_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "teaching_request": MOCK_TEACHING_REQUEST_CHEMISTRY,
            "style_config": MOCK_STYLE_CONFIG_CHEMISTRY,
            "outline": {
                "deck_title": "中和反应与离子方程式",
                "subject": "化学",
                "knowledge_points": ["中和反应的本质", "离子方程式书写"],
                "teaching_scene": "practice",
                "slides": [],
            },
            "deck_content": MOCK_DECK_CHEMISTRY,
        }
    else:
        return {
            "session_id": f"mock_mech_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "teaching_request": MOCK_TEACHING_REQUEST,
            "style_config": MOCK_STYLE_CONFIG,
            "outline": MOCK_PPT_OUTLINE,
            "deck_content": MOCK_SLIDE_DECK_CONTENT,
        }
