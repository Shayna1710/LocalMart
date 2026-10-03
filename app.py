from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
mysql = MySQL(app)

@app.context_processor
def inject_cart_count():
    cart = session.get("cart", {})
    return {"cart_count": sum(max(0, int(q)) for q in cart.values()), "wishlist_count": wishlist_count()}

# -----------------------------
# Small database helper
# -----------------------------
def query(sql, params=(), one=False):
    # Parameterized SQL reduces the risk of SQL injection.
    cur = mysql.connection.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return rows[0] if one and rows else (rows if not one else None)

def initialize_demo_admin():
    # Creates the academic demo admin if it does not already exist.
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM users WHERE email=%s", ("admin@localmart.com",))
    exists = cur.fetchone()
    if not exists:
        cur.execute(
            "INSERT INTO users(name,email,password_hash,role) VALUES(%s,%s,%s,'admin')",
            ("LocalMart Admin", "admin@localmart.com", generate_password_hash("admin123"))
        )
        mysql.connection.commit()
    cur.close()

# -----------------------------
# Authentication decorators
# -----------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access is required.", "danger")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

@app.before_request
def prepare_app():
    # The schema must be imported before the first request.
    if request.endpoint != "static":
        try:
            initialize_demo_admin()
        except Exception:
            # Database setup errors are shown naturally when a database route is used.
            pass

# -----------------------------
# Public/customer pages
# -----------------------------
@app.route("/")
def index():
    products = query("""SELECT p.*, c.name AS category_name
                        FROM products p LEFT JOIN categories c ON c.id=p.category_id
                        WHERE p.stock > 0 ORDER BY p.id DESC LIMIT 12""")
    categories = query("SELECT * FROM categories ORDER BY name")
    return render_template("index.html", products=products, categories=categories)

@app.route("/products")
def products():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    sql = """SELECT p.*, c.name AS category_name
             FROM products p LEFT JOIN categories c ON c.id=p.category_id
             WHERE 1=1"""
    params = []
    if search:
        sql += " AND (p.name LIKE %s OR p.description LIKE %s)"
        params += [f"%{search}%", f"%{search}%"]
    if category.isdigit():
        sql += " AND p.category_id=%s"
        params.append(int(category))
    sort = request.args.get("sort", "newest")
    order_map = {"newest":"p.id DESC", "price_low":"p.price ASC", "price_high":"p.price DESC", "name":"p.name ASC", "popular":"p.id DESC"}
    sql += " ORDER BY " + order_map.get(sort, "p.id DESC")
    rows = query(sql, params)
    categories = query("SELECT * FROM categories ORDER BY name")
    return render_template("products.html", products=rows, categories=categories,
                           search=search, selected_category=category, selected_sort=sort)

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = query("""SELECT p.*, c.name AS category_name
                       FROM products p LEFT JOIN categories c ON c.id=p.category_id
                       WHERE p.id=%s""", (product_id,), one=True)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for("products"))
    related = query("""SELECT p.*, c.name AS category_name FROM products p
                     LEFT JOIN categories c ON c.id=p.category_id
                     WHERE p.category_id=%s AND p.id<>%s AND p.stock>0 ORDER BY p.id DESC LIMIT 4""",
                    (product["category_id"], product_id))
    reviews = query("""SELECT r.rating,r.comment,r.created_at,u.name FROM reviews r
                      JOIN users u ON u.id=r.user_id WHERE r.product_id=%s ORDER BY r.id DESC""", (product_id,))
    rating = query("SELECT COALESCE(AVG(rating),0) AS avg_rating, COUNT(*) AS review_count FROM reviews WHERE product_id=%s", (product_id,), one=True)
    wished = bool(session.get("user_id") and query("SELECT id FROM wishlists WHERE user_id=%s AND product_id=%s", (session["user_id"], product_id), one=True))
    return render_template("product_detail.html", product=product, related=related, reviews=reviews, rating=rating, wished=wished)

