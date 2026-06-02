# ISO 20022 Banking Test Platform

A test application for viewing, handling, and executing financial flows (Payments, Statements, Mandates) following the ISO 20022 standard.

## Project Structure

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
The project is designed to be setup from the root directory with a single command:

```bash
# 1. Install all dependencies (Backend venv + Frontend packages)
npm install

# 2. Apply database migrations
cd backend

# Activate virtual environment
Windows: .\backend\venv\Scripts\activate
macOS/Linux: source backend/venv/bin/activate

alembic upgrade head
```

### 3. Running the App
Start the tiers in separate terminal windows from the project root:

**Terminal 1 (Backend):** `npm run backend`  
**Terminal 2 (Frontend):** `npm run frontend`

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
- **Database Migrations**: If `alembic upgrade head` fails with a naming convention error, ensure the migration script explicitly names constraints for SQLite batch mode.
- **Python Imports (Yellow/Red Squiggles)**: 
    1. In VS Code, run `Python: Select Interpreter` and point to `backend/venv/Scripts/python.exe`.
    2. If issues persist, ensure the `backend` directory is added to your IDE's "Source Roots" or `python.analysis.extraPaths`.