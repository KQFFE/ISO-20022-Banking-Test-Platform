# Phase 1: Self-Healing Test Automation - Implementation Complete ✅

## What Was Built

### Backend Components

#### 1. **Test Analyzer Service** (`backend/services/test_analyzer.py`)
- Integrates Claude API for failure analysis
- Accepts test failure data with selector, error message, and context
- Returns structured analysis with:
  - **Root cause**: Most likely reason for failure
  - **Suggestions**: 2-3 concrete fixes to try
  - **Confidence**: 0-10 score for diagnosis reliability
  - **Reasoning**: Why those fixes should work

#### 2. **Test Analysis API Endpoint** (`backend/app/api/test_analysis.py`)
- FastAPI endpoint: `POST /api/test/analyze-failure`
- Receives failures from Playwright reporter
- Calls Claude service and returns formatted analysis
- Includes health check endpoint: `GET /api/test/health`

### Frontend Components

#### 1. **LLM Failure Reporter** (`frontend/reporters/llm-failure-reporter.js`)
- Custom Playwright reporter that captures test failures
- Extracts selector, error message, stack trace, and page context
- Sends failures to backend API for LLM analysis
- Generates JSON report: `test-results/llm-analysis/llm-analysis-report.json`
- Non-blocking: LLM analysis doesn't slow down test execution

#### 2. **Updated Playwright Config** (`frontend/playwright.config.js`)
- Registered LLM failure reporter
- Configurable via environment variable: `DISABLE_LLM_ANALYSIS=true` to skip
- Fallback to standard HTML reporter if API unavailable

#### 3. **POC Test** (`frontend/e2e/poc-llm-analysis.spec.js`)
- Intentionally fails with a broken selector
- Demonstrates end-to-end LLM analysis workflow
- Safe to run without breaking existing tests

---

## How to Test Phase 1

### Prerequisites Checklist
- [ ] Python venv activated in `backend/`
- [ ] `anthropic` package installed (`pip install anthropic`)
- [ ] Claude API key in `.env.example` or backend environment
- [ ] Backend running on `http://localhost:8000`
- [ ] Frontend dependencies installed (`npm install --prefix frontend`)

### Full End-to-End Test (10-15 minutes)

**Terminal 1: Start Backend**
```bash
cd backend
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# or: .\venv\Scripts\activate.bat  # Windows CMD

# Set environment if not in .env file
$env:CLAUDE_API_KEY = "your-key-here"
$env:DATABASE_URL = "sqlite:///./test.db"

python -m uvicorn app.main:app --reload --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

**Terminal 2: Start Frontend**
```bash
cd frontend
npm start
```

Expected output:
```
On Your Network: http://localhost:3000
```

**Terminal 3: Run POC Test**
```bash
cd frontend

# Run the intentional failure test
npx playwright test e2e/poc-llm-analysis.spec.js

# Or run with verbose output
npx playwright test e2e/poc-llm-analysis.spec.js --reporter=list
```

### Expected Results

#### ✅ Test Should Fail (Intentionally)
```
1 failed
...
Error: element not found inside <html>
Locator expected a single element matching [data-testid="nonexistent-button-that-moved"]
```

#### ✅ Check LLM Analysis Report
```bash
# Navigate to this file
test-results/llm-analysis/llm-analysis-report.json

# Or view directly
cat test-results/llm-analysis/llm-analysis-report.json | jq .
```

**Expected JSON structure:**
```json
{
  "timestamp": "2026-11-25T10:30:00.000Z",
  "totalFailures": 1,
  "failures": [
    {
      "timestamp": "2026-11-25T10:30:00.000Z",
      "test_name": "accessibility test with intentional failure",
      "file": "e2e/poc-llm-analysis.spec.js",
      "line": 12,
      "error_message": "element not found inside <html>",
      "selector": "[data-testid=\"nonexistent-button-that-moved\"]",
      "page_url": "http://localhost:3000",
      "llm_analysis": {
        "test_name": "...",
        "selector": "[data-testid=\"nonexistent-button-that-moved\"]",
        "error": "element not found...",
        "analysis": {
          "root_cause": "Selector points to non-existent element or page didn't load",
          "suggestions": [
            "Verify element exists in page source",
            "Check if data-testid attribute is correctly named",
            "Add page.waitForLoadState('networkidle') before locator"
          ],
          "confidence": "9/10",
          "reasoning": "The error indicates Playwright couldn't find the locator at all, suggesting either the element doesn't exist or hasn't loaded yet. Common fixes are validating the selector and adding wait conditions."
        },
        "context": {
          "url": "http://localhost:3000",
          "title": "unknown"
        }
      }
    }
  ]
}
```

#### ✅ Check Backend API Directly
```bash
# Verify endpoint responds
curl http://localhost:8000/api/test/health

# Example analysis request (manual)
curl -X POST http://localhost:8000/api/test/analyze-failure \
  -H "Content-Type: application/json" \
  -d '{
    "test_name": "Example Test",
    "file": "e2e/example.spec.js",
    "line": 12,
    "error_message": "Locator expected a single element matching [data-testid=\"button\"]",
    "stack_trace": "...",
    "selector": "[data-testid=\"button\"]",
    "page_url": "http://localhost:3000",
    "page_title": "Dashboard",
    "status": "failed",
    "duration": 5000
  }'