# -----------------------------
# Registration/login
# -----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        if not name or not email or len(password) < 6:
            flash("Enter valid details. Password must contain at least 6 characters.", "danger")
            return redirect(url_for("register"))
        if query("SELECT id FROM users WHERE email=%s", (email,), one=True):
            flash("Email is already registered.", "warning")
            return redirect(url_for("register"))
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name,email,password_hash,role) VALUES(%s,%s,%s,'customer')",
                    (name, email, generate_password_hash(password)))
        mysql.connection.commit()
        cur.close()
        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = query("SELECT * FROM users WHERE email=%s", (email,), one=True)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["role"] = user["role"]
            flash("Login successful.", "success")
            return redirect(url_for("admin_dashboard" if user["role"] == "admin" else "index"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

# -----------------------------
# Shopping cart
# -----------------------------
def wishlist_count():
    if not session.get("user_id"):
        return 0
    try:
        row = query("SELECT COUNT(*) AS n FROM wishlists WHERE user_id=%s", (session["user_id"],), one=True)
        return int(row["n"]) if row else 0
    except Exception:
        return 0

def cart_items():
    cart = session.get("cart", {})
    if not cart:
        return [], 0
    ids = [int(pid) for pid in cart.keys()]
    placeholders = ",".join(["%s"] * len(ids))
    rows = query(f"SELECT id,name,price,stock,image_url FROM products WHERE id IN ({placeholders})", ids)
    items, total = [], 0
    for row in rows:
        qty = min(max(1, int(cart.get(str(row["id"]), 1))), int(row["stock"]))
        line_total = float(row["price"]) * qty
        items.append({"product": row, "quantity": qty, "line_total": line_total})
        total += line_total
    return items, total

@app.route("/cart")
def cart():
    items, total = cart_items()
    return render_template("cart.html", items=items, total=total)

@app.route("/cart/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    product = query("SELECT id,name,stock FROM products WHERE id=%s", (product_id,), one=True)
    if not product or product["stock"] <= 0:
        flash("Product is unavailable.", "danger")
        return redirect(url_for("products"))
    qty = max(1, int(request.form.get("quantity", 1)))
    cart = session.get("cart", {})
    cart[str(product_id)] = min(int(cart.get(str(product_id), 0)) + qty, int(product["stock"]))
    session["cart"] = cart
    flash("Product added to cart.", "success")
    return redirect(request.referrer or url_for("products"))

@app.route("/cart/update", methods=["POST"])
def update_cart():
    cart = session.get("cart", {})
    for pid in list(cart.keys()):
        field = f"qty_{pid}"
        if field in request.form:
            qty = max(0, int(request.form[field]))
            product = query("SELECT stock FROM products WHERE id=%s", (int(pid),), one=True)
            if qty == 0 or not product:
                cart.pop(pid, None)
            else:
                cart[pid] = min(qty, int(product["stock"]))
    session["cart"] = cart
    flash("Cart updated.", "success")
    return redirect(url_for("cart"))

# -----------------------------
# Checkout and order tracking
# -----------------------------
@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    items, total = cart_items()
    if not items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("products"))
    if request.method == "POST":
        address = request.form["address"].strip()
        payment_method = request.form.get("payment_method", "Cash on Delivery")
        coupon = request.form.get("coupon", "").strip().upper()
        if len(address) < 10:
            flash("Please enter a complete delivery address.", "danger")
            return redirect(url_for("checkout"))
        discount = 0
        if coupon:
            c = query("SELECT * FROM coupons WHERE code=%s AND active=1 AND (expires_at IS NULL OR expires_at>=NOW())", (coupon,), one=True)
            if c:
                discount = min(float(c["discount_amount"]), total) if c["discount_type"] == "flat" else total * float(c["discount_amount"]) / 100
            else:
                flash("Invalid or expired coupon code.", "warning")
                return redirect(url_for("checkout"))
        final_total = max(0, total - discount)
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO orders(user_id,total_amount,address,status,payment_method,coupon_code,discount_amount) VALUES(%s,%s,%s,'Pending',%s,%s,%s)",
                    (session["user_id"], final_total, address, payment_method, coupon or None, discount))
        order_id = cur.lastrowid
        for item in items:
            p = item["product"]
            cur.execute("""INSERT INTO order_items(order_id,product_id,quantity,unit_price)
                           VALUES(%s,%s,%s,%s)""",
                        (order_id, p["id"], item["quantity"], p["price"]))
            cur.execute("UPDATE products SET stock=stock-%s WHERE id=%s AND stock >= %s",
                        (item["quantity"], p["id"], item["quantity"]))
        mysql.connection.commit()
        cur.close()
        session["cart"] = {}
        flash(f"Order #{order_id} placed successfully.", "success")
        return redirect(url_for("orders"))
    return render_template("checkout.html", items=items, total=total)

@app.route("/orders")
@login_required
def orders():
    rows = query("SELECT * FROM orders WHERE user_id=%s ORDER BY created_at DESC",
                 (session["user_id"],))
    return render_template("orders.html", orders=rows)

@app.route("/order/<int:order_id>")
@login_required
def order_detail(order_id):
    order = query("""SELECT o.*,u.name,u.email FROM orders o JOIN users u ON u.id=o.user_id
                     WHERE o.id=%s AND o.user_id=%s""",
                  (order_id, session["user_id"]), one=True)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("orders"))
    items = query("""SELECT oi.*,p.name FROM order_items oi JOIN products p ON p.id=oi.product_id
                     WHERE oi.order_id=%s""", (order_id,))
    return render_template("order_detail.html", order=order, items=items)

