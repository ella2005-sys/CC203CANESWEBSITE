import sqlite3
import os
from datetime import datetime
from flask import Flask, render_template, request, session, redirect, url_for, flash, g

# ---------------- Initialization ----------------
app = Flask(__name__)
app.secret_key = 'flowershop_secret_key_v2'

UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---------------- Database Helpers ----------------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('flowershop.db')
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(exception=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def allowed_file(fname):
    return '.' in fname and fname.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_product_by_id(pid):
    db = get_db()
    return db.execute('SELECT * FROM products WHERE id = ?', (pid,)).fetchone()

# ---------------- Occasion Products ----------------
occasion_products_data = {
    'wedding': [
        {'id': 1, 'name': 'The Rosé All Day Bouquet', 'description': 'A charming and lush arrangement...', 'price': 1899, 'image': 'wedding1.jpeg'},
        {'id': 2, 'name': 'Holly Kisses', 'description': 'A charming bouquet of whites and pinks...', 'price': 2399, 'image': 'wedding2.jpeg'},
        {'id': 3, 'name': 'The Ethereal Spire Bouquet',
         'description': 'An elegant, clean, and modern arrangement of pristine White Calla Lilies given an ethereal softness by delicate, whispering airy grass and filler.',
         'price': 1299, 'image': 'wedding3.jpeg'},
        {'id': 4, 'name': 'The Ivory Stream',
         'description': 'A modern study in purity, featuring sleek, sculptural White Calla Lilies softened by a whisper of airy, delicate grasses.',
         'price': 1599, 'image': 'wedding4.jpeg'},
        {'id': 5, 'name': 'The Cloud Nine Bouquet',
         'description': 'A voluminous, romantic clutch of lush white Peonies and Garden Roses, designed to be as soft and intoxicating as a summer cloud.',
         'price': 2599, 'image': 'wedding5.jpeg'},
        {'id': 6, 'name': 'The Spring Dream Bouquet',
         'description': 'A voluminous, highly textured mix of blush Ranunculus, pale pink Tulips, and delicate Sweet Peas, creating an incredibly romantic, layered, and airy presentation.',
         'price': 3679, 'image': 'wedding6.jpeg'},
        {'id': 7, 'name': 'The Winter Tide Bouquet',
         'description': 'A breathtaking cascading arrangement of white Lilies and Roses, accented with cool, icy-blue Thistle and silvery Dusty Miller foliage, creating a dramatic and elegant "something blue" statement.',
         'price': 2500, 'image': 'wedding7.jpeg'},
        {'id': 8, 'name': 'The First Blush Bouquet',
         'description': 'A charming and crisp combination of blush pink Tulips and pure White Calla Lilies, beautifully framed by delicate, feathery Astilbe, for a look that is both modern and sweetly romantic.',
         'price': 2800, 'image': 'wedding8.jpeg'},
],
    'birthday': [
        {'id': 101, 'name': 'Island Dusk', 'description': 'Lush pink lilies...', 'price': 2499, 'image': 'bday1.jpeg'},
         {'id': 102, 'name': 'Ivory Whisper',
             'description': 'A timeless bouquet of exquisite, creamy white roses nestled amongst rich magnolia leaves, wrapped in neutral kraft paper and tied with a sophisticated forest-green satin ribbon, conveying purity and deep respect.',
             'price': 4899, 'image': 'bday2.jpeg'},
            {'id': 103, 'name': 'Sweet Duet',
             'description': 'A charming mix of rich burgundy spray roses and large, creamy white roses, complemented by lush foliage and wrapped in soft pink and white paper, finished with a passionate red satin bow.',
             'price': 3600, 'image': 'bday3.jpeg'},
            {'id': 104, 'name': 'Blush Bloom',
             'description': 'A tender arrangement combining ruffled pink carnations, soft blush roses, and delicate white Alstroemeria, surrounded by abundant greenery and beautifully wrapped in coordinating pink paper with a satin ribbon.',
             'price': 4500, 'image': 'bday4.jpeg'},

    ],
    'anniversary': [
        {'id': 1001, 'name': 'Crimson Bouquet', 'description': 'Fresh crimson roses...', 'price': 3499, 'image': 'a1.jpeg'},
        {'id': 1002, 'name': 'Starlight Serenade',
'description': 'An ethereal and enchanting mix, this bouquet features the majestic, freckled petals of Pink Stargazer Lilies, harmoniously surrounded by a soft cloud of delicate blush and cream roses. Accented with sprigs of pure white stock flowers, this arrangement is wrapped in layers of pale pink and white, capturing the feeling of a dreamy, romantic evening. Perfect for celebrating purity, prosperity, and profound joy.',
'price': 3500, 'image': 'a2.jpeg'},
        {'id': 1003, 'name': 'Opulent Dream',
         'description': 'A breathtaking, grand statement piece overflowing with hundreds of champagne and soft blush roses, creating a spectacular ombre dome. Encased in voluminous layers of sheer white mesh, crinkle paper, and petal-pink matte wrapping, this bouquet is the ultimate expression of admiration, extravagance, and endless love.',
         'price': 3500, 'image': 'a3.jpeg'},
        {'id': 1004, 'name': 'Fairy Dust',
         'description': 'A dreamy ethereal bouquet. Cream pink roses are surrounded by Babys Breath delicate butterfly accents. An expression of grace gentle affection.',
         'price': 4500, 'image': 'a4.jpeg'},
    ],
    'graduation': [
        {'id': 10001, 'name': 'Achievement Teddy', 'description': 'A celebratory bouquet...', 'price': 5500, 'image': 'g1.jpg'},
{'id': 10002, 'name': 'Rustic Rhapsody',
             'description': 'A sophisticated, highly textural bouquet blending deep mauve roses, striking crimson gladioli, and soft pink carnations, accented with pale blue and white fillers and wispy grass, wrapped elegantly in cream and dark charcoal paper.',
             'price': 3800, 'image': 'g2.jpg'},
            {'id': 10003, 'name': 'Pearl Petal Promise',
             'description': 'A luxurious, romantic arrangement featuring large pink lilies dusted with pearlescent accents, nestled among creamy white and blush pink roses and large white tulip-like blooms, finished with a heart-jeweled pink ribbon.',
             'price': 4700, 'image': 'g3.jpg'},
            {'id': 10004, 'name': 'Minted Morning',
             'description': 'A sophisticated, monochromatic bouquet featuring crisp white roses and unique pale mint-green blooms, accented by tall, spiky green filler, all wrapped in textured sage-green paper for an elegant, contemporary look.',
             'price': 4800, 'image': 'g4.jpg'},
    ],
    'valentines': [
        {'id': 100001, 'name': 'Hearts Desire', 'description': 'Deep velvet red roses...', 'price': 4890, 'image': 'v1.jpg'},
{'id': 100002, 'name': 'valentines Vow',
             'description': 'A lavish and layered bouquet overflowing with deep red roses, light pink spray roses, and ruffled carnations, framed by bright red decorative fringe and accented with a custom ribbon declaring, "Be my Valentine?"',
             'price': 6000, 'image': 'v2.jpg'},
            {'id': 100003, 'name': 'Fuschia Fascination',
             'description': 'A vibrant arrangement of deep fuchsia roses accented with delicate white fillers and subtle greenery, dramatically wrapped in layers of bold and soft pink paper and tied with a matching ribbon.',
             'price': 7000, 'image': 'v3.jpg'},
            {'id': 100004, 'name': 'Pure Heart Grande',
             'description': 'An extravagant, dome-shaped heart crafted from hundreds of pristine, creamy white roses, set in a clear vase with exposed green stems and finished with a delicate pink satin ribbon—a powerful symbol of pure, deep love and admiration',
             'price': 5900, 'image': 'v4.jpg'},
    ]
}

# ---------------- Initialize DB ----------------
def init_db_and_seed():
    conn = sqlite3.connect('flowershop.db')
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
            image TEXT,
            stock INTEGER NOT NULL DEFAULT 0
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

# ---------------- Public Routes ----------------
@app.route('/')
def home():
    db = get_db()
    featured = db.execute('SELECT * FROM products LIMIT 3').fetchall()
    return render_template('home.html', featured=featured, user=session.get('user'))

@app.route('/shop')
def shop():
    db = get_db()
    products = db.execute('SELECT * FROM products').fetchall()
    return render_template('shop.html', products=products, user=session.get('user'))

@app.route('/occasions/<category>')
def show_occasion(category):
    category = category.lower()
    if category not in occasion_products_data:
        flash(f"Category '{category}' not found.", "danger")
        return redirect(url_for('shop'))
    products_list = occasion_products_data[category]
    return render_template('occasion.html', occasion_products=products_list,
                           occasion_type=category.title(), user=session.get('user'))

@app.route('/story')
def story():
    return render_template('story.html', user=session.get('user'))

@app.route('/about')
def about():
    return render_template('about.html', user=session.get('user'))

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        message = request.form.get('message', '').strip()
        if name and email and message:
            flash("Thank you for contacting us! We'll reply soon.", "success")
        else:
            flash("Please fill in all fields.", "danger")
    return render_template('contact.html', user=session.get('user'))

@app.route('/find_my_flora')
def find_my_flora():
    return render_template('quiz.html', user=session.get('user'))

# ---------------- Auth Routes ----------------
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

# ---------------- Cart & Checkout ----------------
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    # Get quantity from form
    quantity = request.form.get('quantity', 1)
    try:
        quantity = int(quantity)
        if quantity < 1:
            quantity = 1
    except:
        quantity = 1

    # Ensure user is logged in
    if 'user' not in session:
        flash("Please login first to add to cart.", "warning")
        return redirect(url_for('login'))

    # Get product from database
    conn = get_db()
    conn.row_factory = sqlite3.Row  # This makes rows behave like dictionaries
    cur = conn.cursor()
    cur.execute("SELECT id, name, price, image FROM products WHERE id = ?", (product_id,))
    prod = cur.fetchone()

    # If product not found in DB, try your additional occasion_products_data
    if not prod:
        occasion_products_flat = []
        for products_list in occasion_products_data.values():
            occasion_products_flat.extend(products_list)
        prod = next((p for p in occasion_products_flat if p['id'] == product_id), None)
        if not prod:
            flash("Product not found.", "danger")
            return redirect(request.referrer or url_for('shop'))

    # Access product fields correctly
    if isinstance(prod, sqlite3.Row):  # From database
        product_data = {
            'id': 1,
            'name': 'The Rose All Day Bouquet',
            'price': 1899,
            'image': 'wedding/wedding1.jpeg',
            'quantity': quantity
        }

        product_data = {
            'id': 2,
            'name': 'Holly Kisses',
            'price': 2399,
            'image': 'wedding/wedding2.jpeg',
            'quantity': quantity
        }

        product_data = {
            'id': 4,
            'name': 'The Ivory Stream',
            'price': 1599,
            'image': 'wedding/wedding4.jpeg',
            'quantity': quantity
        }

        product_data = {
            'id': 5,
            'name': 'The Cloud Nine Bouquet',
            'price': 1599,
            'image': 'wedding/wedding4.jpeg',
            'quantity': quantity
        }
    else:  # From your occasion_products_data
        product_data = {
            'id': prod['id'],
            'name': prod['name'],
            'price': prod['price'],
            'image': prod['image'],
            'quantity': quantity
        }

    # Add/update cart in session
    cart = session.get('cart', {})
    pid = str(product_data['id'])
    if pid in cart:
        cart[pid]['quantity'] += quantity
    else:
        cart[pid] = product_data

    session['cart'] = cart
    session.modified = True

    flash(f"Added {quantity} x {product_data['name']} to cart!", "success")
    return redirect(request.referrer or url_for('shop'))

@app.route('/account')
def account():
    if 'user' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    # Fetch orders for logged-in user
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM orders WHERE user_id = ?", (1,))  # Replace 1 with session user id
    orders = cur.fetchall()

    return render_template('account.html', orders=orders)



@app.route('/cart')
def cart():
    if 'user' not in session:
        flash("Please log in first to view your cart.", "warning")
        return redirect(url_for('login'))

    cart_items = []
    total = 0.0
    cart = session.get('cart', {})

    for pid, item in cart.items():
        item_total = item['price'] * item['quantity']
        cart_items.append({
            'id': item['id'],
            'name': item['name'],
            'price': item['price'],
            'qty': item['quantity'],
            'item_total': round(item_total, 2),
            'image': item['image']
        })
        total += item_total

    shipping_cost = 5.0
    grand_total = total + shipping_cost

    return render_template('cart.html',
                           cart_items=cart_items,
                           subtotal=round(total, 2),
                           shipping_cost=shipping_cost,
                           total=round(grand_total, 2),
                           user=session.get('user'))

@app.route('/increase/<int:product_id>')
def increase_item(product_id):
    cart = session.get('cart', {})
    pid = str(product_id)
    if pid in cart:
        cart[pid]['quantity'] += 1
        session['cart'] = cart
        session.modified = True
    return redirect(url_for('cart'))

@app.route('/decrease/<int:product_id>')
def decrease_item(product_id):
    cart = session.get('cart', {})
    pid = str(product_id)
    if pid in cart:
        if cart[pid]['quantity'] > 1:
            cart[pid]['quantity'] -= 1
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


@app.route('/checkout', methods=['GET'])
def checkout():
    if 'user' not in session:
        flash("Please login first to checkout.", "warning")
        return redirect(url_for('login'))

    cart_items = []
    total = 0.0
    cart = session.get('cart', {})

    for pid, item in cart.items():
        item_total = item['price'] * item['quantity']
        cart_items.append({
            'id': item['id'],
            'name': item['name'],
            'price': item['price'],
            'qty': item['quantity'],
            'item_total': round(item_total, 2)
        })
        total += item_total

    shipping_cost = 5.0
    grand_total = total + shipping_cost

    return render_template('checkout.html',
                           cart_items=cart_items,
                           subtotal=round(total,2),
                           shipping_cost=shipping_cost,
                           total=round(grand_total,2),
                           user=session.get('user'))



@app.route('/process_checkout', methods=['POST'])
def process_checkout():
    if 'user' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))

    cart = session.get('cart', {})
    if not cart:
        flash("Your cart is empty.", "warning")
        return redirect(url_for('shop'))

    fullname = request.form.get('fullname')
    address = request.form.get('address')
    contact = request.form.get('contact')
    payment = request.form.get('payment')

    total = sum(item['price']*item['quantity'] for item in cart.values())
    shipping_cost = 5.0
    grand_total = total + shipping_cost

    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO orders (user_id, fullname, shipping_address, contact_number, payment_method, total, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (1, fullname, address, contact, payment, grand_total, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    order_id = cur.lastrowid

    for item in cart.values():
        cur.execute("INSERT INTO order_items (order_id, product_id, quantity) VALUES (?, ?, ?)",
                    (order_id, item['id'], item['quantity']))
    db.commit()

    session.pop('cart', None)
    flash(f"Order placed successfully! Order ID: {order_id}", "success")
    return redirect(url_for('shop'))

from functools import wraps

# Decorator to require admin login
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session.get('role') != 'admin':
            flash("Admin access required.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ======================
# Admin Dashboard Route
# ======================
@app.route('/admin')
def admin_dashboard():
    if 'admin' not in session:
        flash("You must be an admin to access this page.", "danger")
        return redirect(url_for('login'))

    db = get_db()
    cur = db.cursor()

    # Get all products
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()

    # Get all orders
    cur.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = cur.fetchall()

    return render_template('admin_dashboard.html', products=products, orders=orders)


# ======================
# Add Product
# ======================
@app.route('/admin/add_product', methods=['POST'])
def admin_add_product():
    if 'admin' not in session:
        flash("You must be an admin to do this.", "danger")
        return redirect(url_for('login'))

    name = request.form.get('name')
    price = request.form.get('price')
    desc = request.form.get('desc')
    image_file = request.files['image']

    if image_file:
        image_filename = image_file.filename
        image_file.save('static/images/' + image_filename)

    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO products (name, price, description, image) VALUES (?, ?, ?, ?)",
                (name, price, desc, image_filename))
    db.commit()

    flash(f"Product '{name}' added successfully!", "success")
    return redirect(url_for('admin_dashboard'))


# ======================
# Edit Product
# ======================
@app.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    db = get_db()
    cur = db.cursor()

    # Fetch product from DB
    cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cur.fetchone()

    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        image_file = request.files.get('image')

        # Handle image upload
        if image_file and image_file.filename != '':
            image_filename = image_file.filename
            image_path = os.path.join('static/images/', image_filename)
            image_file.save(image_path)
        else:
            image_filename = product['image']  # keep old image if not changed

        # Update DB
        cur.execute("""
            UPDATE products 
            SET name=?, price=?, image=? 
            WHERE id=?
        """, (name, price, image_filename, product_id))
        db.commit()
        flash("Product updated successfully!", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_edit_product.html', product=product)



# ======================
# Delete Product
# ======================
@app.route('/admin/delete_product/<int:product_id>')
def admin_delete_product(product_id):
    if 'admin' not in session:
        flash("You must be an admin to do this.", "danger")
        return redirect(url_for('login'))

    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM products WHERE id=?", (product_id,))
    db.commit()

    flash("Product deleted successfully!", "success")
    return redirect(url_for('admin_dashboard'))




# ======================
# Update Order Status
# ======================
@app.route('/admin/update_order/<int:order_id>', methods=['POST'])
def admin_update_order(order_id):
    status = request.form.get('status')
    tracking_number = request.form.get('tracking_number')

    db = get_db()
    cur = db.cursor()
    cur.execute("""
        UPDATE orders
        SET status = ?, tracking_number = ?
        WHERE id = ?
    """, (status, tracking_number, order_id))
    db.commit()

    flash(f"Order {order_id} updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))



@app.route('/admin/order_details/<int:order_id>')
def admin_order_details(order_id):
    if 'admin' not in session:
        flash("You must be an admin to access this page.", "danger")
        return redirect(url_for('login'))

    db = get_db()
    cur = db.cursor()

    # Get order info
    cur.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    order = cur.fetchone()

    # Get order items
    cur.execute("""
        SELECT oi.quantity, p.name, p.price, p.image
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id=?
    """, (order_id,))
    items = cur.fetchall()

    return render_template('admin_orders_dashboard.html', order=order, items=items)


# ---------------- Run App ----------------
if __name__ == '__main__':
    init_db_and_seed()
    app.run(debug=True)
