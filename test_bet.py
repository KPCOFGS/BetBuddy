import sqlite3
import argparse

def insert_test_data(match_id):
    # Connect to the SQLite database (replace with your actual database path)
    con = sqlite3.connect('bettingBuddy.db')
    cursor = con.cursor()

    # Data to insert into the Users table
    test_data = (
        9999,  # BetID
        1,  # userID (foreign key to Users)
        match_id,  # matchID
        'Minnesota Vikings',  # team
        1,  # amount
        -250.0,  # odds
        0.4,  # potential_payout
        '2024-12-07 23:25:55',  # timestamp
        'open'  # bet_status
    )

    # Insert the test data into the Bets table (assuming the structure you mentioned)
    cursor.execute('''
    INSERT INTO Bets (betID, userID, matchID, team, amount, odds, potential_payout, timestamp, bet_status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    ''', test_data)

    # Commit the transaction and close the connection
    con.commit()
    con.close()

    print("Test data inserted successfully!")

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Insert test data into the Bets table.")
    parser.add_argument("matchID", help="The matchID to insert into the database.")
    args = parser.parse_args()

    # Call the function with the user-provided matchID
    insert_test_data(args.matchID)
