import pytest
import os
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import get_db
from app.db.models import Base, Transaction

# Use a separate in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_temp.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure SQLite enforces foreign key constraints for cascades during tests
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    try:
        Base.metadata.create_all(bind=engine)
        yield
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        # Using a small delay or try-except for Windows file locking issues
        if os.path.exists("test_temp.db"):
            try:
                os.remove("test_temp.db")
            except PermissionError:
                pass

def test_full_transaction_lifecycle():
    # Ensure XML uses dynamic dates to avoid validation errors
    today_iso = datetime.now().date().isoformat()
    now_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    valid_xml = (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03">'
        f'<CstmrCdtTrfInitn>'
        f'<GrpHdr><MsgId>API-TEST-BATCH-001</MsgId><CreDtTm>{now_iso}</CreDtTm></GrpHdr>'
        f'<PmtInf>'
        f'<PmtMtd>TRF</PmtMtd><ReqdExctnDt>{today_iso}</ReqdExctnDt>'
        f'<DbtrAgt><FinInstnId><BIC>VALIDBIC</BIC></FinInstnId></DbtrAgt>'
        f'<DbtrAcct><Id><IBAN>DE12345</IBAN></Id></DbtrAcct>'
        f'<CdtTrfTxInf><PmtId><InstrId>API-TEST-001</InstrId></PmtId>'
        f'<Amt><InstdAmt Ccy="EUR">99.99</InstdAmt></Amt></CdtTrfTxInf>'
        f'</PmtInf></CstmrCdtTrfInitn></Document>'
    ).encode('utf-8')

    with TestClient(app) as client:
        # 1. Create a flow
        flow_res = client.post("/flows/", json={
            "name": "Integration Test Flow",
            "direction": "Outbound",
            "message_format": "Pain.001",
            "file_format": "XML",
            "bic_codes": ["VALIDBIC"],
            "valid_ibans": ["DE%"],
            "duplicate_check": True
        })
        assert flow_res.status_code == 200
        flow_id = flow_res.json()["id"]

        # 2. Upload the valid XML file
        files = {"file": ("test.xml", valid_xml, "application/xml")}
        upload_res = client.post(f"/transactions/upload/{flow_id}", files=files)
        
        if upload_res.status_code != 200:
            print(f"Upload failed with: {upload_res.json()}")
            
        assert upload_res.status_code == 200
        assert upload_res.json()["transactions_imported"] == 1

        # 3. Test Duplicate Check logic
        files_dup = {"file": ("test_dup.xml", valid_xml, "application/xml")}
        upload_dup_res = client.post(f"/transactions/upload/{flow_id}", files=files_dup)
        assert upload_dup_res.status_code == 200
        
        db = TestingSessionLocal()
        try:
            # First transaction batch should be Pending
            tx1 = db.query(Transaction).filter(Transaction.instruction_id == "API-TEST-BATCH-001").first()
            assert tx1.status == "Pending"
            
            # Second transaction with same MsgId should be Validation Failed due to Duplicate Check
            tx2 = db.query(Transaction).filter(Transaction.instruction_id == "API-TEST-BATCH-001", Transaction.id != tx1.id).first()
            assert tx2.status == "Validation Failed"
            assert "Duplicate Error" in tx2.raw_data["validation_errors"][0]

            # 4. Test Execution (XML Generation)
            exec_res = client.post(f"/transactions/{tx1.id}/execute")
            assert exec_res.status_code == 200
            output_filename = exec_res.json()["output_file"]
            
            # 5. Test Download/Inline View
            view_res = client.get(f"/transactions/download/{output_filename}?inline=true")
            assert view_res.status_code == 200
            assert b"EXEC-API-TEST-BATCH-001" in view_res.content
            assert view_res.headers["content-disposition"].startswith("inline")
        finally:
            db.close()

