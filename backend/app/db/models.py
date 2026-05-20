from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, Float, ForeignKey
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone

class Base(DeclarativeBase):
    pass

class Flow(Base):
    __tablename__ = "flows"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    direction = Column(String)  # Inbound/Outbound
    source_system = Column(String)
    destination_system = Column(String)
    message_format = Column(String) # e.g. Pain.001
    file_format = Column(String)    # e.g. XML
    bic_codes = Column(JSON)        # List of BICs
    valid_ibans = Column(JSON)      # List of IBANs
    input_path = Column(String)
    output_path = Column(String)
    special_character_support = Column(Boolean, default=False)
    back_dated = Column(Boolean, default=False)
    future_dated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    flow_id = Column(Integer, ForeignKey("flows.id"))
    instruction_id = Column(String)
    amount = Column(Float)
    currency = Column(String)
    status = Column(String, default="Pending")
    raw_data = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
