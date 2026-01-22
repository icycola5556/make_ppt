---
description: 如何添加新布局或修改布局选择逻辑
---

# 布局系统指南

## 当前布局（共 10 种）

| 布局 ID | 名称 | 图片插槽数 |
|---------|------|-----------|
| `title_only` | 纯标题页 | 0 |
| `title_bullets` | 标题+要点 | 0 |
| `title_bullets_right_img` | 左文右图 | 1 |
| `operation_steps` | 左图右步骤 | 1 |
| `concept_comparison` | 左右对比 | 2 |
| `grid_4` | 四宫格 | 4 |
| `table_comparison` | 表格对比 | 0 |
| `timeline_horizontal` | 水平时间轴 | 0 |
| `center_visual` | 中心视觉 | 1 |
| `split_vertical` | 上下分栏 | 1 |

## 关键文件

- `backend/app/modules/render/layout_configs.py` - 布局定义
- `backend/app/modules/render/layout_engine.py` - 选择逻辑
- `backend/app/prompts/render.py` - Layout Agent 提示词

## 添加新布局

1. 在 `layout_configs.py` 的 `VOCATIONAL_LAYOUTS` 中添加：
```python
"new_layout": LayoutConfig(
    layout_id="new_layout",
    display_name="新布局",
    description="布局描述",
    grid_template_areas='...',
    image_slots=[...],
    suitable_slide_types=[...],
    suitable_keywords=[...],
)
```

2. 在 `layout_engine.py` 的 `_find_alternative_layout` 中添加替代关系
3. 如需要，更新 `render.py` 中的提示词

## 防重复机制

`resolve_layout()` 函数接受 `previous_layout` 参数：
- 对重复布局扣 80 分
- 如果仍选中相同布局，调用 `_find_alternative_layout()` 寻找替代
