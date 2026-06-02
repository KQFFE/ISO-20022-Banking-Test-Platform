from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
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
    special_character_support: Optional[bool] = False
    back_dated: Optional[bool] = False
    future_dated: Optional[bool] = False
    duplicate_check: Optional[bool] = False
    currency_validation: Optional[bool] = False
    allowed_currency: Optional[str] = ""

class FlowRead(FlowCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)

@router.get("/", response_model=List[FlowRead])
def list_flows(db: Session = Depends(get_db)):
    """Returns all available flow definitions."""
    return db.query(Flow).all()

@router.post("/", response_model=FlowRead)
def create_flow(flow: FlowCreate, db: Session = Depends(get_db)):
    """Creates a new flow definition."""
    try:
        # Use the Mapper to definitively find which keys the Flow constructor accepts
        flow_data = flow.model_dump()
        valid_attrs = Flow.__mapper__.attrs.keys()
        db_flow = Flow(**{k: v for k, v in flow_data.items() if k in valid_attrs})
        db.add(db_flow)
        db.commit()
        db.refresh(db_flow)
        return db_flow
    except (SQLAlchemyError, TypeError, AttributeError) as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")

@router.put("/{flow_id}", response_model=FlowRead)
def update_flow(flow_id: int, flow: FlowCreate, db: Session = Depends(get_db)):
    """Updates an existing flow definition."""
    db_flow = db.query(Flow).filter(Flow.id == flow_id).first()
    if not db_flow:
        raise HTTPException(status_code=404, detail="Flow definition not found")
    
    update_data = flow.model_dump()
    valid_attrs = Flow.__mapper__.attrs.keys()
    for key, value in update_data.items():
        if key in valid_attrs:
            setattr(db_flow, key, value)
    
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