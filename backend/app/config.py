import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/mediscan.db")
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret")
RECEIPTS_FOLDER = os.getenv("RECEIPTS_FOLDER", "receipts")