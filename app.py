import random
from flask import Flask, get_flashed_messages, jsonify, render_template, request, session, redirect, url_for, flash
import mysql
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

import secrets
import string

app = Flask(__name__, template_folder='./templates') #MODIFY THIS AS NEEDED

#Generate a random secret key
app.secret_key = secrets.token_urlsafe(32)

#Change the details below as needed to connect to the DB
mysql_config = {
    'host': 'HOST', 
    'user': 'root',
    'password': 'PW',
    'database': 'bettingBuddy' 
}

con = mysql.connector.connect(**mysql_config)

#---------------------------------------------------------------

#Opens the Home Screen HTML file for the user
@app.route('/')
def index():
   clear_session()
   return render_template('home.html')

#---------------------------------------------------------------

#Define a function to clear the session
def clear_session():
    # Check if 'user_id' exists in the session
    if 'user_id' in session:
        # Clear the 'user_id' from the session
        session.pop('user_id')

#---------------------------------------------------------------

if __name__ == '__main__':
   app.run(debug = True)
