import mysql.connector
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'Asad@1234'),
    'database': os.getenv('DB_NAME', 'saista_bakers'),
    'port': int(os.getenv('DB_PORT', 3306))
}

def get_db_connection():
    from fastapi import HTTPException
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print(f"DB Error: {err}")
        raise HTTPException(status_code=500, detail="Database connection failed")
