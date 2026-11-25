"""
LLM-powered test failure analysis service.

Integrates Claude API to analyze failed Playwright selectors and provide
fix suggestions and root cause analysis.
"""

import json
import os
from typing import Optional, TypedDict
from anthropic import Anthropic

_client = None


def _get_client():
    """Lazy-load Anthropic client on first use."""
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


class TestFailure(TypedDict):
    """Schema for a test failure event."""
    selector: str
    error_message: str
    page_url: str
    page_title: str
    test_name: str
    stack_trace: str
    timestamp: str


class AnalysisResult(TypedDict):
    """Schema for LLM analysis result."""
    root_cause: str
    suggestions: list[str]
    confidence: int
    reasoning: str


def analyze_test_failure(failure: TestFailure) -> AnalysisResult:
    """
    Analyze a test failure using Claude API.

    Args:
        failure: TestFailure dict with selector, error, and context

    Returns:
        AnalysisResult with root cause, suggestions, and confidence score
    """
    model = os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")

    prompt = _build_analysis_prompt(failure)

    try:
        client = _get_client()
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text
        result = _parse_analysis_response(content)

    except Exception as e:
        # Fallback to mock response if API fails (e.g., new account with no model access)
        if "not_found_error" in str(e) or "404" in str(e):
            import logging
            logging.warning(f"Claude API unavailable: {str(e)}. Using mock response.")
            result = _mock_analysis_response(failure)
        else:
            raise

    return result


def _build_analysis_prompt(failure: TestFailure) -> str:
    """Build the Claude prompt for test failure analysis."""
    return f"""You are a Playwright test automation expert. Analyze this test failure and provide diagnostic suggestions.

**Test Details:**
- Test Name: {failure['test_name']}
- Error Message: {failure['error_message']}
- Failed Selector: {failure['selector']}
- Page URL: {failure['page_url']}
- Page Title: {failure['page_title']}
- Stack Trace: {failure['stack_trace']}

**Task:** Provide a concise analysis with:
1. **Root Cause** (one line): The most likely reason for failure
2. **Suggestions** (list 2-3 concrete fixes):
   - Alternative selectors to try
   - DOM traversal changes
   - Waiting strategies
3. **Confidence** (0-10): How confident you are in the diagnosis
4. **Reasoning** (brief): Why you think these suggestions will work

Format your response as JSON:
{{
  "root_cause": "...",
  "suggestions": ["...", "...", "..."],
  "confidence": 8,
  "reasoning": "..."
}}

Be practical and suggest things Playwright developers actually do. Focus on common failures like:
- Selector specificity too high/low
- Element not in viewport
- Dynamic class names or IDs
- Stale element references
- Timing issues (need explicit wait)
- Incorrect XPath or CSS syntax
"""


def _parse_analysis_response(content: str) -> AnalysisResult:
    """Parse Claude's JSON response into structured result."""
    try:
        # Try to extract JSON if Claude wrapped it in markdown
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0].strip()
        else:
            json_str = content

        data = json.loads(json_str)

        return AnalysisResult(
            root_cause=data.get("root_cause", "Unknown"),
            suggestions=data.get("suggestions", []),
            confidence=min(10, max(0, int(data.get("confidence", 5)))),
            reasoning=data.get("reasoning", ""),
        )
    except (json.JSONDecodeError, IndexError, ValueError) as e:
        # Fallback if parsing fails
        return AnalysisResult(
            root_cause="Analysis parsing failed",
            suggestions=["Review error manually", "Check DOM structure", "Add wait condition"],
            confidence=2,
            reasoning=f"Error parsing Claude response: {str(e)}. Raw: {content[:200]}",
        )


def format_analysis_for_report(
    failure: TestFailure, analysis: AnalysisResult
) -> dict:
    """
    Format analysis result for inclusion in Playwright HTML report.

    Returns a dict suitable for JSON serialization and report embedding.
    """
    return {
        "test_name": failure["test_name"],
        "selector": failure["selector"],
        "error": failure["error_message"],
        "analysis": {
            "root_cause": analysis["root_cause"],
            "suggestions": analysis["suggestions"],
            "confidence": f"{analysis['confidence']}/10",
            "reasoning": analysis["reasoning"],
        },
        "context": {
            "url": failure["page_url"],
            "title": failure["page_title"],
        },
    }


def _mock_analysis_response(failure: TestFailure) -> AnalysisResult:
    """
    Generate a mock analysis response when Claude API is unavailable.
    
    Used as fallback for new accounts without model access.
    Demonstrates the expected response format.
    """
    selector = failure.get("selector", "")
    error = failure.get("error_message", "").lower()
    
    # Basic heuristics based on selector and error
    if "not found" in error or "element" in error:
        root_cause = f"Selector '{selector}' does not match any elements on the page (element not found)"
        suggestions = [
            f"Verify the selector syntax: '{selector}'",
            "Check if the element exists with: await page.locator('{selector}').count()",
            "Consider adding a waitForSelector before the assertion"
        ]
        confidence = 7
    elif "timeout" in error:
        root_cause = "Element not visible within timeout period"
        suggestions = [
            "Increase timeout: await expect(element).toBeVisible({ timeout: 10000 })",
            "Add explicit wait: await page.waitForSelector(selector)",
            "Check if element requires scrolling or interaction to become visible"
        ]
        confidence = 6
    else:
        root_cause = f"Test assertion failed for selector '{selector}'"
        suggestions = [
            "Review the DOM structure on the page",
            "Verify selector specificity and CSS/XPath correctness",
            "Add explicit waits if elements are dynamically loaded"
        ]
        confidence = 5
    
    return AnalysisResult(
        root_cause=root_cause,
        suggestions=suggestions,
        confidence=confidence,
        reasoning="[MOCK RESPONSE] Your Anthropic API key doesn't have access to Claude models yet. "
                 "To enable real Claude analysis: visit https://console.anthropic.com/settings and verify model access. "
                 "This mock response demonstrates the analysis format."
    )

