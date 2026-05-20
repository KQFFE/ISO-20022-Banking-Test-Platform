# ISO 20022 Banking Test Platform

A test application for viewing, handling, and executing financial flows (Payments, Statements, Mandates) following the ISO 20022 standard.

## Project Structure

## Key Features
- **ISO 20022 Parsing**: Support for `pain.001` (Customer Credit Transfer Initiation) and `camt.054` (Bank-to-Customer Debit/Credit Notification).
- **Batch Processing**: Automatically groups multiple payment instructions within a single file under a unique Message ID (MsgId).
- **Smart Summaries**: Calculates total batch amounts and transaction counts during upload for easy reconciliation.
- **Validation**: Built-in BIC and IBAN validation based on flow-specific rules.
- **Output Generation**: Generates compliant multi-entry CAMT.054 XML files based on processed batch data.

## Accessibility Standards
This project aims to comply with **WCAG 2.1 AA** standards:
- **Perceivable**: Text alternatives for non-text content and high color contrast (min 4.5:1).
- **Operable**: Full keyboard navigability and clear focus indicators.
- **Understandable**: Consistent navigation and input assistance (labels/error messages).
- **Robust**: Use of semantic HTML and ARIA landmarks where necessary.

### Backend (Python / FastAPI)
- `backend/app/api/`: REST API endpoints for authentication, flow management, and transaction handling (including file uploads and parsing).
- `backend/app/core/`: Configuration (Environment variables) and Security (SSO/OAuth).
- `backend/app/db/`: Database models (SQLAlchemy for `Flow` and `Transaction` entities) and session management.
- `backend/app/parsers/`: The "Brain" of the app. Contains logic for parsing and validating ISO 20022 XML files (e.g., Pain.001, Camt.054).
- `backend/app/services/`: Business logic for file management and triggering flow executions (to be implemented).
- `backend/uploads/`: Local directory for storing uploaded input files.
- `backend/outputs/`: Local directory where generated ISO 20022 response files (e.g. CAMT.054) are saved.

### Frontend (React)
- `frontend/src/pages/`: Top-level views (Dashboard, Transactions, Flows).
- `frontend/src/components/`: Reusable UI components.
- `frontend/src/context/`: Global state management, specifically for User SSO sessions.
- `frontend/src/services/`: API client logic to communicate with the FastAPI backend.

## How to Run the App

### 1. Prerequisites
- Python 3.9+
- Node.js & npm

### 2. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

### Simplified Setup & Development (From Project Root)

This project uses `npm` scripts at the root to orchestrate both backend (Python) and frontend (React) development.

1.  **Initial Setup (One-time)**:
    This command creates the Python virtual environment, installs all Python dependencies, installs Node.js dependencies for both the root and frontend, and sets up Alembic.
    ```bash
    # From the project root (d:\Dev\IKANO testapp\)
    npm install # Installs root npm dependencies (like concurrently)
    npm run install:backend # Installs Python dependencies
    npm run install:frontend # Installs frontend npm dependencies
    # Then, for database setup (if not already done):
    # cd backend && alembic upgrade head
    ```

2.  **Start Development Servers**:
    Use the universal `npm` commands from the project root to start both tiers. The scripts handle virtual environment paths automatically across Windows and Linux.

    **Terminal 1 (Backend):**
    ```bash
    npm run backend
    ```

    **Terminal 2 (Frontend):**
    ```bash
    npm run frontend
    ```

### 3. Database Migrations (Alembic)
To manage database schema changes without losing data:
1.  **Install Alembic**:
    ```bash
    pip install alembic
    ```
2.  **Initialize Alembic** (one-time setup, run from `backend` directory):
    ```bash
    alembic init alembic
    # Follow configuration steps in alembic/env.py and alembic.ini
    ```
3.  **Generate a migration script** after model changes:
    ```bash
    alembic revision --autogenerate -m "Description of changes"
    ```
4.  **Apply migrations** to your database:
    ```bash
    alembic upgrade head
    ```

### 4. Running Tests
To run automated tests and check coverage:
```bash
cd backend
pytest
```
   The backend will be available at `http://127.0.0.1:8000`.

### Troubleshooting "Import could not be resolved"
If your editor (VS Code, PyCharm, etc.) still flags imports as missing:
1. **VS Code**: Press `Ctrl + Shift + P`, search for **"Python: Select Interpreter"**, and select the interpreter located in `backend/venv/Scripts/python.exe`.
2. **PyCharm**: Go to `File > Settings > Project > Python Interpreter` and point it to the `venv` folder.
3. Ensure you have run `pip install -r backend/requirements.txt` from the project root.
4. **Terminal Environment**: If VS Code warns about terminal environment injection, enable `"python.terminal.useEnvFile": true` in your settings to ensure `.env` variables are loaded automatically.

### 3. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Ensure `package.json` is populated, then install packages:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm start
   ```
   The frontend will be available at `http://localhost:3000`.

## How to Test the App

Once the application is running:

1. **Go to "Flow Definitions"**: Fill out the "Create New Flow" form.
   - **Name**: SEPA Test
   - **Direction**: Outbound
   - **Message Format**: Pain.001
   - Click **Add Flow**.
2. **Go to "Transactions"**:
   - The "Select Flow" dropdown will now show **SEPA Test**. Select it.
   - Select your `test_payment.xml` file.
   - Click **Upload and Process**.
3. **View Results**:
   - A row will appear in the "Processed Transactions" table.
   - The **Generate Output** button will be active.
   - Clicking it will create the **CAMT.054** file in your `backend/outputs/` folder.

> **Note on Styling**: This project uses Tailwind CSS. If the UI looks unstyled, ensure you have Tailwind configured or add the Tailwind Play CDN to your `frontend/public/index.html` for testing purposes.

## Security & Privacy
- **Authentication**: Integrated via SSO (OpenID Connect).
- **Data Handling**: Designed for testing; ensures IBAN and BIC validations are performed during file processing.