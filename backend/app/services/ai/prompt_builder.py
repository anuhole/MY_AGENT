"""
AutoTestAI - Prompt Builder
Pre-built, optimized prompt templates for test case parsing,
locator mapping, and code generation across all language/tool combos.
"""
import json
from typing import Optional

from app.models.schemas import (
    GenerationConfig, TestSuite, LocatorMap,
    Language, AutomationTool, TestFramework, ReportTool,
)


class PromptBuilder:
    """Builds optimized prompts for LLM code generation."""

    # ── System Prompts ────────────────────────────────────────────────────

    @staticmethod
    def system_prompt(config: GenerationConfig) -> str:
        """Generate the system prompt based on language/tool/framework selection."""

        lang_details = {
            Language.JAVA: "Java 17+",
            Language.PYTHON: "Python 3.10+",
            Language.JAVASCRIPT: "JavaScript (Node.js 18+)",
            Language.TYPESCRIPT: "TypeScript 5+",
        }

        tool_details = {
            AutomationTool.SELENIUM: "Selenium WebDriver 4",
            AutomationTool.PLAYWRIGHT: "Playwright",
        }

        framework_details = {
            TestFramework.TESTNG: "TestNG 7",
            TestFramework.JUNIT5: "JUnit 5",
            TestFramework.PYTEST: "pytest 7+",
            TestFramework.MOCHA: "Mocha + Chai",
            TestFramework.JEST: "Jest",
            TestFramework.PLAYWRIGHT_TEST: "Playwright Test (@playwright/test)",
        }

        report_details = {
            ReportTool.EXTENT_REPORTS: "ExtentReports 5",
            ReportTool.ALLURE: "Allure Report",
            ReportTool.PLAYWRIGHT_HTML: "Playwright HTML Reporter",
        }

        lang = lang_details.get(config.language, config.language.value)
        tool = tool_details.get(config.automation_tool, config.automation_tool.value)
        framework = framework_details.get(config.test_framework, config.test_framework.value)
        report = report_details.get(config.report_tool, config.report_tool.value)

        wait_strategy = (
            "Explicit waits (WebDriverWait with ExpectedConditions)"
            if config.automation_tool == AutomationTool.SELENIUM
            else "Playwright auto-waiting (with additional waitForSelector where needed)"
        )

        return f"""You are an expert Senior SDET (Software Development Engineer in Test) with 15+ years
of experience in test automation. You write clean, maintainable, production-grade automation code.

TECHNOLOGY STACK:
- Language: {lang}
- Automation Tool: {tool}
- Test Framework: {framework}
- Reporting: {report}
- Build Tool: {"Maven" if config.language == Language.JAVA else "pip/poetry" if config.language == Language.PYTHON else "npm"}

CODE STANDARDS (MANDATORY):
1. Follow Page Object Model (POM) design pattern strictly
2. Use {wait_strategy} — NEVER use Thread.sleep() / time.sleep() / setTimeout for waits
3. Every test method must have descriptive names matching the test case
4. All assertions must include meaningful failure messages
5. Capture screenshots on test failure automatically
6. Add {report} logging/annotations for each test step
7. Use proper test data management (externalized, not hardcoded in tests)
8. Add comprehensive JavaDoc/docstrings/JSDoc comments
9. Follow {lang} naming conventions and best practices
10. Make code modular, reusable, and easy to maintain

OUTPUT FORMAT:
- Return ONLY the code with proper file path comments at the top
- Separate multiple files with: // === FILE: path/to/File.ext ===
- Include all imports and dependencies
- Code must be complete and compilable/runnable without modifications"""

    # ── Page Object Generation ────────────────────────────────────────────

    @staticmethod
    def page_object_prompt(
        config: GenerationConfig,
        locator_map: LocatorMap,
        page_name: str = "Page",
    ) -> str:
        """Generate prompt for creating Page Object classes."""

        elements_json = json.dumps(
            [e.model_dump() for e in locator_map.elements],
            indent=2,
        )

        forms_json = json.dumps(locator_map.forms, indent=2)

        return f"""Generate a Page Object Model class for the following page:

PAGE NAME: {page_name}
PAGE TITLE: {locator_map.page_title or 'Unknown'}
BASE URL: {config.base_url or 'https://example.com'}

DETECTED ELEMENTS:
{elements_json}

DETECTED FORMS:
{forms_json}

REQUIREMENTS:
1. Create a "{page_name}Page" class extending BasePage
2. Define all interactive element locators as class-level constants
3. Use the BEST available locator for each element (prefer data-testid > id > name > css > xpath)
4. Create action methods for each interactive element (click, type, select, etc.)
5. Create verification methods (isDisplayed, getText, isEnabled, etc.)
6. Add proper wait strategies before each element interaction
7. Include methods for form submission if forms are detected
8. Add page load verification method
9. Package: {config.package_name}.pages"""

    # ── Test Class Generation ─────────────────────────────────────────────

    @staticmethod
    def test_class_prompt(
        config: GenerationConfig,
        test_suite: TestSuite,
        locator_map: Optional[LocatorMap] = None,
    ) -> str:
        """Generate prompt for creating test classes."""

        test_cases_json = json.dumps(
            [tc.model_dump() for tc in test_suite.test_cases],
            indent=2,
        )

        locator_info = ""
        if locator_map:
            locator_info = f"""
AVAILABLE ELEMENT LOCATORS:
{json.dumps([e.model_dump() for e in locator_map.elements], indent=2)}
"""

        return f"""Generate test class(es) for the following manual test cases:

TEST CASES:
{test_cases_json}
{locator_info}
REQUIREMENTS:
1. Create test methods for EACH test case
2. Each test method should implement ALL steps from the manual test case
3. Use Page Object methods (don't interact with elements directly in tests)
4. Add report logging for each step (e.g., ExtentTest.log(), allure.step(), etc.)
5. Add proper assertions with meaningful messages for each expected result
6. Configure test priority/order based on the test case priority
7. Add @Test annotations with description matching the test case title
8. Include setup and teardown methods
9. Use data providers/parametrize if test cases share similar patterns with different data
10. Package: {config.package_name}.tests

NAMING CONVENTION:
- Test class: {{Module}}Test (e.g., LoginTest, RegistrationTest)
- Test method: test_{{test_case_title_camelCase}} (e.g., testValidLogin)"""

    # ── Framework/Config Generation ───────────────────────────────────────

    @staticmethod
    def framework_prompt(config: GenerationConfig) -> str:
        """Generate prompt for framework setup files (BaseTest, config, utilities)."""

        if config.language == Language.JAVA and config.automation_tool == AutomationTool.SELENIUM:
            return PromptBuilder._java_selenium_framework_prompt(config)
        elif config.language == Language.JAVA and config.automation_tool == AutomationTool.PLAYWRIGHT:
            return PromptBuilder._java_playwright_framework_prompt(config)
        elif config.language == Language.PYTHON and config.automation_tool == AutomationTool.SELENIUM:
            return PromptBuilder._python_selenium_framework_prompt(config)
        elif config.language == Language.PYTHON and config.automation_tool == AutomationTool.PLAYWRIGHT:
            return PromptBuilder._python_playwright_framework_prompt(config)
        elif config.language in (Language.JAVASCRIPT, Language.TYPESCRIPT):
            return PromptBuilder._js_playwright_framework_prompt(config)
        else:
            return PromptBuilder._generic_framework_prompt(config)

    @staticmethod
    def _java_selenium_framework_prompt(config: GenerationConfig) -> str:
        report_setup = (
            "ExtentReports 5 with ExtentSparkReporter"
            if config.report_tool == ReportTool.EXTENT_REPORTS
            else "Allure Report with @Step, @Description, @Epic annotations"
        )
        return f"""Generate the complete framework setup files for a Java + Selenium + {config.test_framework.value} project:

1. **pom.xml** - Maven build file with dependencies:
   - Selenium WebDriver 4.x
   - {config.test_framework.value}
   - {"ExtentReports 5" if config.report_tool == ReportTool.EXTENT_REPORTS else "Allure TestNG/JUnit5"}
   - WebDriverManager (io.github.bonigarcia)
   - Log4j2 for logging
   - GroupId: {config.package_name}

2. **BasePage.java** ({config.package_name}.pages):
   - WebDriver instance
   - WebDriverWait instance (configurable timeout)
   - Common methods: click, type, getText, isDisplayed, waitForElement, scrollTo, switchToFrame, etc.
   - Screenshot capture method
   - Constructor accepting WebDriver

3. **BaseTest.java** ({config.package_name}.base):
   - @BeforeMethod: Initialize WebDriver via WebDriverManager (Chrome default, configurable)
   - @AfterMethod: Quit WebDriver, capture screenshot on failure
   - WebDriver getter
   - {report_setup} setup in @BeforeSuite/@AfterSuite

4. **ConfigReader.java** ({config.package_name}.utils):
   - Read from config.properties file
   - Properties: base.url, browser, headless, timeout, screenshot.path

5. **config.properties**:
   - base.url={config.base_url or 'https://example.com'}
   - browser={config.browser}
   - headless={str(config.headless).lower()}
   - implicit.wait=10
   - explicit.wait=15
   - screenshot.path=./screenshots

6. **testng.xml** / **junit-platform.properties** (test runner config)

7. **ExtentReportManager.java** or **AllureListener.java** ({config.package_name}.reports):
   - Report initialization and configuration
   - Test listener for auto-logging pass/fail/skip
   - Screenshot attachment on failure"""

    @staticmethod
    def _java_playwright_framework_prompt(config: GenerationConfig) -> str:
        framework = config.test_framework.value
        report_setup = (
            "ExtentReports 5 with ExtentSparkReporter"
            if config.report_tool == ReportTool.EXTENT_REPORTS
            else "Allure Report with @Step, @Description annotations"
        )
        return f"""Generate the complete framework setup files for a Java + Playwright + {framework} project:

1. **pom.xml** - Maven build file with dependencies:
   - com.microsoft.playwright:playwright (latest)
   - {framework}
   - {"ExtentReports 5" if config.report_tool == ReportTool.EXTENT_REPORTS else "Allure"}
   - Log4j2 for logging
   - GroupId: {config.package_name}

2. **BasePage.java** ({config.package_name}.pages):
   - Playwright Page instance
   - Common methods: click, fill, getText, isVisible, waitForSelector, navigate, etc.
   - Screenshot capture via page.screenshot()
   - Constructor accepting Playwright Page

3. **BaseTest.java** ({config.package_name}.base):
   - @BeforeClass/@BeforeSuite: Launch Playwright browser
   - @BeforeMethod: Create new BrowserContext and Page
   - @AfterMethod: Close context, capture screenshot on failure
   - @AfterClass/@AfterSuite: Close browser and Playwright
   - {report_setup} setup

4. **ConfigReader.java** ({config.package_name}.utils):
   - Read from config.properties
   - Properties: base.url, browser, headless, timeout, trace.enabled

5. **config.properties**:
   - base.url={config.base_url or 'https://example.com'}
   - browser={config.browser}
   - headless={str(config.headless).lower()}
   - timeout=30000
   - trace.enabled=true
   - screenshot.path=./screenshots

6. **testng.xml** or **junit-platform.properties** ({framework} runner config)

7. **ExtentReportManager.java** or **AllureListener.java** ({config.package_name}.reports):
   - Report initialization
   - Listener for auto-logging
   - Screenshot + trace attachment on failure"""

    @staticmethod
    def _python_selenium_framework_prompt(config: GenerationConfig) -> str:
        report = (
            "pytest-html + ExtentReports (via python-extent-reports)"
            if config.report_tool == ReportTool.EXTENT_REPORTS
            else "allure-pytest"
        )
        return f"""Generate the complete framework setup files for a Python + Selenium + pytest project:

1. **requirements.txt**:
   - selenium>=4.0
   - pytest>=7.0
   - webdriver-manager
   - {"extent-reports" if config.report_tool == ReportTool.EXTENT_REPORTS else "allure-pytest"}
   - python-dotenv

2. **conftest.py** (root):
   - @pytest.fixture(scope="function"): WebDriver setup/teardown
   - Browser configuration via pytest command-line options
   - Screenshot on failure (pytest_runtest_makereport hook)
   - Report integration fixtures

3. **base_page.py** (pages/):
   - WebDriver instance
   - WebDriverWait helper
   - Common methods: click, type_text, get_text, is_displayed, wait_for, scroll_to
   - Screenshot method

4. **config.py** (utils/):
   - Load from .env or config.ini
   - BASE_URL, BROWSER, HEADLESS, TIMEOUT settings

5. **pytest.ini** / **pyproject.toml**:
   - Test paths, markers, reporting options

6. **.env**:
   - BASE_URL={config.base_url or 'https://example.com'}
   - BROWSER={config.browser}
   - HEADLESS={str(config.headless)}"""

    @staticmethod
    def _python_playwright_framework_prompt(config: GenerationConfig) -> str:
        return f"""Generate the complete framework setup files for a Python + Playwright + pytest project:

1. **requirements.txt**:
   - playwright
   - pytest
   - pytest-playwright
   - {"allure-pytest" if config.report_tool == ReportTool.ALLURE else "pytest-html"}

2. **conftest.py** (root):
   - Playwright browser/context/page fixtures
   - Screenshot on failure
   - Trace recording config
   - Report integration

3. **base_page.py** (pages/):
   - Playwright Page instance
   - Common methods: navigate, click, fill, get_text, is_visible, wait_for
   - Screenshot method

4. **config.py** (utils/):
   - Settings from environment or .env file

5. **pytest.ini** / **pyproject.toml**:
   - Playwright configuration
   - BASE_URL={config.base_url or 'https://example.com'}"""

    @staticmethod
    def _js_playwright_framework_prompt(config: GenerationConfig) -> str:
        lang_ext = "ts" if config.language == Language.TYPESCRIPT else "js"
        return f"""Generate the complete framework setup files for a {'TypeScript' if config.language == Language.TYPESCRIPT else 'JavaScript'} + Playwright project:

1. **package.json**:
   - @playwright/test
   - {'typescript, @types/node' if config.language == Language.TYPESCRIPT else ''}
   - Scripts: test, test:headed, test:debug, report

2. **playwright.config.{lang_ext}**:
   - Base URL: {config.base_url or 'https://example.com'}
   - Browser projects: chromium, firefox, webkit
   - Reporter: html, list
   - Retries, timeout, screenshot on failure

3. **base.page.{lang_ext}** (pages/):
   - Playwright Page instance
   - Common helper methods
   - Navigation and assertion helpers

4. **global-setup.{lang_ext}** (if needed):
   - Authentication state, storage state

5. {'**tsconfig.json**' if config.language == Language.TYPESCRIPT else ''}"""

    @staticmethod
    def _generic_framework_prompt(config: GenerationConfig) -> str:
        return f"""Generate framework setup files for:
- Language: {config.language.value}
- Tool: {config.automation_tool.value}
- Framework: {config.test_framework.value}
- Report: {config.report_tool.value}

Include: build config, base classes, utilities, test runner config, and report setup."""

    # ── Screenshot Analysis ───────────────────────────────────────────────

    @staticmethod
    def screenshot_analysis_prompt() -> str:
        """Generate prompt for analyzing UI screenshots."""
        return """Analyze this screenshot of a web application UI and provide:

1. **Page Identification**: What type of page is this? (login, dashboard, form, list, etc.)

2. **UI Components**: List ALL visible interactive elements:
   - Buttons (text, position, likely purpose)
   - Input fields (type, placeholder text, labels)
   - Links/navigation items
   - Dropdowns/select elements
   - Checkboxes/radio buttons
   - Tables/data grids
   - Modals/dialogs
   - Navigation menus

3. **User Flow**: What user actions/journey does this page support?

4. **Element Hierarchy**: Describe the layout structure (header, sidebar, main content, footer)

5. **Suggested Locator Strategies**: For each identified element, suggest:
   - Likely HTML tag
   - Possible id/name/class attributes
   - Text content for text-based locators

Return the analysis as a structured JSON object with the above categories."""

    # ── Code Review/Validation ────────────────────────────────────────────

    @staticmethod
    def review_prompt(code: str, config: GenerationConfig) -> str:
        """Generate prompt for AI self-review of generated code."""
        return f"""Review the following generated automation code for quality and correctness:

```
{code}
```

CHECK FOR:
1. ❌ Any use of Thread.sleep() / time.sleep() / hardcoded waits
2. ❌ Missing imports or undefined references
3. ❌ Direct element interactions in test classes (should use Page Objects)
4. ❌ Missing assertions or assertions without messages
5. ❌ Hardcoded test data in test methods
6. ❌ Missing report logging steps
7. ❌ Syntax errors or compilation issues
8. ❌ Missing null checks or error handling
9. ❌ Non-descriptive method/variable names

RESPOND WITH:
- "PASS" if code is production-ready
- "ISSUES:" followed by a numbered list of problems and their fixes
- "FIXED_CODE:" followed by the corrected version (only if issues found)"""
