import os
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, responses
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Transaction
from app.services.transaction_service import process_iso_upload, execute_iso_transaction

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
    Endpoint to handle ISO 20022 file uploads. Delegates logic to transaction_service.
    """
    return await process_iso_upload(db, flow_id, file)

@router.post("/{transaction_id}/execute")
async def execute_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """
    Executes a transaction by generating a response file.
    """
    return execute_iso_transaction(db, transaction_id)

@router.get("/download/{filename}")
async def download_output(filename: str, inline: bool = False):
    """Serves the generated ISO 20022 files."""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return responses.FileResponse(
        path=file_path, 
        media_type='application/xml',
        content_disposition_type="inline" if inline else "attachment",
        filename=filename
    )

@router.delete("/{transaction_id}")
async def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Deletes a transaction record from the database."""
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Optional: Clean up the generated output file from disk
    output_file = tx.raw_data.get("output_file") if tx.raw_data else None
    if output_file:
        file_path = os.path.join(OUTPUT_DIR, output_file)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.delete(tx)
    db.commit()
    
    return {"status": "Success", "detail": f"Transaction {transaction_id} deleted."}