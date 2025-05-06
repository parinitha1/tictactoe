import os
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# ------------------ DB Setup ------------------

def init_db():
    if not os.path.exists('database.db'):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE leaderboard (player TEXT, wins INTEGER)''')
        c.execute('''CREATE TABLE chat (username TEXT, message TEXT)''')
        c.execute('''CREATE TABLE users (username TEXT PRIMARY KEY, password TEXT)''')
        conn.commit()
        conn.close()

# ------------------ Auth Routes ------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        if c.fetchone():
            return "Username already taken!"
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session['username'] = username
            return redirect('/')
        return "Invalid credentials!"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

# ------------------ Game Routes ------------------

@app.route('/')
def index():
    if 'username' not in session:
        return redirect('/login')
    return render_template('index.html', username=session['username'])

@app.route('/leaderboard')
def leaderboard():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM leaderboard ORDER BY wins DESC LIMIT 10")
    data = c.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/add-win', methods=['POST'])
def add_win():
    player = request.json['player']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM leaderboard WHERE player=?", (player,))
    if c.fetchone():
        c.execute("UPDATE leaderboard SET wins = wins + 1 WHERE player=?", (player,))
    else:
        c.execute("INSERT INTO leaderboard VALUES (?, ?)", (player, 1))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

# ------------------ Chat ------------------

@socketio.on('send_message')
def handle_send_message(data):
    username = data['username']
    message = data['message']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO chat VALUES (?, ?)", (username, message))
    conn.commit()
    conn.close()
    emit('receive_message', data, broadcast=True)

@socketio.on('connect')
def on_connect():
    print("Client connected")

# ------------------ Start ------------------

if __name__ == '__main__':
    init_db()
    socketio.run(app, host="0.0.0.0", port=8001, debug=True, allow_unsafe_werkzeug=True)

