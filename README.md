# ISO 20022 Banking Test Platform

This application serves as a comprehensive test platform for interacting with and managing financial messages based on the ISO 20022 standard. It provides tools for viewing, validating, processing, and generating various financial message types, primarily focusing on payments and statements. The core scope includes simulating real-world financial message workflows, enabling developers and financial professionals to test integrations, validate message structures, and understand the lifecycle of ISO 20022 transactions in a controlled environment.

## Project Structure

The project is organized into two main components:
- **Backend**: A FastAPI application handling API requests, business logic, database interactions, and ISO 20022 message processing.
- **Frontend**: A React application providing a user interface for interacting with the backend, uploading files, viewing transactions, and managing flow definitions.

## Key Features
- **ISO 20022 Parsing**: Support for `pain.001` (Customer Credit Transfer Initiation) and `camt.054` (Bank-to-Customer Debit/Credit Notification).
- **Batch Processing**: Automatically groups multiple payment instructions within a single file under a unique Message ID (the MsgId field).
- **Smart Summaries**: Calculates total batch amounts and transaction counts during upload for easy reconciliation.
- **Validation**: Built-in BIC, IBAN, and date window validation (30-day back/future checks).
- **Output Generation**: Generates multi-entry CAMT.054 XML files based on processed batch data.

## Accessibility
The project uses WCAG 2.1 AA as a design goal, not a claim of conformance:
- **Perceivable**: Text alternatives for non-text content and high color contrast (min 4.5:1).
- **Operable**: Full keyboard navigability and clear focus indicators.
- **Understandable**: Consistent navigation and input assistance (labels/error messages).
- **Robust**: Use of semantic HTML and ARIA landmarks where necessary.

### Automated Accessibility Testing
The frontend CI pipeline includes an automated accessibility gate using `@axe-core/playwright`.

This runs against key pages in the app and checks for common WCAG 2.1 AA violations, including:
- unlabeled form controls
- missing form field names
- invalid ARIA usage
- poor color-contrast and semantic navigation issues (as flagged by axe)

The accessibility suite is in `frontend/e2e/accessibility.spec.js` and is included in the GitHub Actions flow before the rest of the frontend suite completes. If axe reports violations, the build fails and the commit is blocked by the required `test` status check.

This is a CI validation layer, not a substitute for manual accessibility testing or an assessment of WCAG conformance.

## Project Architecture

### Backend (`/backend`)
- **API Layer**: `app/api/` handles HTTP routing (FastAPI).
- **Service Layer**: `app/services/transaction_service.py` contains the core business logic.
- **Logic Layer**: `app/parsers/` contains ISO 20022 specific parsing and validation.
- **Data Layer**: `app/db/` manages SQLAlchemy models and migrations (Alembic).

### Frontend (`/frontend`)
- **Views**: `src/pages/`
    - **Overview**: High-level system stats.
    - **Payments**: Testing and execution of payment flows.
    - **Transactions**: Audit history of all processed messages.
    - **Mandates and DD**: Specific testing for mandate management.
    - **Batches**: Grouped view of message IDs and batch totals.
    - **Flow Definitions**: Management of BIC/IBAN validation rules.
    - **Test Files**: Scoped generation of ISO 20022 XML files.
    - **Market Rules**: Documentation of field-level requirements.
- **Stability**: `e2e/` contains Playwright end-to-end tests targeting `data-testid` attributes.

## Getting Started

### 1. Prerequisites
- Python 3.9+
- Node.js & npm

### 2. Setup
For a fresh checkout, you need to install both Python and frontend dependencies explicitly.

```bash
# Backend venv + Python requirements
cd backend
python -m venv venv

# Activate the backend virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows Command Prompt:
# .\venv\Scripts\activate.bat
# macOS/Linux:
# source venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Frontend dependencies (run in a normal shell, not inside the backend venv)
cd ..
npm install --prefix frontend
```

The root-level `npm install` is not the full setup for this project because the backend and frontend are separate runtime environments. The backend uses a venv under `backend/venv`, while the frontend uses `npm` packages in `frontend/` including the accessibility tooling (`@axe-core/playwright`).

After dependencies are installed, apply the database migrations from the activated backend venv:

```bash
cd backend
python -m alembic upgrade head
```

> Important: the venv is created under `backend/venv`, not at the repository root. The correct activation path is `cd backend` followed by `./venv/Scripts/Activate.ps1` on Windows or `source venv/bin/activate` on macOS/Linux.

### 3. Running the App
Start the tiers in separate terminal windows from the project root:

