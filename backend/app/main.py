from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from app.api import auth, trans, flows
from app.db.session import get_db
from app.db.models import Transaction, Flow
from fastapi import Depends
from sqlalchemy.orm import Session

app = FastAPI(title="ISO 20022 Banking Test Platform")

# 1. Session Middleware for SSO
# In production, use a strong secret key loaded from environment variables
app.add_middleware(
    SessionMiddleware, 
    secret_key="IKANO_SECRET_KEY_FOR_TESTING_ONLY" 
)

# 2. CORS Middleware
# Allows your React frontend (localhost:3000) to make requests to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler to maintain CORS on 500 errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    origin = request.headers.get("origin")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "message": str(exc)},
        headers={"Access-Control-Allow-Origin": origin} if origin else {}
    )

# 3. Include Routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(trans.router, prefix="/transactions", tags=["Transactions"])
app.include_router(flows.router, prefix="/flows", tags=["Flows"])

# 4. Stats Endpoint (used by Dashboard.js)
@app.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_tx = db.query(Transaction).count()
    active_flows = db.query(Flow).count()
    executed_tx = db.query(Transaction).filter(Transaction.status == "Executed").count()
    
    return {
        "total_transactions": total_tx,
        "active_flows": active_flows,
        "executed_transactions": executed_tx
    }

@app.get("/")
async def root():
    return {"message": "ISO 20022 Banking Test Platform API is running."}