def test_clear_all_transactions():
    with TestClient(app) as client:
        # 1. Create a flow first
        flow_res = client.post("/flows/", json={
            "name": "Clear Test Flow",
            "direction": "Outbound",
            "message_format": "Pain.001",
            "file_format": "XML"
        })
        flow_id = flow_res.json()["id"]

        # 2. Manually insert a transaction into the DB to ensure there is something to clear
        db = TestingSessionLocal()
        try:
            db.add(Transaction(flow_id=flow_id, instruction_id="TX-TO-CLEAR", status="Pending", amount=10.0, currency="EUR"))
            db.commit()
        finally:
            db.close()

        # 3. Call Clear History
        response = client.delete("/transactions/")
        assert response.status_code == 200
        assert response.json()["detail"] == "All transactions cleared successfully"
        
        # 4. Verify stats reflect zero transactions
        stats_res = client.get("/stats")
        assert stats_res.json()["total_transactions"] == 0
        assert stats_res.json()["executed_transactions"] == 0

def test_flow_currency_validation_persistence():
    with TestClient(app) as client:
        flow_data = {
            "name": "Currency Restricted Flow",
            "direction": "Outbound",
            "message_format": "Pain.001",
            "file_format": "XML",
            "currency_validation": True,
            "allowed_currency": "SEK"
        }
        
        # 1. Create flow with currency rules
        create_res = client.post("/flows/", json=flow_data)
        assert create_res.status_code == 200
        created_flow = create_res.json()
        assert created_flow["currency_validation"] is True
        assert created_flow["allowed_currency"] == "SEK"

        # 2. Verify it appears in the list
        list_res = client.get("/flows/")
        matches = [f for f in list_res.json() if f["id"] == created_flow["id"]]
        assert len(matches) == 1
        assert matches[0]["allowed_currency"] == "SEK"
        
        # 3. Cleanup
        client.delete(f"/flows/{created_flow['id']}")

def test_upload_currency_validation_failure():
    today_iso = datetime.now().date().isoformat()
    now_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # XML with EUR
    mismatched_xml = (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03">'
        f'<CstmrCdtTrfInitn><GrpHdr><MsgId>CURRENCY-FAIL</MsgId><CreDtTm>{now_iso}</CreDtTm></GrpHdr>'
        f'<PmtInf><PmtMtd>TRF</PmtMtd><ReqdExctnDt>{today_iso}</ReqdExctnDt>'
        f'<DbtrAgt><FinInstnId><BIC>TESTBIC</BIC></FinInstnId></DbtrAgt>'
        f'<DbtrAcct><Id><IBAN>SE123</IBAN></Id></DbtrAcct>'
        f'<CdtTrfTxInf><PmtId><InstrId>TX-FAIL</InstrId></PmtId>'
        f'<Amt><InstdAmt Ccy="EUR">100.00</InstdAmt></Amt></CdtTrfTxInf>'
        f'</PmtInf></CstmrCdtTrfInitn></Document>'
    ).encode('utf-8')

    with TestClient(app) as client:
        # 1. Create flow that ONLY allows SEK
        flow_res = client.post("/flows/", json={
            "name": "SEK Only Flow",
            "direction": "Outbound",
            "message_format": "Pain.001",
            "currency_validation": True,
            "allowed_currency": "SEK"
        })
        flow_id = flow_res.json()["id"]

        # 2. Upload EUR file
        files = {"file": ("test.xml", mismatched_xml, "application/xml")}
        upload_res = client.post(f"/transactions/upload/{flow_id}", files=files)
        
        if upload_res.status_code != 200:
            print(f"Upload failed: {upload_res.json()}")
            
        assert upload_res.status_code == 200
        data = upload_res.json()
        assert data["transactions_imported"] >= 1
        
        # Verify transaction was flagged as Validation Failed
        db = TestingSessionLocal()
        try:
            tx = db.query(Transaction).filter(Transaction.instruction_id == "CURRENCY-FAIL").first()
            # Debugging info if assertion fails
            assert tx.status == "Validation Failed", f"Expected 'Validation Failed' but got '{tx.status}'. Errors: {tx.raw_data.get('validation_errors')}"
            assert any(word in err.lower() for err in tx.raw_data["validation_errors"] for word in ["currency", "ccy", "sek"])
        finally:
            db.close()

