"""
AutoTestAI - Code Validator
Validates generated code for syntax, completeness, and best practices.
"""
import re
import logging
from typing import List, Tuple

from app.models.schemas import GenerationConfig, Language

logger = logging.getLogger(__name__)


class CodeValidator:
    """Validates generated automation code before delivery."""

    # Anti-patterns to detect
    ANTI_PATTERNS = {
        Language.JAVA: [
            (r"Thread\.sleep\s*\(", "Thread.sleep() detected — use WebDriverWait instead"),
            (r"driver\.findElement\s*\(", "Direct findElement in test class — use Page Object methods"),
            (r"System\.out\.println", "System.out.println — use proper logging (Log4j/SLF4J)"),
        ],
        Language.PYTHON: [
            (r"time\.sleep\s*\(", "time.sleep() detected — use explicit waits instead"),
            (r"driver\.find_element\s*\(", "Direct find_element in test — use Page Object methods"),
            (r"\bprint\s*\(", "print() statement — use proper logging"),
        ],
        Language.JAVASCRIPT: [
            (r"setTimeout\s*\(", "setTimeout detected — use Playwright auto-wait or waitForSelector"),
            (r"page\.\$\s*\(", "Direct page.$ in test — use Page Object methods"),
            (r"console\.log\s*\(", "console.log — use proper test reporter logging"),
        ],
        Language.TYPESCRIPT: [
            (r"setTimeout\s*\(", "setTimeout detected — use Playwright auto-wait"),
            (r"page\.\$\s*\(", "Direct page.$ in test — use Page Object methods"),
        ],
    }

    @staticmethod
    def validate(code: str, config: GenerationConfig) -> Tuple[bool, List[str]]:
        """
        Validate generated code.

        Args:
            code: Generated code string
            config: Generation configuration

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check for empty code
        if not code or len(code.strip()) < 50:
            issues.append("Generated code is empty or too short")
            return False, issues

        # Check anti-patterns
        anti_patterns = CodeValidator.ANTI_PATTERNS.get(config.language, [])
        for pattern, message in anti_patterns:
            matches = re.findall(pattern, code)
            if matches:
                issues.append(f"⚠️ {message} ({len(matches)} occurrence(s))")

        # Language-specific syntax checks
        if config.language == Language.JAVA:
            issues.extend(CodeValidator._validate_java(code))
        elif config.language == Language.PYTHON:
            issues.extend(CodeValidator._validate_python(code))
        elif config.language in (Language.JAVASCRIPT, Language.TYPESCRIPT):
            issues.extend(CodeValidator._validate_js(code))

        # Check for required components
        issues.extend(CodeValidator._validate_structure(code, config))

        is_valid = len([i for i in issues if not i.startswith("⚠️")]) == 0
        return is_valid, issues

    @staticmethod
    def _validate_java(code: str) -> List[str]:
        """Java-specific validation."""
        issues = []

        # Check for class declaration
        if "class " not in code:
            issues.append("Missing class declaration")

        # Check for imports
        if "import " not in code:
            issues.append("Missing import statements")

        # Check balanced braces
        open_braces = code.count("{")
        close_braces = code.count("}")
        if open_braces != close_braces:
            issues.append(f"Unbalanced braces: {open_braces} open, {close_braces} close")

        return issues

    @staticmethod
    def _validate_python(code: str) -> List[str]:
        """Python-specific validation."""
        issues = []

        # Check for class or function definition
        if "class " not in code and "def " not in code:
            issues.append("Missing class or function definitions")

        # Check for import
        if "import " not in code and "from " not in code:
            issues.append("Missing import statements")

        return issues

    @staticmethod
    def _validate_js(code: str) -> List[str]:
        """JavaScript/TypeScript-specific validation."""
        issues = []

        # Check for exports or class
        if "export" not in code and "class " not in code and "module.exports" not in code:
            issues.append("Missing exports or class definitions")

        return issues

    @staticmethod
    def _validate_structure(code: str, config: GenerationConfig) -> List[str]:
        """Check for required structural elements."""
        issues = []
        code_lower = code.lower()

        # Check for assertion keywords
        assertion_keywords = ["assert", "expect", "verify", "should"]
        if not any(kw in code_lower for kw in assertion_keywords):
            issues.append("⚠️ No assertions found in test code")

        # Check for wait-related keywords (good practice)
        wait_keywords = ["wait", "waitfor", "wait_for", "expected_conditions", "waitforselector"]
        if not any(kw in code_lower for kw in wait_keywords):
            issues.append("⚠️ No explicit wait mechanisms found")

        return issues

    @staticmethod
    def extract_files(raw_code: str) -> List[Tuple[str, str]]:
        """
        Extract individual files from LLM response containing multiple files.
        Files are expected to be separated by: // === FILE: path/to/File.ext ===

        Args:
            raw_code: Raw LLM response with potentially multiple files

        Returns:
            List of (file_path, file_content) tuples
        """
        # Pattern to match file separators
        file_pattern = r"(?://|#)\s*===\s*FILE:\s*(.+?)\s*===\s*\n"
        parts = re.split(file_pattern, raw_code)

        files = []
        if len(parts) >= 3:
            # parts[0] is content before first separator (usually empty)
            # parts[1] is first file path, parts[2] is first file content, etc.
            for i in range(1, len(parts), 2):
                if i + 1 < len(parts):
                    file_path = parts[i].strip()
                    content = parts[i + 1].strip()
                    # Remove markdown code block markers if present
                    content = re.sub(r"^```\w*\n", "", content)
                    content = re.sub(r"\n```\s*$", "", content)
                    files.append((file_path, content))
        else:
            # Single file, try to extract file path from first comment
            content = raw_code.strip()
            content = re.sub(r"^```\w*\n", "", content)
            content = re.sub(r"\n```\s*$", "", content)

            # Try to detect file path from package/class declaration
            path_match = re.search(r"package\s+([\w.]+);", content)
            if path_match:
                pkg = path_match.group(1).replace(".", "/")
                class_match = re.search(r"class\s+(\w+)", content)
                class_name = class_match.group(1) if class_match else "Generated"
                files.append((f"src/main/java/{pkg}/{class_name}.java", content))
            else:
                files.append(("generated_code.txt", content))

        return files
