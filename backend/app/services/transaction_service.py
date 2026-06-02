import os
import shutil
import re
from datetime import datetime
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.db.models import Transaction, Flow
from app.api.flows import FlowRead
from app.parsers.registry import parser_registry, generator_registry
from app.parsers.validator import ISO20022Validator

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

OUTPUT_DIR = "outputs"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def _validate_transaction_item(item: dict, flow: Flow, index: int) -> list:
    """Helper to validate a single transaction item against flow rules."""
    errors = []
    bic = item.get('bic')
    iban = item.get('iban')
    instr_id = item.get('instruction_id') or f"Tx {index+1}"
    
    if not ISO20022Validator.validate_bic(bic, flow.bic_codes or []):
        errors.append(f"{instr_id}: Invalid BIC '{bic}'")
    if not ISO20022Validator.validate_iban(iban, flow.valid_ibans or []):
        allowed = ", ".join(flow.valid_ibans) if flow.valid_ibans else "None"
        errors.append(f"{instr_id}: IBAN '{iban}' does not match allowed patterns: [{allowed}]")
    if flow.currency_validation and flow.allowed_currency:
        if not ISO20022Validator.validate_currency(item.get("currency"), flow.allowed_currency):
            errors.append(f"{instr_id}: Currency Mismatch: Flow requires {flow.allowed_currency}, but found {item.get('currency')}")
    
    date_errs = ISO20022Validator.validate_date(item.get('date'), flow.back_dated, flow.future_dated)
    errors.extend([f"{instr_id}: {err}" for err in date_errs])
    return errors

async def process_iso_upload(db: Session, flow_id: int, file: UploadFile):
    """
    Service logic to handle ISO 20022 file uploads.
    """
    flow = db.query(Flow).filter(Flow.id == flow_id).first()
    if not flow:
        raise HTTPException(status_code=404, detail="Flow definition not found")

    if flow.file_format.upper() == "XML" and not file.filename.lower().endswith(".xml"):
        raise HTTPException(status_code=400, detail=f"Invalid file type. Flow '{flow.name}' expects an XML file.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        with open(file_path, "rb") as f:
            content = f.read()

        xml_str = content.decode('utf-8', errors='ignore')

        msg_format = flow.message_format.upper()
        if "PAIN.001" in msg_format and "<CstmrCdtTrfInitn" not in xml_str:
            raise HTTPException(status_code=400, detail="Content mismatch: Expected a PAIN.001 file.")
        if "CAMT.054" in msg_format and "<BkToCstmrDbtCdtNtfctn" not in xml_str:
            raise HTTPException(status_code=400, detail="Content mismatch: Expected a CAMT.054 file.")

        ParserClass = parser_registry.get(flow.message_format.upper())
        if not ParserClass:
            raise HTTPException(status_code=400, detail=f"No parser found for message format: {flow.message_format}")
        parser = ParserClass(content)
        parsed_data = parser.get_transactions()

        msg_match = re.search(r'<(?:[\w-]*:)?MsgId[^>]*>([^<]+)</(?:[\w-]*:)?MsgId>', xml_str)
        nb_match = re.search(r'<(?:NbOfTxs|NbOfNtries)>(\d+)</', xml_str)
        sum_match = re.search(r'<(?:CtrlSum|Sum)>([\d.]+)</', xml_str)

        msg_id = msg_match.group(1).strip() if msg_match else None
        display_id = msg_id if msg_id else file.filename
        batch_count = int(nb_match.group(1)) if nb_match else len(parsed_data)
        batch_total = float(sum_match.group(1)) if sum_match else sum(float(item.get('amount', 0)) for item in parsed_data)

        batch_status = "Pending"
        validation_errors = []

        if flow.duplicate_check and msg_id:
            existing = db.query(Transaction).filter(Transaction.flow_id == flow.id, Transaction.instruction_id == msg_id).first()
            if existing:
                validation_errors.append(f"Duplicate Error: A file with MsgId '{msg_id}' was already processed (System ID: {existing.id})")

        for i, item in enumerate(parsed_data):
            item_errors = _validate_transaction_item(item, flow, i)
            validation_errors.extend(item_errors)

        if validation_errors:
            batch_status = "Validation Failed"

        first_tx = parsed_data[0] if parsed_data else {}
        batch_data = {
            "instruction_id": display_id,
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

def execute_iso_transaction(db: Session, transaction_id: int):
    """
    Service logic to execute a transaction by generating an output notification.
    """
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    flow = db.query(Flow).filter(Flow.id == tx.flow_id).first()
    output_format = (flow.message_format if flow else "CAMT.054").upper()
    flow_data_dict = FlowRead.model_validate(flow).model_dump() if flow else {}
    GeneratorClass = generator_registry.get(output_format)
    if not GeneratorClass:
        raise HTTPException(status_code=400, detail=f"No generator found for format: {output_format}")
    generator = GeneratorClass()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_filename_prefix = output_format.replace('.', '').upper()
    output_filename = f"{output_filename_prefix}_{tx.instruction_id}_{timestamp}.xml"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    raw_data_content = dict(tx.raw_data or {})
    transactions_list = raw_data_content.get("transactions", [])
    batch_total = raw_data_content.get("batch_total", tx.amount or 0.0)
    batch_count = raw_data_content.get("batch_count", 1)
    tx_data_for_generator = {"transaction": tx, "raw_data_content": raw_data_content, "transactions_list": transactions_list, "batch_total": batch_total, "batch_count": batch_count, "flow_data": flow_data_dict}
    xml_content = generator.generate_xml(tx_data_for_generator, flow_data_dict)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xml_content)
    raw_data = dict(tx.raw_data or {})
    raw_data["output_file"] = output_filename
    tx.raw_data = raw_data
    tx.status = "Executed"
    db.commit()
    return {"status": "Success", "output_file": output_filename}