import pytest
import os
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
    # Ensure XML declaration is at the absolute start of the byte string
    valid_xml = b'<?xml version="1.0" encoding="UTF-8"?><Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03"><CstmrCdtTrfInitn><PmtInf><PmtId><InstrId>API-TEST-001</InstrId></PmtId><Amt><InstdAmt Ccy="EUR">99.99</InstdAmt></Amt><DbtrAgt><FinInstnId><BIC>VALIDBIC</BIC></FinInstnId></DbtrAgt><DbtrAcct><Id><IBAN>DE12345</IBAN></Id></DbtrAcct></PmtInf></CstmrCdtTrfInitn></Document>'

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
            # First TX should be Pending
            tx1 = db.query(Transaction).filter(Transaction.id == 1).first()
            assert tx1.status == "Pending"
            
            # Second TX with same MsgId should be Validation Failed
            tx2 = db.query(Transaction).filter(Transaction.id == 2).first()
            assert tx2.status == "Validation Failed"
            assert "Duplicate Error" in tx2.raw_data["validation_errors"][0]

            # 4. Test Execution (XML Generation)
            exec_res = client.post(f"/transactions/{tx1.id}/execute")
            assert exec_res.status_code == 200
            output_filename = exec_res.json()["output_file"]
            
            # 5. Test Download/Inline View
            view_res = client.get(f"/transactions/download/{output_filename}?inline=true")
            assert view_res.status_code == 200
            assert b"EXEC-API-TEST-001" in view_res.content
            assert view_res.headers["content-disposition"] == "inline"
        finally:
            db.close()