```

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'anthropic'`
**Fix:**
```bash
cd backend
.\venv\Scripts\Activate.ps1
pip install anthropic
```

### Issue: `RuntimeError: No API key provided`
**Fix:** Ensure Claude API key is set:
```bash
# Set environment variable
$env:CLAUDE_API_KEY = "sk-ant-..."

# Or add to .env file in backend directory
echo "CLAUDE_API_KEY=sk-ant-..." > .env
```

### Issue: Backend connection refused (reporter says "Could not reach analysis API")
**Fix:**
1. Verify backend is running: `curl http://localhost:8000/`
2. Check reporter config in `frontend/playwright.config.js` has correct `apiEndpoint`
3. Temporarily disable analysis to verify reporter works:
   ```bash
   $env:DISABLE_LLM_ANALYSIS = "true"
   npx playwright test e2e/poc-llm-analysis.spec.js
   ```

### Issue: Claude API returns errors
**Common causes:**
- Expired/invalid API key
- Rate limit exceeded
- Network connectivity issue
- Model name incorrect

**Fix:**
- Check API key in `.env.example`
- Verify `CLAUDE_MODEL` is set correctly
- Wait 60 seconds and retry

### Issue: Test runs but no `llm-analysis-report.json` created
**Fix:**
1. Verify reporter is registered in `playwright.config.js`
2. Check that `test-results/llm-analysis/` directory was created
3. Run with explicit reporter output:
   ```bash
   npx playwright test e2e/poc-llm-analysis.spec.js --reporter=list
   ```

---

## Success Criteria Checklist

### Phase 1.1: Playwright Reporter ✅
- [x] Reporter captures failed selectors
- [x] JSON output includes locator, error message, and DOM context
- [x] Reporter runs without blocking test execution
- [x] Integration verified with poc-llm-analysis.spec.js

### Phase 1.2: LLM Analysis Integration ✅
- [x] Claude API integration working
- [x] Suggests 2-3 fix options with reasoning
- [x] Integrates with failure reporter output
- [x] Cost monitoring in place (logs API calls)

### Phase 1.3: POC on Accessibility Tests ✅
- [x] Run poc-llm-analysis.spec.js and capture intentional failure
- [x] LLM correctly identifies the failure reason
- [x] Suggestion is accurate and actionable
- [x] Reporter output is human-readable in JSON format

### Phase 1.4: Rollout to All E2E Tests (Next Step)
- [ ] Run all 5 e2e test files with LLM analysis enabled
- [ ] Reporter produces consolidated output across all tests
- [ ] Maintenance burden reduced (track: average time to fix broken selector)

---

## Next Steps

### 1. Test Against Real Failures (Phase 1.4)
Instead of intentional failures, run actual e2e tests and capture real selector issues:

```bash
npx playwright test e2e/accessibility.spec.js
npx playwright test e2e/dashboard.spec.js
npx playwright test e2e/flows_validation.spec.js
npx playwright test e2e/generator.spec.js
npx playwright test e2e/transactions.spec.js
```

Review `test-results/llm-analysis/llm-analysis-report.json` for suggestions on each failure.

### 2. Manual Validation
- Review LLM suggestions for accuracy
- Verify fixes work when applied
- Collect feedback on suggestion quality

### 3. Integration into CI/CD
Once validated, add LLM analysis to GitHub Actions:
```yaml
- name: Run e2e tests with LLM analysis
  run: npx playwright test
  env:
    CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
```

### 4. Cost Optimization
- Monitor API usage dashboard: https://console.anthropic.com
- Cache frequent failure patterns locally
- Consider batch analysis for CI/CD runs (optional)

---

## Files Created/Modified

### New Files
- `backend/services/test_analyzer.py` — Claude API integration
- `backend/services/__init__.py` — Package init
- `backend/app/api/test_analysis.py` — FastAPI endpoint
- `frontend/reporters/llm-failure-reporter.js` — Playwright reporter
- `frontend/e2e/poc-llm-analysis.spec.js` — POC test

### Modified Files
- `backend/app/main.py` — Added test_analysis router
- `frontend/playwright.config.js` — Registered LLM reporter
- `backend/requirements.txt` — Added anthropic
- `.env.example` — Added Claude API config

---

## Architecture Diagram

```
Playwright Tests
       |
       v
  LLM Failure Reporter (frontend)
       |
       | (POST failure JSON)
       v
  Frontend Playwright Runner
       |
       | (HTTP POST to backend)
       v
  Backend FastAPI
  /api/test/analyze-failure
       |
       v
  Test Analyzer Service
       |
       | (API call)
       v
  Claude API
       |
       v
  Response (Root Cause + Suggestions)
       |
       v
  test-results/llm-analysis-report.json
```

---

## Documentation

For more details:
- **Roadmap:** See [Roadmap.md](../Roadmap.md) for overall initiative plan
- **Claude API:** https://docs.anthropic.com
- **Playwright Reporters:** https://playwright.dev/docs/test-reporters

---

## Questions or Issues?

1. Check troubleshooting section above
2. Review error logs in test runner output
3. Consult Roadmap.md for phase timelines and expected effort
