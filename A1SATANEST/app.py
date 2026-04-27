from __future__ import annotations

import hmac
import os
import random
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Sequence

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.db"

DB_TYPE = os.environ.get("DB_TYPE", "sqlite").strip().lower()
ORACLE_USER = os.environ.get("ORACLE_USER", "")
ORACLE_PASSWORD = os.environ.get("ORACLE_PASSWORD", "")
ORACLE_DSN = os.environ.get("ORACLE_DSN", "")

app = Flask(__name__)
app.secret_key = os.environ.get("A1_SECRET_KEY", "a1satanest-change-this-secret")
ADMIN_PASSWORD = os.environ.get("A1_ADMIN_PASSWORD", "A1@SecureAdmin")


PRODUCT_SEED = [
    {
        "name": "Original Laptop Battery",
        "category": "Power",
        "price": 2499,
        "mrp": 3299,
        "description": "Long backup battery with 6-month warranty",
        "image": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?auto=format&fit=crop&w=1200&q=80",
        "stock": 32,
        "rating": 4.7,
    },
    {
        "name": "65W Fast Laptop Charger",
        "category": "Power",
        "price": 1399,
        "mrp": 1899,
        "description": "Smart heat control and surge protection",
        "image": "https://images.unsplash.com/photo-1606312619070-d48b4c652a52?auto=format&fit=crop&w=1200&q=80",
        "stock": 50,
        "rating": 4.6,
    },
    {
        "name": "NVMe SSD 1TB",
        "category": "Storage",
        "price": 5299,
        "mrp": 6899,
        "description": "Blazing fast boot and app loading speed",
        "image": "https://images.unsplash.com/photo-1591488320449-011701bb6704?auto=format&fit=crop&w=1200&q=80",
        "stock": 20,
        "rating": 4.8,
    },
    {
        "name": "16GB DDR4 RAM",
        "category": "Performance",
        "price": 3199,
        "mrp": 4099,
        "description": "Upgrade multitasking for coding and editing",
        "image": "https://images.unsplash.com/photo-1562976540-1502c2145186?auto=format&fit=crop&w=1200&q=80",
        "stock": 40,
        "rating": 4.5,
    },
    {
        "name": "Laptop Cooling Pad RGB",
        "category": "Accessories",
        "price": 1499,
        "mrp": 2199,
        "description": "Dual fan cooling with adjustable stand",
        "image": "https://images.unsplash.com/photo-1618761714954-0b8cd0026356?auto=format&fit=crop&w=1200&q=80",
        "stock": 45,
        "rating": 4.4,
    },
    {
        "name": "Premium Keyboard + Mouse Combo",
        "category": "Accessories",
        "price": 1899,
        "mrp": 2599,
        "description": "Silent keys and ergonomic wireless mouse",
        "image": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=1200&q=80",
        "stock": 38,
        "rating": 4.3,
    },
    {
        "name": "HP 65W Smart Laptop Adapter",
        "category": "Power",
        "price": 1899,
        "mrp": 2599,
        "description": "Original-grade replacement adapter with smart voltage protection",
        "image": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?auto=format&fit=crop&w=1200&q=80",
        "stock": 34,
        "rating": 4.5,
    },
    {
        "name": "ASUS 100W USB-C GaN Charger",
        "category": "Power",
        "price": 3299,
        "mrp": 4499,
        "description": "Fast multi-device charging for modern Type-C laptops",
        "image": "https://images.unsplash.com/photo-1615526675159-e248c3021d3f?auto=format&fit=crop&w=1200&q=80",
        "stock": 26,
        "rating": 4.4,
    },
    {
        "name": "Crucial MX500 1TB SATA SSD",
        "category": "Storage",
        "price": 6199,
        "mrp": 7999,
        "description": "Reliable 1TB SATA SSD upgrade for older laptops",
        "image": "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?auto=format&fit=crop&w=1200&q=80",
        "stock": 29,
        "rating": 4.7,
    },
    {
        "name": "Samsung 990 EVO 1TB NVMe SSD",
        "category": "Storage",
        "price": 8299,
        "mrp": 10999,
        "description": "High-speed NVMe Gen4 storage for premium performance",
        "image": "https://images.unsplash.com/photo-1628557044797-f21a177c37ec?auto=format&fit=crop&w=1200&q=80",
        "stock": 18,
        "rating": 4.8,
    },
    {
        "name": "Seagate One Touch 2TB External HDD",
        "category": "Storage",
        "price": 5999,
        "mrp": 7999,
        "description": "Portable 2TB backup drive for project and media storage",
        "image": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?auto=format&fit=crop&w=1200&q=80",
        "stock": 21,
        "rating": 4.5,
    },
    {
        "name": "Kingston Fury 32GB DDR4 RAM Kit",
        "category": "Performance",
        "price": 6999,
        "mrp": 8699,
        "description": "Dual-channel RAM kit for heavy multitasking workloads",
        "image": "https://images.unsplash.com/photo-1541029071515-84cc54f84dc5?auto=format&fit=crop&w=1200&q=80",
        "stock": 17,
        "rating": 4.6,
    },
    {
        "name": "TP-Link Archer T3U USB Wi-Fi Adapter",
        "category": "Accessories",
        "price": 1499,
        "mrp": 2199,
        "description": "Dual-band USB adapter for faster and stable wireless connectivity",
        "image": "https://images.unsplash.com/photo-1518779578993-ec3579fee39f?auto=format&fit=crop&w=1200&q=80",
        "stock": 44,
        "rating": 4.4,
    },
    {
        "name": "Logitech M331 Silent Plus Mouse",
        "category": "Accessories",
        "price": 1299,
        "mrp": 1799,
        "description": "Low-noise wireless mouse with long battery life",
        "image": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?auto=format&fit=crop&w=1200&q=80",
        "stock": 52,
        "rating": 4.5,
    },
]