def test_upload_multiple_validation_failures():
    today = datetime.now().date().isoformat()
    bad_xml = (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03">'
        f'<CstmrCdtTrfInitn><GrpHdr><MsgId>MULTI-FAIL</MsgId><CreDtTm>2024-01-01T12:00:00</CreDtTm></GrpHdr>'
        f'<PmtInf><PmtMtd>TRF</PmtMtd><ReqdExctnDt>{today}</ReqdExctnDt>'
        f'<DbtrAgt><FinInstnId><BIC>WRONGBIC</BIC></FinInstnId></DbtrAgt>'
        f'<DbtrAcct><Id><IBAN>NO-MATCH</IBAN></Id></DbtrAcct>'
        f'<CdtTrfTxInf><PmtId><InstrId>TX-1</InstrId></PmtId>'
        f'<Amt><InstdAmt Ccy="USD">1.00</InstdAmt></Amt></CdtTrfTxInf>'
        f'</PmtInf></CstmrCdtTrfInitn></Document>'
    ).encode('utf-8')

    with TestClient(app) as client:
        flow_res = client.post("/flows/", json={
            "name": "Strict Flow", "direction": "Outbound", "message_format": "Pain.001",
            "bic_codes": ["GOODBIC"], "valid_ibans": ["DE%"], "currency_validation": True, "allowed_currency": "EUR"
        })
        flow_id = flow_res.json()["id"]
        upload_res = client.post(f"/transactions/upload/{flow_id}", files={"file": ("test.xml", bad_xml, "application/xml")})
        assert upload_res.status_code == 200, f"Upload failed: {upload_res.json()}"
        
        db = TestingSessionLocal()
        try:
            tx = db.query(Transaction).filter(Transaction.instruction_id == "MULTI-FAIL").first()
            assert tx is not None, "Transaction record 'MULTI-FAIL' was not found in the database."
            errors = tx.raw_data.get("validation_errors", [])
            assert any("BIC" in e for e in errors)
            assert any("IBAN" in e for e in errors)
            assert any("Currency" in e for e in errors)
        finally:
            db.close()

def test_camt_054_upload_lifecycle():
    # Simplified camt.054 XML
    camt_xml = (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.054.001.02">'
        f'<BkToCstmrDbtCdtNtfctn><GrpHdr><MsgId>CAMT-REPORT-001</MsgId><CreDtTm>2024-01-01T12:00:00</CreDtTm></GrpHdr>'
        f'<Ntfctn><Id>NTF-001</Id><CreDtTm>2024-01-01T12:00:00</CreDtTm>'
        f'<Acct><Id><IBAN>SE123</IBAN></Id></Acct>'
        f'<Ntry><Amt Ccy="EUR">50.00</Amt><Sts>BOOK</Sts>'
        f'<BookgDt><Dt>{datetime.now().date().isoformat()}</Dt></BookgDt>'
        f'<NtryDtls><TxDtls>'
        f'<Refs><EndToEndId>REF-123</EndToEndId></Refs>'
        f'<RltdPties><Dbtr><Nm>John Doe</Nm><PstlAdr><Ctry>SE</Ctry><AdrLine>Street 1</AdrLine></PstlAdr></Dbtr></RltdPties>'
        f'<RmtInf><Ustrd>Invoice 1</Ustrd><Strd><CdtrRefInf><Ref>REF-999</Ref></CdtrRefInf></Strd></RmtInf>'
        f'<RltdDts><AccptncDtTm>2024-01-01T12:00:00</AccptncDtTm></RltdDts>'
        f'</TxDtls></NtryDtls>'
        f'</Ntry></Ntfctn></BkToCstmrDbtCdtNtfctn></Document>'
    ).encode('utf-8')

    with TestClient(app) as client:
        # 1. Create Inbound Flow
        flow_res = client.post("/flows/", json={
            "name": "Bank Reporting Flow",
            "direction": "Inbound",
            "message_format": "camt.054",
            "file_format": "XML"
        })
        flow_id = flow_res.json()["id"]

        # 2. Upload
        files = {"file": ("report.xml", camt_xml, "application/xml")}
        upload_res = client.post(f"/transactions/upload/{flow_id}", files=files)
        
        assert upload_res.status_code == 200
        assert upload_res.json()["transactions_imported"] == 1

        # 3. Test Execution to cover Camt054Generator
        db = TestingSessionLocal()
        try:
            tx = db.query(Transaction).filter(Transaction.instruction_id == "CAMT-REPORT-001").first()
            assert tx.amount == 50.0
            assert tx.currency == "EUR"
            
            exec_res = client.post(f"/transactions/{tx.id}/execute")
            assert exec_res.status_code == 200
            assert "output_file" in exec_res.json()
        finally:
            db.close()