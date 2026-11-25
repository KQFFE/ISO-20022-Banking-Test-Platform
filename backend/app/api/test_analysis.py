"""
API endpoints for LLM-powered test failure analysis.

Receives test failures from Playwright reporter and provides Claude-based
root cause analysis and fix suggestions.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services import analyze_test_failure, format_analysis_for_report

router = APIRouter()


class TestFailureRequest(BaseModel):
    """Request schema for test failure analysis."""
    test_name: str
    file: str
    line: int
    error_message: str
    stack_trace: str
    selector: str
    page_url: str
    page_title: str = "unknown"
    status: str
    duration: int


@router.post("/analyze-failure")
async def analyze_failure(failure: TestFailureRequest):
    """
    Analyze a test failure using Claude API.

    Receives failure details from Playwright reporter and returns
    root cause analysis with fix suggestions.

    Args:
        failure: TestFailureRequest with error details

    Returns:
        Analysis result with root_cause, suggestions, and confidence
    """
    try:
        # Convert request to service-compatible dict
        failure_dict = {
            "test_name": failure.test_name,
            "error_message": failure.error_message,
            "selector": failure.selector,
            "page_url": failure.page_url,
            "page_title": failure.page_title,
            "stack_trace": failure.stack_trace,
            "timestamp": "",
        }

        # Call Claude API via service
        analysis = analyze_test_failure(failure_dict)

        # Format for report
        report = format_analysis_for_report(failure_dict, analysis)

        return {
            "success": True,
            "analysis": report,
            "debug": {
                "test_name": failure.test_name,
                "selector": failure.selector,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing test failure: {str(e)}",
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for test analysis service."""
    return {"status": "healthy", "service": "test-analyzer"}
