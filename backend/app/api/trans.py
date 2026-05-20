import os
import shutil
import re
import xml.sax.saxutils as saxutils
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

        # Extract summary data from XML tags (e.g., <Sum>, <CtrlSum>, <NbOfNtries>, <NbOfTxs>)
        # Using regex for flexible extraction across different ISO namespaces
        xml_str = content.decode('utf-8', errors='ignore')
        msg_match = re.search(r'<MsgId>([^<]+)</MsgId>', xml_str)
        nb_match = re.search(r'<(?:NbOfTxs|NbOfNtries)>(\d+)</', xml_str)
        sum_match = re.search(r'<(?:CtrlSum|Sum)>([\d.]+)</', xml_str)

        msg_id = msg_match.group(1) if msg_match else file.filename
        batch_count = int(nb_match.group(1)) if nb_match else len(parsed_data)
        batch_total = float(sum_match.group(1)) if sum_match else sum(float(item.get('amount', 0)) for item in parsed_data)

        # 4. Validate and Save as a single Batch record
        batch_status = "Pending"
        validation_errors = []
        for i, item in enumerate(parsed_data):
            bic = item.get('bic')
            iban = item.get('iban')
            instr_id = item.get('instruction_id') or f"Tx {i+1}"
            
            if not ISO20022Validator.validate_bic(bic, flow.bic_codes or []):
                validation_errors.append(f"{instr_id}: Invalid BIC '{bic}'")
            if not ISO20022Validator.validate_iban(iban, flow.valid_ibans or []):
                validation_errors.append(f"{instr_id}: Invalid IBAN '{iban}'")

        if validation_errors:
            batch_status = "Validation Failed"

        # Create one summary record for the entire file
        first_tx = parsed_data[0] if parsed_data else {}
        batch_data = {
            "instruction_id": msg_id, # Mapping MsgId to instruction_id for display
            "amount": batch_total,
            "currency": first_tx.get('currency', 'SEK'),
            "status": batch_status,
            "raw_data": {
                "batch_total": batch_total,
                "batch_count": batch_count,
                "transactions": parsed_data,
                "validation_errors": validation_errors
            }
        }

        tx = Transaction(flow_id=flow.id, **{k: v for k, v in batch_data.items() if hasattr(Transaction, k)})
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
    
    # Extract batch data from raw_data for comprehensive reporting
    raw_data_content = dict(tx.raw_data or {})
    transactions_list = raw_data_content.get("transactions", [])
    batch_total = raw_data_content.get("batch_total", tx.amount or 0.0)
    batch_count = raw_data_content.get("batch_count", 1)

    xml_header = (
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
        f'            <TxsSummry>\n'
        f'                <TtlNtries>\n'
        f'                    <NbOfNtries>{batch_count}</NbOfNtries>\n'
        f'                    <Sum>{float(batch_total):.2f}</Sum>\n'
        f'                    <CdtDbtInd>DBIT</CdtDbtInd>\n'
        f'                </TtlNtries>\n'
        f'            </TxsSummry>\n'
    )

    xml_entries = ""
    for item in transactions_list:
        # Ensure all data is XML-safe (escaped) and values are handled correctly
        amt = float(item.get("amount", 0))
        ccy = saxutils.escape(str(item.get("currency", tx.currency)))
        e2e = saxutils.escape(str(
            item.get("end_to_end_id") or 
            item.get("instruction_id") or 
            tx.instruction_id
        ))
        
        xml_entries += (
            f'            <Ntry>\n'
            f'                <Amt Ccy="{ccy}">{amt:.2f}</Amt>\n'
            f'                <CdtDbtInd>DBIT</CdtDbtInd>\n'
            f'                <Sts>BOOK</Sts>\n'
            f'                <NtryDtls>\n'
            f'                    <TxDtls>\n'
            f'                        <Refs>\n'
            f'                            <EndToEndId>{e2e}</EndToEndId>\n'
            f'                        </Refs>\n'
            f'                    </TxDtls>\n'
            f'                </NtryDtls>\n'
            f'            </Ntry>\n'
        )

    # Fallback for single transactions or legacy data structure
    if not xml_entries:
        xml_entries = (
            f'            <Ntry>\n'
            f'                <Amt Ccy="{tx.currency}">{float(tx.amount or 0):.2f}</Amt>\n'
            f'                <CdtDbtInd>DBIT</CdtDbtInd>\n'
            f'                <Sts>BOOK</Sts>\n'
            f'                <NtryDtls>\n'
            f'                    <TxDtls>\n'
            f'                        <Refs>\n'
            f'                            <EndToEndId>{tx.instruction_id}</EndToEndId>\n'
            f'                        </Refs>\n'
            f'                    </TxDtls>\n'
            f'                </NtryDtls>\n'
            f'            </Ntry>\n'
        )

    xml_content = xml_header + xml_entries + (
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