**Terminal 1 (Backend):** activate the backend venv and run `npm run backend`  
**Terminal 2 (Frontend):** use a normal shell and run `npm run frontend`

### GitHub Actions / CI on Commit
Every push to `main` and every pull request triggers the workflow in `.github/workflows/ci.yml`.

The CI job does the following:

1. installs the root Node dependencies
2. creates a Python virtual environment under `backend/venv`
3. installs the backend Python requirements
4. applies database migrations using Alembic
5. starts the FastAPI backend on `http://localhost:8000`
6. runs the backend `pytest` suite
7. installs the Playwright browser dependencies
8. runs the accessibility suite (`e2e/accessibility.spec.js`)
9. runs the remaining frontend Playwright E2E suite

If any of these steps fail, the GitHub Actions job fails and the commit is marked as not passing the required `test` status check.

This is how GitHub prevents a broken commit from being merged when branch protection or a ruleset requires the status check to pass.

#### CI structure in practice
This repository is a validation-focused project, not a remote deployment project. The workflow is designed to protect the branch by checking that:
- the backend still works
- database migrations still succeed
- the API responds correctly
- frontend behavior still passes Playwright assertions
- accessibility regressions are caught automatically

#### Why a commit may not build in GitHub Actions
A common cause is that the repository originally contained Windows-specific shell commands in the root install scripts, while GitHub Actions runs on Linux. For example, commands such as `if not exist ...` and `venv\Scripts\...` work in Windows `cmd`, but fail under the Linux `sh` shell used by GitHub runners.

This is why the fix was to avoid the Windows-only script path in CI and to install backend dependencies explicitly in the workflow instead of relying on a shell-specific postinstall script.

#### How to fix that issue
Use CI-safe commands such as:

```bash
python -m venv backend/venv
backend/venv/bin/python -m pip install -r backend/requirements.txt
npm ci --ignore-scripts
npm install --prefix frontend
```

Then run the tests in the same environment that matches the project structure. If you use a branch protection rule or ruleset in GitHub, make the required status check `test` and require it before merge.


## Testing & Quality

### Automated Testing
We use `pytest` for the backend and `Playwright` for frontend E2E.

### Synthetic ISO 20022 Test Data

The backend includes a deterministic generator for test-only German `pain.001.001.03` files. It uses no external services or customer data and creates synthetic payer/merchant labels, EUR amounts, future execution dates, and checksum-valid German IBANs. Synthetic BICs are paired with the bank-code portion of the generated debtor IBAN.

Generate a file from the `backend` directory:

```bash
python -m app.services.synthetic_data --count 25 --seed 42 --output outputs/synthetic-pain001.xml
```

The count must be between 1 and 500. Reusing the seed on the same day reproduces the payment data. The generator validates IBAN checksums and routing-pair consistency, not account ownership, registered BIC status, every ISO 20022 business rule, or full XSD conformance. The resulting file is for local testing only and must not be sent to a bank or payment network.

Run its focused tests from the `backend` directory with `pytest tests/test_synthetic_data.py`.

#### Backend Tests (Pytest)
- **Logic Tests**: `backend/tests/test_iso_logic.py`
- **API Integration**: `backend/tests/test_api.py`

**Run Tests & View Coverage:**
```bash
# Run all backend tests
npm run test:backend

# Generate HTML coverage report
npm run test:backend:cov
# Open backend/htmlcov/index.html to view results
```

#### Frontend Tests (Playwright E2E)
Focuses on the "Golden Path", accessibility, and error handling.

The suite includes:
- end-to-end user journeys for flows, payments, and transactions
- validation checks for duplicate uploads and error states
- browser-level assertions for UI correctness
- automated WCAG accessibility checks using `@axe-core/playwright`

```bash
# 1. Install frontend dependencies (if you have not already)
npm install --prefix frontend

# 2. Install browser binaries (first time only)
npm run test:frontend:install

# 3. Run E2E suite (Ensure dev servers are running)
npm run test:frontend
```

If you have not run the frontend installation after pulling in the new axe dependency, the project will not have the accessibility package available in CI or locally.

The accessibility spec is intentionally separate so the repo can distinguish between functional regression failures and accessibility violations. This makes it easier to debug and fix both categories independently while still blocking broken code in CI.

### Visual regression benchmark and optional AI diagnostics

The separate Playwright visual suite renders the **real Overview page** at a fixed desktop viewport with fixed, synthetic statistics. It intercepts the statistics API and blocks other external requests; it does not use a backend database. For offline styling, the Tailwind utilities used by the React source are compiled locally instead of loading the application's Tailwind CDN script. This is an approximation of the CDN's default styling, so CDN changes and external assets are not tested. No production or customer data should be used.

