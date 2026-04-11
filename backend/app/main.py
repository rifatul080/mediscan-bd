from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.models import medicine, transaction, user
from app.models.medicine_chaldal import MedicineChaldal
from app.models.medicine_unified import MedicineUnified
from app.routers import medicines, billing, detection

Base.metadata.create_all(bind=engine)

app = FastAPI(title="MediScan BD API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(medicines.router)
app.include_router(billing.router)
app.include_router(detection.router)

@app.get("/")
def root():
    return {"message": "MediScan BD Backend is running"}