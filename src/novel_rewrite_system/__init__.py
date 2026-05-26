"""中文小说生成与本地改写系统基础包。"""

from novel_rewrite_system.config import (
    AppConfig,
    CloudModelConfig,
    GenerationConfig,
    LocalModelConfig,
    Settings,
    load_settings,
)
from novel_rewrite_system.errors import (
    ConfigError,
    DuplicateProjectError,
    EmptyTextError,
    ModelConfigError,
    ProjectError,
    ProjectNotFoundError,
    error_to_dict,
    error_to_text,
)
from novel_rewrite_system.deepseek_client import DeepSeekClient
from novel_rewrite_system.ollama_client import OllamaClient
from novel_rewrite_system.models import (
    FakeModelClient,
    ModelClient,
    ModelRequest,
    ModelResponse,
)
from novel_rewrite_system.projects import (
    PROJECT_INDEX_FILENAME,
    PROJECT_SUBDIRECTORIES,
    ProjectIndexRecord,
    add_project_record,
    create_project_directories,
    get_project_record,
    list_project_records,
)
from novel_rewrite_system.analysis import StyleAnalysisResult, analyze_style
from novel_rewrite_system.rewrite import LocalRewriteResult, rewrite_locally
from novel_rewrite_system.generation import DraftGenerationResult, generate_draft
from novel_rewrite_system.pipeline import PipelineResult, run_minimal_pipeline
from novel_rewrite_system.webui import WebUiRunResult, run_webui_pipeline
from novel_rewrite_system.source_processing import (
    ManualSourceProcessingResult,
    process_manual_source,
)
from novel_rewrite_system.text_cleaning import clean_text
from novel_rewrite_system.text_chunks import TextChunk, split_text
from novel_rewrite_system.requirements import StoryRequirement

__all__ = [
    "AppConfig",
    "CloudModelConfig",
    "ConfigError",
    "DeepSeekClient",
    "DraftGenerationResult",
    "OllamaClient",
    "PipelineResult",
    "WebUiRunResult",
    "DuplicateProjectError",
    "EmptyTextError",
    "FakeModelClient",
    "GenerationConfig",
    "LocalModelConfig",
    "LocalRewriteResult",
    "ModelConfigError",
    "ModelClient",
    "ModelRequest",
    "ModelResponse",
    "ManualSourceProcessingResult",
    "PROJECT_INDEX_FILENAME",
    "PROJECT_SUBDIRECTORIES",
    "ProjectError",
    "ProjectIndexRecord",
    "ProjectNotFoundError",
    "Settings",
    "TextChunk",
    "StoryRequirement",
    "StyleAnalysisResult",
    "add_project_record",
    "analyze_style",
    "clean_text",
    "create_project_directories",
    "error_to_dict",
    "error_to_text",
    "generate_draft",
    "get_project_record",
    "list_project_records",
    "load_settings",
    "process_manual_source",
    "rewrite_locally",
    "run_minimal_pipeline",
    "run_webui_pipeline",
    "split_text",
]
