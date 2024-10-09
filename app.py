import sqlite3
from flask import Flask, render_template, request, session, redirect, url_for, flash
import secrets
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='./static')

# Generate a random secret key
app.secret_key = secrets.token_urlsafe(32)

# Connect to the SQLite database
def get_db_connection():
    con = sqlite3.connect('bettingBuddy.db', check_same_thread=False)
    con.row_factory = sqlite3.Row  # To access columns by name
    return con

# Create tables if they don't exist
def create_tables():
    with get_db_connection() as con:
        con.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            userID INTEGER PRIMARY KEY AUTOINCREMENT,
            fName TEXT,
            lName TEXT,
            tokenAmnt INTEGER,
            username TEXT UNIQUE,
            password TEXT
        );''')

create_tables()

# Opens the Home Screen HTML file for the user
@app.route('/')
def index():
    clear_session()
    return render_template('home.html')

# Define a function to clear the session
def clear_session():
    session.pop('user_id', None)

# Opens the signup page
@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/signupprocess', methods=['POST'])
def signupprocess():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Hash the password before storing it
        hashed_password = generate_password_hash(password)

        # Insert user into the database
        with get_db_connection() as con:
            con.execute("INSERT INTO Users (username, password) VALUES (?, ?)", (username, hashed_password))

        flash('Signup successful! Please log in.')
        return redirect(url_for('login'))  # Corrected route name

# Opens the login page
@app.route('/sign_in')
def login():
    return render_template('sign_in.html')

@app.route('/signinprocess', methods=['POST'])
def loginprocess():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = get_db_connection().cursor()
        cursor.execute("SELECT password FROM Users WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result and check_password_hash(result[0], password):
            session['user_id'] = username  # Store username in session
            flash('Login successful')
            return redirect(url_for('index'))  # Redirect to home after successful login
        else:
            flash('Login unsuccessful. Check your username and password.')
            return redirect(url_for('login'))  # Redirect to login page

if __name__ == '__main__':
    app.run(debug=True)
