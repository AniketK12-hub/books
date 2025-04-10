from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# -------------------- MySQL Connection --------------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",  # Add your MySQL password if set
    database="onlinebookstore"
)
cursor = db.cursor()

# -------------------- Home (with search) --------------------
@app.route('/')
def home():
    search_query = request.args.get('q')  # Get search query from URL

    if search_query:
        # Search in title or author
        cursor.execute("SELECT * FROM books WHERE title LIKE %s OR author LIKE %s",
                       ('%' + search_query + '%', '%' + search_query + '%'))
    else:
        cursor.execute("SELECT * FROM books")

    books = cursor.fetchall()
    logged_in = 'user_email' in session
    return render_template('index.html', books=books, logged_in=logged_in)


# -------------------- Signup --------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
        db.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')

# -------------------- Login --------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()

        if user:
            session['user_email'] = email
            return redirect(url_for('home'))
        else:
            return "Invalid credentials. Please try again."

    return render_template('login.html')

# -------------------- Admin Login --------------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin@123':
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return "Invalid admin credentials"

    return render_template('admin_login.html')

# -------------------- Admin Dashboard --------------------
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()

    cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = cursor.fetchall()

    return render_template('admin_dashboard.html', books=books, orders=orders)

# -------------------- Add Book --------------------
@app.route('/admin/add-book', methods=['POST'])
def add_book():
    title = request.form['title']
    author = request.form['author']
    price = request.form['price']
    image = request.form['image']

    cursor.execute("INSERT INTO books (title, author, price, image) VALUES (%s, %s, %s, %s)",
                   (title, author, price, image))
    db.commit()
    return redirect(url_for('admin_dashboard'))

# -------------------- Add to Cart --------------------
@app.route('/add-to-cart/<int:book_id>')
def add_to_cart(book_id):
    if 'user_email' not in session:
        return redirect(url_for('login'))

    cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
    book = cursor.fetchone()

    if not book:
        return "Book not found"

    if 'cart' not in session:
        session['cart'] = []

    session['cart'].append({
        'id': book[0],
        'title': book[1],
        'author': book[2],
        'price': float(book[3]),
        'image': book[4]
    })

    session.modified = True
    return redirect(url_for('home'))

# -------------------- View Cart --------------------
@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    total_price = sum(item['price'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total_price)

# -------------------- Checkout --------------------
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        address = request.form['address']
        payment_method = request.form['payment_method']

        cart_items = session.get('cart', [])
        total_price = sum(item['price'] for item in cart_items)
        item_summary = ", ".join([f"{item['title']} (₹{item['price']})" for item in cart_items])

        cursor.execute("INSERT INTO orders (name, email, address, payment_method, items, total) VALUES (%s, %s, %s, %s, %s, %s)",
                       (name, email, address, payment_method, item_summary, total_price))
        db.commit()

        session.pop('cart', None)

        return render_template('order_success.html', name=name)

    return render_template('checkout.html')

# -------------------- Logout --------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# -------------------- Run App --------------------
if __name__ == '__main__':
    app.run(debug=True)
