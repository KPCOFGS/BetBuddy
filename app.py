import sqlite3
from asyncio import current_task
from operator import ifloordiv
from zoneinfo import available_timezones

import pandas as pd
import requests
from flask import Flask, render_template, request, session, redirect, url_for, flash
import secrets
from datetime import datetime

from unicodedata import category
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string

# Function to generate a long random string
def generate_recovery_string():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=64))



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
            tokenAmnt INTEGER DEFAULT 1000,
            username TEXT UNIQUE,
            password TEXT,
            recovery_string TEXT UNIQUE
        );
        ''')
        con.execute('''
        CREATE TABLE IF NOT EXISTS Bets (
            betID INTEGER PRIMARY KEY AUTOINCREMENT,
            userID INTEGER,
            matchID TEXT,
            team TEXT,
            amount INTEGER,
            odds REAL,
            potential_payout REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (userID) REFERENCES Users(userID)
        );
        ''')

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
@app.route('/signup', methods=['GET'])
def signup():
    # Generate a recovery string
    recovery_string = generate_recovery_string()
    return render_template('signup.html', recovery_string=recovery_string)
@app.route('/signupprocess', methods=['POST'])
def signupprocess():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm-password']
        recovery_string = request.form['recovery_string']  # Get the recovery string from the form

        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return render_template('signup.html', username=username, recovery_string=recovery_string)

        with get_db_connection() as con:
            cursor = con.cursor()
            cursor.execute("SELECT 1 FROM Users WHERE username = ?", (username,))
            user_exists = cursor.fetchone()

            if user_exists:
                flash('Username already exists. Please choose a different one.', 'error')
                return render_template('signup.html', username=username, recovery_string=recovery_string)

            # If you want to regenerate the recovery string only if needed
            cursor.execute("SELECT 1 FROM Users WHERE recovery_string = ?", (recovery_string,))
            while cursor.fetchone():  # Check if the string exists, regenerate if needed
                recovery_string = generate_recovery_string()
                cursor.execute("SELECT 1 FROM Users WHERE recovery_string = ?", (recovery_string,))

            hashed_password = generate_password_hash(password)

            # Insert user with the recovery string
            con.execute("INSERT INTO Users (username, password, tokenAmnt, recovery_string) VALUES (?, ?, ?, ?)",(username, hashed_password, 1000, recovery_string))

        flash('Sign Up successful! Please log in.', 'success')
        return redirect(url_for('login'))


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

    # Retrieve user's balance from the database
    with get_db_connection() as con:
        cursor = con.cursor()
        cursor.execute("SELECT tokenAmnt FROM Users WHERE username = ?", (username,))
        result = cursor.fetchone()
        if result:
            user_balance = result['tokenAmnt']
        else:
            user_balance = 0  # Default to 0 if no balance is found

    # Fetch sports data if the category is specified
    if category not in session:
        sports_data = FetchSportsData(category)
        if sports_data:
            session[category] = sports_data
    else:
        sports_data = session[category]

    # Pass user_balance and other data to the template
    return render_template('user.html', username=username, user_balance=user_balance, data=sports_data)
def FetchSportsData(category):
    # Define Parameters
    API_KEY = '668973ec82ed19bae55f0bd240052f2e'
    BOOKMAKERS = 'draftkings'
    MARKETS = 'h2h'
    ODDS_FORMAT = 'american'
    DATE_FORMAT = 'iso'
    NFL = 'americanfootball_nfl'
    NBA = 'basketball_nba'
    # Determine the sports category to fetch
    if category == 'NFL':
        sport = NFL
    elif category == 'NBA':
        sport = NBA
    else:
        return None
    # Fetch odds data for the specified category
    odds_response = requests.get(f'https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={API_KEY}&regions=us&markets={MARKETS},spreads&oddsFormat={ODDS_FORMAT}')
    # Return the JSON response if successful
    if odds_response.status_code == 200:
        data = odds_response.json()
        current_date = datetime.utcnow().date()
        matches = []
        for event in data:
            try:
                # Validate bookmakers
                bookmakers = event.get('bookmakers', [])
                if not bookmakers:
                    continue
                # Validate markets
                markets = bookmakers[0].get('markets', [])
                if not markets:
                    continue
                # Validate outcomes
                outcomes = markets[0].get('outcomes', [])
                if not outcomes:
                    continue
                # Extract home and away prices
                home_team_price = next(
                    (outcome['price'] for outcome in outcomes if outcome['name'] == event['home_team']), None
                )
                away_team_price = next(
                    (outcome['price'] for outcome in outcomes if outcome['name'] == event['away_team']), None
                )
                if home_team_price is None or away_team_price is None:
                    continue
                # Grab commence time
                match_date = event.get('commence_time')
                if match_date:
                    match_date = datetime.fromisoformat(match_date.replace('Z', '+00:00')).date()
                # Add match data
                matches.append({
                    'home_team': event['home_team'],
                    'away_team': event['away_team'],
                    'match_date': match_date,
                    'home_team_price': home_team_price,
                    'away_team_price': away_team_price,
                })
            except (KeyError, IndexError) as e:
                print(f"Error processing event: {event}. Error: {e}")
                continue
        return matches
    else:
        # Raise an exception if the API request fails
        raise Exception(f"Error fetching data: {odds_response.status_code}")
# Forget password page
@app.route('/forget_password', methods=['GET', 'POST'])
def forget_password():
    if request.method == 'POST':
        recovery_string = request.form['recovery_string'].strip()  # Strip leading/trailing spaces

        # Check the database for the recovery string
        with get_db_connection() as con:
            cursor = con.cursor()
            cursor.execute("SELECT username, password FROM Users WHERE recovery_string = ?", (recovery_string,))
            user = cursor.fetchone()

            if user:
                # If the recovery string matches, show the reset password form
                return render_template('display_user_info.html', username=user['username'])
            else:
                # If no match, show an error
                flash('Invalid recovery string. Please try again.', 'error')
                return render_template('forget_password.html')

    return render_template('forget_password.html')

# Reset password page
@app.route('/display_user_info/<username>', methods=['GET', 'POST'])
def reset_password(username):
    if request.method == 'POST':
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if passwords match
        if new_password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return render_template('display_user_info.html', username=username)

        # Hash the new password before updating
        hashed_password = generate_password_hash(new_password)

        # Update the password in the database
        with get_db_connection() as con:
            cursor = con.cursor()
            cursor.execute("UPDATE Users SET password = ? WHERE username = ?", (hashed_password, username))
            con.commit()

        flash('Your password has been reset successfully!', 'success')
        return redirect(url_for('login'))

    return render_template('display_user_info.html', username=username)
@app.route('/place_bet', methods=['POST'])
def place_bet():
    if request.method == 'POST':
        # Extract form data
        user_id = request.form['user_id']
        match_id = request.form['match_id']
        team = request.form['team']  # Team selected by the user
        bet_amount = int(request.form['amount'])
        home_odds = float(request.form['home_odds'])  # Home odds
        away_odds = float(request.form['away_odds'])  # Away odds

        # Ensure the user has enough balance
        with get_db_connection() as con:
            cursor = con.cursor()
            cursor.execute("SELECT tokenAmnt FROM Users WHERE username = ?", (user_id,))
            user_balance = cursor.fetchone()

            if user_balance and user_balance['tokenAmnt'] >= bet_amount:
                # Determine the odds based on the selected team
                if team == request.form['home_team']:  # If the user selected the home team
                    odds = home_odds
                elif team == request.form['away_team']:  # If the user selected the away team
                    odds = away_odds
                else:
                    flash('Invalid team selection.', 'error')
                    return redirect(url_for('UserPage', username=user_id))

                # Calculate potential payout based on American odds
                if odds > 0:  # Positive odds
                    potential_payout = bet_amount * (odds / 100)
                else:  # Negative odds
                    potential_payout = bet_amount * (100 / abs(odds))

                # Insert the bet into the Bets table
                cursor.execute('''
                    INSERT INTO Bets (userID, matchID, team, amount, odds, potential_payout)
                    VALUES (
                        (SELECT userID FROM Users WHERE username = ?),
                        ?, ?, ?, ?, ?
                    )''', (user_id, match_id, team, bet_amount, odds, potential_payout))

                # Deduct the bet amount from the user's balance
                cursor.execute("UPDATE Users SET tokenAmnt = tokenAmnt - ? WHERE username = ?", (bet_amount, user_id))
                con.commit()

                flash(f'Your bet has been placed! Potential Payout: ${potential_payout:.2f}', 'success')
                return redirect(url_for('UserPage', username=user_id))
            else:
                flash('Insufficient funds to place this bet. Please add more tokens.', 'error')
                return redirect(url_for('UserPage', username=user_id))

    # In case of a wrong method or some issue, redirect to user page
    return redirect(url_for('UserPage', username=user_id))

if __name__ == '__main__':
    app.run(debug=True)
