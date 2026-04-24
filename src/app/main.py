from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, products, admin

app = FastAPI(title="Saista Bakers - User Service", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    from app.database import get_db_connection
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1")
    cur.fetchone()
    cur.close(); conn.close()
    return {"status": "healthy", "service": "user-service", "version": "2.0.0"}


@app.get("/users/{user_id}")
def get_user_info(user_id: int):
    """Internal endpoint for cross-service user lookup."""
    from app.database import get_db_connection
    from fastapi import HTTPException
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, full_name, role FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": row[0], "username": row[1], "email": row[2], "full_name": row[3], "role": row[4]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=5001, reload=True)
