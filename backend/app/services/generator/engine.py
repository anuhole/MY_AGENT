"""
AutoTestAI - Code Generation Engine
Orchestrates the entire code generation pipeline:
Parse inputs → Analyze HTML → Build context → Generate code → Validate → Package
"""
import os
import json
import shutil
import logging
import zipfile
from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime

from app.config import settings
from app.models.schemas import (
    GenerationConfig, GenerationRequest, GenerationResult,
    GeneratedFile, TestSuite, LocatorMap,
    Language, AutomationTool, TestFramework, ReportTool,
    JobStatus, validate_combination,
)
from app.services.ai.llm_orchestrator import LLMOrchestrator
from app.services.ai.prompt_builder import PromptBuilder
from app.services.ai.code_validator import CodeValidator

logger = logging.getLogger(__name__)


class CodeGenerationEngine:
    """
    Main engine for generating test automation projects.
    Coordinates parsing, AI generation, validation, and packaging.
    """

    def __init__(self, llm: Optional[LLMOrchestrator] = None):
        self.llm = llm or LLMOrchestrator()
        self.prompt_builder = PromptBuilder()
        self.validator = CodeValidator()

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        Execute the full code generation pipeline.

        Args:
            request: Complete generation request with config, test cases, and locators

        Returns:
            GenerationResult with all generated files and metadata
        """
        config = request.config
        job_id = request.request_id

        logger.info(f"[{job_id}] Starting code generation: "
                     f"{config.language.value} + {config.automation_tool.value} + "
                     f"{config.test_framework.value}")

        result = GenerationResult(
            job_id=job_id,
            status=JobStatus.GENERATING,
            config=config,
        )

        # Validate combination
        if not validate_combination(config):
            result.status = JobStatus.FAILED
            result.errors.append(
                f"Invalid combination: {config.language.value} + "
                f"{config.automation_tool.value} + {config.test_framework.value} + "
                f"{config.report_tool.value}"
            )
            return result

        try:
            # Step 1: Generate framework files (BaseTest, BasePage, config, build file)
            logger.info(f"[{job_id}] Generating framework files...")
            result.status = JobStatus.GENERATING
            
            try:
                framework_files = await self._generate_framework(config)
                result.files.extend(framework_files)
            except Exception as llm_err:
                logger.warning(f"[{job_id}] Framework LLM generation bypassed: {llm_err}")

            # Step 2: Generate Page Object classes
            if request.locator_map and request.locator_map.elements:
                logger.info(f"[{job_id}] Generating Page Object classes...")
                try:
                    page_files = await self._generate_page_objects(config, request.locator_map)
                    result.files.extend(page_files)
                except Exception as llm_err:
                    logger.warning(f"[{job_id}] Page Object LLM generation bypassed: {llm_err}")

            # Step 3: Generate test classes
            if request.test_suite and request.test_suite.test_cases:
                logger.info(f"[{job_id}] Generating test classes...")
                try:
                    test_files = await self._generate_tests(
                        config, request.test_suite, request.locator_map
                    )
                    result.files.extend(test_files)
                except Exception as llm_err:
                    logger.warning(f"[{job_id}] Test classes LLM generation bypassed: {llm_err}")

            # Fallback: If no files were generated (e.g. no API key or LLM error), generate via Template Engine
            if not result.files or not any(f.file_type == "test" for f in result.files):
                logger.info(f"[{job_id}] Synthesizing complete production-ready framework via Template Engine...")
                from app.services.generator.template_engine import TemplateGenerationEngine
                template_files = TemplateGenerationEngine.generate_all(
                    config, request.test_suite, request.locator_map
                )
                # Avoid duplicates
                existing_paths = {f.file_path for f in result.files}
                for tf in template_files:
                    if tf.file_path not in existing_paths:
                        result.files.append(tf)

            # Step 4: Validate generated code
            logger.info(f"[{job_id}] Validating generated code...")
            result.status = JobStatus.VALIDATING
            for gf in result.files:
                is_valid, issues = self.validator.validate(gf.content, config)
                if issues:
                    result.warnings.extend(
                        [f"[{gf.file_path}] {issue}" for issue in issues]
                    )

            # Step 5: Write files to disk and create ZIP
            logger.info(f"[{job_id}] Packaging project...")
            output_dir = self._write_project(job_id, config, result.files)
            result.output_directory = output_dir
            result.zip_path = self._create_zip(output_dir, job_id)

            result.status = JobStatus.COMPLETED
            result.completed_at = datetime.utcnow()

            logger.info(
                f"[{job_id}] Generation complete! "
                f"{len(result.files)} files generated, "
                f"{len(result.warnings)} warnings"
            )

        except Exception as e:
            logger.error(f"[{job_id}] Generation failed: {e}", exc_info=True)
            # Try emergency template fallback
            try:
                from app.services.generator.template_engine import TemplateGenerationEngine
                template_files = TemplateGenerationEngine.generate_all(config, request.test_suite, request.locator_map)
                output_dir = self._write_project(job_id, config, template_files)
                result.files = template_files
                result.output_directory = output_dir
                result.zip_path = self._create_zip(output_dir, job_id)
                result.status = JobStatus.COMPLETED
                result.completed_at = datetime.utcnow()
                result.warnings.append("Project generated using production template engine (LLM unavailable).")
                return result
            except Exception as e2:
                result.status = JobStatus.FAILED
                result.errors.append(f"Primary error: {e}; Fallback error: {e2}")

        return result

    async def _generate_framework(self, config: GenerationConfig) -> List[GeneratedFile]:
        """Generate framework setup files via LLM."""
        system_prompt = self.prompt_builder.system_prompt(config)
        user_prompt = self.prompt_builder.framework_prompt(config)

        raw_response = await self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
            max_tokens=8192,
        )

        # Extract individual files from response
        extracted = self.validator.extract_files(raw_response)

        files = []
        for file_path, content in extracted:
            files.append(GeneratedFile(
                file_path=file_path,
                content=content,
                file_type="framework",
                description=f"Framework file: {Path(file_path).name}",
            ))

        return files

    async def _generate_page_objects(
        self,
        config: GenerationConfig,
        locator_map: LocatorMap,
    ) -> List[GeneratedFile]:
        """Generate Page Object Model classes via LLM."""
        system_prompt = self.prompt_builder.system_prompt(config)

        # Determine page name from title or URL
        page_name = "Main"
        if locator_map.page_title:
            # Convert title to PascalCase class name
            words = locator_map.page_title.split()[:3]
            page_name = "".join(w.capitalize() for w in words)

        user_prompt = self.prompt_builder.page_object_prompt(
            config, locator_map, page_name
        )

        raw_response = await self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
            max_tokens=6144,
        )

        extracted = self.validator.extract_files(raw_response)

        files = []
        for file_path, content in extracted:
            files.append(GeneratedFile(
                file_path=file_path,
                content=content,
                file_type="page_object",
                description=f"Page Object: {Path(file_path).stem}",
            ))

        return files

    async def _generate_tests(
        self,
        config: GenerationConfig,
        test_suite: TestSuite,
        locator_map: Optional[LocatorMap],
    ) -> List[GeneratedFile]:
        """Generate test classes via LLM."""
        system_prompt = self.prompt_builder.system_prompt(config)
        user_prompt = self.prompt_builder.test_class_prompt(
            config, test_suite, locator_map
        )

        raw_response = await self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=8192,
        )

        extracted = self.validator.extract_files(raw_response)

        files = []
        for file_path, content in extracted:
            files.append(GeneratedFile(
                file_path=file_path,
                content=content,
                file_type="test",
                description=f"Test class: {Path(file_path).stem}",
            ))

        return files

    def _write_project(
        self,
        job_id: str,
        config: GenerationConfig,
        files: List[GeneratedFile],
    ) -> str:
        """Write generated files to disk as a project directory."""
        project_name = config.project_name or f"autotestai-{job_id[:8]}"
        output_dir = os.path.join(settings.OUTPUT_DIR, project_name)

        # Clean existing directory
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)

        os.makedirs(output_dir, exist_ok=True)

        # Write each file
        for gf in files:
            file_full_path = os.path.join(output_dir, gf.file_path)
            os.makedirs(os.path.dirname(file_full_path), exist_ok=True)

            with open(file_full_path, "w", encoding="utf-8") as f:
                f.write(gf.content)

            logger.debug(f"Written: {gf.file_path}")

        # Generate README
        readme_content = self._generate_readme(config, files)
        readme_path = os.path.join(output_dir, "README.md")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)

        logger.info(f"Project written to: {output_dir}")
        return output_dir

    def _create_zip(self, output_dir: str, job_id: str) -> str:
        """Create a ZIP archive of the generated project."""
        zip_name = f"{os.path.basename(output_dir)}.zip"
        zip_path = os.path.join(settings.OUTPUT_DIR, zip_name)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(output_dir))
                    zf.write(file_path, arcname)

        logger.info(f"ZIP created: {zip_path}")
        return zip_path

    def _generate_readme(
        self,
        config: GenerationConfig,
        files: List[GeneratedFile],
    ) -> str:
        """Generate a README.md for the project."""
        lang_name = config.language.value.capitalize()
        tool_name = config.automation_tool.value.capitalize()
        framework_name = config.test_framework.value
        report_name = config.report_tool.value.replace("_", " ").title()

        run_instructions = {
            Language.JAVA: """## Running Tests

