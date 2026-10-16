import os
import sqlite3
import random
import string
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'whimsy_forest_secret_fairy_key'

# Reliable absolute database path for Render
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'letters.db')

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS letters (
            id TEXT PRIMARY KEY,
            secret_code TEXT UNIQUE NOT NULL,
            audience TEXT NOT NULL,
            paper_theme TEXT NOT NULL,
            font_style TEXT NOT NULL,
            stamp_type TEXT NOT NULL,
            recipient TEXT NOT NULL,
            message TEXT NOT NULL,
            author TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database schema on boot
init_db()

def generate_secret_code():
    words = ["FERN", "MOSS", "MOON", "FAIRY", "GLADE", "DEW", "IVY", "CEDAR"]
    prefix = random.choice(words)
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}-{suffix}"

@app.route('/')
def home():
    conn = get_db()
    public_letters = conn.execute(
        "SELECT * FROM letters WHERE audience = 'stranger' ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return render_template('index.html', public_letters=public_letters)

@app.route('/garden')
def garden():
    conn = get_db()
    letters = conn.execute(
        "SELECT * FROM letters WHERE audience = 'stranger' ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return render_template('garden.html', letters=letters)

@app.route('/create', methods=['POST'])
def create_letter():
    audience = request.form.get('audience', 'loved_one')
    paper_theme = request.form.get('paper_theme', 'paper-parchment')
    font_style = request.form.get('font_style', 'font-cormorant')
    stamp_type = request.form.get('stamp_type', '🌿')
    recipient = request.form.get('recipient', '').strip()
    message = request.form.get('message', '').strip()
    author = request.form.get('author', '').strip()

    if not recipient:
        recipient = "To a Gentle Soul" if audience == 'stranger' else "Dearest"
    if not author:
        author = "An Unknown Wanderer" if audience == 'stranger' else "A Quiet Soul"

    if not message:
        flash("Please whisper some words onto the paper before sealing.")
        return redirect(url_for('home'))

    secret_code = generate_secret_code()
    letter_id = secret_code.lower()

    conn = get_db()
    conn.execute('''
        INSERT INTO letters (id, secret_code, audience, paper_theme, font_style, stamp_type, recipient, message, author)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (letter_id, secret_code, audience, paper_theme, font_style, stamp_type, recipient, message, author))
    conn.commit()
    conn.close()

    return redirect(url_for('view_letter', secret_code=secret_code, newly_created=1))

@app.route('/unlock', methods=['POST'])
def unlock_letter():
    code = request.form.get('secret_code', '').strip().upper()
    conn = get_db()
    letter = conn.execute("SELECT * FROM letters WHERE secret_code = ?", (code,)).fetchone()
    conn.close()

    if letter:
        return redirect(url_for('view_letter', secret_code=letter['secret_code']))
    else:
        flash("No sealed letter found with this forest code. Check your spelling.")
        return redirect(url_for('home'))

@app.route('/letter/<secret_code>')
def view_letter(secret_code):
    conn = get_db()
    letter = conn.execute("SELECT * FROM letters WHERE secret_code = ?", (secret_code.upper(),)).fetchone()
    conn.close()

    if not letter:
        flash("This letter has dissolved into the forest mist or does not exist.")
        return redirect(url_for('home'))

    newly_created = request.args.get('newly_created', '0') == '1'
    return render_template('letter.html', letter=letter, newly_created=newly_created)

if __name__ == '__main__':
    app.run(debug=True, port=5000)