from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os

from app.database import get_db_connection
from app.models import UserCreate, UserLogin, Token

router = APIRouter()

SECRET_KEY = os.getenv('SECRET_KEY', 'saista-bakers-secret-key-2024-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, role: str = "customer"):
    to_encode = data.copy()
    to_encode.update({
        "exp": datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS),
        "role": role
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    exc = HTTPException(status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise exc
        return {"user_id": int(user_id), "role": payload.get("role", "customer")}
    except JWTError:
        raise exc

def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.post("/signup", status_code=201)
def signup(user: UserCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE username=%s OR email=%s", (user.username, user.email))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username or email already exists")
        h = get_password_hash(user.password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, full_name, role) VALUES (%s,%s,%s,%s,%s)",
            (user.username, user.email, h, user.full_name or "", "customer")
        )
        conn.commit()
        user_id = cursor.lastrowid
        token = create_access_token({"sub": str(user_id)}, role="customer")
        return {"message": "User created successfully", "user_id": user_id, "access_token": token, "role": "customer"}
    finally:
        cursor.close(); conn.close()


@router.post("/login")
def login(user: UserLogin):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username, email, full_name, password_hash, role FROM users WHERE username=%s", (user.username,))
        row = cursor.fetchone()
        if not row or not verify_password(user.password, row[4]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        user_id, username, email, full_name, _, role = row
        token = create_access_token({"sub": str(user_id)}, role=role)
        return {
            "access_token": token, "token_type": "bearer",
            "user_id": user_id, "username": username,
            "full_name": full_name, "email": email,
            "role": role, "message": "Login successful"
        }
    finally:
        cursor.close(); conn.close()


@router.post("/admin/login")
def admin_login(user: UserLogin):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username, email, full_name, password_hash, role FROM users WHERE username=%s AND role='admin'", (user.username,))
        row = cursor.fetchone()
        if not row or not verify_password(user.password, row[4]):
            raise HTTPException(status_code=401, detail="Invalid admin credentials")
        user_id, username, email, full_name, _, role = row
        token = create_access_token({"sub": str(user_id)}, role="admin")
        return {
            "access_token": token, "token_type": "bearer",
            "user_id": user_id, "username": username,
            "full_name": full_name, "email": email,
            "role": "admin", "message": "Admin login successful"
        }
    finally:
        cursor.close(); conn.close()


@router.get("/profile")
def get_profile(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username, email, full_name, role, created_at FROM users WHERE id=%s", (current_user["user_id"],))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        return {"id": row[0], "username": row[1], "email": row[2], "full_name": row[3], "role": row[4], "created_at": str(row[5])}
    finally:
        cursor.close(); conn.close()
