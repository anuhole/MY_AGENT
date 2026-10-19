"""
AutoTestAI - Code Generation API Routes
Endpoints for triggering, monitoring, and downloading generated automation projects.
"""
import os
import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from app.config import settings
from app.models.schemas import (
    GenerationConfig, GenerationRequest, GenerationResult,
    TestSuite, LocatorMap, JobStatus,
    validate_combination, VALID_COMBINATIONS,
)
from app.services.generator.engine import CodeGenerationEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/generate", tags=["Code Generation"])

# In-memory job store (replace with DB in production)
_jobs: Dict[str, GenerationResult] = {}

# Shared engine instance
_engine = CodeGenerationEngine()


@router.post("", response_model=dict)
async def generate_code(
    config: GenerationConfig,
    test_suite: Optional[TestSuite] = None,
    locator_map: Optional[LocatorMap] = None,
    html_source: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
):
    """
    Trigger code generation with the specified configuration.

    Accepts test cases, locator maps, and HTML source as inputs.
    Returns a job ID for tracking progress.
    """
    # Validate the combination
    if not validate_combination(config):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid combination: {config.language.value} + "
                f"{config.automation_tool.value} + {config.test_framework.value} + "
                f"{config.report_tool.value}. "
                f"See /api/generate/combinations for valid options."
            ),
        )

    # Parse HTML if provided as string
    parsed_locator_map = locator_map
    if html_source and not locator_map:
        from app.services.parser.html_analyzer import analyze_html
        parsed_locator_map = analyze_html(html_source)

    # Create generation request
    request = GenerationRequest(
        config=config,
        test_suite=test_suite,
        locator_map=parsed_locator_map,
        html_source=html_source,
    )

    # Initialize job status
    result = GenerationResult(
        job_id=request.request_id,
        status=JobStatus.PENDING,
        config=config,
    )
    _jobs[request.request_id] = result

    # Run generation in background
    async def _run_generation():
        try:
            gen_result = await _engine.generate(request)
            _jobs[request.request_id] = gen_result
        except Exception as e:
            logger.error(f"Background generation failed: {e}", exc_info=True)
            _jobs[request.request_id].status = JobStatus.FAILED
            _jobs[request.request_id].errors.append(str(e))

    if background_tasks:
        background_tasks.add_task(_run_generation)
    else:
        # Sync execution for testing
        await _run_generation()

    return {
        "job_id": request.request_id,
        "status": "accepted",
        "message": (
            f"Code generation started for "
            f"{config.language.value} + {config.automation_tool.value} + "
            f"{config.test_framework.value}"
        ),
    }


@router.get("/{job_id}/status")
async def get_job_status(job_id: str):
    """Check the status of a code generation job."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    result = _jobs[job_id]
    return {
        "job_id": job_id,
        "status": result.status.value,
        "files_generated": len(result.files),
        "errors": result.errors,
        "warnings": result.warnings,
        "created_at": str(result.created_at),
        "completed_at": str(result.completed_at) if result.completed_at else None,
    }


@router.get("/{job_id}/preview")
async def preview_generated_code(job_id: str):
    """Preview the generated code files without downloading."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    result = _jobs[job_id]

    if result.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed yet. Status: {result.status.value}",
        )

    return {
        "job_id": job_id,
        "config": result.config.model_dump(),
        "files": [
            {
                "path": f.file_path,
                "type": f.file_type,
                "description": f.description,
                "content": f.content,
                "lines": len(f.content.split("\n")),
            }
            for f in result.files
        ],
        "warnings": result.warnings,
    }


@router.get("/{job_id}/download")
async def download_project(job_id: str):
    """Download the generated project as a ZIP file."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    result = _jobs[job_id]

    if result.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Status: {result.status.value}",
        )

    if not result.zip_path or not os.path.exists(result.zip_path):
        raise HTTPException(status_code=404, detail="ZIP file not found")

    filename = os.path.basename(result.zip_path)
    return FileResponse(
        result.zip_path,
        media_type="application/zip",
        filename=filename,
    )


@router.get("/combinations")
async def get_valid_combinations():
    """Get all valid language/tool/framework/report combinations."""
    return {
        "combinations": [
            {
                "language": c[0].value,
                "automation_tool": c[1].value,
                "test_framework": c[2].value,
                "report_tool": c[3].value,
            }
            for c in VALID_COMBINATIONS
        ],
        "total": len(VALID_COMBINATIONS),
    }


@router.get("/jobs")
async def list_jobs():
    """List all generation jobs."""
    return {
        "jobs": [
            {
                "job_id": job_id,
                "status": result.status.value,
                "config": {
                    "language": result.config.language.value,
                    "tool": result.config.automation_tool.value,
                    "framework": result.config.test_framework.value,
                },
                "files_count": len(result.files),
                "created_at": str(result.created_at),
            }
            for job_id, result in _jobs.items()
        ],
        "total": len(_jobs),
    }
