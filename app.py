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

with open("API.txt", "r") as file:
    YOUR_API = file.readline().strip()  # Read the first line and remove any trailing whitespace or newline

NFL = 'americanfootball_nfl'
NBA = 'basketball_nba'
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
def create_tables():
    with get_db_connection() as con:
        # Create Users table
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

        # Create Bets table without bet_status column initially
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

        # Add the bet_status column if it doesn't already exist
        try:
            con.execute('ALTER TABLE Bets ADD COLUMN bet_status TEXT DEFAULT "open";')
        except sqlite3.OperationalError:
            # Column already exists
            pass

        # Create MatchResults table if it doesn't already exist
        con.execute('''
        CREATE TABLE IF NOT EXISTS MatchResults (
            matchID TEXT PRIMARY KEY,
            winning_team TEXT
        );
        ''')
        con.execute('''
        CREATE TABLE IF NOT EXISTS UserLogins (
            userID INTEGER PRIMARY KEY,
            last_login DATE,
            FOREIGN KEY (userID) REFERENCES Users(userID)
        );
        ''')
        con.execute('''
        CREATE TABLE IF NOT EXISTS AllMatches (
            matchID TEXT PRIMARY KEY
        );
        ''')
create_tables()
def FetchScoresData(NFL=NFL, NBA=NBA):
    # Initialize an empty list to store results for each sport
    all_game_winners = []

    # Loop through the provided categories (NFL, NBA)
    for category in (NFL, NBA):
        # Fetch odds data for the specified category
        odds_response = requests.get(f'https://api.the-odds-api.com/v4/sports/{category}/scores/?daysFrom=3&apiKey={YOUR_API}')

        # Check if the response was successful
        if odds_response.status_code == 200:
            data = odds_response.json()  # Assuming the data comes as JSON

            # Iterate through each game in the response
            for game in data:
                # Filter only completed games
                if not game.get('completed', False):
                    continue

                matchID = game.get('id')
                scores = game.get('scores', [])

                # Ensure scores data is present
                if scores and len(scores) == 2:
                    # Unpack scores
                    team1, team2 = scores[0], scores[1]
                    team1_name, team1_score = team1.get('name'), int(team1.get('score', 0))
                    team2_name, team2_score = team2.get('name'), int(team2.get('score', 0))

                    # Determine winner
                    if team1_score > team2_score:
                        winner = team1_name
                    elif team2_score > team1_score:
                        winner = team2_name
                    else:
                        winner = "Tie"

                    insert_match_result(matchID, winner)

                    # Append game result
                    all_game_winners.append({
                        'matchID': matchID,
                        'winner': winner
                    })
        else:
            # Raise an exception if the API request fails
            raise Exception(f"Error fetching data for {category}: {odds_response.status_code}")

    return all_game_winners