REVIEW_SEED = [
    ("Ravi Mehta", "My MacBook screen issue was resolved within 24 hours, at nearly 35% lower cost.", 5),
    ("Sneha Roy", "Pickup, repair, and delivery were completely transparent. Live updates were excellent.", 5),
    ("Arjun Das", "The battery replacement was genuine and overall laptop performance improved noticeably.", 4),
]


TABLE_DDLS: dict[str, dict[str, str]] = {
    "products": {
        "sqlite": """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price INTEGER NOT NULL,
                mrp INTEGER NOT NULL,
                description TEXT,
                image TEXT,
                stock INTEGER NOT NULL,
                rating REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """,
        "oracle": """
            CREATE TABLE products (
                id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                name VARCHAR2(255) NOT NULL,
                category VARCHAR2(120) NOT NULL,
                price NUMBER NOT NULL,
                mrp NUMBER NOT NULL,
                description CLOB,
                image VARCHAR2(2000),
                stock NUMBER NOT NULL,
                rating NUMBER(4,2) NOT NULL,
                created_at VARCHAR2(32) NOT NULL
            )
        """,
    },
    "service_requests": {
        "sqlite": """
            CREATE TABLE IF NOT EXISTS service_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                city TEXT NOT NULL,
                laptop_brand TEXT NOT NULL,
                issue_type TEXT NOT NULL,
                urgency TEXT NOT NULL,
                problem_details TEXT NOT NULL,
                estimated_price INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """,
        "oracle": """
            CREATE TABLE service_requests (
                id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                customer_name VARCHAR2(255) NOT NULL,
                phone VARCHAR2(40) NOT NULL,
                email VARCHAR2(255),
                city VARCHAR2(120) NOT NULL,
                laptop_brand VARCHAR2(255) NOT NULL,
                issue_type VARCHAR2(120) NOT NULL,
                urgency VARCHAR2(40) NOT NULL,
                problem_details CLOB NOT NULL,
                estimated_price NUMBER NOT NULL,
                status VARCHAR2(120) NOT NULL,
                created_at VARCHAR2(32) NOT NULL
            )
        """,
    },
    "orders": {
        "sqlite": """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                city TEXT NOT NULL,
                address TEXT NOT NULL,
                total_amount INTEGER NOT NULL,
                payment_mode TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """,
        "oracle": """
            CREATE TABLE orders (
                id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                customer_name VARCHAR2(255) NOT NULL,
                phone VARCHAR2(40) NOT NULL,
                city VARCHAR2(120) NOT NULL,
                address CLOB NOT NULL,
                total_amount NUMBER NOT NULL,
                payment_mode VARCHAR2(80) NOT NULL,
                status VARCHAR2(120) NOT NULL,
                created_at VARCHAR2(32) NOT NULL
            )
        """,
    },
    "order_items": {
        "sqlite": """
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price INTEGER NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        """,
        "oracle": """
            CREATE TABLE order_items (
                id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                order_id NUMBER NOT NULL,
                product_id NUMBER NOT NULL,
                quantity NUMBER NOT NULL,
                unit_price NUMBER NOT NULL
            )
        """,
    },
    "reviews": {
        "sqlite": """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                message TEXT NOT NULL,
                rating INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """,
        "oracle": """
            CREATE TABLE reviews (
                id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                customer_name VARCHAR2(255) NOT NULL,
                message CLOB NOT NULL,
                rating NUMBER NOT NULL,
                created_at VARCHAR2(32) NOT NULL
            )
        """,
    },
    "support_requests": {
        "sqlite": """
            CREATE TABLE IF NOT EXISTS support_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                topic TEXT NOT NULL,
                priority TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """,
        "oracle": """
            CREATE TABLE support_requests (
                id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                customer_name VARCHAR2(255) NOT NULL,
                email VARCHAR2(255) NOT NULL,
                phone VARCHAR2(40) NOT NULL,
                topic VARCHAR2(150) NOT NULL,
                priority VARCHAR2(40) NOT NULL,
                message CLOB NOT NULL,
                status VARCHAR2(100) NOT NULL,
                created_at VARCHAR2(32) NOT NULL
            )
        """,
    },
    "contact_messages": {
        "sqlite": """
            CREATE TABLE IF NOT EXISTS contact_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                city TEXT,
                inquiry_type TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """,
        "oracle": """
            CREATE TABLE contact_messages (
                id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                full_name VARCHAR2(255) NOT NULL,
                email VARCHAR2(255) NOT NULL,
                phone VARCHAR2(40),
                city VARCHAR2(120),
                inquiry_type VARCHAR2(150) NOT NULL,
                message CLOB NOT NULL,
                status VARCHAR2(100) NOT NULL,
                created_at VARCHAR2(32) NOT NULL
            )
        """,
    },
    "customer_otps": {
        "sqlite": """
            CREATE TABLE IF NOT EXISTS customer_otps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT NOT NULL,
                otp_code TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """,
        "oracle": """
            CREATE TABLE customer_otps (
                id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                phone VARCHAR2(40) NOT NULL,
                otp_code VARCHAR2(8) NOT NULL,
                expires_at VARCHAR2(32) NOT NULL,
                used NUMBER(1) DEFAULT 0 NOT NULL,
                created_at VARCHAR2(32) NOT NULL
            )
        """,
    },
}


