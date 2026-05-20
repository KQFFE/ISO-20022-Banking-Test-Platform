from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.db.session import get_db
from app.db.models import Flow

router = APIRouter()

class FlowCreate(BaseModel):
    name: str
    direction: str
    message_format: str
    file_format: Optional[str] = "XML"
    bic_codes: Optional[List[str]] = []
    valid_ibans: Optional[List[str]] = []
    back_dated: Optional[bool] = False
    future_dated: Optional[bool] = False

@router.get("/")
def list_flows(db: Session = Depends(get_db)):
    """Returns all available flow definitions."""
    return db.query(Flow).all()

@router.post("/")
def create_flow(flow: FlowCreate, db: Session = Depends(get_db)):
    """Creates a new flow definition."""
    db_flow = Flow(**flow.dict())
    db.add(db_flow)
    db.commit()
    db.refresh(db_flow)
    return db_flow

@router.delete("/{flow_id}")
def delete_flow(flow_id: int, db: Session = Depends(get_db)):
    """Deletes a flow definition from the database."""
    db_flow = db.query(Flow).filter(Flow.id == flow_id).first()
    if not db_flow:
        raise HTTPException(status_code=404, detail="Flow definition not found")
    
    db.delete(db_flow)
    db.commit()
    return {"status": "Success", "detail": f"Flow {flow_id} deleted."}