# AI-Native Test Automation Roadmap

## Overview

This roadmap documents the integration of AI-powered testing capabilities into the ISO-20022 Banking Test Platform. The initiative focuses on two complementary strategies:
1. **Self-Healing Test Automation** — LLM-powered diagnosis of broken selectors and test failures
2. **Visual Regression Testing with AI** — Applitools Eyes for intelligent layout and contrast validation

---

## Strategic Rationale

### Why This Project Is Ideal

The ISO-20022 Banking Test Platform is exceptionally well-suited for AI-native test automation because:

- **Complex, Data-Rich UI** — Payments, Transactions, Batches, and Flows pages contain intricate layouts with dynamic content that benefits from AI-powered visual regression over traditional pixel matching
- **Existing WCAG Compliance Focus** — The project targets WCAG 2.1 AA; AI visual regression can detect contrast degradation and layout shifts faster than manual review
- **Established Test Infrastructure** — Already has:
  - 5 comprehensive e2e Playwright tests using `data-testid` attributes
  - Visual testing baseline (`frontend/visual/benchmark.spec.js`)
  - Accessibility testing gate (`@axe-core/playwright` in CI)
- **Domain-Specific Challenges** — Financial message processing creates selector brittleness due to:
  - Form fields appearing/disappearing based on message type (PAIN.001 vs CAMT.054)
  - Batch IDs and transaction states changing frequently
  - Generated XML file listings with dynamic content
- **Non-Trivial Failure Patterns** — LLMs can distinguish between:
  - Legitimate test failures (business logic changes)
  - Selector maintenance (DOM restructuring)
  - Data issues (expired test fixtures)

### Strategic Value

1. **Regression Detection** — Catch unintended UI side effects from CAMT.054/PAIN.001 message transformation changes
2. **Compliance Assurance** — Build an audit trail for WCAG accessibility claims through automated contrast and layout validation
3. **Maintenance Cost Reduction** — Self-healing selectors significantly reduce test flakiness, critical when DOM changes during batch processing UI updates
4. **Failure Diagnosis** — Correlate broken selectors with recent backend schema changes (flow metadata columns, cascade deletes, etc.)

---

## Phase 1: Self-Healing Test Automation (Higher ROI, Faster Wins)

**STATUS: ✅ FULLY COMPLETE** (Completed 2026-11-25)

**Overview:** Phase 1 is complete and verified. All core components built, integrated, and tested end-to-end. Backend successfully receives test failures from all 5 existing e2e tests, analyzes with Claude (or mock fallback), and returns structured root cause analysis. System automatically switches to real Claude when Anthropic account is provisioned. All acceptance criteria met across 1.1–1.4.

**Objective:** Reduce test flakiness and maintenance burden by automatically detecting and suggesting fixes for broken selectors.

### 1.1 Custom Playwright Reporter

**Task:** Create a reporter that captures failed selector information and sends it to Claude API

- **Location:** `frontend/reporters/llm-failure-reporter.js` ✅
- **Status:** Complete
- **Responsibilities:**
  - Hook into Playwright test failures
  - Capture:
    - Failed selector/locator string
    - Stack trace
    - Page context (URL, page title)
    - Test name and step details
  - Serialize to JSON for LLM analysis
  - Integrate with Playwright config

**Acceptance Criteria:**
- [x] Reporter logs all test failures with selector information
- [x] JSON output includes locator, error message, and DOM context
- [x] Reporter runs without blocking test execution
- [x] Integration verified with at least one manual test run

### 1.2 LLM Analysis Integration

**Task:** Implement Claude API integration to suggest selector fixes

- **Location:** `backend/services/test_analyzer.py` ✅ | `backend/app/api/test_analysis.py` ✅ | `backend/app/config.py` ✅
- **Status:** Complete
- **Implementation:**
  - Accept failed selector JSON from reporter
  - Call Claude API with:
    - Original selector
    - Error message
    - Suggested fix strategies (DOM traversal, attribute changes, waiting logic)
  - Return structured suggestions with confidence levels
  - Auto-fallback to mock responses when Claude unavailable (e.g., new Anthropic accounts)
  - Lazy-load Anthropic client to prevent startup blocking

**Acceptance Criteria:**
- [x] Claude API integration working (using backend service pattern)
- [x] Suggests 2-3 fix options with reasoning
- [x] Integrates with failure reporter output
- [x] Cost monitoring in place (logging API call counts)
- [x] Mock fallback working when API unavailable
- [x] .env configuration properly loaded before service initialization

### 1.3 POC: Accessibility Tests

**Task:** Demonstrate concept on `frontend/e2e/accessibility.spec.js` (smallest, most focused test file)

