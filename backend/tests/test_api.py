import pytest
import os
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import get_db
from app.db.models import Base, Transaction

# Use a separate in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_temp.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("test_temp.db"):
        os.remove("test_temp.db")

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