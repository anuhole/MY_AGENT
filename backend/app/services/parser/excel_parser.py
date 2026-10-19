"""
AutoTestAI - Excel Parser
Parses .xlsx/.xls files containing manual test cases into structured TestSuite objects.
Supports multiple common Excel formats and auto-detects column mappings.
"""
import re
import logging
from typing import List, Optional, Dict, Tuple
from pathlib import Path

import openpyxl

from app.models.schemas import TestCase, TestStep, TestSuite

logger = logging.getLogger(__name__)


# Common column name patterns for auto-detection
COLUMN_PATTERNS = {
    "test_case_id": [
        r"test\s*case\s*id", r"tc\s*id", r"id", r"test\s*id",
        r"case\s*id", r"sl\.?\s*no", r"s\.?\s*no", r"#", r"serial",
    ],
    "title": [
        r"test\s*case\s*(name|title|description)", r"title", r"name",
        r"summary", r"description", r"test\s*scenario", r"scenario",
    ],
    "module": [
        r"module", r"feature", r"component", r"area", r"category",
    ],
    "priority": [
        r"priority", r"severity", r"importance",
    ],
    "preconditions": [
        r"pre\s*condition", r"prerequisite", r"setup",
    ],
    "steps": [
        r"test\s*step", r"step", r"action", r"procedure",
        r"steps\s*to\s*reproduce", r"test\s*procedure",
    ],
    "test_data": [
        r"test\s*data", r"data", r"input", r"input\s*data",
    ],
    "expected_result": [
        r"expected\s*result", r"expected\s*outcome", r"expected",
        r"expected\s*output", r"result",
    ],
    "postconditions": [
        r"post\s*condition", r"cleanup", r"teardown",
    ],
    "tags": [
        r"tag", r"label", r"keyword",
    ],
}


def _match_column(header: str, patterns: List[str]) -> bool:
    """Check if a header matches any of the given patterns."""
    header_clean = header.strip().lower()
    for pattern in patterns:
        if re.search(pattern, header_clean):
            return True
    return False


def _detect_columns(headers: List[str]) -> Dict[str, int]:
    """Auto-detect column mappings from header row."""
    mapping = {}
    for col_idx, header in enumerate(headers):
        if not header:
            continue
        for field, patterns in COLUMN_PATTERNS.items():
            if field not in mapping and _match_column(str(header), patterns):
                mapping[field] = col_idx
                break
    return mapping


def _split_multiline(text: str) -> List[str]:
    """Split multiline text into list of items."""
    if not text:
        return []
    lines = [line.strip() for line in text.strip().split("\n")]
    items = []
    for line in lines:
        # Remove numbering like "1.", "1)", "- ", "• "
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", line)
        cleaned = re.sub(r"^[\-•]\s*", "", cleaned)
        if cleaned:
            items.append(cleaned)
    return items


def _parse_steps_column(
    steps_text: str,
    data_text: Optional[str] = None,
    expected_text: Optional[str] = None,
) -> List[TestStep]:
    """Parse step descriptions into structured TestStep objects."""
    if not steps_text:
        return []

    step_lines = _split_multiline(str(steps_text))
    data_lines = _split_multiline(str(data_text)) if data_text else []
    expected_lines = _split_multiline(str(expected_text)) if expected_text else []

    steps = []
    for i, action in enumerate(step_lines):
        step = TestStep(
            step_number=i + 1,
            action=action,
            test_data=data_lines[i] if i < len(data_lines) else None,
            expected_result=expected_lines[i] if i < len(expected_lines) else None,
        )
        steps.append(step)
    return steps


def _get_cell_value(row, col_idx: int) -> Optional[str]:
    """Safely get cell value from a row."""
    try:
        val = row[col_idx].value
        return str(val).strip() if val is not None else None
    except (IndexError, AttributeError):
        return None