# -----------------------------
# Marketplace extras
# -----------------------------
@app.route("/wishlist")
@login_required
def wishlist():
    rows = query("""SELECT p.*,c.name AS category_name FROM wishlists w
                    JOIN products p ON p.id=w.product_id LEFT JOIN categories c ON c.id=p.category_id
                    WHERE w.user_id=%s ORDER BY w.id DESC""", (session["user_id"],))
    return render_template("wishlist.html", products=rows)

@app.route("/wishlist/toggle/<int:product_id>", methods=["POST"])
@login_required
def toggle_wishlist(product_id):
    existing = query("SELECT id FROM wishlists WHERE user_id=%s AND product_id=%s", (session["user_id"], product_id), one=True)
    cur=mysql.connection.cursor()
    if existing:
        cur.execute("DELETE FROM wishlists WHERE id=%s", (existing["id"],)); flash("Removed from wishlist.", "info")
    else:
        cur.execute("INSERT IGNORE INTO wishlists(user_id,product_id) VALUES(%s,%s)", (session["user_id"], product_id)); flash("Added to wishlist.", "success")
    mysql.connection.commit(); cur.close()
    return redirect(request.referrer or url_for("products"))

@app.route("/product/<int:product_id>/review", methods=["POST"])
@login_required
def add_review(product_id):
    rating=int(request.form.get("rating",5)); comment=request.form.get("comment","").strip()
    if rating<1 or rating>5 or len(comment)<3:
        flash("Please provide a rating and short review.", "danger"); return redirect(url_for("product_detail",product_id=product_id))
    cur=mysql.connection.cursor(); cur.execute("INSERT INTO reviews(product_id,user_id,rating,comment) VALUES(%s,%s,%s,%s) ON DUPLICATE KEY UPDATE rating=VALUES(rating),comment=VALUES(comment)", (product_id,session["user_id"],rating,comment)); mysql.connection.commit(); cur.close()
    flash("Thanks for your review!", "success"); return redirect(url_for("product_detail",product_id=product_id))

@app.route("/account")
@login_required
def account():
    user=query("SELECT id,name,email,created_at FROM users WHERE id=%s", (session["user_id"],), one=True)
    stats=query("SELECT COUNT(*) AS orders,COALESCE(SUM(total_amount),0) AS spent FROM orders WHERE user_id=%s AND status<>'Cancelled'", (session["user_id"],), one=True)
    return render_template("account.html", user=user, stats=stats)