The test compares the page with a platform-specific screenshot, then injects four controlled changes: a missing action, an incorrect label, a shifted card, and an incorrect value. An unchanged control measures false positives. `results.json` reports changed pixels and true/false positives and negatives using a 0.00005 changed-pixel ratio cutoff. These five cases are a small calibration exercise, not evidence of real-world detection accuracy. The test fails if the baseline differs beyond the threshold, a seeded change is missed, or the unchanged control is detected. Screenshot comparison and this benchmark do not replace functional or axe accessibility tests.

From `frontend`, with dependencies and Playwright Chromium installed:

```bash
npm run test:visual:tools
npm run test:visual
```

The included Windows screenshot in `frontend/visual/benchmark.spec.js-snapshots/` is a **candidate, not an approved baseline**. Review it against the intended UI and synthetic fixture before accepting it in version control. Other operating systems require their own baseline; screenshots also depend on browser version, fonts, and rendering environment. When a baseline is absent, or an intentional UI change needs a new candidate, generate it explicitly:

```bash
npx playwright test --config visual/playwright.config.js --update-snapshots
```

This command overwrites that platform's baseline; inspect the resulting image and diff before accepting it. Never approve a baseline merely because a test or model suggests it. Keep reviewed baseline files under version control. Run without `--update-snapshots` for actual comparisons. The visual suite is intentionally outside ordinary CI and the existing accessibility suite; it is not a CI gate until a reproducible runner and its reviewed baseline are established.

After a run, `frontend/test-results/visual-benchmark/` contains the reference, the current UI, benchmark images, diffs, and `results.json`. A baseline mismatch still writes `actual-ui.png` and its manifest before failing, so it can be inspected. These files are local, ignored artifacts and can be overwritten by later runs.

#### Optional OpenAI diagnostic

No live model is called by the visual suite or ordinary CI. To use the optional diagnostic later, create an OpenAI API account and supply an API key with billing or available credits; a ChatGPT subscription does not necessarily include API usage. Image uploads may incur costs and are subject to the provider's data policies. Review **both** `baseline.png` and the selected case image in the latest output directory for synthetic, sanitized content before every upload. The checksums only detect changes after capture; they do not prove that content is safe. Do not use the command with real payment or customer data.

Set `OPENAI_API_KEY` in your environment without committing it, then explicitly confirm review (PowerShell example, from `frontend`):

```powershell
$env:OPENAI_API_KEY = ([System.Net.NetworkCredential]::new('', (Read-Host "OpenAI API key" -AsSecureString))).Password
node visual/diagnose.js actual-ui --confirm-reviewed-synthetic
# Or analyze a seeded case, e.g.:
node visual/diagnose.js missing-action --confirm-reviewed-synthetic
Remove-Item Env:OPENAI_API_KEY
```

The command defaults to `gpt-4o`; optionally set `OPENAI_VISION_MODEL` to an available vision-capable model. It sends only the selected reference and current image, not the benchmark ground truth, to OpenAI. It writes a local `<case>-diagnostic.json`. API, authentication, rate-limit, and malformed-response errors are reported rather than treated as success. The result is advisory only: it never changes selectors, approves baselines, or changes the Playwright result. Models can miss differences, hallucinate, and vary across runs.

For diagnostic usefulness, independently review each model output against the known seeded change (and the unchanged control). Copy `frontend/visual/ratings.example.json` to a local, untracked location and add one entry per case: `detected` records whether the model reported any visual change; `correct` means it identifies the actual change or correctly says none; `actionable` means it gives a useful location and description; `falseClaim` flags any invented difference; `notes` records the rationale. Then run `node visual/score.js <ratings.json>` from `frontend`. It compares `detected` with the controlled ground truth and reports true/false positives and negatives alongside the usefulness counts. Score only the controlled cases, not `actual-ui`, whose ground truth is unknown. The example is illustrative, not a measured result. Repeat runs and broaden cases before drawing conclusions.

### Troubleshooting
- **Database Migrations**: If `python -m alembic upgrade head` fails with a naming convention error, ensure the migration script explicitly names constraints for SQLite batch mode.
- **Frontend won't start / `react-scripts` not recognized**: run `npm install --prefix frontend` in a normal terminal. This error means the frontend dependencies have not been installed yet; the backend venv state does not affect the frontend.
- **Python Imports (Yellow/Red Squiggles)**: 
    1. In VS Code, run `Python: Select Interpreter` and point to `backend/venv/Scripts/python.exe`.
    2. If issues persist, ensure the `backend` directory is added to your IDE's "Source Roots" or `python.analysis.extraPaths`.