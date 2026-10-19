"""
AutoTestAI - DOCX Parser
Parses .docx files containing manual test cases (tables and paragraphs).
"""
import re
import logging
from typing import List, Optional
from pathlib import Path

from docx import Document
from docx.table import Table

from app.models.schemas import TestCase, TestStep, TestSuite

logger = logging.getLogger(__name__)


def _clean_text(text: str) -> str:
    """Clean and normalize text."""
    if not text:
        return ""
    return " ".join(text.strip().split())


def _extract_from_table(table: Table) -> List[TestCase]:
    """
    Extract test cases from a DOCX table.
    Supports multiple table formats:
    - Single table with all test cases
    - One table per test case with step details
    """
    rows = table.rows
    if len(rows) < 2:
        return []

    # Get headers
    headers = [_clean_text(cell.text).lower() for cell in rows[0].cells]
    logger.debug(f"Table headers: {headers}")

    # Try to detect if this is a test case detail table (key-value pairs)
    if len(headers) == 2 and any(
        kw in headers[0] for kw in ["field", "attribute", "property", ""]
    ):
        return _parse_detail_table(rows)

    # Otherwise parse as a list table
    return _parse_list_table(headers, rows)


def _parse_detail_table(rows) -> List[TestCase]:
    """Parse a key-value detail table (one test case per table)."""
    data = {}
    for row in rows:
        cells = row.cells
        if len(cells) >= 2:
            key = _clean_text(cells[0].text).lower()
            value = cells[1].text.strip()
            data[key] = value

    # Map known keys
    tc_id = None
    title = None
    steps_text = None
    expected_text = None
    preconditions = None

    for key, value in data.items():
        if any(p in key for p in ["test case id", "tc id", "id"]):
            tc_id = value
        elif any(p in key for p in ["title", "name", "description", "scenario"]):
            title = value
        elif any(p in key for p in ["step", "procedure", "action"]):
            steps_text = value
        elif any(p in key for p in ["expected", "result"]):
            expected_text = value
        elif any(p in key for p in ["precondition", "prerequisite"]):
            preconditions = value

    if not (tc_id or title):
        return []

    steps = _parse_steps_text(steps_text, expected_text)

    tc = TestCase(
        test_case_id=tc_id or "TC001",
        title=title or "Untitled Test Case",
        steps=steps,
        preconditions=_split_lines(preconditions) if preconditions else [],
    )
    return [tc]


def _parse_list_table(headers: List[str], rows) -> List[TestCase]:
    """Parse a table where each row is a test case or test step."""
    # Detect column indices
    col_map = {}
    for idx, header in enumerate(headers):
        if any(p in header for p in ["test case id", "tc id", "id", "s.no", "sl"]):
            col_map["id"] = idx
        elif any(p in header for p in ["title", "name", "description", "scenario"]):
            col_map["title"] = idx
        elif any(p in header for p in ["step", "action", "procedure"]):
            col_map["steps"] = idx
        elif any(p in header for p in ["data", "input"]):
            col_map["data"] = idx
        elif any(p in header for p in ["expected", "result"]):
            col_map["expected"] = idx
        elif any(p in header for p in ["module", "feature"]):
            col_map["module"] = idx
        elif any(p in header for p in ["priority", "severity"]):
            col_map["priority"] = idx
        elif any(p in header for p in ["precondition"]):
            col_map["preconditions"] = idx

    test_cases = []
    for row in list(rows)[1:]:  # Skip header
        cells = row.cells
        tc_id = _clean_text(cells[col_map["id"]].text) if "id" in col_map else None
        title = _clean_text(cells[col_map["title"]].text) if "title" in col_map else None
        steps_text = cells[col_map["steps"]].text if "steps" in col_map else None
        data_text = cells[col_map["data"]].text if "data" in col_map else None
        expected_text = cells[col_map["expected"]].text if "expected" in col_map else None
        module = _clean_text(cells[col_map["module"]].text) if "module" in col_map else None
        priority = _clean_text(cells[col_map["priority"]].text) if "priority" in col_map else None

        if not (tc_id or title or steps_text):
            continue

        steps = _parse_steps_text(steps_text, expected_text, data_text)

        tc = TestCase(
            test_case_id=tc_id or f"TC{len(test_cases) + 1:03d}",
            title=title or f"Test Case {len(test_cases) + 1}",
            module=module,
            priority=priority or "Medium",
            steps=steps,
        )
        test_cases.append(tc)

    return test_cases


