# wordle_db.py
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os
from dotenv import load_dotenv
from pytz import timezone

load_dotenv()

# Get environmental variables
host = os.getenv('host')
user = os.getenv('user')
password = os.getenv('password')
database = os.getenv('database')

def connect_to_db():
    # Connect to the MySQL database
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(
            host = host,
            user = user,
            password = password,
            database = database
        )

        if connection.is_connected():
            db_info = connection.get_server_info()
            print("Connect  to MySQL Server version ", db_info)

            cursor = connection.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS wordle_stats")
            connection.commit() # Commit the changes

            connection.database = "wordle_stats"
            cursor.execute("CREATE TABLE IF NOT EXISTS user_stats (user_id VARCHAR(255), username VARCHAR(255), games_played INT DEFAULT 0, total_guesses INT DEFAULT 0, games_won INT DEFAULT 0, games_lost INT DEFAULT 0, average_guesses_per_game INT DEFAULT 0, last_played DATE, PRIMARY KEY (user_id))")
            connection.commit()  # Commit the changes
    except Error as e:
        print("Error while connecting to MySQL", e)

    return connection, cursor

def execute_query(connection, cursor, query, params=None):
    # Ping the server to ensure the connection is active
    connection.ping(reconnect=True)

    # Execute the query
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    
    return cursor


def update_user_stats(connection, cursor, user_id, username, game_won, num_guesses):
    # Update the user stats in the database
    execute_query(connection, cursor, 'SELECT username, games_played, games_won, games_lost, total_guesses, average_guesses_per_game, last_played FROM user_stats WHERE user_id = %s', (user_id,))
    row = cursor.fetchone()
    eastern = timezone('US/Eastern')
    current_date = datetime.now(eastern).date()

    # If the user has no stats yet, insert a new row
    if row is None:
        execute_query(connection, cursor, 'INSERT INTO user_stats (user_id, username, games_played, games_won, games_lost, total_guesses, average_guesses_per_game, last_played) VALUES (%s, %s, 1, %s, %s, %s, %s, %s)', (user_id, username, int(game_won), int(not game_won), num_guesses, num_guesses, current_date))
    else:
     # Otherwise, update the existing row
        username, games_played, games_won, games_lost, total_guesses, average_guesses_per_game, last_played = row
        if last_played < current_date:
            username = username
            games_played = 0 if games_played is None else games_played
            games_won = 0 if games_won is None else games_won
            games_lost = 0 if games_lost is None else games_lost
            total_guesses = 0 if total_guesses is None else total_guesses
            average_guesses_per_game = 0 if average_guesses_per_game is None else average_guesses_per_game
            execute_query(connection, cursor, 'UPDATE user_stats SET username = %s, games_played = %s, games_won = %s, games_lost = %s, total_guesses = %s, average_guesses_per_game = %s, last_played = %s WHERE user_id = %s', (username, games_played + 1, games_won + int(game_won), games_lost + int(not game_won), total_guesses + num_guesses, int((total_guesses + num_guesses) / (games_played + 1)), current_date, user_id))
    # Commit the changes
    connection.commit()

def get_user_stats(connection, cursor, **kwargs):
    user_id = kwargs.get('user_id', None)
    username = kwargs.get('username', None)
    

    if user_id is not None and isinstance(user_id, int):
        execute_query(connection, cursor, 'SELECT * FROM user_stats WHERE user_id = %s', (user_id,))
    elif username is not None and isinstance(username, str):
        execute_query(connection, cursor, 'SELECT * FROM user_stats WHERE username = %s', (username,))
    else:
        return None
    return cursor.fetchall()


def reset_database(connection, cursor):
    # Drop existing tables and recreate them
    execute_query(connection, cursor, "DROP TABLE IF EXISTS user_stats")

    # Recreate the table
    execute_query(connection, cursor, '''
                   CREATE TABLE IF NOT EXISTS user_stats (
                   user_id VARCHAR(255) PRIMARY KEY,
                   username VARCHAR(255),
                   games_played INT DEFAULT 0,
                   games_won INT DEFAULT 0,
                   games_lost INT DEFAULT 0,
                   total_guesses INT DEFAULT 0,
                   average_guesses_per_game INT DEFAULT 0,
                   last_played DATE
                     )
                     ''')
    
    # Commit the changes
    connection.commit()

#connection, cursor = connect_to_db()

#reset_database(connection, cursor)



    


