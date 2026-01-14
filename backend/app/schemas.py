from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, computed_field


TeachingScene = Literal["theory", "practice", "review", "unknown"]

# 7 professional categories based on research
ProfessionalCategory = Literal[
    "engineering", "medical", "agriculture", "arts", "business", "science", "civil",
    "transportation", "tourism", "food", "textile", "resources", "water", "media",
    "public-security", "public-service", "sports", "unknown"
]

# Confirmation types for multi-turn interaction
ConfirmationType = Literal[
    "knowledge_points",  # 确认是否需要补充知识点
    "slide_count",       # 确认页数调整
    "teaching_scene",    # 确认教学场景
    "exercises_count",   # 确认习题数量
    "none"
]


# --- Sub-models for structured TeachingRequest ---

class SubjectInfo(BaseModel):
    subject_name: Optional[str] = None
    subject_category: ProfessionalCategory = "unknown"
    sub_field: Optional[str] = None

class KnowledgePointDetail(BaseModel):
    id: str
    name: str
    type: Literal["theory", "practice", "mixed"] = "theory"
    is_core: bool = True
    difficulty_level: Literal["easy", "medium", "hard"] = "medium"
    estimated_teaching_time_min: Optional[int] = None

class KnowledgeStructure(BaseModel):
    total_count: int = 0
    relation_type: Literal["single", "parallel", "progressive", "causal", "unknown"] = "unknown"
    relation_description: Optional[str] = None
    relation_graph: Optional[Any] = None

class TeachingScenarioDetail(BaseModel):
    scene_type: TeachingScene = "unknown"
    scene_label: str = "未指定"
    sub_type: Optional[str] = None

class TeachingObjectivesStructured(BaseModel):
    knowledge: List[str] = Field(default_factory=list)
    ability: List[str] = Field(default_factory=list)
    literacy: List[str] = Field(default_factory=list)
    auto_generated: bool = True

class SlideRequirementsDetail(BaseModel):
    target_count: Optional[int] = None
    min_count: Optional[int] = None
    max_count: Optional[int] = None
    flexibility: Literal["fixed", "adjustable"] = "adjustable"
    lesson_duration_min: int = 45
    llm_recommended_count: Optional[int] = None  # LLM推荐的页数
    page_conflict_resolution: Optional[str] = None  # 用户选择的解决方式: "accept_recommended", "custom", "keep_original"

class CaseRequirement(BaseModel):
    enabled: bool = True
    count: int = 0
    case_type: Optional[str] = None
    description: Optional[str] = None

class ExerciseRequirement(BaseModel):
    enabled: bool = True
    total_count: int = 0
    per_knowledge_point: int = 0
    types: List[str] = Field(default_factory=list)

class InteractionRequirement(BaseModel):
    enabled: bool = True
    types: List[str] = Field(default_factory=list)

class WarningRequirement(BaseModel):
    enabled: bool = False
    color: Optional[str] = None

class AnimationRequirement(BaseModel):
    enabled: bool = False

class SpecialRequirementsDetailed(BaseModel):
    cases: CaseRequirement = Field(default_factory=CaseRequirement)
    exercises: ExerciseRequirement = Field(default_factory=ExerciseRequirement)
    interaction: InteractionRequirement = Field(default_factory=InteractionRequirement)
    warnings: WarningRequirement = Field(default_factory=WarningRequirement)
    animations: AnimationRequirement = Field(default_factory=AnimationRequirement)

class PageDistribution(BaseModel):
    cover: int = 1
    objectives: int = 1
    introduction: int = 0
    concept_definition: int = 0
    explanation: int = 0
    case_study: int = 0
    exercises: int = 0
    interaction: int = 0  # 互动页（问答、讨论等）
    summary: int = 1

class ParsingMetadata(BaseModel):
    """Simplified metadata - removed unused fields (借鉴 Presenton)"""
    raw_input: Optional[str] = None
    input_source: str = "text"
    parsing_method: Literal["llm_extraction", "llm_extraction_with_tools", "heuristic", "mixed"] = "mixed"
    request_id: Optional[str] = None
    timestamp: Optional[str] = None

# ConfirmationStatusDetail 已移除 - 状态合并到 TeachingRequest.stage (借鉴 PPTAgent)
# 保留注释说明迁移原因

