# ============================================================
#  DATABASE KECIL (SQLite) — nyatet order & statistik REAL
#  Nggak ada angka markup. Semua dihitung dari data asli.
# ============================================================

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "store.db")


def init_db():
    """Bikin tabel kalau belum ada."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Tabel user: catat siapa aja yang pernah buka bot
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            first_seen TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Tabel order: catat tiap order (status: pending/paid)
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id TEXT,
            product_name TEXT,
            price INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Tabel stock: simpan kredensial akun per produk (status: available/sold)
    c.execute("""
        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT,
            cred TEXT,
            status TEXT DEFAULT 'available',
            sold_to INTEGER,
            sold_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def register_user(user_id, username, full_name):
    """Simpan user (kalau baru). Return True kalau user baru."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    exists = c.fetchone()
    if not exists:
        c.execute(
            "INSERT INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
            (user_id, username, full_name),
        )
        conn.commit()
    conn.close()
    return not exists


def add_order(user_id, product_id, product_name, price):
    """Catat order baru (status pending). Return order id."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO orders (user_id, product_id, product_name, price) VALUES (?, ?, ?, ?)",
        (user_id, product_id, product_name, price),
    )
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    return order_id


def mark_paid(order_id):
    """Tandai order lunas (dipanggil admin setelah verifikasi)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE orders SET status = 'paid' WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()


def get_user_stats(user_id):
    """Statistik untuk 1 user: jumlah order lunas & total belanja."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT COUNT(*), COALESCE(SUM(price), 0) FROM orders WHERE user_id = ? AND status = 'paid'",
        (user_id,),
    )
    count, total = c.fetchone()
    conn.close()
    return {"orders": count, "total_spent": total}


def get_store_stats():
    """Statistik toko REAL: total order lunas, total omzet, total user."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*), COALESCE(SUM(price), 0) FROM orders WHERE status = 'paid'")
    total_orders, total_revenue = c.fetchone()
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    conn.close()
    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "total_users": total_users,
    }


def get_best_sellers(limit=5):
    """Jasa paling laku (dari order lunas). Return list (nama, jumlah)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT product_name, COUNT(*) as jml
        FROM orders WHERE status = 'paid'
        GROUP BY product_id ORDER BY jml DESC LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_top_buyers(limit=5):
    """Pelanggan paling loyal (total belanja terbesar). Return list."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT u.full_name, u.username, COUNT(o.id) as jml, COALESCE(SUM(o.price),0) as total
        FROM orders o JOIN users u ON o.user_id = u.user_id
        WHERE o.status = 'paid'
        GROUP BY o.user_id ORDER BY total DESC LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_user_history(user_id, limit=10):
    """Riwayat order 1 user. Return list (nama, harga, status, tanggal)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT product_name, price, status, created_at
        FROM orders WHERE user_id = ?
        ORDER BY created_at DESC LIMIT ?
    """, (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows


# ============================================================
#  STOCK / VENDING — simpan & keluarkan kredensial akun
# ============================================================

def add_stock(product_id, cred):
    """Tambah 1 kredensial ke stok (status available)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO stock (product_id, cred, status) VALUES (?, ?, 'available')",
        (product_id, cred),
    )
    conn.commit()
    conn.close()


def get_available_stock_count(product_id):
    """Jumlah stok masih available untuk 1 produk."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT COUNT(*) FROM stock WHERE product_id = ? AND status = 'available'",
        (product_id,),
    )
    n = c.fetchone()[0]
    conn.close()
    return n


def total_stock_count(product_id):
    """Total semua stok (available + sold) untuk 1 produk."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM stock WHERE product_id = ?", (product_id,))
    n = c.fetchone()[0]
    conn.close()
    return n


def pop_stock(product_id):
    """Ambil 1 stok available, tandai sold, return kredensial. None kalau habis."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT id, cred FROM stock WHERE product_id = ? AND status = 'available' "
        "ORDER BY id LIMIT 1",
        (product_id,),
    )
    row = c.fetchone()
    if not row:
        conn.close()
        return None
    sid, cred = row
    c.execute("UPDATE stock SET status = 'sold' WHERE id = ?", (sid,))
    conn.commit()
    conn.close()
    return cred


def get_order(order_id):
    """Ambil 1 order by id. Return dict atau None."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT id, user_id, product_id, product_name, price, status, created_at "
        "FROM orders WHERE id = ?",
        (order_id,),
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0], "user_id": row[1], "product_id": row[2],
        "product_name": row[3], "price": row[4], "status": row[5],
        "created_at": row[6],
    }
