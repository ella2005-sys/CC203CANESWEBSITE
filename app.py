import os
import random
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from config import get_db, close_db  # assumes you have config.py with get_db() / close_db()

app = Flask(__name__)
app.secret_key = 'flowershop_secret_key_v1'

# --- file upload config ---
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(fname):
    return '.' in fname and fname.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------- Database teardown ----------------
@app.teardown_appcontext
def teardown_db(exception):
    close_db()

# --- initialize DB and seed sample products (runs once on startup) ---
def init_db_and_seed():
    db_path = 'flowershop.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        description TEXT,
        image TEXT
    );

    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        fullname TEXT,
        shipping_address TEXT,
        contact_number TEXT,
        payment_method TEXT,
        total REAL,
        status TEXT DEFAULT 'Processing',
        tracking_number TEXT,
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    );
    """)
    conn.commit()
    conn.close()

# ---------------- Helpers ----------------
def get_product_by_id(pid):
    db = get_db()
    return db.execute('SELECT * FROM products WHERE id = ?', (pid,)).fetchone()

# ---------------- Public routes ----------------
@app.route('/')
def home():
    db = get_db()
    featured = db.execute('SELECT * FROM products LIMIT 3').fetchall()  # only 3
    return render_template('home.html', featured=featured, user=session.get('user'))



@app.route('/about')
def about():
    return render_template('about.html', user=session.get('user'))

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        if name and email and message:
            flash("Thank you for contacting us! We'll reply soon.", "success")
        else:
            flash("Please fill in all fields.", "danger")
    return render_template('contact.html', user=session.get('user'))

@app.route('/shop')
def shop():
    db = get_db()
    products = db.execute('SELECT * FROM products').fetchall()
    return render_template('shop.html', products=products, user=session.get('user'))

@app.route('/story')
def story():
    user = session.get('user')
    return render_template('story.html', user=user)

# ---------------- Cart routes ----------------
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user' not in session:
        flash("You must log in to add items to your cart.", "danger")
        return redirect(url_for('login'))
    cart = session.get('cart', {})
    pid = str(product_id)
    cart[pid] = cart.get(pid, 0) + 1
    session['cart'] = cart
    session.modified = True
    flash("Item added to cart!", "success")
    return redirect(request.referrer or url_for('shop'))

@app.route('/cart')
def cart():
    cart_dict = session.get('cart', {})
    items = []
    total = 0.0
    for pid, qty in cart_dict.items():
        prod = get_product_by_id(int(pid))
        if prod:
            item_total = prod['price'] * qty
            items.append({
                'id': prod['id'],
                'name': prod['name'],
                'price': prod['price'],
                'qty': qty,
                'item_total': round(item_total, 2),
                'image': prod['image']
            })
            total += item_total
    return render_template('cart.html', cart_items=items, total=round(total,2), user=session.get('user'))

@app.route('/increase/<int:product_id>')
def increase_item(product_id):
    cart = session.get('cart', {})
    pid = str(product_id)
    if pid in cart:
        cart[pid] += 1
        session['cart'] = cart
        session.modified = True
    return redirect(url_for('cart'))

@app.route('/decrease/<int:product_id>')
def decrease_item(product_id):
    cart = session.get('cart', {})
    pid = str(product_id)
    if pid in cart:
        if cart[pid] > 1:
            cart[pid] -= 1
        else:
            del cart[pid]
        session['cart'] = cart
        session.modified = True
    return redirect(url_for('cart'))

@app.route('/remove/<int:product_id>')
def remove_item(product_id):
    cart = session.get('cart', {})
    pid = str(product_id)
    if pid in cart:
        del cart[pid]
        session['cart'] = cart
        session.modified = True
    return redirect(url_for('cart'))

# ---------------- Checkout ----------------
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user' not in session:
        flash("You must log in to checkout.", "danger")
        return redirect(url_for('login'))

    cart_dict = session.get('cart', {})
    if not cart_dict:
        flash("Your cart is empty.", "warning")
        return redirect(url_for('shop'))

    cart_items = []
    total = 0.0
    for pid, qty in cart_dict.items():
        prod = get_product_by_id(int(pid))
        if prod:
            item_total = prod['price'] * qty
            cart_items.append({
                'id': prod['id'],
                'name': prod['name'],
                'qty': qty,
                'price': prod['price'],
                'item_total': round(item_total,2),
                'image': prod['image']
            })
            total += item_total

    if request.method == 'POST':
        fullname = request.form.get('fullname', '').strip()
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()
        payment = request.form.get('payment', '').strip()
        if fullname and address and phone and payment:
            db = get_db()
            cur = db.execute('SELECT id FROM users WHERE username = ?', (session.get('user'),))
            row = cur.fetchone()
            user_id = row['id'] if row else None

            tracking_number = "TRK" + str(random.randint(100000, 999999))
            created_at = datetime.utcnow().isoformat()

            db.execute('''
                INSERT INTO orders (user_id, fullname, shipping_address, contact_number, payment_method, total, status, tracking_number, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, fullname, address, phone, payment, round(total,2), 'Processing', tracking_number, created_at))
            db.commit()
            order_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

            for item in cart_items:
                db.execute('INSERT INTO order_items (order_id, product_id, quantity) VALUES (?, ?, ?)',
                           (order_id, item['id'], item['qty']))
            db.commit()

            session['last_order_tracking'] = tracking_number
            session.pop('cart', None)
            flash(f"Order placed! Tracking number: {tracking_number}", "success")
            return redirect(url_for('track_order'))
        else:
            flash("Please fill all checkout fields.", "danger")

    return render_template('checkout.html', cart_items=cart_items, total=round(total,2), user=session.get('user'))

# ---------------- Track order ----------------
@app.route('/track', methods=['GET', 'POST'])
def track_order():
    if request.method == 'POST':
        tnum = request.form.get('tracking_number', '').strip().upper()
        if not tnum:
            flash("Please input a tracking number.", "warning")
            return redirect(url_for('track_order'))
        db = get_db()
        order = db.execute('SELECT * FROM orders WHERE tracking_number = ?', (tnum,)).fetchone()
        if order:
            items = db.execute('''
                SELECT oi.quantity, p.name, p.price, p.image
                FROM order_items oi JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = ?
            ''', (order['id'],)).fetchall()
            return render_template('tracking_result.html', order=order, items=items, user=session.get('user'))
        flash("Tracking number not found.", "danger")
        return redirect(url_for('track_order'))

    last = session.get('last_order_tracking')
    order = None
    items = []
    if last:
        db = get_db()
        order = db.execute('SELECT * FROM orders WHERE tracking_number = ?', (last,)).fetchone()
        if order:
            items = db.execute('''
                SELECT oi.quantity, p.name, p.price, p.image
                FROM order_items oi JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = ?
            ''', (order['id'],)).fetchall()
    return render_template('track_order.html', order=order, items=items, user=session.get('user'))

# ---------------- Auth ----------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if not (username and email and password):
            flash("Please fill all fields.", "danger")
            return redirect(url_for('signup'))
        db = get_db()
        existing = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if existing:
            flash("Email already registered.", "danger")
        else:
            db.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, password))
            db.commit()
            flash("Signup successful. Please login.", "success")
            return redirect(url_for('login'))
    return render_template('signup.html', user=session.get('user'))

# ---------------- Admin credentials ----------------
ADMIN_EMAIL = "admin@mystiflora.com"
ADMIN_PASSWORD = "Admin123"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        if email == ADMIN_EMAIL.lower() and password == ADMIN_PASSWORD:
            session['admin'] = True
            flash("Welcome, admin.", "success")
            return redirect(url_for('admin_dashboard'))
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
        if user:
            session['user'] = user['username']
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for('shop'))
        flash("Invalid credentials.", "danger")
    return render_template('login.html', user=session.get('user'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('last_order_tracking', None)
    flash("Logged out.", "success")
    return redirect(url_for('home'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    flash("Admin logged out.", "success")
    return redirect(url_for('login'))

# ---------------- Admin: dashboard, orders, product CRUD ----------------
@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('admin'):
        flash("Please login as admin.", "danger")
        return redirect(url_for('login'))

    db = get_db()
    search = request.form.get('search', '').strip().lower()
    if search:
        orders = db.execute('''
            SELECT * FROM orders
            WHERE lower(fullname) LIKE ? OR contact_number LIKE ? OR tracking_number LIKE ?
            ORDER BY created_at DESC
        ''', (f'%{search}%', f'%{search}%', f'%{search}%')).fetchall()
    else:
        orders = db.execute('SELECT * FROM orders ORDER BY created_at DESC').fetchall()

    products = db.execute('SELECT * FROM products ORDER BY id DESC').fetchall()
    return render_template('admin_dashboard.html', orders=orders, products=products, user=session.get('user'), search=search)

# ---------------- Admin: order details ----------------
@app.route('/admin/order/<int:order_id>', methods=['GET', 'POST'])
def admin_order_details(order_id):
    if not session.get('admin'):
        flash("Please login as admin.", "danger")
        return redirect(url_for('login'))

    db = get_db()
    order = db.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for('admin_dashboard'))

    items = db.execute('''
        SELECT oi.quantity, p.name, p.price
        FROM order_items oi JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    ''', (order_id,)).fetchall()

    if request.method == 'POST':
        fullname = request.form.get('fullname', '').strip()
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()
        status = request.form.get('status', '').strip()
        db.execute('UPDATE orders SET fullname = ?, shipping_address = ?, contact_number = ?, status = ? WHERE id = ?',
                   (fullname, address, phone, status, order_id))
        db.commit()
        flash("Order updated.", "success")
        return redirect(url_for('admin_order_details', order_id=order_id))

    return render_template('admin_order_details.html', order=order, items=items, user=session.get('user'))

# ---------------- Admin: add/edit/delete product ----------------
@app.route('/admin/add_product', methods=['GET', 'POST'])
def admin_add_product():
    if not session.get('admin'):
        flash("Please login as admin.", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        price = request.form.get('price', '').strip()
        desc = request.form.get('desc', '').strip()
        file = request.files.get('image')

        if not (name and price and desc):
            flash("Please fill all fields.", "danger")
            return redirect(url_for('admin_add_product'))

        filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            flash("Please upload a valid image file (png/jpg/jpeg/gif).", "danger")
            return redirect(url_for('admin_add_product'))

        db = get_db()
        try:
            db.execute('INSERT INTO products (name, price, description, image) VALUES (?, ?, ?, ?)',
                       (name, float(price), desc, filename))
            db.commit()
            flash("Product added.", "success")
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            flash(f"Error adding product: {e}", "danger")
            return redirect(url_for('admin_add_product'))

    return render_template('admin_add_product.html', user=session.get('user'))

@app.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    if not session.get('admin'):
        flash("Please login as admin.", "danger")
        return redirect(url_for('login'))

    db = get_db()
    prod = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not prod:
        flash("Product not found.", "danger")
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        price = request.form.get('price', '').strip()
        desc = request.form.get('desc', '').strip()
        file = request.files.get('image')

        filename = prod['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        try:
            db.execute('UPDATE products SET name = ?, price = ?, description = ?, image = ? WHERE id = ?',
                       (name, float(price), desc, filename, product_id))
            db.commit()
            flash("Product updated.", "success")
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            flash(f"Error updating product: {e}", "danger")
            return redirect(url_for('admin_edit_product', product_id=product_id))

    return render_template('admin_edit_product.html', product=prod, user=session.get('user'))

@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
def admin_delete_product(product_id):
    if not session.get('admin'):
        flash("Please login as admin.", "danger")
        return redirect(url_for('login'))
    db = get_db()
    prod = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not prod:
        flash("Product not found.", "danger")
        return redirect(url_for('admin_dashboard'))
    try:
        image_name = prod['image']
        if image_name:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_name)
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except Exception:
                    pass
        db.execute('DELETE FROM products WHERE id = ?', (product_id,))
        db.execute('DELETE FROM order_items WHERE product_id = ?', (product_id,))
        db.commit()
        flash("Product deleted.", "success")
    except Exception as e:
        flash(f"Error deleting product: {e}", "danger")
    return redirect(url_for('admin_dashboard'))

# ---------------- Run app ----------------
if __name__ == '__main__':
    init_db_and_seed()  # Ensure DB is created on first run
    app.run(debug=True)