class DatabaseManager:
    def __init__(self, db_type: str) -> None:
        self.db_type = db_type
        self.is_oracle = db_type == "oracle"
        self.oracle_module = None

        if self.is_oracle:
            if not ORACLE_USER or not ORACLE_PASSWORD or not ORACLE_DSN:
                raise RuntimeError("Oracle selected but ORACLE_USER/ORACLE_PASSWORD/ORACLE_DSN is not configured.")
            try:
                import oracledb  # type: ignore
            except ImportError as exc:
                raise RuntimeError("Install 'oracledb' package to use Oracle mode.") from exc
            self.oracle_module = oracledb

    @contextmanager
    def connect(self):
        if self.is_oracle:
            assert self.oracle_module is not None
            conn = self.oracle_module.connect(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=ORACLE_DSN)
        else:
            conn = sqlite3.connect(DB_PATH)

        try:
            if not self.is_oracle:
                conn.row_factory = sqlite3.Row
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _adapt_query(self, query: str) -> str:
        if not self.is_oracle:
            return query

        out: list[str] = []
        bind_index = 1
        for ch in query:
            if ch == "?":
                out.append(f":{bind_index}")
                bind_index += 1
            else:
                out.append(ch)
        return "".join(out)

    def _normalize_params(self, params: Sequence[Any] | None) -> Sequence[Any]:
        return tuple(params or [])

    def _rows_to_dicts(self, cursor, rows: Iterable[Any]) -> list[dict[str, Any]]:
        columns = [str(col[0]).lower() for col in cursor.description] if cursor.description else []
        result: list[dict[str, Any]] = []
        for row in rows:
            result.append({columns[i]: row[i] for i in range(len(columns))})
        return result

    def table_exists(self, conn, table_name: str) -> bool:
        if self.is_oracle:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = :1", [table_name.upper()])
            return int(cursor.fetchone()[0]) > 0

        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?", [table_name])
        return cursor.fetchone() is not None

    def execute(self, conn, query: str, params: Sequence[Any] | None = None):
        cursor = conn.cursor()
        cursor.execute(self._adapt_query(query), self._normalize_params(params))
        return cursor

    def executemany(self, conn, query: str, params_seq: Iterable[Sequence[Any]]):
        cursor = conn.cursor()
        cursor.executemany(self._adapt_query(query), [self._normalize_params(params) for params in params_seq])
        return cursor

    def fetchall(self, conn, query: str, params: Sequence[Any] | None = None) -> list[dict[str, Any]]:
        cursor = self.execute(conn, query, params)
        rows = cursor.fetchall()
        return self._rows_to_dicts(cursor, rows)

    def fetchone(self, conn, query: str, params: Sequence[Any] | None = None) -> dict[str, Any] | None:
        cursor = self.execute(conn, query, params)
        row = cursor.fetchone()
        if row is None:
            return None
        return self._rows_to_dicts(cursor, [row])[0]

    def scalar(self, conn, query: str, params: Sequence[Any] | None = None) -> Any:
        cursor = self.execute(conn, query, params)
        row = cursor.fetchone()
        if row is None:
            return None
        return row[0]

    def insert_and_get_id(self, conn, table_name: str, data: dict[str, Any]) -> int:
        columns = list(data.keys())

        if self.is_oracle:
            assert self.oracle_module is not None
            col_sql = ", ".join(columns)
            bind_sql = ", ".join([f":{col}" for col in columns])
            returning_var = conn.cursor().var(self.oracle_module.NUMBER)
            sql = f"INSERT INTO {table_name} ({col_sql}) VALUES ({bind_sql}) RETURNING id INTO :out_id"
            payload = dict(data)
            payload["out_id"] = returning_var
            conn.cursor().execute(sql, payload)
            return int(returning_var.getvalue()[0])

        placeholders = ", ".join(["?"] * len(columns))
        col_sql = ", ".join(columns)
        cursor = conn.cursor()
        cursor.execute(
            f"INSERT INTO {table_name} ({col_sql}) VALUES ({placeholders})",
            [data[column] for column in columns],
        )
        return int(cursor.lastrowid)


