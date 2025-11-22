import os
from dotenv import load_dotenv

# Pastikan .env dibaca dari root proyek (folder yang sama dengan file ini)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

class Config:
    # Wajib: DATABASE_URL harus ada di .env
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError(
            "DATABASE_URL tidak ditemukan. Buat file .env di root proyek dan isi koneksi MySQL."
        )

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Pastikan UPLOAD_DIR absolute agar konsisten
    UPLOAD_DIR = os.path.join(BASE_DIR, os.getenv("UPLOAD_DIR", "media"))
    MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", 10))

    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

    SHEETS_ENABLED = os.getenv("SHEETS_ENABLED", "false").lower() == "true"
    SHEETS_SPREADSHEET_ID = os.getenv("SHEETS_SPREADSHEET_ID", "")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS", os.path.join(BASE_DIR, "credentials.json")
    )
