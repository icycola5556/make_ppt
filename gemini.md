# Gemini Context: contrast-banana-pptgen/pptgen_workflow

## 1. Project Overview
- **Name**: PPTGen Workflow
- **Goal**: End-to-end AI teaching slide generation pipeline (Intent -> Style -> Outline -> Content -> Render).
- **Tech Stack**:
  - **Backend**: Python 3.12+, FastAPI, Pydantic, Jinja2.
  - **Frontend**: Vue 3, Vite, TailwindCSS (for some components).
- **Core Logic**: "Chain of Thought" workflow where each module's output feeds the next.

## 2. Architecture & Modules
The system is linear and stateful (`SessionState`).
- **3.1 Intent** (`modules/intent`): Parses user natural language -> Structured `TeachingRequest`.
- **3.2 Style** (`modules/style`): Selects visual theme based on subject/scene -> `StyleConfig`.
- **3.3 Outline** (`modules/outline`): Generates slide plan -> `PPTOutline`.
- **3.4 Content** (`modules/content`): Fills slide details -> `SlideDeckContent`.
- **3.5 Render** (`modules/render`): Layout engine transforms content -> HTML Slides.
- **Entry**: `POST /api/workflow/run` (Main).

## 3. Core Data Schemas (Pydantic)
Ref: `backend/app/common/schemas.py`

### 3.1 TeachingRequest
Structured requirements parsed from user input.
- `subject_info`: `ProfessionalCategory` (17 types: engineering, medical, arts...).
- `teaching_scenario`: `TeachingScene` ("theory", "practice", "review").
- `slide_requirements`: `target_count` (int).
- `stage`: "parsing" | "confirmed" | "ready".

### 3.2 StyleConfig
Visual design tokens path: `backend/app/modules/style`.
- `style_name`: Unique ID (e.g., "tech_blue").
- `color`: Primary, secondary, accent, background hex codes.
- `font`: Title and body font families.
- `layout`: Density ("compact"/"comfortable").

### 3.3 PPTOutline
High-level structure.
- `slides`: List of `OutlineSlide` (title, bullets[], notes).
- **Rule**: Minimum 2 bullets per slide.

### 3.4 SlideDeckContent
Full content details for rendering.
- `pages`: List of `SlidePage`.
- `SlidePage`: Contains `elements` (text, image, chart) and `layout` template reference.

## 4. Key Directories
- **App Entry**: `backend/app/main.py`
- **Modules**: `backend/app/modules/{intent, style, outline, content, render}`
- **Prompts**: `backend/app/prompts/` (Jinja2 templates for LLM).
- **Schemas**: `backend/app/common/schemas.py`
- **Frontend Views**: `frontend/src/views/Module3{x}.vue`

## 5. Development Roles
- **Backend**: Handles logic, LLM calls (`LLMClient`), and state management.
- **Frontend**: Visualization, user confirmation, and step progression.
