"""
AutoTestAI - Pydantic Models
Data models for test cases, projects, and generation requests.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid


# ── Enums ─────────────────────────────────────────────────────────────────

class Language(str, Enum):
    JAVA = "java"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"


class AutomationTool(str, Enum):
    SELENIUM = "selenium"
    PLAYWRIGHT = "playwright"


class TestFramework(str, Enum):
    TESTNG = "testng"
    JUNIT5 = "junit5"
    PYTEST = "pytest"
    MOCHA = "mocha"
    JEST = "jest"
    PLAYWRIGHT_TEST = "playwright_test"


class ReportTool(str, Enum):
    EXTENT_REPORTS = "extent_reports"
    ALLURE = "allure"
    PLAYWRIGHT_HTML = "playwright_html"


class JobStatus(str, Enum):
    PENDING = "pending"
    PARSING = "parsing"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


# ── Test Case Models ──────────────────────────────────────────────────────

class TestStep(BaseModel):
    """Represents a single step in a test case."""
    step_number: int
    action: str
    test_data: Optional[str] = None
    element_description: Optional[str] = None
    expected_result: Optional[str] = None


class TestCase(BaseModel):
    """Represents a parsed manual test case."""
    test_case_id: str
    title: str
    module: Optional[str] = None
    priority: Optional[str] = "Medium"
    preconditions: List[str] = Field(default_factory=list)
    steps: List[TestStep] = Field(default_factory=list)
    postconditions: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class TestSuite(BaseModel):
    """Collection of test cases from a single source file."""
    source_file: str
    total_cases: int = 0
    test_cases: List[TestCase] = Field(default_factory=list)
    parse_warnings: List[str] = Field(default_factory=list)


# ── Locator Models ────────────────────────────────────────────────────────

class ElementLocator(BaseModel):
    """Represents a web element and its locator strategies."""
    element_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    tag: str
    element_type: Optional[str] = None
    text: Optional[str] = None
    locators: Dict[str, str] = Field(default_factory=dict)
    # locators example: {"id": "username", "css": "#username", "xpath": "//input[@id='username']"}
    attributes: Dict[str, str] = Field(default_factory=dict)
    is_interactive: bool = False
    description: Optional[str] = None


class LocatorMap(BaseModel):
    """Complete map of all elements found in HTML analysis."""
    source_url: Optional[str] = None
    page_title: Optional[str] = None
    elements: List[ElementLocator] = Field(default_factory=list)
    forms: List[Dict[str, Any]] = Field(default_factory=list)


# ── Generation Models ─────────────────────────────────────────────────────

class GenerationConfig(BaseModel):
    """Configuration for code generation."""
    language: Language = Language.JAVA
    automation_tool: AutomationTool = AutomationTool.SELENIUM
    test_framework: TestFramework = TestFramework.TESTNG
    report_tool: ReportTool = ReportTool.EXTENT_REPORTS
    base_url: Optional[str] = None
    browser: str = "chrome"
    headless: bool = False
    package_name: str = "com.autotestai.tests"
    project_name: str = "AutoTestAI-Generated"


class GenerationRequest(BaseModel):
    """Request to generate automation code."""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    config: GenerationConfig
    test_suite: Optional[TestSuite] = None
    locator_map: Optional[LocatorMap] = None
    html_source: Optional[str] = None
    screenshot_analysis: Optional[Dict[str, Any]] = None


class GeneratedFile(BaseModel):
    """Represents a single generated file."""
    file_path: str
    content: str
    file_type: str  # "page_object", "test", "config", "utility", "build", "report"
    description: str


class GenerationResult(BaseModel):
    """Result of code generation."""
    job_id: str
    status: JobStatus = JobStatus.PENDING
    config: GenerationConfig
    files: List[GeneratedFile] = Field(default_factory=list)
    output_directory: Optional[str] = None
    zip_path: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


# ── Upload Response Models ────────────────────────────────────────────────

class UploadResponse(BaseModel):
    """Response after uploading a file."""
    filename: str
    file_type: str
    file_path: str
    message: str


class ParseResponse(BaseModel):
    """Response after parsing uploaded test cases."""
    source_file: str
    test_suite: TestSuite
    locator_map: Optional[LocatorMap] = None
    message: str


# ── Validation Helpers ────────────────────────────────────────────────────

VALID_COMBINATIONS = [
    (Language.JAVA, AutomationTool.SELENIUM, TestFramework.TESTNG, ReportTool.EXTENT_REPORTS),
    (Language.JAVA, AutomationTool.SELENIUM, TestFramework.JUNIT5, ReportTool.ALLURE),
    (Language.JAVA, AutomationTool.PLAYWRIGHT, TestFramework.JUNIT5, ReportTool.EXTENT_REPORTS),
    (Language.JAVA, AutomationTool.PLAYWRIGHT, TestFramework.TESTNG, ReportTool.EXTENT_REPORTS),
    (Language.JAVA, AutomationTool.PLAYWRIGHT, TestFramework.TESTNG, ReportTool.ALLURE),
    (Language.PYTHON, AutomationTool.SELENIUM, TestFramework.PYTEST, ReportTool.EXTENT_REPORTS),
    (Language.PYTHON, AutomationTool.SELENIUM, TestFramework.PYTEST, ReportTool.ALLURE),
    (Language.PYTHON, AutomationTool.PLAYWRIGHT, TestFramework.PYTEST, ReportTool.ALLURE),
    (Language.PYTHON, AutomationTool.PLAYWRIGHT, TestFramework.PYTEST, ReportTool.PLAYWRIGHT_HTML),
    (Language.JAVASCRIPT, AutomationTool.PLAYWRIGHT, TestFramework.MOCHA, ReportTool.PLAYWRIGHT_HTML),
    (Language.JAVASCRIPT, AutomationTool.PLAYWRIGHT, TestFramework.JEST, ReportTool.PLAYWRIGHT_HTML),
    (Language.TYPESCRIPT, AutomationTool.PLAYWRIGHT, TestFramework.PLAYWRIGHT_TEST, ReportTool.PLAYWRIGHT_HTML),
]


def validate_combination(config: GenerationConfig) -> bool:
    """Check if the language/tool/framework/report combination is valid."""
    combo = (config.language, config.automation_tool, config.test_framework, config.report_tool)
    return combo in VALID_COMBINATIONS


def get_valid_combinations_for_language(language: Language) -> list:
    """Get all valid combinations for a given language."""
    return [c for c in VALID_COMBINATIONS if c[0] == language]