class TeachingRequest(BaseModel):
    """Refactored Module 3.1 output: highly structured teaching requirements."""
    
    request_id: Optional[str] = None
    timestamp: Optional[str] = None
    
    subject_info: SubjectInfo = Field(default_factory=SubjectInfo)
    knowledge_points: List[KnowledgePointDetail] = Field(default_factory=list)
    knowledge_structure: KnowledgeStructure = Field(default_factory=KnowledgeStructure)
    
    teaching_scenario: TeachingScenarioDetail = Field(default_factory=TeachingScenarioDetail)
    teaching_objectives: TeachingObjectivesStructured = Field(default_factory=TeachingObjectivesStructured)
    
    slide_requirements: SlideRequirementsDetail = Field(default_factory=SlideRequirementsDetail)
    special_requirements: SpecialRequirementsDetailed = Field(default_factory=SpecialRequirementsDetailed)
    
    estimated_page_distribution: PageDistribution = Field(default_factory=PageDistribution)
    parsing_metadata: ParsingMetadata = Field(default_factory=ParsingMetadata)
    
    # ===== 内部状态字段 (保持状态机逻辑) =====
    # 用于内部多轮交互逻辑，使用 exclude=True 从对外 API 隐藏
    internal_interaction_stage: Literal[
        "initial", "supplementing_kp", "confirm_kp", "confirm_pages",
        "check_additional_kps", "add_additional_kps", "ask_config_modification",
        "adjust_configurations", "confirm_goals", "final_confirm", "confirmed"
    ] = Field(default="initial", exclude=False)
    
    display_summary: Optional[str] = None
    
    # Interaction metadata for tracking user modifications
    interaction_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # ===== 扁平化高频字段 (借鉴 Presenton) =====
    # 这些字段会出现在 JSON 输出顶层，便于访问
    @computed_field
    @property
    def stage(self) -> Literal["parsing", "confirming", "ready"]:
        """Simplified stage for external API (借鉴 PPTAgent)"""
        if self.internal_interaction_stage in ["initial", "supplementing_kp"]:
            return "parsing"
        elif self.internal_interaction_stage == "confirmed":
            return "ready"
        else:
            return "confirming"
    
    @computed_field
    @property
    def subject(self) -> Optional[str]:
        """扁平化字段：学科名称"""
        return self.subject_info.subject_name
    
    @computed_field
    @property
    def professional_category(self) -> ProfessionalCategory:
        """扁平化字段：专业领域"""
        return self.subject_info.subject_category
    
    @computed_field
    @property
    def teaching_scene(self) -> TeachingScene:
        """扁平化字段：教学场景"""
        return self.teaching_scenario.scene_type
    
    @computed_field
    @property
    def n_slides(self) -> Optional[int]:
        """扁平化字段：目标页数 (借鉴 Presenton 命名)"""
        return self.slide_requirements.target_count
    
    # 兼容性别名 - 用于内部状态机逻辑
    @property
    def interaction_stage(self) -> str:
        return self.internal_interaction_stage
    
    @interaction_stage.setter
    def interaction_stage(self, value):  # type: ignore
        self.internal_interaction_stage = value

    # ===== Setters for backward compatibility =====
    # 允许现有代码通过 req.subject = "xxx" 赋值
    @subject.setter
    def subject(self, value: Optional[str]):
        self.subject_info.subject_name = value
    
    @professional_category.setter
    def professional_category(self, value: ProfessionalCategory):
        self.subject_info.subject_category = value
    
    @teaching_scene.setter
    def teaching_scene(self, value: TeachingScene):
        self.teaching_scenario.scene_type = value
    
    @n_slides.setter
    def n_slides(self, value: Optional[int]):
        self.slide_requirements.target_count = value
        
    # 保留其他 legacy 属性
    @property
    def slide_count(self) -> Optional[int]:
        return self.slide_requirements.target_count
    
    @slide_count.setter
    def slide_count(self, value: Optional[int]):
        self.slide_requirements.target_count = value
        
    @property
    def min_slide_count(self) -> Optional[int]:
        return self.slide_requirements.min_count
    
    @min_slide_count.setter
    def min_slide_count(self, value: Optional[int]):
        self.slide_requirements.min_count = value
        
    @property
    def teaching_goals(self) -> TeachingObjectivesStructured:
        return self.teaching_objectives
    
    @property
    def kp_names(self) -> List[str]:
        return [kp.name for kp in self.knowledge_points]

    # Legacy field mappings for special requirements
    @property
    def include_cases(self) -> bool:
        return self.special_requirements.cases.enabled
    
    @property
    def include_exercises(self) -> bool:
        return self.special_requirements.exercises.enabled
    
    @property
    def include_interaction(self) -> bool:
        return self.special_requirements.interaction.enabled
    
    @property
    def warning_mark(self) -> bool:
        return self.special_requirements.warnings.enabled


