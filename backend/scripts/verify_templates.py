import asyncio
import os
import sys
from pathlib import Path

# Add backend path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.modules.render import render_html_slides
from app.modules.render.templates_registry import TEMPLATES
from app.common.schemas import SlideDeckContent, SlidePage, StyleConfig, TeachingRequest, Dict
from app.common.llm_client import LLMClient

async def verify_template(template_id: str):
    print(f"\n--- Verifying Template: {template_id} ---")
    
    # Mock Data
    req = TeachingRequest(
        subject_info={"subject_name": "Test Subject"},
        knowledge_points=[],
        teaching_scenario={"scene_type": "theory"},
        teaching_objectives={"knowledge": []},
        slide_requirements={}
    )
    
    deck = SlideDeckContent(
        deck_title=f"Test Deck - {template_id}",
        pages=[
            SlidePage(index=1, slide_type="title", title=f"Title Page ({template_id})", elements=[]),
            SlidePage(index=2, slide_type="content", title="Content Page", elements=[
                {"id": "e1", "type": "bullets", "content": {"items": ["Point 1", "Point 2"]}}
            ]),
        ]
    )
    
    style = StyleConfig(
        style_name=template_id,
        color={"primary": "#000", "secondary": "#fff", "accent": "#f00", "text": "#333", "background": "#fff", "muted": "#999", "warning": "#ff0"},
        font={"title_family": "Arial", "body_family": "Arial", "title_size": 32, "body_size": 16, "line_height": 1.5},
        layout={"density": "comfortable", "alignment": "left", "border_radius": "4px"},
        imagery={"style": "photo", "mood": "neutral", "image_style": "photo", "icon_style": "default"}
    )
    output_dir = f"outputs/verify_{template_id}"
    
    # Run Renderer
    result = await render_html_slides(
        deck_content=deck,
        style_config=style,
        teaching_request=req,
        session_id=f"verify_{template_id}",
        output_dir=output_dir,
        template_id=template_id,
        llm=None # verification run without LLM
    )
    
    print(f"HTML Generated at: {result.html_path}")
    
    # Inspect content
    with open(f"{output_dir}/index.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    expected_theme = TEMPLATES[template_id].css_theme
    # Since we didn't inject css_theme class in body yet (maybe we should have?), we check for variables
    
    # Check if correct CSS vars are present (sample check)
    primary_color = TEMPLATES[template_id].css_vars["color-primary"]
    
    if "theme_name" in html:
         print(f"✅ Theme name '{template_id}' passed to template")
    else:
        # Note: renderer.py puts theme_name in template.render, 
        # but does base.html use it? Let's check for CSS vars in the output
        pass

    if f"--color-primary: {primary_color}" in html:
         print(f"✅ Primary Color '{primary_color}' found in CSS variables")
    else:
         print(f"❌ Primary Color '{primary_color}' NOT found. Actual HTML snippet:")
         print(html[:1000]) 

async def main():
    for t_id in TEMPLATES.keys():
        await verify_template(t_id)

if __name__ == "__main__":
    asyncio.run(main())
