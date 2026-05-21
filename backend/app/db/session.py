from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from starlette.config import Config

# Load configuration from environment variables or .env file
config = Config(".env")

# Database connection URL
# Example: "postgresql://user:password@host:port/dbname"
# For SQLite, it would be "sqlite:///./sql_app.db"
DATABASE_URL = config.get("DATABASE_URL", default="sqlite:///./test.db")

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})

# Ensure SQLite enforces foreign key constraints for cascades
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()