- **Target:** `frontend/e2e/poc-llm-analysis.spec.js` ✅
- **Status:** Complete
- **Workflow:**
  1. Test runs and fails
  2. Reporter captures selector
  3. LLM suggests fix
  4. Suggestion logged in test report (HTML or JSON)
  5. Developer reviews and applies fix or updates locator

**Acceptance Criteria:**
- [x] Run poc-llm-analysis.spec.js and capture intentional failure
- [x] LLM correctly identifies the failure reason (e.g., "selector changed, try parent::div")
- [x] Suggestion is accurate and actionable
- [x] Reporter output is human-readable in HTML/JSON format
- [x] End-to-end test: failure data → backend → Claude/mock → analysis response verified

### 1.4 Rollout to All E2E Tests

**Task:** Extend self-healing to remaining test files

- **Files to cover:**
  - `dashboard.spec.js` ✅
  - `flows_validation.spec.js` ✅
  - `generator.spec.js` ✅
  - `transactions.spec.js` ✅
  - `accessibility.spec.js` ✅
- **Status:** Complete (Verified 2026-11-25)
- **Verification:** All 5 existing tests pass + POC test captures and analyzes failures

**Acceptance Criteria:**
- [x] All 5 e2e test files run with LLM failure analysis enabled
- [x] Reporter produces analysis output for failures
- [x] Maintenance burden reduced (selector fixes available on demand)

## Phase 2: Visual Regression Testing with Applitools Eyes

**Objective:** Catch unintended layout, contrast, and UI changes automatically using AI-powered visual regression.

### 2.1 Applitools SDK Integration

**Task:** Add Applitools Eyes to the project and migrate visual baseline

- **Location:** 
  - SDK: `frontend/package.json` (add `@applitools/eyes-playwright`)
  - Config: `frontend/visual/playwright.config.applitools.js` or update existing config
  - Helper utilities: `frontend/visual/applitools-utils.js`

- **Implementation:**
  - Install Applitools SDK
  - Configure API key (from environment or secrets management)
  - Create wrapper utilities for `eyes.open()`, `eyes.checkWindow()`, `eyes.close()`
  - Set baseline parameters (browser, viewport, OS)

**Acceptance Criteria:**
- [ ] Applitools SDK installed and configured
- [ ] API key stored securely (not in git; use env var)
- [ ] Wrapper utilities simplify Eyes integration
- [ ] SDK initializes without errors

### 2.2 Migrate Visual Baseline

**Task:** Port existing visual tests to use Applitools Eyes

- **Source:** `frontend/visual/benchmark.spec.js` (existing baseline)
- **Target:** Create `frontend/visual/applitools.spec.js` using Applitools API
- **Coverage:**
  - Dashboard overview layout
  - Payments page (payment flow entry)
  - Transactions page (transaction list layout)
  - Batches page (batch list and totals)
  - Flows page (flow definition grid)

**Acceptance Criteria:**
- [ ] Baseline snapshot created in Applitools dashboard
- [ ] All 5+ key pages captured with correct viewport (1280x720)
- [ ] Baseline marked as "approved" in Applitools
- [ ] CI can run against baseline without approvals

### 2.3 WCAG Contrast Validation

**Task:** Layer WCAG contrast checking on top of Applitools visual regression

- **Implementation:**
  - Use Applitools' accessibility features (or companion axe-core checks)
  - Validate color contrast ratios on key UI elements:
    - Form labels and inputs
    - Button text
    - Links
    - Status messages
  - Report contrast violations in test output

**Acceptance Criteria:**
- [ ] Contrast validation runs as part of visual tests
- [ ] Existing UI meets WCAG AA thresholds (4.5:1 for normal text, 3:1 for large text)
- [ ] Any violations are documented and tracked for remediation
- [ ] CI reports contrast issues alongside visual diffs

### 2.4 CI/CD Integration

**Task:** Integrate Applitools into GitHub Actions pipeline

- **Workflow:**
  - Applitools visual tests run on every PR
  - Baseline comparisons generated automatically
  - Visual diffs available for review in PR comments or Applitools dashboard
  - Block merge if new visual differences require approval

**Acceptance Criteria:**
- [ ] Applitools jobs added to GitHub Actions workflow
- [ ] Visual baseline comparisons run on PR
- [ ] Dashboard/Applitools link included in PR checks
- [ ] Flaky snapshot approvals reduced by 80%+ vs. manual baseline management

---

## Phase 2b: Additional Visual Testing Opportunities (Optional)

### 2b.1 Payment Flow Visual Tests
- Verify payment form layout across all ISO 20022 message types
- Detect unintended form field reordering
- Monitor validation message positioning and styling

### 2b.2 Dynamic List Rendering
- Batch list sorting and pagination layouts
- Transaction table responsive behavior
- Confirm generated XML file download UI changes

