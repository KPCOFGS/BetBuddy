
import sqlite3

def insert_test_data():
    # Connect to the SQLite database (replace with your actual database path)
    con = sqlite3.connect('bettingBuddy.db')
    cursor = con.cursor()

    # Data to insert into the Users table
    test_data = (
        999,  # userID
        1,  # userID (foreign key to Users)
        'e0b1a11b515324fa603bb16ff278dcbf',  # matchID
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

# Call the function to insert the test data
insert_test_data()
