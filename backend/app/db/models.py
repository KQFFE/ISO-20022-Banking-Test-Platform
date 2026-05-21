from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, Float, ForeignKey, MetaData
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime, timezone

# Naming convention for constraints to ensure stable names in SQLite migrations.
# This is required for Alembic's batch mode to function correctly.
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=naming_convention)

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
    duplicate_check = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to allow cascading deletes
    transactions = relationship("Transaction", back_populates="flow", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    flow_id = Column(Integer, ForeignKey("flows.id", ondelete="CASCADE"))
    instruction_id = Column(String)
    amount = Column(Float)
    currency = Column(String)
    status = Column(String, default="Pending")
    raw_data = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    flow = relationship("Flow", back_populates="transactions")