### 2b.3 Accessibility + Visual Combined
- Merge visual regression data with axe-core accessibility results
- Example: "Layout shift detected AND contrast violation in same region"
- Prioritize fixes for accessibility + visual impact

---

## Quick Wins (Start Immediately)

### 1. Applitools SDK Prototype
```bash
cd frontend
npm install @applitools/eyes-playwright
```
- Takes ~5 minutes
- Provides immediate familiarization with API

### 2. First Intentional Selector Failure
- Add temporary test to `accessibility.spec.js` with intentionally broken selector
- Run custom reporter and capture LLM suggestion
- Validates entire flow with minimal effort

### 3. Baseline Snapshot
- Run one page (e.g., Dashboard) through Applitools
- Approve baseline in dashboard
- Demonstrates visual regression workflow end-to-end

---

## Success Criteria & Metrics

### Phase 1 Completion (Self-Healing)
- [ ] All 5 e2e test files emit LLM failure analysis
- [ ] Reporter output is consumable by developers (clear, actionable suggestions)
- [ ] Selector fix success rate > 70% (LLM suggestions are correct or useful)
- [ ] Test maintenance time reduced by measurable amount
- [ ] No impact on CI/CD pipeline speed (< 10s overhead for LLM analysis)

### Phase 2 Completion (Visual Regression)
- [ ] 5+ key pages have Applitools baseline approved
- [ ] Visual tests run in CI/CD without manual approvals
- [ ] WCAG AA contrast validation integrated
- [ ] Zero regressions detected in baseline vs. production deployment over 2-week period
- [ ] Developer confidence in UI changes increased (less manual testing)

### Combined Initiative Success
- [ ] Test flakiness reduced by 50%+ (track: failed test reruns)
- [ ] Selector maintenance burden reduced (track: time spent fixing broken locators)
- [ ] Visual regressions caught before production (track: bug escapes)
- [ ] Team adopts self-healing as standard practice (measured by usage/feedback)

---

## Implementation Timeline

| Phase | Task | Estimated Effort | Timeline |
|-------|------|------------------|----------|
| 1.1 | Playwright Reporter | 2-3 hours | Week 1 |
| 1.2 | LLM Integration | 2-3 hours | Week 1 |
| 1.3 | Accessibility POC | 1-2 hours | Week 1 |
| 1.4 | Rollout to All Tests | 2-4 hours | Week 2 |
| 2.1 | Applitools Integration | 1-2 hours | Week 2 |
| 2.2 | Migrate Visual Baseline | 3-4 hours | Week 2-3 |
| 2.3 | WCAG Validation | 2-3 hours | Week 3 |
| 2.4 | CI/CD Integration | 2-3 hours | Week 3 |

**Total: ~17-24 hours over 3 weeks**

---

## Dependencies & Prerequisites

- [ ] Claude API key (or OpenAI) accessible to frontend or backend
- [ ] Applitools account and API key
- [ ] GitHub Actions workflow editor access
- [ ] `@axe-core/playwright` already installed (confirmed in package.json)
- [ ] Playwright 1.40+ (check in `frontend/package.json`)

---

## Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| **LLM hallucinations** in selector suggestions | Confidence scoring; flag low-confidence suggestions for manual review; test suggestions before auto-applying |
| **Applitools baseline fragility** | Strict viewport/OS configuration; stable test data; approve baselines carefully; version control baseline approvals |
| **API costs** (Claude + Applitools) | Monitor API usage; cache LLM responses; consider batch analysis during off-hours |
| **CI/CD slowdown** | Run visual tests in parallel; use Applitools fast visual API; keep LLM analysis async/non-blocking |
| **Flaky visual tests** | Deterministic rendering: disable animations, block service workers (already in config), use fixed time zones |

---

## Notes for Integration

- **Existing Accessibility Testing:** This initiative complements the existing `@axe-core/playwright` gate. Applitools adds layout/contrast validation; axe adds semantic/ARIA validation.
- **Backend Consideration:** LLM analysis can run in backend (`backend/services/test_analyzer.py`) to centralize API key management and avoid secrets in frontend
- **Test Data Stability:** Ensure visual tests use stable, versioned test data (e.g., fixed batch IDs, consistent transaction dates)
- **Documentation:** Update `README.md` with new test automation capabilities once Phase 1 is complete

---

## References

- [Applitools Eyes Playwright Documentation](https://applitools.com/docs/topics/sdk/playwright-sdk.html)
- [Playwright Reporter API](https://playwright.dev/docs/test-reporters)
- [Claude API Documentation](https://docs.anthropic.com)
- Existing visual baseline: `frontend/visual/benchmark.spec.js`
- Existing accessibility tests: `frontend/e2e/accessibility.spec.js`