```bash
# Install dependencies
mvn clean install -DskipTests

# Run all tests
mvn test

# Run specific test class
mvn test -Dtest=LoginTest

# Run with specific browser
mvn test -Dbrowser=firefox

# Generate report
mvn surefire-report:report
```""",
            Language.PYTHON: """## Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (if using Playwright)
playwright install

# Run all tests
pytest

# Run specific test
pytest tests/test_login.py -v

# Run with HTML report
pytest --html=reports/report.html

# Run with Allure
pytest --alluredir=reports/allure-results
allure serve reports/allure-results
```""",
            Language.JAVASCRIPT: """## Running Tests

```bash
# Install dependencies
npm install

# Install Playwright browsers
npx playwright install

# Run all tests
npm test

# Run headed (visible browser)
npm run test:headed

# Run with debug
npm run test:debug

# View report
npx playwright show-report
```""",
            Language.TYPESCRIPT: """## Running Tests

```bash
# Install dependencies
npm install

# Install Playwright browsers
npx playwright install

# Run all tests
npm test

# Run headed
npm run test:headed

# View report
npx playwright show-report
```""",
        }

        files_list = "\n".join(
            f"- `{gf.file_path}` — {gf.description}" for gf in files
        )

        return f"""# 🤖 AutoTestAI Generated Project

> Auto-generated test automation project by **AutoTestAI**

## Tech Stack
| Component | Technology |
|---|---|
| Language | **{lang_name}** |
| Automation Tool | **{tool_name}** |
| Test Framework | **{framework_name}** |
| Reporting | **{report_name}** |

## Project Structure
{files_list}

{run_instructions.get(config.language, '')}

## Configuration
- Base URL: `{config.base_url or 'https://example.com'}`
- Browser: `{config.browser}`
- Headless: `{config.headless}`

## Reports
After running tests, reports are generated in the `reports/` directory.

---
*Generated by AutoTestAI on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*
"""
