from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database import get_db_connection
from app.models import ProductCreate, ProductUpdate

router = APIRouter()


@router.get("/products/categories")
def get_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM products WHERE available=TRUE ORDER BY category")
    cats = [r[0] for r in cursor.fetchall()]
    cursor.close(); conn.close()
    return {"categories": cats}


@router.get("/products")
def get_products(category: Optional[str] = Query(None)):
    conn = get_db_connection()
    cursor = conn.cursor()
    if category:
        cursor.execute("SELECT id, name, description, price, category FROM products WHERE available=TRUE AND category=%s ORDER BY name", (category,))
    else:
        cursor.execute("SELECT id, name, description, price, category FROM products WHERE available=TRUE ORDER BY category, name")
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return {"products": [{"id": r[0], "name": r[1], "description": r[2], "price": float(r[3]), "category": r[4]} for r in rows]}


@router.get("/products/{product_id}")
def get_product(product_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, price, category FROM products WHERE id=%s AND available=TRUE", (product_id,))
    row = cursor.fetchone()
    cursor.close(); conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"id": row[0], "name": row[1], "description": row[2], "price": float(row[3]), "category": row[4]}
