"""
AutoTestAI - Upload API Routes
Handles file uploads for test cases (Excel/DOCX), HTML source code, and screenshots.
"""
import os
import logging
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Query

from app.config import settings
from app.models.schemas import (
    UploadResponse, ParseResponse, TestSuite, LocatorMap,
)
from app.services.parser.excel_parser import parse_excel, get_sheet_names
from app.services.parser.docx_parser import parse_docx
from app.services.parser.html_analyzer import analyze_html, analyze_html_file

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/upload", tags=["Upload"])

ALLOWED_TEST_EXTENSIONS = {".xlsx", ".xls", ".docx", ".csv"}
ALLOWED_HTML_EXTENSIONS = {".html", ".htm"}
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
MAX_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


async def _save_upload(file: UploadFile, subfolder: str) -> str:
    """Save uploaded file to disk and return the path."""
    upload_dir = os.path.join(settings.UPLOAD_DIR, subfolder)
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, file.filename)

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail=f"Uploaded file '{file.filename}' is empty (0 bytes).",
        )
    if len(content) > MAX_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    with open(file_path, "wb") as f:
        f.write(content)

    return file_path


@router.post("/testcases", response_model=ParseResponse)
async def upload_test_cases(
    file: UploadFile = File(...),
    sheet_name: Optional[str] = Query(None, description="Sheet name for Excel files"),
):
    """
    Upload and parse a test case file (Excel or DOCX).

    Returns parsed test cases in structured format.
    """
    ext = Path(file.filename).suffix.lower()

    if ext not in ALLOWED_TEST_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {ALLOWED_TEST_EXTENSIONS}",
        )

    # Save file
    file_path = await _save_upload(file, "testcases")

    try:
        # Parse based on file type
        if ext in {".xlsx", ".xls"}:
            test_suite = parse_excel(file_path, sheet_name=sheet_name)
        elif ext == ".docx":
            test_suite = parse_docx(file_path)
        elif ext == ".csv":
            # CSV can be handled by Excel parser (openpyxl doesn't support CSV directly)
            # For now, convert to xlsx or use a different approach
            raise HTTPException(status_code=501, detail="CSV support coming soon")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {ext}")

        if not test_suite.test_cases:
            logger.warning(f"No test cases found in {file.filename}")

        return ParseResponse(
            source_file=file.filename,
            test_suite=test_suite,
            message=f"Successfully parsed {test_suite.total_cases} test cases from {file.filename}",
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to parse {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Parse error: {str(e)}")


@router.post("/html", response_model=dict)
async def upload_html(
    file: UploadFile = File(None),
    html_content: Optional[str] = None,
    source_url: Optional[str] = Query(None, description="URL the HTML was fetched from"),
):
    """
    Upload HTML source code for element analysis.

    Accepts either a file upload or raw HTML string.
    Returns element locator map.
    """
    if file:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_HTML_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {ext}. Allowed: {ALLOWED_HTML_EXTENSIONS}",
            )

        file_path = await _save_upload(file, "html")
        locator_map = analyze_html_file(file_path)

    elif html_content is not None:
        if not html_content.strip():
            raise HTTPException(
                status_code=400,
                detail="HTML content cannot be empty.",
            )
        locator_map = analyze_html(html_content, source_url=source_url)

    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either a file upload or html_content",
        )

    return {
        "message": f"Analyzed HTML: {len(locator_map.elements)} elements found",
        "locator_map": locator_map.model_dump(),
    }


@router.post("/screenshots", response_model=UploadResponse)
async def upload_screenshots(
    file: UploadFile = File(...),
):
    """
    Upload a UI screenshot for Vision AI analysis.
    """
    ext = Path(file.filename).suffix.lower()

    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {ext}. Allowed: {ALLOWED_IMAGE_EXTENSIONS}",
        )

    file_path = await _save_upload(file, "screenshots")

    return UploadResponse(
        filename=file.filename,
        file_type="screenshot",
        file_path=file_path,
        message=f"Screenshot uploaded: {file.filename}",
    )


@router.get("/sheets/{filename}")
async def get_excel_sheets(filename: str):
    """Get sheet names from an uploaded Excel file."""
    file_path = os.path.join(settings.UPLOAD_DIR, "testcases", filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    sheets = get_sheet_names(file_path)
    return {"filename": filename, "sheets": sheets}
