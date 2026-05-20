import os
import shutil
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, responses
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Transaction, Flow
from app.parsers.pain_001 import Pain001Parser
from app.parsers.validator import ISO20022Validator

router = APIRouter()

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

OUTPUT_DIR = "outputs"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

@router.get("/")
def list_transactions(db: Session = Depends(get_db)):
    return db.query(Transaction).all()

@router.post("/upload/{flow_id}")
async def upload_iso_file(flow_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Endpoint to handle ISO 20022 file uploads.
    """
    # 1. Verify Flow exists
    flow = db.query(Flow).filter(Flow.id == flow_id).first()
    if not flow:
        raise HTTPException(status_code=404, detail="Flow definition not found")

    # 2. Save file to disk
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. Parse content
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        
        parser = Pain001Parser(content)
        parsed_data = parser.get_transactions()

        # 4. Validate and Save to DB
        for item in parsed_data:
            # Extract BIC/IBAN for validation logic, but keep them in item for raw_data storage
            bic = item.get('bic')
            iban = item.get('iban')
            
            # Perform validation against Flow rules
            is_valid_bic = ISO20022Validator.validate_bic(bic, flow.bic_codes or [])
            is_valid_iban = ISO20022Validator.validate_iban(iban, flow.valid_ibans or [])
            
            # Basic date validation logic (Simplified for demo)
            today = datetime.now().date()
            tx_date = today # In a real scenario, extract this from the XML
            
            date_valid = True
            if not flow.back_dated and tx_date < today:
                date_valid = False
            if not flow.future_dated and tx_date > today:
                date_valid = False

            if not is_valid_bic or not is_valid_iban or not date_valid:
                item['status'] = "Validation Failed"

            # Store everything in raw_data to ensure we have access to fields not in the DB model
            tx = Transaction(flow_id=flow.id, raw_data=item, **{k: v for k, v in item.items() if hasattr(Transaction, k)})
            db.add(tx)
        
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse ISO file: {str(e)}")

    return {"filename": file.filename, "transactions_imported": len(parsed_data)}

@router.post("/{transaction_id}/execute")
async def execute_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """
    Executes a transaction by generating a CAMT.054 output notification.
    """
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Determine output filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_filename = f"CAMT054_{tx.instruction_id}_{timestamp}.xml"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # 3. Construct the CAMT.054 XML content using DB records
    cre_dt_tm = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    # Ensure amount is a float to avoid formatting errors if it's stored as a string or None
    try:
        amount_val = float(tx.amount) if tx.amount is not None else 0.0
    except (TypeError, ValueError):
        amount_val = 0.0

    # Safely get EndToEndId from model or raw_data, fallback to instruction_id
    e2e_id = getattr(tx, "end_to_end_id", None)
    if not e2e_id and tx.raw_data:
        e2e_id = tx.raw_data.get("end_to_end_id")
    if not e2e_id:
        e2e_id = tx.instruction_id

    xml_content = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.054.001.02">\n'
        f'    <BkToCstmrDbtCdtNtfctn>\n'
        f'        <GrpHdr>\n'
        f'            <MsgId>NOTIF-{tx.instruction_id}</MsgId>\n'
        f'            <CreDtTm>{cre_dt_tm}</CreDtTm>\n'
        f'        </GrpHdr>\n'
        f'        <Ntfctn>\n'
        f'            <Id>NTF-{tx.id}</Id>\n'
        f'            <CreDtTm>{cre_dt_tm}</CreDtTm>\n'
        f'            <Ntry>\n'
        f'                <Amt Ccy="{tx.currency}">{amount_val:.2f}</Amt>\n'
        f'                <CdtDbtInd>DBIT</CdtDbtInd>\n'
        f'                <Sts>BOOK</Sts>\n'
        f'                <NtryDtls>\n'
        f'                    <TxDtls>\n'
        f'                        <Refs>\n'
        f'                            <EndToEndId>{e2e_id}</EndToEndId>\n'
        f'                        </Refs>\n'
        f'                    </TxDtls>\n'
        f'                </NtryDtls>\n'
        f'            </Ntry>\n'
        f'        </Ntfctn>\n'
        f'    </BkToCstmrDbtCdtNtfctn>\n'
        f'</Document>'
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xml_content)

    # Update transaction and ensure SQLAlchemy detects the change in the JSON field by re-assigning a new dict
    raw_data = dict(tx.raw_data or {})
    raw_data["output_file"] = output_filename
    tx.raw_data = raw_data
    tx.status = "Executed"
    db.commit()

    return {"status": "Success", "output_file": output_filename}

@router.get("/download/{filename}")
async def download_output(filename: str):
    """Serves the generated ISO 20022 files."""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return responses.FileResponse(path=file_path, filename=filename, media_type='application/xml')

@router.delete("/{transaction_id}")
async def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Deletes a transaction record from the database."""
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    db.delete(tx)
    db.commit()
    
    return {"status": "Success", "detail": f"Transaction {transaction_id} deleted."}