db = DatabaseManager(DB_TYPE)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def parse_iso(dt_text: str) -> datetime:
    return datetime.fromisoformat(dt_text)


def limit_suffix(rows: int) -> str:
    return f" FETCH FIRST {rows} ROWS ONLY" if db.is_oracle else f" LIMIT {rows}"


def init_db() -> None:
    with db.connect() as conn:
        for table_name, ddl in TABLE_DDLS.items():
            if not db.table_exists(conn, table_name):
                conn.cursor().execute(ddl["oracle" if db.is_oracle else "sqlite"])

        existing_products = db.fetchall(conn, "SELECT name FROM products")
        existing_names = {str(row["name"]).strip().lower() for row in existing_products}

        missing_items = [item for item in PRODUCT_SEED if item["name"].strip().lower() not in existing_names]
        if missing_items:
            db.executemany(
                conn,
                """
                INSERT INTO products(name, category, price, mrp, description, image, stock, rating, created_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item["name"],
                        item["category"],
                        item["price"],
                        item["mrp"],
                        item["description"],
                        item["image"],
                        item["stock"],
                        item["rating"],
                        now_iso(),
                    )
                    for item in missing_items
                ],
            )

        review_count = int(db.scalar(conn, "SELECT COUNT(*) FROM reviews") or 0)
        if review_count == 0:
            db.executemany(
                conn,
                "INSERT INTO reviews(customer_name, message, rating, created_at) VALUES (?, ?, ?, ?)",
                [(name, message, rating, now_iso()) for name, message, rating in REVIEW_SEED],
            )


def compute_estimate(issue_type: str, urgency: str) -> int:
    base = {
        "Screen": 4200,
        "Battery": 2500,
        "Keyboard": 1800,
        "Motherboard": 6200,
        "Heating": 1500,
        "Software": 1200,
        "Other": 2000,
    }.get(issue_type, 2000)

    urgency_multiplier = {
        "standard": 1.0,
        "priority": 1.25,
        "express": 1.45,
    }.get(urgency, 1.0)

    return int(base * urgency_multiplier)


def stats_payload() -> dict[str, Any]:
    with db.connect() as conn:
        services = int(db.scalar(conn, "SELECT COUNT(*) FROM service_requests") or 0)
        completed = int(
            db.scalar(conn, "SELECT COUNT(*) FROM service_requests WHERE status IN ('Done', 'Delivered')") or 0
        )
        orders = int(db.scalar(conn, "SELECT COUNT(*) FROM orders") or 0)
        revenue_services = int(db.scalar(conn, "SELECT COALESCE(SUM(estimated_price), 0) FROM service_requests") or 0)
        revenue_orders = int(db.scalar(conn, "SELECT COALESCE(SUM(total_amount), 0) FROM orders") or 0)

    completion_rate = round((completed / services) * 100, 1) if services else 96.2

    return {
        "service_requests": services,
        "completed_repairs": completed,
        "orders": orders,
        "revenue": revenue_services + revenue_orders,
        "completion_rate": completion_rate,
    }


def is_admin_authenticated() -> bool:
    return bool(session.get("admin_authenticated"))


def generate_otp() -> str:
    return f"{random.randint(100000, 999999)}"


def get_customer_phone() -> str | None:
    phone = session.get("customer_phone")
    if not isinstance(phone, str):
        return None
    return phone.strip() or None


@app.route("/")
def index():
    return render_template("index.html", stats=stats_payload())


@app.route("/products")
def products_page():
    return render_template("products.html")


@app.route("/booking")
def booking_page():
    return render_template("booking.html")


@app.route("/support")
def support_page():
    return render_template("support.html")


@app.route("/contact")
def contact_page():
    return render_template("contact.html")


@app.route("/customer/login")
def customer_login_page():
    if get_customer_phone():
        return redirect(url_for("customer_dashboard_page"))
    return render_template("customer_login.html")


@app.route("/customer/dashboard")
def customer_dashboard_page():
    if not get_customer_phone():
        return redirect(url_for("customer_login_page"))
    return render_template("customer_dashboard.html")


@app.route("/customer/logout")
def customer_logout():
    session.pop("customer_phone", None)
    return redirect(url_for("customer_login_page"))


@app.route("/admin")
def admin_page():
    if not is_admin_authenticated():
        return redirect(url_for("admin_login", next="/admin"))
    return render_template("admin.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        if is_admin_authenticated():
            return redirect(url_for("admin_page"))
        return render_template("admin_login.html", error=None, next_url=request.args.get("next", "/admin"))

    password = (request.form.get("password") or "").strip()
    next_url = (request.form.get("next") or "/admin").strip()

    if hmac.compare_digest(password, ADMIN_PASSWORD):
        session["admin_authenticated"] = True
        if not next_url.startswith("/"):
            next_url = "/admin"
        return redirect(next_url)

    return render_template(
        "admin_login.html",
        error="Invalid password. Please try again.",
        next_url=next_url if next_url.startswith("/") else "/admin",
    ), 401


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_authenticated", None)
    return redirect(url_for("admin_login"))


@app.route("/api/stats")
def api_stats():
    return jsonify(stats_payload())


@app.route("/api/products")
def api_products():
    category = request.args.get("category", "all")
    search = request.args.get("search", "").strip().lower()

    query = "SELECT * FROM products"
    params: list[Any] = []
    where = []

    if category != "all":
        where.append("category = ?")
        params.append(category)

    if search:
        where.append("LOWER(name) LIKE ?")
        params.append(f"%{search}%")

    if where:
        query += " WHERE " + " AND ".join(where)

    query += " ORDER BY rating DESC, created_at DESC"

    with db.connect() as conn:
        rows = db.fetchall(conn, query, params)

    return jsonify(rows)


@app.route("/api/reviews")
def api_reviews():
    query = (
        "SELECT customer_name, message, rating, created_at "
        "FROM reviews ORDER BY id DESC" + limit_suffix(6)
    )
    with db.connect() as conn:
        rows = db.fetchall(conn, query)
    return jsonify(rows)


@app.post("/api/book-service")
def api_book_service():
    payload = request.get_json(silent=True) or {}

    required = ["customer_name", "phone", "city", "laptop_brand", "issue_type", "urgency", "problem_details"]
    missing = [field for field in required if not str(payload.get(field, "")).strip()]
    if missing:
        return jsonify({"ok": False, "message": "Please fill all required fields.", "missing": missing}), 400

    estimated_price = compute_estimate(payload["issue_type"], payload["urgency"])

    with db.connect() as conn:
        ticket_id = db.insert_and_get_id(
            conn,
            "service_requests",
            {
                "customer_name": payload["customer_name"].strip(),
                "phone": payload["phone"].strip(),
                "email": payload.get("email", "").strip(),
                "city": payload["city"].strip(),
                "laptop_brand": payload["laptop_brand"].strip(),
                "issue_type": payload["issue_type"].strip(),
                "urgency": payload["urgency"].strip(),
                "problem_details": payload["problem_details"].strip(),
                "estimated_price": estimated_price,
                "status": "Pending Pickup",
                "created_at": now_iso(),
            },
        )

    return jsonify(
        {
            "ok": True,
            "ticket_id": ticket_id,
            "estimated_price": estimated_price,
            "message": "Booking created successfully.",
        }
    )


@app.post("/api/place-order")
def api_place_order():
    payload = request.get_json(silent=True) or {}
    customer = payload.get("customer", {})
    items = payload.get("items", [])

    required_customer = ["customer_name", "phone", "city", "address", "payment_mode"]
    missing = [field for field in required_customer if not str(customer.get(field, "")).strip()]
    if missing:
        return jsonify({"ok": False, "message": "Customer details incomplete.", "missing": missing}), 400

    if not isinstance(items, list) or not items:
        return jsonify({"ok": False, "message": "Cart is empty."}), 400

    product_ids = [item.get("product_id") for item in items if item.get("product_id")]
    if not product_ids:
        return jsonify({"ok": False, "message": "Invalid cart items."}), 400

    placeholders = ",".join(["?"] * len(product_ids))

    with db.connect() as conn:
        products = db.fetchall(
            conn,
            f"SELECT id, name, price, stock FROM products WHERE id IN ({placeholders})",
            product_ids,
        )

        product_map = {int(row["id"]): row for row in products}
        order_total = 0
        line_items: list[tuple[int, int, int]] = []

        for item in items:
            pid = int(item.get("product_id", 0))
            qty = int(item.get("quantity", 1))
            if pid not in product_map or qty <= 0:
                return jsonify({"ok": False, "message": "Invalid product found in cart."}), 400

            product = product_map[pid]
            if qty > int(product["stock"]):
                return jsonify({"ok": False, "message": f"'{product['name']}' has only {product['stock']} left."}), 400

            line_total = int(product["price"]) * qty
            order_total += line_total
            line_items.append((pid, qty, int(product["price"])))

        order_id = db.insert_and_get_id(
            conn,
            "orders",
            {
                "customer_name": customer["customer_name"].strip(),
                "phone": customer["phone"].strip(),
                "city": customer["city"].strip(),
                "address": customer["address"].strip(),
                "total_amount": order_total,
                "payment_mode": customer["payment_mode"].strip(),
                "status": "Order Confirmed",
                "created_at": now_iso(),
            },
        )

        db.executemany(
            conn,
            "INSERT INTO order_items(order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
            [(order_id, pid, qty, price) for pid, qty, price in line_items],
        )

        for pid, qty, _ in line_items:
            db.execute(conn, "UPDATE products SET stock = stock - ? WHERE id = ?", [qty, pid])

    return jsonify({"ok": True, "order_id": order_id, "total": order_total, "message": "Order placed successfully."})


@app.post("/api/support-request")
def api_support_request():
    payload = request.get_json(silent=True) or {}
    required = ["customer_name", "email", "phone", "topic", "priority", "message"]
    missing = [field for field in required if not str(payload.get(field, "")).strip()]
    if missing:
        return jsonify({"ok": False, "message": "Please complete all required support fields.", "missing": missing}), 400

    with db.connect() as conn:
        ticket_id = db.insert_and_get_id(
            conn,
            "support_requests",
            {
                "customer_name": payload["customer_name"].strip(),
                "email": payload["email"].strip(),
                "phone": payload["phone"].strip(),
                "topic": payload["topic"].strip(),
                "priority": payload["priority"].strip(),
                "message": payload["message"].strip(),
                "status": "Open",
                "created_at": now_iso(),
            },
        )

    return jsonify({"ok": True, "ticket_id": ticket_id, "message": "Support ticket created successfully."})


@app.post("/api/contact-message")
def api_contact_message():
    payload = request.get_json(silent=True) or {}
    required = ["full_name", "email", "inquiry_type", "message"]
    missing = [field for field in required if not str(payload.get(field, "")).strip()]
    if missing:
        return jsonify({"ok": False, "message": "Please complete the contact form.", "missing": missing}), 400

    with db.connect() as conn:
        message_id = db.insert_and_get_id(
            conn,
            "contact_messages",
            {
                "full_name": payload["full_name"].strip(),
                "email": payload["email"].strip(),
                "phone": payload.get("phone", "").strip(),
                "city": payload.get("city", "").strip(),
                "inquiry_type": payload["inquiry_type"].strip(),
                "message": payload["message"].strip(),
                "status": "New",
                "created_at": now_iso(),
            },
        )

    return jsonify({"ok": True, "message_id": message_id, "message": "Your message has been received."})


@app.post("/api/customer/send-otp")
def api_customer_send_otp():
    payload = request.get_json(silent=True) or {}
    phone = str(payload.get("phone", "")).strip()

    if len(phone) < 10:
        return jsonify({"ok": False, "message": "Please enter a valid phone number."}), 400

    otp_code = generate_otp()
    expires_at = (datetime.now() + timedelta(minutes=5)).isoformat(timespec="seconds")

    with db.connect() as conn:
        db.insert_and_get_id(
            conn,
            "customer_otps",
            {
                "phone": phone,
                "otp_code": otp_code,
                "expires_at": expires_at,
                "used": 0,
                "created_at": now_iso(),
            },
        )

    return jsonify(
        {
            "ok": True,
            "message": "OTP sent successfully.",
            "demo_otp": otp_code,
            "expires_in_seconds": 300,
        }
    )


@app.post("/api/customer/verify-otp")
def api_customer_verify_otp():
    payload = request.get_json(silent=True) or {}
    phone = str(payload.get("phone", "")).strip()
    otp = str(payload.get("otp", "")).strip()

    if len(phone) < 10 or len(otp) != 6:
        return jsonify({"ok": False, "message": "Phone or OTP is invalid."}), 400

    with db.connect() as conn:
        row = db.fetchone(
            conn,
            "SELECT id, otp_code, expires_at, used FROM customer_otps WHERE phone = ? ORDER BY id DESC" + limit_suffix(1),
            [phone],
        )

        if row is None:
            return jsonify({"ok": False, "message": "No OTP found. Please request a new OTP."}), 400

        if int(row["used"]) == 1:
            return jsonify({"ok": False, "message": "OTP already used. Request a new one."}), 400

        if datetime.now() > parse_iso(str(row["expires_at"])):
            return jsonify({"ok": False, "message": "OTP expired. Request a new one."}), 400

        if not hmac.compare_digest(otp, str(row["otp_code"])):
            return jsonify({"ok": False, "message": "Incorrect OTP. Please try again."}), 400

        db.execute(conn, "UPDATE customer_otps SET used = 1 WHERE id = ?", [int(row["id"])])

    session["customer_phone"] = phone
    return jsonify({"ok": True, "message": "Login successful."})


@app.get("/api/customer/overview")
def api_customer_overview():
    phone = get_customer_phone()
    if not phone:
        return jsonify({"ok": False, "message": "Unauthorized"}), 401

    with db.connect() as conn:
        services = db.fetchall(
            conn,
            """
            SELECT id, laptop_brand, issue_type, urgency, estimated_price, status, created_at
            FROM service_requests
            WHERE phone = ?
            ORDER BY id DESC
            """
            + limit_suffix(20),
            [phone],
        )

        orders = db.fetchall(
            conn,
            """
            SELECT id, city, total_amount, payment_mode, status, created_at
            FROM orders
            WHERE phone = ?
            ORDER BY id DESC
            """
            + limit_suffix(20),
            [phone],
        )

    return jsonify({"ok": True, "phone": phone, "services": services, "orders": orders})


@app.route("/api/admin/overview")
def api_admin_overview():
    if not is_admin_authenticated():
        return jsonify({"ok": False, "message": "Unauthorized"}), 401

    with db.connect() as conn:
        recent_services = db.fetchall(
            conn,
            """
            SELECT id, customer_name, city, issue_type, urgency, estimated_price, status, created_at
            FROM service_requests
            ORDER BY id DESC
            """
            + limit_suffix(8),
        )

        recent_orders = db.fetchall(
            conn,
            """
            SELECT id, customer_name, city, total_amount, payment_mode, status, created_at
            FROM orders
            ORDER BY id DESC
            """
            + limit_suffix(8),
        )

    return jsonify({"stats": stats_payload(), "recent_services": recent_services, "recent_orders": recent_orders})


init_db()


if __name__ == "__main__":
    app.run(debug=True)
