from fastapi import APIRouter, HTTPException, Depends
from app.database import get_db_connection
from app.models import ProductCreate, ProductUpdate, AdminEmailRequest, OrderStatusUpdate
from app.routes.auth import require_admin
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

router = APIRouter(prefix="/admin", tags=["admin"])


def admin_send_email(to_email: str, subject: str, body: str):
    try:
        smtp_server = os.getenv('SMTP_SERVER', 'localhost')
        smtp_port = int(os.getenv('SMTP_PORT', 1025))
        sender = os.getenv('SENDER_EMAIL', 'admin@saistabakers.com')
        smtp_user = os.getenv('SMTP_USER', '')
        smtp_pass = os.getenv('SMTP_PASSWORD', '')

        msg = MIMEMultipart('alternative')
        msg['From'] = sender
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.ehlo()
            if smtp_port == 587:
                server.starttls()
        if smtp_user and smtp_pass:
            server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


# ── Dashboard Stats ──────────────────────────────────────────
@router.get("/stats")
def get_stats(admin=Depends(require_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM orders WHERE status != 'cart'")
    total_orders = cur.fetchone()[0]
    cur.execute("SELECT COALESCE(SUM(total_price),0) FROM orders WHERE status='confirmed' OR status='completed'")
    revenue = float(cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM users WHERE role='customer'")
    total_customers = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM orders WHERE status='pending'")
    pending_orders = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM custom_orders WHERE status='pending'")
    pending_custom = cur.fetchone()[0]
    cur.close(); conn.close()
    return {
        "total_orders": total_orders,
        "revenue": revenue,
        "total_customers": total_customers,
        "pending_orders": pending_orders,
        "pending_custom_orders": pending_custom
    }


# ── Orders Management ────────────────────────────────────────
@router.get("/orders")
def get_all_orders(admin=Depends(require_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.id, o.user_id, u.username, u.email, o.total_price, o.status,
               o.payment_mode, o.payment_status, o.delivery_date, o.delivery_address, o.created_at
        FROM orders o
        LEFT JOIN users u ON o.user_id = u.id
        WHERE o.status != 'cart'
        ORDER BY o.created_at DESC
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return {"orders": [
        {
            "id": r[0], "user_id": r[1], "username": r[2] or "Unknown",
            "email": r[3] or "", "total_price": float(r[4] or 0),
            "status": r[5], "payment_mode": r[6], "payment_status": r[7],
            "delivery_date": str(r[8]) if r[8] else None,
            "delivery_address": r[9], "created_at": str(r[10])
        } for r in rows
    ]}


@router.put("/orders/{order_id}/status")
def update_order_status(order_id: int, body: OrderStatusUpdate, admin=Depends(require_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status=%s WHERE id=%s", (body.status, order_id))
    conn.commit()
    cur.close(); conn.close()
    return {"message": f"Order #{order_id} status updated to {body.status}"}


@router.get("/custom-orders")
def get_all_custom_orders(admin=Depends(require_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT co.id, co.user_id, u.username, u.email, co.pound, co.flavour,
               co.description, co.estimated_price, co.final_price, co.status,
               co.delivery_date, co.created_at
        FROM custom_orders co
        LEFT JOIN users u ON co.user_id = u.id
        ORDER BY co.created_at DESC
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return {"custom_orders": [
        {
            "id": r[0], "user_id": r[1], "username": r[2] or "Unknown",
            "email": r[3] or "", "pound": r[4], "flavour": r[5],
            "description": r[6], "estimated_price": float(r[7] or 0),
            "final_price": float(r[8]) if r[8] else None,
            "status": r[9], "delivery_date": str(r[10]) if r[10] else None,
            "created_at": str(r[11])
        } for r in rows
    ]}


# ── Customers Management ─────────────────────────────────────
@router.get("/customers")
def get_customers(admin=Depends(require_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, full_name, created_at FROM users WHERE role='customer' ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return {"customers": [
        {"id": r[0], "username": r[1], "email": r[2], "full_name": r[3], "created_at": str(r[4])} for r in rows
    ]}


@router.post("/email-customer")
def email_customer(req: AdminEmailRequest, admin=Depends(require_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT email, username FROM users WHERE id=%s", (req.customer_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Customer not found")
    email, username = row
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
      <div style="background:linear-gradient(135deg,#f7cac9,#a7d7c5);padding:25px;border-radius:12px;text-align:center;margin-bottom:20px">
        <h1 style="font-family:Georgia,serif;color:#3d2b1f;margin:0">🎂 Saista Bakers</h1>
      </div>
      <p>Dear <strong>{username}</strong>,</p>
      <div style="background:#fdfaf9;border-radius:12px;padding:20px;border-left:4px solid #f7cac9">
        {req.message}
      </div>
      <p style="color:#aaa;font-size:0.85em;margin-top:20px">Saista Bakers Team | ❤️ Crafted with Love</p>
    </div>"""
    success = admin_send_email(email, req.subject, html)
    return {"message": "Email sent successfully" if success else "Email queued (SMTP may not be configured locally)"}


# ── Products Management ──────────────────────────────────────
@router.get("/products")
def admin_get_products(admin=Depends(require_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, description, price, category, available FROM products ORDER BY category, name")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return {"products": [
        {"id": r[0], "name": r[1], "description": r[2], "price": float(r[3]), "category": r[4], "available": bool(r[5])} for r in rows
    ]}


@router.post("/products", status_code=201)
def add_product(product: ProductCreate, admin=Depends(require_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO products (name, description, price, category, available) VALUES (%s,%s,%s,%s,%s)",
        (product.name, product.description, product.price, product.category, product.available))
    conn.commit()
    pid = cur.lastrowid
    cur.close(); conn.close()
    return {"message": "Product added", "product_id": pid}


@router.put("/products/{product_id}")
def update_product(product_id: int, product: ProductUpdate, admin=Depends(require_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    fields = []
    values = []
    if product.name is not None: fields.append("name=%s"); values.append(product.name)
    if product.description is not None: fields.append("description=%s"); values.append(product.description)
    if product.price is not None: fields.append("price=%s"); values.append(product.price)
    if product.category is not None: fields.append("category=%s"); values.append(product.category)
    if product.available is not None: fields.append("available=%s"); values.append(product.available)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    values.append(product_id)
    cur.execute(f"UPDATE products SET {', '.join(fields)} WHERE id=%s", values)
    conn.commit()
    cur.close(); conn.close()
    return {"message": "Product updated"}


@router.delete("/products/{product_id}")
def delete_product(product_id: int, admin=Depends(require_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE products SET available=FALSE WHERE id=%s", (product_id,))
    conn.commit()
    cur.close(); conn.close()
    return {"message": "Product deactivated"}