def FetchAllData(NFL=NFL, NBA=NBA):
    # Initialize an empty list to store results for each sport
    all_match = []

    # Loop through the provided categories (NFL, NBA)
    for category in (NFL, NBA):
        # Fetch odds data for the specified category
        odds_response = requests.get(f'https://api.the-odds-api.com/v4/sports/{category}/scores/?daysFrom=3&apiKey={YOUR_API}')

        # Check if the response was successful
        if odds_response.status_code == 200:
            data = odds_response.json()  # Assuming the data comes as JSON

            # Iterate through each game in the response
            for game in data:
                matchID = game.get('id')
                with get_db_connection() as con:
                    cursor = con.cursor()
                    cursor.execute('SELECT COUNT(*) FROM AllMatches WHERE matchID = ?', (matchID,))
                    result = cursor.fetchone()

                    if result[0] == 0:  # If no record exists with the given match_id
                        con.execute('''
                            INSERT INTO AllMatches (matchID)
                            VALUES (?);
                        ''', (matchID,))  # Ensure matchID is passed as a tuple with one element
                        con.commit()
                # Append game result
                all_match.append({
                    'matchID': matchID,
                })
        else:
            # Raise an exception if the API request fails
            raise Exception(f"Error fetching data for {category}: {odds_response.status_code}")

    return all_match
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

            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

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
        with get_db_connection() as con:
            cursor = con.cursor()
            cursor.execute("SELECT userID, password, tokenAmnt FROM Users WHERE username = ?", (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user['password'], password):
                user_id = user['userID']
                session['user_id'] = username  # Store username in session

                # Check last login date for daily reward
                cursor.execute("SELECT last_login FROM UserLogins WHERE userID = ?", (user_id,))
                reward_row = cursor.fetchone()

                today_date = datetime.utcnow().date()
                reward_message = None

                if reward_row:
                    last_login_date = datetime.strptime(reward_row['last_login'], "%Y-%m-%d").date()
                    if last_login_date < today_date:  # New day login
                        # Grant daily reward
                        cursor.execute("UPDATE Users SET tokenAmnt = tokenAmnt + 500 WHERE userID = ?", (user_id,))
                        cursor.execute("UPDATE UserLogins SET last_login = ? WHERE userID = ?", (today_date, user_id))
                        reward_message = 'You have received your daily reward of 500 tokens!'
                else:
                    # First-time login or no record exists
                    cursor.execute("INSERT INTO UserLogins (userID, last_login) VALUES (?, ?)", (user_id, today_date))
                    cursor.execute("UPDATE Users SET tokenAmnt = tokenAmnt + 500 WHERE userID = ?", (user_id,))
                    reward_message = 'You have received your daily reward of 500 tokens!'

                con.commit()

                # Redirect with appropriate message
                if reward_message:
                    flash(reward_message, 'success')
                else:
                    flash('Login successful!', 'success')

                return redirect(url_for('UserPage', username=username))
            else:
                # Set an error message if login fails
                error_message = 'Username or password is incorrect'
                return render_template('sign_in.html', error_message=error_message)
@app.route('/user/<username>', methods=['GET'])
def UserPage(username):
    user_id = session.get('user_id')
    if not user_id:
        flash("You must log in first.")
        return redirect(url_for('login'))
    category = request.args.get('category')

    # Retrieve user's balance and bet history
    with get_db_connection() as con:
        cursor = con.cursor()
        cursor.execute("SELECT tokenAmnt FROM Users WHERE username = ?", (username,))
        result = cursor.fetchone()
        user_balance = result['tokenAmnt'] if result else 0

    user_bets = fetch_user_bets(username)  # Fetch user bets

    # Fetch sports data if category is specified
    sports_data = None
    if category not in session:
        sports_data = FetchSportsData(category)
        if sports_data:
            session[category] = sports_data
    else:
        sports_data = session[category]
    FetchScoresData()
    FetchAllData()
    update_user_tokens_for_bets()
    return render_template(
        'user.html', username=username, user_balance=user_balance, data=sports_data, user_bets=user_bets
    )

def FetchSportsData(category, NFL=NFL, NBA=NBA):
    BOOKMAKERS = 'draftkings'
    MARKETS = 'h2h'
    ODDS_FORMAT = 'american'
    DATE_FORMAT = 'iso'
    # Determine the sports category to fetch
    if category == 'NFL':
        sport = NFL
    elif category == 'NBA':
        sport = NBA
    else:
        return None
    # Fetch odds data for the specified category
    odds_response = requests.get(f'https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={YOUR_API}&regions=us&markets={MARKETS},spreads&oddsFormat={ODDS_FORMAT}')
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
                    match_date = datetime.fromisoformat(match_date.replace('Z', '+00:00'))
                # Add match data
                matches.append({
                    'id': event['id'],  # Fetch and store the match ID
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
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')

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
        team = request.form['team']  # Team selected by the user
        bet_amount = int(request.form['amount'])
        home_odds = float(request.form['home_odds'])  # Home odds
        away_odds = float(request.form['away_odds'])  # Away odds

        match_id = request.form['id']

        # Ensure the user has enough balance
        with get_db_connection() as con:
            cursor = con.cursor()
            cursor.execute("SELECT tokenAmnt FROM Users WHERE username = ?", (user_id,))
            user_balance = cursor.fetchone()

            if user_balance and user_balance['tokenAmnt'] >= bet_amount:
                if team == request.form['home_team']:
                    odds = home_odds
                elif team == request.form['away_team']:
                    odds = away_odds
                else:
                    flash('Invalid team selection.', 'error')
                    return redirect(url_for('UserPage', username=user_id))

                if odds > 0:  # Positive odds
                    potential_payout = bet_amount * (odds / 100)
                else:  # Negative odds
                    potential_payout = bet_amount * (100 / abs(odds))

                cursor.execute('''
                    INSERT INTO Bets (userID, matchID, team, amount, odds, potential_payout)
                    VALUES (
                        (SELECT userID FROM Users WHERE username = ?),
                        ?, ?, ?, ?, ?
                    )''', (user_id, match_id, team, bet_amount, odds, potential_payout))

                cursor.execute("UPDATE Users SET tokenAmnt = tokenAmnt - ? WHERE username = ?", (bet_amount, user_id))
                con.commit()

                flash(f'Your bet has been placed! Potential Payout: ${potential_payout:.2f}', 'success')
                return redirect(url_for('UserPage', username=user_id))
            else:
                flash('Insufficient funds to place this bet. Please add more tokens.', 'error')
                return redirect(url_for('UserPage', username=user_id))

    return redirect(url_for('UserPage', username=user_id))
def insert_match_result(match_id, winner_team):
    with get_db_connection() as con:
        cursor = con.cursor()
        cursor.execute('SELECT COUNT(*) FROM MatchResults WHERE matchID = ?', (match_id,))
        result = cursor.fetchone()

        if result[0] == 0:  # If no record exists with the given match_id
            con.execute('''
                INSERT INTO MatchResults (matchID, winning_team)
                VALUES (?, ?);
            ''', (match_id, winner_team))
            con.commit()
def fetch_user_bets(username):
    with get_db_connection() as con:
        cursor = con.cursor()
        cursor.execute("SELECT * FROM Bets WHERE userID = (SELECT userID FROM Users WHERE username = ?)", (username,))
        return cursor.fetchall()
@app.route('/logout', methods=['POST'])
def logout():
    # Clear the session
    session.pop('user_id', None)
    return redirect(url_for('index'))

def get_match_results(match_id):
    url = f"https://api.the-odds-api.com/v4/sports/sport_key/events/{match_id}?apiKey={YOUR_API}"
    response = requests.get(url)
    if response.status_code == 200:
        match_data = response.json()
        # Extract winner based on TheOddsAPI response structure
        winning_team = match_data.get('outcomes', {}).get('winner')
        return {'match_name': match_data.get('name'), 'winner': winning_team}
    return None

def determine_bet_result(match_data, team_bet_on):
    winner = match_data.get('winner')
    if winner:
        return 'win' if winner == team_bet_on else 'lose'
    return 'Pending'

@app.route('/past_bets', methods=['GET'])
def past_bets():
    user_id = session.get('user_id')
    if not user_id:
        flash("You must be logged in to view past bets.")
        return redirect(url_for('login'))

    with get_db_connection() as con:
        # Fetch pending bets
        pending_bets = con.execute(
            "SELECT betID, matchID, team FROM Bets WHERE userID = (SELECT userID FROM Users WHERE username = ?) AND bet_status = 'open'",
            (user_id,)
        ).fetchall()

        # Check results for pending bets
        for bet in pending_bets:
            result = get_match_results(bet['matchID'])  # Fetch match result from API
            if result:
                winner = result.get('winner')
                if winner:
                    bet_status = 'Hit' if winner == bet['team'] else 'Lost'
                    con.execute(
                        "UPDATE Bets SET bet_status = ? WHERE betID = ?", (bet_status, bet['betID'])
                    )

        # Fetch all bets to display, now updated
        all_bets = con.execute(
            "SELECT matchID, team, amount, bet_status FROM Bets WHERE userID = (SELECT userID FROM Users WHERE username = ?)",
            (user_id,)
        ).fetchall()

    bets_with_results = []
    for bet in all_bets:
        result = get_match_results(bet['matchID'])
        if result:
            bets_with_results.append({
                'match': result.get('match_name', 'Unknown Match'),
                'team': bet['team'],
                'amount': bet['amount'],
                'status': bet['bet_status'],
                'result': determine_bet_result(result, bet['team'])
            })
        else:
            bets_with_results.append({
                'match': 'Unknown Match',
                'team': bet['team'],
                'amount': bet['amount'],
                'status': bet['bet_status'],
                'result': 'Pending'
            })

    return render_template('past_bets.html', bets=bets_with_results)

def update_pending_bets():
    with get_db_connection() as con:
        pending_bets = con.execute("SELECT betID, matchID, team FROM Bets WHERE bet_status = 'open'").fetchall()
        for bet in pending_bets:
            result = get_match_results(bet['matchID'])
            if result:
                winner = result.get('winner')
                if winner:
                    bet_status = 'Hit' if winner == bet['team'] else 'Lost'
                    con.execute("UPDATE Bets SET bet_status = ? WHERE betID = ?", (bet_status, bet['betID']))

def update_user_tokens_for_bets():
    with get_db_connection() as con:
        cursor = con.cursor()

        # Get all matchIDs from the Bets table
        cursor.execute('SELECT betID, userID, matchID, potential_payout FROM Bets WHERE bet_status = "open"')
        bets = cursor.fetchall()

        # Get all matchIDs from the MatchResults table
        cursor.execute('SELECT matchID FROM MatchResults')
        match_results_ids = cursor.fetchall()

        # Get all matchIDs from the AllMatches table
        cursor.execute('SELECT matchID FROM AllMatches')
        all_matches_ids = cursor.fetchall()

        # Convert match_results_ids and all_matches_ids to sets for faster lookup
        match_results_set = {result[0] for result in match_results_ids}
        all_matches_set = {result[0] for result in all_matches_ids}

        # Iterate through each bet and check for conditions
        for bet in bets:
            betID, userID, bet_matchID, potential_payout = bet

            # Check if the matchID exists in MatchResults
            if bet_matchID in match_results_set:
                # If the matchID exists in MatchResults, update the user's tokenAmnt
                cursor.execute('''
                    UPDATE Users
                    SET tokenAmnt = tokenAmnt + ?
                    WHERE userID = ?
                ''', (potential_payout, userID))

                # Update the bet_status to "closed" after processing the bet
                cursor.execute('''
                    UPDATE Bets
                    SET bet_status = "closed"
                    WHERE betID = ?
                ''', (betID,))

                # Remove the bet from the Bets table
                cursor.execute('''
                    DELETE FROM Bets
                    WHERE betID = ?
                ''', (betID,))

                # Commit the changes
                con.commit()

            # If matchID does not exist in MatchResults, check in AllMatches table
            elif bet_matchID not in match_results_set:
                if bet_matchID in all_matches_set:
                    # Do nothing if the matchID exists in AllMatches
                    continue
                else:
                    # Delete the bet if the matchID does not exist in AllMatches
                    cursor.execute('''
                        DELETE FROM Bets
                        WHERE betID = ?
                    ''', (betID,))
                    # Commit the changes
                    con.commit()
FetchScoresData()
FetchAllData()
update_user_tokens_for_bets()
if __name__ == '__main__':
    app.run(debug=True)