def _parse_steps_text(
    steps_text: Optional[str],
    expected_text: Optional[str] = None,
    data_text: Optional[str] = None,
) -> List[TestStep]:
    """Parse step text into structured TestStep objects."""
    if not steps_text:
        return []

    step_lines = _split_lines(steps_text)
    expected_lines = _split_lines(expected_text) if expected_text else []
    data_lines = _split_lines(data_text) if data_text else []

    steps = []
    for i, action in enumerate(step_lines):
        steps.append(
            TestStep(
                step_number=i + 1,
                action=action,
                test_data=data_lines[i] if i < len(data_lines) else None,
                expected_result=expected_lines[i] if i < len(expected_lines) else None,
            )
        )
    return steps


def _split_lines(text: str) -> List[str]:
    """Split text into clean lines/items."""
    if not text:
        return []
    lines = text.strip().split("\n")
    result = []
    for line in lines:
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", line.strip())
        cleaned = re.sub(r"^[\-•·]\s*", "", cleaned)
        if cleaned:
            result.append(cleaned)
    return result


def _extract_from_paragraphs(doc: Document) -> List[TestCase]:
    """
    Extract test cases from document paragraphs (non-table content).
    Looks for patterns like:
    - Test Case ID: TC001
    - Title: ...
    - Steps: ...
    """
    test_cases = []
    current_data = {}
    current_field = None

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            if current_data:
                tc = _build_tc_from_dict(current_data, len(test_cases) + 1)
                if tc:
                    test_cases.append(tc)
                current_data = {}
                current_field = None
            continue

        # Check for key:value patterns
        match = re.match(r"^([\w\s]+):\s*(.+)$", text)
        if match:
            key = match.group(1).strip().lower()
            value = match.group(2).strip()
            current_data[key] = value
            current_field = key
        elif current_field:
            # Continuation of previous field
            current_data[current_field] = current_data.get(current_field, "") + "\n" + text

    # Don't forget the last test case
    if current_data:
        tc = _build_tc_from_dict(current_data, len(test_cases) + 1)
        if tc:
            test_cases.append(tc)

    return test_cases


def _build_tc_from_dict(data: dict, index: int) -> Optional[TestCase]:
    """Build a TestCase from a key-value dictionary."""
    tc_id = None
    title = None
    steps_text = None
    expected_text = None

    for key, value in data.items():
        if any(p in key for p in ["test case id", "tc id", "id"]):
            tc_id = value
        elif any(p in key for p in ["title", "name", "description"]):
            title = value
        elif any(p in key for p in ["step", "procedure", "action"]):
            steps_text = value
        elif any(p in key for p in ["expected", "result"]):
            expected_text = value

    if not (tc_id or title or steps_text):
        return None

    steps = _parse_steps_text(steps_text, expected_text)

    return TestCase(
        test_case_id=tc_id or f"TC{index:03d}",
        title=title or f"Test Case {index}",
        steps=steps,
    )


def parse_docx(file_path: str) -> TestSuite:
    """
    Parse a DOCX file containing manual test cases.
    Extracts from both tables and paragraphs.

    Args:
        file_path: Path to the .docx file

    Returns:
        TestSuite with parsed test cases
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"DOCX file not found: {file_path}")

    logger.info(f"Parsing DOCX file: {path.name}")
    warnings = []

    try:
        doc = Document(file_path)
    except Exception as e:
        raise ValueError(f"Failed to open DOCX file: {e}")

    all_test_cases: List[TestCase] = []

    # Extract from tables first (most structured)
    for table_idx, table in enumerate(doc.tables):
        try:
            tcs = _extract_from_table(table)
            all_test_cases.extend(tcs)
            logger.info(f"Table {table_idx + 1}: extracted {len(tcs)} test cases")
        except Exception as e:
            warnings.append(f"Error parsing table {table_idx + 1}: {e}")

    # If no test cases from tables, try paragraphs
    if not all_test_cases:
        try:
            tcs = _extract_from_paragraphs(doc)
            all_test_cases.extend(tcs)
            logger.info(f"Paragraphs: extracted {len(tcs)} test cases")
        except Exception as e:
            warnings.append(f"Error parsing paragraphs: {e}")

    if not all_test_cases:
        warnings.append("No test cases could be extracted from the document.")

    logger.info(f"Total parsed: {len(all_test_cases)} test cases from {path.name}")

    return TestSuite(
        source_file=path.name,
        total_cases=len(all_test_cases),
        test_cases=all_test_cases,
        parse_warnings=warnings,
    )
