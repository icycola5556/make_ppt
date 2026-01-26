"""
Module 3.5: Template Registry
Defines the available templates (styles) for the PPT generation.
"""
from typing import Dict, Optional
from pydantic import BaseModel

class TemplateDefinition(BaseModel):
    id: str
    name: str
    description: str
    system_prompt_modifier: str  # Instruction to Layout Agent
    css_theme: str  # Maps to a CSS file or CSS variables
    cover_image: Optional[str] = None
    
    # CSS Variables override for this template
    css_vars: Dict[str, str]

TEMPLATES: Dict[str, TemplateDefinition] = {
    "business": TemplateDefinition(
        id="business",
        name="Business Professional",
        description="Clean, authoritative style suitable for corporate reports and pitches.",
        system_prompt_modifier="""
        ### Style Preference: Business
        - PRIORITIZE: 'table_comparison', 'grid_4' (for KPI/stats), 'split_vertical'.
        - AVOID: 'timeline_horizontal' (unless strictly chronological).
        - tone: Formal, structured, data-driven.
        """,
        css_theme="theme-business",
        css_vars={
            "font-family-title": "'Playfair Display', serif",
            "font-family-body": "'Lato', sans-serif",
            "color-primary": "#1e3a8a",       # Deep Blue
            "color-secondary": "#64748b",     # Slate
            "color-accent": "#d97706",        # Amber
            "color-background": "#f8fafc",    # Slate-50
            "layout-border-radius": "4px",
        }
    ),
    "tech": TemplateDefinition(
        id="tech",
        name="Modern Tech",
        description="Sleek, dark-mode inspired style for technology and innovation topics.",
        system_prompt_modifier="""
        ### Style Preference: Tech
        - PRIORITIZE: 'concept_comparison', 'timeline_horizontal', 'grid_4'.
        - AVOID: 'title_bullets' (too boring).
        - tone: Innovative, futuristic, high-impact.
        """,
        css_theme="theme-tech",
        css_vars={
            "font-family-title": "'Rajdhani', sans-serif",
            "font-family-body": "'Inter', sans-serif",
            "color-primary": "#06b6d4",       # Cyan
            "color-secondary": "#3b82f6",     # Blue
            "color-accent": "#f472b6",        # Pink
            "color-background": "#0f172a",    # Slate-900 (Dark)
            "color-text": "#f1f5f9",          # Light text
            "layout-border-radius": "12px",
            "color-surface": "rgba(30, 41, 59, 0.8)", # Glass effect
        }
    ),
    "consulting": TemplateDefinition(
        id="consulting",
        name="Strategy Consulting",
        description="Minimalist, high-contrast style focusing on logic and clarity.",
        system_prompt_modifier="""
        ### Style Preference: Consulting
        - PRIORITIZE: 'split_vertical', 'center_visual', 'table_comparison'.
        - AVOID: Cluttered layouts.
        - tone: Insightful, clear, direct.
        """,
        css_theme="theme-consulting",
        css_vars={
            "font-family-title": "'Helvetica Neue', sans-serif",
            "font-family-body": "'Georgia', serif",
            "color-primary": "#000000",
            "color-secondary": "#525252",
            "color-accent": "#dc2626",        # Red
            "color-background": "#ffffff",
            "layout-border-radius": "0px",    # Sharp edges
        }
    ),
    "flow": TemplateDefinition(
        id="flow",
        name="Process & Flow",
        description="Visual style emphasizing steps, evolution, and connections.",
        system_prompt_modifier="""
        ### Style Preference: Flow
        - PRIORITIZE: 'timeline_horizontal', 'operation_steps', 'grid_4'.
        - AVOID: Static layouts.
        - tone: Dynamic, instructional, sequential.
        """,
        css_theme="theme-flow",
        css_vars={
            "font-family-title": "'Quicksand', sans-serif",
            "font-family-body": "'Nunito', sans-serif",
            "color-primary": "#059669",       # Emerald
            "color-secondary": "#10b981",     # Teal
            "color-accent": "#fbbf24",        # Yellow
            "color-background": "#ecfdf5",    # Green-50
            "layout-border-radius": "20px",   # Round
        }
    )
}

def get_template(template_id: str) -> TemplateDefinition:
    return TEMPLATES.get(template_id, TEMPLATES["business"])
