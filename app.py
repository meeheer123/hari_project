from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3

def initialize_database():
    conn = sqlite3.connect('schema.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            price REAL,
            quantity INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            username TEXT UNIQUE,
            password TEXT,
            age INTEGER,
            phonenumber TEXT,
            email TEXT UNIQUE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            user_id INTEGER,
            phone TEXT,
            email TEXT,
            date TEXT,
            time TEXT,
            doctor_id INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            specialty TEXT,
            experience TEXT
        )
    ''')

    cursor.execute('''
        INSERT INTO doctors (name, specialty, experience)
        VALUES ('Dr. John Doe', 'Cardiology', '10 years')
    ''')
    cursor.execute('''
        INSERT INTO doctors (name, specialty, experience)
        VALUES ('Dr. Jane Smith', 'Dermatology', '5 years')
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            price REAL,
            quantity INTEGER
        )
    ''')

    cursor.execute('''
        INSERT INTO medicines (name, description, price, quantity)
        VALUES (?, ?, ?, ?)
    ''', ('Paracetamol', 'Pain reliever', 5.99, 50))

    cursor.execute('''
        INSERT INTO medicines (name, description, price, quantity)
        VALUES (?, ?, ?, ?)
    ''', ('Ibuprofen', 'Anti-inflammatory', 7.99, 30))

    conn.commit()
    cursor.close()
    conn.close()

initialize_database()
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

@app.route('/login/user', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('schema.db')
        cursor = conn.cursor()

        cursor.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            session['user_id'] = user[0]
            return redirect(url_for('homepage'))

        return render_template('login-user.html', error='Invalid username or password')
    else:
        return render_template('login-user.html')

@app.route('/shop')
def shop():
    conn = sqlite3.connect('schema.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM medicines')
    medicines = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('shop.html', medicines=medicines)

@app.route('/add_to_cart/<int:medicine_id>')
def add_to_cart(medicine_id):
    if 'cart' not in session:
        session['cart'] = []

    session['cart'].append(medicine_id)
    return redirect(url_for('shop'))

@app.route('/cart')
def view_cart():
    if 'cart' not in session or not session['cart']:
        return "Your cart is empty"

    conn = sqlite3.connect('schema.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM medicines WHERE id IN ({})'.format(
        ','.join('?' * len(session['cart']))), session['cart'])
    cart_items = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('cart.html', cart_items=cart_items)

@app.route('/checkout', methods=['POST'])
def checkout():
    session.pop('cart', None)
    return "Checkout successful!"

@app.route('/signup/user', methods=['POST', 'GET'])
def user_signup():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        age = request.form['age']
        phonenumber = request.form['phonenumber']
        email = request.form['email']

        conn = sqlite3.connect('schema.db')
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO users (name, username, password, age, phonenumber, email)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, username, password, age, phonenumber, email))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('user_login'))

    return render_template('signup-user.html')

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('user_login'))
    else:
        return redirect(url_for('homepage'))

@app.route('/homepage')
def homepage():
    conn = sqlite3.connect('schema.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM doctors')
    doctors = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('userpage.html', doctors=doctors)

@app.route('/view_profile/<int:doctor_id>')
def view_profile(doctor_id):
    conn = sqlite3.connect('schema.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM doctors WHERE id = ?', (doctor_id,))
    doctor = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('profile.html', doctor=doctor)

@app.route('/user_appointments')
def user_appointments():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))

    user_id = session['user_id']
    conn = sqlite3.connect('schema.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM appointments WHERE user_id = ?', (user_id,))
    appointments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('user_appointments.html', appointments=appointments)

@app.route('/book_appointment/<int:doctor_id>', methods=['GET', 'POST'])
def book_appointment(doctor_id):
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        date = request.form['date']
        time = request.form['time']

        conn = sqlite3.connect('schema.db')
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO appointments (name, email, phone, doctor_id, date, time, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, phone, doctor_id, date, time, session['user_id']))

        conn.commit()
        cursor.close()
        conn.close()

        return 'Appointment booked successfully!'

    return render_template('book_appointment.html', doctor_id=doctor_id)

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_term = request.form['search_term'].strip().lower()

        conn = sqlite3.connect('schema.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM medicines WHERE LOWER(name) LIKE ?', ('%' + search_term + '%',))
        medicines = cursor.fetchall()

        cursor.close()
        conn.close()

        if medicines:
            in_stock_medicines = [medicine for medicine in medicines if medicine[4] > 0]  # Filter out medicines with quantity > 0
            if in_stock_medicines:
                return render_template('search.html', medicines=in_stock_medicines)
            else:
                return render_template('search.html', message='Medicine out of Stock')
        else:
            return render_template('search.html', message='No medicines found matching the search term.')

    return render_template('search.html')

if __name__ == '__main__':
    app.run(debug=True)
