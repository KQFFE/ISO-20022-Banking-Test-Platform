# ISO 20022 Banking Test Platform

This application serves as a comprehensive test platform for interacting with and managing financial messages based on the ISO 20022 standard. It provides tools for viewing, validating, processing, and generating various financial message types, primarily focusing on payments and statements. The core scope includes simulating real-world financial message workflows, enabling developers and financial professionals to test integrations, validate message structures, and understand the lifecycle of ISO 20022 transactions in a controlled environment.

## Project Structure

The project is organized into two main components:
- **Backend**: A FastAPI application handling API requests, business logic, database interactions, and ISO 20022 message processing.
- **Frontend**: A React application providing a user interface for interacting with the backend, uploading files, viewing transactions, and managing flow definitions.

## Key Features
- **ISO 20022 Parsing**: Support for `pain.001` (Customer Credit Transfer Initiation) and `camt.054` (Bank-to-Customer Debit/Credit Notification).
- **Batch Processing**: Automatically groups multiple payment instructions within a single file under a unique Message ID (MsgId).
- **Smart Summaries**: Calculates total batch amounts and transaction counts during upload for easy reconciliation.
- **Validation**: Built-in BIC, IBAN, and date window validation (30-day back/future checks).
- **Output Generation**: Generates compliant multi-entry CAMT.054 XML files based on processed batch data.

## Accessibility Standards
This project aims to comply with **WCAG 2.1 AA** standards:
- **Perceivable**: Text alternatives for non-text content and high color contrast (min 4.5:1).
- **Operable**: Full keyboard navigability and clear focus indicators.
- **Understandable**: Consistent navigation and input assistance (labels/error messages).
- **Robust**: Use of semantic HTML and ARIA landmarks where necessary.

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
The project is designed to be set up from the root directory with a single command:

```bash
# 1. Install all dependencies (backend venv + frontend packages)
npm install
```

If you are setting up a fresh machine manually, use the following explicit steps instead:

```bash
# Backend setup
cd backend
python -m venv venv

# Activate the backend virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows Command Prompt:
# .\venv\Scripts\activate.bat
# macOS/Linux:
# source venv/bin/activate

# Install backend requirements
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Frontend setup (run in a normal shell, not inside the backend venv)
cd ..
npm install --prefix frontend

# Apply database migrations from the activated backend venv
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

1. installs the Node dependencies
2. creates a Python virtual environment under `backend/venv`
3. installs the backend Python requirements
4. starts the FastAPI backend on `http://localhost:8000`
5. runs the backend `pytest` suite
6. installs the Playwright browser dependencies
7. runs the frontend Playwright suite

If any of these steps fail, the GitHub Actions job fails and the commit is marked as not passing the required `test` status check.

This is how GitHub prevents a broken commit from being merged when branch protection or a ruleset requires the status check to pass.

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

```bash
# 1. Install browser binaries (first time only)
npm run test:frontend:install

# 2. Run E2E suite (Ensure dev servers are running)
npm run test:frontend
```

### Troubleshooting
- **Database Migrations**: If `python -m alembic upgrade head` fails with a naming convention error, ensure the migration script explicitly names constraints for SQLite batch mode.
- **Frontend won't start / `react-scripts` not recognized**: run `npm install --prefix frontend` in a normal terminal. This error means the frontend dependencies have not been installed yet; the backend venv state does not affect the frontend.
- **Python Imports (Yellow/Red Squiggles)**: 
    1. In VS Code, run `Python: Select Interpreter` and point to `backend/venv/Scripts/python.exe`.
    2. If issues persist, ensure the `backend` directory is added to your IDE's "Source Roots" or `python.analysis.extraPaths`.