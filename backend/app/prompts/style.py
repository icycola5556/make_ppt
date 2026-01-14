
STYLE_SYSTEM_PROMPT = """你是PPT风格设计助手。你将基于教学场景输出风格配置JSON。
只输出JSON对象，不要解释。"""

STYLE_SCHEMA_HINT = """{
  "style_name": "string",
  "color": {
    "primary": "#RRGGBB",
    "secondary": "#RRGGBB",
    "accent": "#RRGGBB",
    "muted": "#RRGGBB",
    "text": "#RRGGBB",
    "background": "#RRGGBB",
    "warning": "#RRGGBB",
    "surface": "#RRGGBB",
    "background_gradient": "string or null"
  },
  "font": {
    "title_family": "string",
    "body_family": "string",
    "code_family": "string",
    "title_size": 34,
    "body_size": 22,
    "line_height": 1.2
  },
  "layout": {
    "density": "compact|comfortable",
    "notes_area": true,
    "alignment": "left|center",
    "header_rule": true,
    "border_radius": "0px",
    "box_shadow": "none|soft|hard"
  },
  "animation": {
    "transition": "none|slide|fade|zoom",
    "element_entry": "none|fade-up|typewriter"
  },
  "imagery": {
    "image_style": "string",
    "icon_style": "string",
    "chart_preference": ["string"]
  }
}"""