def parse_excel(file_path: str, sheet_name: Optional[str] = None) -> TestSuite:
    """
    Parse an Excel file containing manual test cases.

    Supports multiple formats:
    - Single row per test case (steps as multiline text)
    - Multiple rows per test case (one row per step)
    - Auto-detects column mappings from headers

    Args:
        file_path: Path to the .xlsx file
        sheet_name: Specific sheet to parse (default: first sheet)

    Returns:
        TestSuite with parsed test cases
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    logger.info(f"Parsing Excel file: {path.name}")
    warnings = []

    try:
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    except Exception as e:
        raise ValueError(f"Failed to open Excel file: {e}")

    # Select sheet
    if sheet_name:
        if sheet_name not in wb.sheetnames:
            raise ValueError(f"Sheet '{sheet_name}' not found. Available: {wb.sheetnames}")
        ws = wb[sheet_name]
    else:
        ws = wb.active

    rows = list(ws.iter_rows())
    if len(rows) < 2:
        warnings.append("File has less than 2 rows (header + data)")
        return TestSuite(
            source_file=path.name,
            total_cases=0,
            test_cases=[],
            parse_warnings=warnings,
        )

    # Extract headers from first row
    headers = [str(cell.value).strip() if cell.value else "" for cell in rows[0]]
    logger.info(f"Detected headers: {headers}")

    # Auto-detect column mappings
    col_map = _detect_columns(headers)
    logger.info(f"Column mapping: {col_map}")

    if "steps" not in col_map and "title" not in col_map:
        warnings.append(
            "Could not detect key columns (steps/title). "
            "Ensure headers contain recognizable names like 'Test Steps', 'Title', etc."
        )

    # Parse data rows
    test_cases: List[TestCase] = []
    current_tc_id = None
    current_steps: List[TestStep] = []
    step_counter = 0

    for row_idx, row in enumerate(rows[1:], start=2):
        # Get values using column mapping
        tc_id = _get_cell_value(row, col_map.get("test_case_id", 0))
        title = _get_cell_value(row, col_map["title"]) if "title" in col_map else None
        module = _get_cell_value(row, col_map["module"]) if "module" in col_map else None
        priority = _get_cell_value(row, col_map["priority"]) if "priority" in col_map else None
        preconditions_text = _get_cell_value(row, col_map["preconditions"]) if "preconditions" in col_map else None
        steps_text = _get_cell_value(row, col_map["steps"]) if "steps" in col_map else None
        data_text = _get_cell_value(row, col_map["test_data"]) if "test_data" in col_map else None
        expected_text = _get_cell_value(row, col_map["expected_result"]) if "expected_result" in col_map else None
        postconditions_text = _get_cell_value(row, col_map["postconditions"]) if "postconditions" in col_map else None
        tags_text = _get_cell_value(row, col_map["tags"]) if "tags" in col_map else None

        # Skip completely empty rows
        if not any([tc_id, title, steps_text]):
            continue

        # Determine if this is a new test case or continuation of steps
        if tc_id and tc_id != current_tc_id:
            # New test case
            if not tc_id:
                tc_id = f"TC{row_idx:03d}"

            # Parse steps (could be multiline in a single cell)
            steps = _parse_steps_column(steps_text, data_text, expected_text)

            # If steps are empty but we have an action column, treat as single step
            if not steps and steps_text:
                steps = [
                    TestStep(
                        step_number=1,
                        action=steps_text,
                        test_data=data_text,
                        expected_result=expected_text,
                    )
                ]

            tc = TestCase(
                test_case_id=tc_id,
                title=title or f"Test Case {tc_id}",
                module=module,
                priority=priority or "Medium",
                preconditions=_split_multiline(preconditions_text) if preconditions_text else [],
                steps=steps,
                postconditions=_split_multiline(postconditions_text) if postconditions_text else [],
                tags=[t.strip() for t in tags_text.split(",")] if tags_text else [],
            )
            test_cases.append(tc)
            current_tc_id = tc_id
            step_counter = len(steps)

        elif steps_text and current_tc_id and test_cases:
            # Continuation row: additional step for current test case
            step_counter += 1
            test_cases[-1].steps.append(
                TestStep(
                    step_number=step_counter,
                    action=steps_text,
                    test_data=data_text,
                    expected_result=expected_text,
                )
            )

    wb.close()

    logger.info(f"Parsed {len(test_cases)} test cases from {path.name}")

    return TestSuite(
        source_file=path.name,
        total_cases=len(test_cases),
        test_cases=test_cases,
        parse_warnings=warnings,
    )


def get_sheet_names(file_path: str) -> List[str]:
    """Get list of sheet names from an Excel file."""
    wb = openpyxl.load_workbook(file_path, read_only=True)
    names = wb.sheetnames
    wb.close()
    return names