class StyleConfig(BaseModel):
    """Module 3.2 output: standardized style config file."""

    style_name: str
    color: Dict[str, str] = Field(
        default_factory=dict,
        description="primary/secondary/accent/background/text/warning etc.",
    )
    font: Dict[str, Any] = Field(default_factory=dict, description="title/body font families & sizes")
    layout: Dict[str, Any] = Field(default_factory=dict, description="layout rules")
    imagery: Dict[str, Any] = Field(default_factory=dict, description="image/icon/chart preference")


class StyleSampleSlide(BaseModel):
    kind: Literal["cover", "content", "steps"]
    title: str
    bullets: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class OutlineSlide(BaseModel):
    index: int
    slide_type: str
    title: str
    bullets: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    interactions: List[str] = Field(default_factory=list)
    assets: List[Dict[str, Any]] = Field(default_factory=list, description="placeholders: type/theme/size/style")


class PPTOutline(BaseModel):
    """Module 3.3 output: slide-by-slide outline."""

    deck_title: str
    subject: str
    knowledge_points: List[str]
    teaching_scene: TeachingScene
    slides: List[OutlineSlide]


class SlideElement(BaseModel):
    """Module 3.4 atomic element on a slide (for later web rendering in Module 3.5)."""

    id: str
    type: Literal["text", "bullets", "image", "shape", "table", "chart", "diagram", "quiz"] = "text"

    # Relative layout on a 16:9 slide canvas, normalized to [0, 1]
    x: float = 0.0
    y: float = 0.0
    w: float = 1.0
    h: float = 1.0

    content: Dict[str, Any] = Field(default_factory=dict, description="Element payload by type")
    style: Dict[str, Any] = Field(default_factory=dict, description="Element style overrides")


class SlidePage(BaseModel):
    """Module 3.4 output per slide: content + layout + placeholders."""

    index: int
    slide_type: str
    title: str

    layout: Dict[str, Any] = Field(default_factory=dict, description="Layout template name + parameters")
    elements: List[SlideElement] = Field(default_factory=list)

    speaker_notes: Optional[str] = None


class SlideDeckContent(BaseModel):
    """Module 3.4 output: slide-by-slide page content for the whole deck."""

    deck_title: str
    pages: List[SlidePage]

class Question(BaseModel):
    key: str
    question: str
    input_type: Literal["text", "select", "number", "bool", "list", "confirm_or_add"] = "text"
    options: Optional[List[str]] = None
    placeholder: Optional[str] = None
    required: bool = True
    # 页面冲突相关字段
    recommended_count: Optional[int] = None  # LLM推荐的页数
    explanation: Optional[str] = None  # 推荐理由说明


class WorkflowRunRequest(BaseModel):
    session_id: str
    user_text: Optional[str] = None
    # Backward/forward compatible alias (some frontends send this key)
    user_input_text: Optional[str] = None
    answers: Optional[Dict[str, Any]] = None
    auto_fill_defaults: bool = False
    # NEW: Stop at specific module for testing
    stop_at: Optional[Literal["3.1", "3.2", "3.3", "3.4"]] = None
    # NEW: For test mode 3.1->3.3: allow user to specify style_name directly
    # Valid values: "theory_clean", "practice_steps", "review_mindmap"
    style_name: Optional[str] = None


class WorkflowRunResponse(BaseModel):
    session_id: str
    status: Literal["need_user_input", "ok", "error"]
    stage: Literal["3.1", "3.2", "3.3", "3.4"]
    questions: List[Question] = Field(default_factory=list)
    teaching_request: Optional[TeachingRequest] = None
    style_config: Optional[StyleConfig] = None
    style_samples: List[StyleSampleSlide] = Field(default_factory=list)
    outline: Optional[PPTOutline] = None
    deck_content: Optional[SlideDeckContent] = None
    logs_preview: List[Dict[str, Any]] = Field(default_factory=list)
    message: Optional[str] = None


class SessionState(BaseModel):
    session_id: str
    created_at: Optional[str] = Field(
        default=None,
        description="ISO 8601 timestamp when the session was created (UTC or with offset).",
    )
    updated_at: Optional[str] = Field(
        default=None,
        description="ISO 8601 timestamp when the session state was last saved (UTC or with offset).",
    )
    teaching_request: Optional[TeachingRequest] = None
    style_config: Optional[StyleConfig] = None
    style_samples: List[StyleSampleSlide] = Field(default_factory=list)
    outline: Optional[PPTOutline] = None
    deck_content: Optional[SlideDeckContent] = None
    stage: Literal["3.1", "3.2", "3.3", "3.4"] = "3.1"

