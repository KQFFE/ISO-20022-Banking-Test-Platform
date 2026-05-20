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

def test_create_flow_and_upload():
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
            "valid_ibans": ["DE%"]
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

        # 3. Verify DB state directly
        db = TestingSessionLocal()
        try:
            tx = db.query(Transaction).filter(Transaction.instruction_id == "API-TEST-001").first()
            assert tx is not None
            assert tx.amount == 99.99
        finally:
            db.close()