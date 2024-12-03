import sqlite3
from operator import ifloordiv
from zoneinfo import available_timezones

import pandas as pd
import requests
from flask import Flask, render_template, request, session, redirect, url_for, flash
import secrets

from unicodedata import category
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
            email TEXT UNIQUE,
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
@app.route('/gambling_addiction_resources')
def gambling_addiction_resources():
    return render_template('ga_resources.html')
# Opens the signup page
@app.route('/signup')
def signup():
    return render_template('signup.html')
@app.route('/signupprocess', methods=['POST'])
def signupprocess():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm-password']

        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return render_template('signup.html', username=username, email=email)

        # Check if the username or email already exists
        with get_db_connection() as con:
            cursor = con.cursor()
            cursor.execute("SELECT 1 FROM Users WHERE username = ?", (username,))
            user_exists = cursor.fetchone()
            cursor.execute("SELECT 1 FROM Users WHERE email = ?", (email,))
            email_exists = cursor.fetchone()

            if user_exists:
                flash('Username already exists. Please choose a different one.', 'error')
                return render_template('signup.html', username=username, email=email)

            if email_exists:
                flash('Email already exists. Please use a different email.', 'error')
                return render_template('signup.html', username=username, email=email)

            # Hash the password before storing it
            hashed_password = generate_password_hash(password)

            # Insert user into the database
            con.execute("INSERT INTO Users (username, email, password) VALUES (?, ?, ?)",
                        (username, email, hashed_password))

        # Flash success message and redirect to login page
        flash('Sign Up successful! Please log in.', 'success')
        return redirect(url_for('login'))  # Redirects to login page


@app.route('/sign_in')
def login():
    signup_message = session.pop('signup_message', None)  # Retrieve and remove the message from the session
    return render_template('sign_in.html', signup_message=signup_message)  # Pass the message to the template
@app.route('/signinprocess', methods=['POST'])
def loginprocess():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if username exists in the database
        cursor = get_db_connection().cursor()
        cursor.execute("SELECT password FROM Users WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result and check_password_hash(result[0], password):
            session['user_id'] = username  # Store username in session
            return redirect(url_for('UserPage', username=username))  # Redirect to user page after successful login
        else:
            # Set an error message if login fails
            error_message = 'Username or password is incorrect'
            return render_template('sign_in.html', error_message=error_message)  # Pass error message to the template

# User Page Navigation
@app.route('/user/<username>', methods=['GET'])
def UserPage(username):
    category = request.args.get('category')

    #Code so a pull request isn't used on every tab switch
    if category not in session:
        sports_data = FetchSportsData(category)
        if sports_data:
            session[category] = sports_data
    else:
        sports_data = session[category]

    return render_template('user.html', username=username, data=sports_data)

# Pulls data from the TheOdds Api
def FetchSportsData(category):

    # Define Parameters
    API_KEY = '668973ec82ed19bae55f0bd240052f2e'
    BOOKMAKERS = 'draftkings,fanduel,'
    MARKETS = 'h2h'
    ODDS_FORMAT = 'american'
    DATE_FORMAT = 'iso'

    available_sports = {
        'NFL': 'americanfootball_nfl',
        'NBA': 'basketball_nba',
    }

    SPORT = available_sports.get(category, None)

    odds_response = requests.get(
        f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds',
        params={
            'api_key': API_KEY,
            'bookmakers': BOOKMAKERS,
            'markets': MARKETS,
            'oddsFormat': ODDS_FORMAT,
            'dateFormat': DATE_FORMAT,
        }
    )


    # Return the JSON response if successful
    if odds_response.status_code == 200:
        data = odds_response.json()
        print(data)

        # Select data that we want and put it into a list
        matches = [
            {
                'home_team': event['home_team'],
                'away_team': event['away_team'],
                'match_date': event['commence_time'],
                'home_team_price': next(
                   outcome['price'] for outcome in event['bookmakers'][0]['markets'][0]['outcomes'] if
                   outcome['name'] == event['home_team']),
                'away_team_price': next(
                    outcome['price'] for outcome in event['bookmakers'][0]['markets'][0]['outcomes'] if
                    outcome['name'] == event['away_team']),

            }
            for event in data
        ]

        print(matches)
        print('Remaining requests', odds_response.headers['x-requests-remaining'])
        print('Used requests', odds_response.headers['x-requests-used'])
        return matches
    else:
        # Handle errors if the API request fails
        print(f"Error fetching data: {odds_response.status_code}")
        return None




if __name__ == '__main__':
    app.run(debug=True)