@app.route("/account/update", methods=["POST"])
@login_required
def update_account():
    name=request.form.get("name","").strip()
    if not name: flash("Name is required.","danger"); return redirect(url_for("account"))
    cur=mysql.connection.cursor(); cur.execute("UPDATE users SET name=%s WHERE id=%s", (name,session["user_id"])); mysql.connection.commit(); cur.close(); session["user_name"]=name
    flash("Profile updated.","success"); return redirect(url_for("account"))

# -----------------------------
# Admin module
# -----------------------------
@app.route("/admin")
@admin_required
def admin_dashboard():
    stats = {
        "products": query("SELECT COUNT(*) AS n FROM products", one=True)["n"],
        "customers": query("SELECT COUNT(*) AS n FROM users WHERE role='customer'", one=True)["n"],
        "orders": query("SELECT COUNT(*) AS n FROM orders", one=True)["n"],
        "sales": query("SELECT COALESCE(SUM(total_amount),0) AS n FROM orders WHERE status <> 'Cancelled'", one=True)["n"],
    }
    recent = query("""SELECT o.*,u.name FROM orders o JOIN users u ON u.id=o.user_id
                      ORDER BY o.created_at DESC LIMIT 10""")
    return render_template("admin/dashboard.html", stats=stats, recent=recent)

@app.route("/admin/products", methods=["GET", "POST"])
@admin_required
def admin_products():
    if request.method == "POST":
        cur = mysql.connection.cursor()
        cur.execute("""INSERT INTO products(name,description,price,stock,category_id,image_url)
                       VALUES(%s,%s,%s,%s,%s,%s)""",
                    (request.form["name"].strip(), request.form["description"].strip(),
                     float(request.form["price"]), int(request.form["stock"]),
                     int(request.form["category_id"]), request.form.get("image_url","").strip()))
        mysql.connection.commit()
        cur.close()
        flash("Product added.", "success")
        return redirect(url_for("admin_products"))
    products = query("""SELECT p.*,c.name AS category_name FROM products p
                        LEFT JOIN categories c ON c.id=p.category_id ORDER BY p.id DESC""")
    categories = query("SELECT * FROM categories ORDER BY name")
    return render_template("admin/products.html", products=products, categories=categories)

@app.route("/admin/products/delete/<int:product_id>", methods=["POST"])
@admin_required
def delete_product(product_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM products WHERE id=%s", (product_id,))
    mysql.connection.commit()
    cur.close()
    flash("Product deleted.", "success")
    return redirect(url_for("admin_products"))

@app.route("/admin/orders")
@admin_required
def admin_orders():
    rows = query("""SELECT o.*,u.name,u.email FROM orders o JOIN users u ON u.id=o.user_id
                    ORDER BY o.created_at DESC""")
    return render_template("admin/orders.html", orders=rows)

@app.route("/admin/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def update_order_status(order_id):
    status = request.form["status"]
    allowed = {"Pending","Confirmed","Packed","Shipped","Delivered","Cancelled"}
    if status not in allowed:
        flash("Invalid order status.", "danger")
        return redirect(url_for("admin_orders"))
    cur = mysql.connection.cursor()
    cur.execute("UPDATE orders SET status=%s WHERE id=%s", (status, order_id))
    mysql.connection.commit()
    cur.close()
    flash("Order status updated.", "success")
    return redirect(url_for("admin_orders"))

@app.route("/admin/customers")
@admin_required
def admin_customers():
    customers = query("""SELECT id,name,email,created_at FROM users
                         WHERE role='customer' ORDER BY id DESC""")
    return render_template("admin/customers.html", customers=customers)

@app.route("/admin/reports")
@admin_required
def admin_reports():
    monthly = query("""SELECT DATE_FORMAT(created_at,'%Y-%m') AS month,COUNT(*) AS orders,
                              COALESCE(SUM(total_amount),0) AS sales
                       FROM orders WHERE status <> 'Cancelled'
                       GROUP BY DATE_FORMAT(created_at,'%Y-%m') ORDER BY month DESC""")
    return render_template("admin/reports.html", monthly=monthly)

@app.route("/health")
def health():
    return jsonify({"status":"ok","application":"LocalMart"})

if __name__ == "__main__":
    # Debug mode is suitable for college development only.
    app.run(debug=True)
