import sqlite3

# ---------------- Database file ----------------
DB_FILE = 'flowershop.db'

# ---------------- Products to insert ----------------
products = [
    # Regular products
    {'name': 'Peony Passion', 'price': 2500, 'description': 'Lush peony bouquet.', 'image': 'peony.jpg', 'stock': 10},
    {'name': 'Lavender Dreams', 'price': 2200, 'description': 'Soothing lavender arrangement.', 'image': 'lavender.jpg', 'stock': 10},
    {'name': 'Sunflower Smile', 'price': 1800, 'description': 'Large sunflowers to lighten the day.', 'image': 'sunflower.jpg', 'stock': 10},
    {'name': 'Tulip Charm', 'price': 2000, 'description': 'Bright tulips for any occasion.', 'image': 'tulip.jpg', 'stock': 10},
    {'name': 'Rose Bouquet', 'price': 3000, 'description': 'A beautiful bouquet of roses.', 'image': 'rose.jpg', 'stock': 10},

    # Occasion products
    {'name': 'The Rosé All Day Bouquet', 'price': 1899, 'description': 'A charming and lush arrangement...', 'image': 'wedding1.jpeg', 'stock': 10},
    {'name': 'Holly Kisses', 'price': 2399, 'description': 'A charming bouquet of whites and pinks...', 'image': 'wedding2.jpeg', 'stock': 10},
    {'name': 'Island Dusk', 'price': 2499, 'description': 'Lush pink lilies...', 'image': 'bday1.jpeg', 'stock': 10},
    {'name': 'Crimson Bouquet', 'price': 3499, 'description': 'Fresh crimson roses...', 'image': 'a1.jpeg', 'stock': 10},
    {'name': 'Achievement Teddy', 'price': 5500, 'description': 'A celebratory bouquet...', 'image': 'g1.jpg', 'stock': 10},
    {'name': 'Hearts Desire', 'price': 4890, 'description': 'Deep velvet red roses...', 'image': 'v1.jpg', 'stock': 10},
]

# ---------------- Insert products into DB ----------------
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Make sure products table exists (with stock column)
c.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    description TEXT,
    image TEXT,
    stock INTEGER NOT NULL DEFAULT 0
)
""")

# Insert products
for p in products:
    c.execute("""
    INSERT INTO products (name, price, description, image, stock)
    VALUES (?, ?, ?, ?, ?)
    """, (p['name'], p['price'], p['description'], p['image'], p['stock']))

conn.commit()
conn.close()
print(f"{len(products)} products have been added to {DB_FILE}.")
