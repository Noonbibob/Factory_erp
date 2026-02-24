from flask import Flask, render_template, request, redirect
import sqlite3
import os
from datetime import date

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ---------------- DATABASE ---------------- #

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # PRODUCTS (NO UNIQUE NAME NOW)
    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        stock INTEGER,
        dc_number TEXT,
        size TEXT
    )
    """)

    # DC
    c.execute("""
    CREATE TABLE IF NOT EXISTS dc (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dc_number TEXT,
        customer_name TEXT,
        dc_date TEXT,
        dc_type TEXT,
        image TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ---------------- #

@app.route("/")
def home():
    return render_template("home.html")

# ---------------- PRODUCTS ---------------- #

@app.route("/products", methods=["GET", "POST"])
def products():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        qty = int(request.form["stock"])
        action = request.form["action"]
        dc_number = request.form.get("dc_number")
        size = request.form.get("size")

        c.execute("""
            SELECT stock FROM products
            WHERE name=? AND dc_number=? AND size=?
        """, (name, dc_number, size))

        existing = c.fetchone()

        if existing:
            current_stock = existing[0]
            new_stock = current_stock + qty if action == "add" else current_stock - qty

            if new_stock <= 0:
                c.execute("""
                    DELETE FROM products
                    WHERE name=? AND dc_number=? AND size=?
                """, (name, dc_number, size))
            else:
                c.execute("""
                    UPDATE products
                    SET stock=?
                    WHERE name=? AND dc_number=? AND size=?
                """, (new_stock, name, dc_number, size))
        else:
            if action == "add":
                c.execute("""
                    INSERT INTO products (name, stock, dc_number, size)
                    VALUES (?, ?, ?, ?)
                """, (name, qty, dc_number, size))

        conn.commit()

    # ---------- FILTER LOGIC ----------

    filter_name = request.args.get("filter_name")
    filter_dc = request.args.get("filter_dc")
    filter_size = request.args.get("filter_size")

    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if filter_name:
        query += " AND name=?"
        params.append(filter_name)

    if filter_dc:
        query += " AND dc_number=?"
        params.append(filter_dc)

    if filter_size:
        query += " AND size=?"
        params.append(filter_size)

    c.execute(query, params)
    products = c.fetchall()

    # Get unique dropdown values
    c.execute("SELECT DISTINCT name FROM products")
    names = [row[0] for row in c.fetchall()]

    c.execute("SELECT DISTINCT dc_number FROM products")
    dcs = [row[0] for row in c.fetchall()]

    c.execute("SELECT DISTINCT size FROM products")
    sizes = [row[0] for row in c.fetchall()]

    conn.close()

    return render_template("products.html",
                           products=products,
                           names=names,
                           dcs=dcs,
                           sizes=sizes)

# ---------------- DC ---------------- #

@app.route("/dc", methods=["GET", "POST"])
def dc():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    search_number = request.args.get("search_number")
    search_date = request.args.get("search_date")

    if request.method == "POST":
        dc_number = request.form["dc_number"]
        customer_name = request.form["customer_name"]
        dc_type = request.form["dc_type"]
        dc_date = request.form.get("dc_date")

        if not dc_date:
            dc_date = date.today().strftime("%Y-%m-%d")

        image = request.files["image"]
        image_path = ""

        if image and image.filename != "":
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], image.filename)
            image.save(image_path)

        c.execute("""
            INSERT INTO dc (dc_number, customer_name, dc_date, dc_type, image)
            VALUES (?, ?, ?, ?, ?)
        """, (dc_number, customer_name, dc_date, dc_type, image_path))

        conn.commit()

    if search_number:
        c.execute("SELECT * FROM dc WHERE dc_number LIKE ?", ('%' + search_number + '%',))
    elif search_date:
        c.execute("SELECT * FROM dc WHERE dc_date=?", (search_date,))
    else:
        c.execute("SELECT * FROM dc")

    records = c.fetchall()
    conn.close()

    current_date = date.today().strftime("%Y-%m-%d")
    return render_template("dc.html", dc=records, current_date=current_date)

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app.run(debug=True)