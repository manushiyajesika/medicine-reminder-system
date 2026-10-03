from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = 'super_secret_key'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            dosage TEXT NOT NULL,
            time TEXT NOT NULL
        )
    ''')
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES ('admin', '1234')")
    except:
        pass
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = username
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error', 'message': 'Invalid Username or Password'})

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/api/medicines', methods=['GET'])
def get_medicines():
    if 'user_id' not in session:
        return jsonify([])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, dosage, time FROM medicines WHERE user_id = ?', (session['user_id'],))
    rows = cursor.fetchall()
    conn.close()
    return jsonify([{'id': r['id'], 'name': r['name'], 'dosage': r['dosage'], 'time': r['time']} for r in rows])

@app.route('/api/medicines', methods=['POST'])
def add_medicine():
    if 'user_id' not in session:
        return jsonify({'status': 'unauthorized'}), 401
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO medicines (user_id, name, dosage, time) VALUES (?, ?, ?, ?)',
                   (session['user_id'], data['name'], data['dosage'], data['time']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# --- FIXED ROUTES ---
@app.route('/api/medicines/<int:med_id>', methods=['PUT'])
def edit_medicine(med_id):
    if 'user_id' not in session:
        return jsonify({'status': 'unauthorized'}), 401
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE medicines SET name = ?, dosage = ?, time = ? WHERE id = ? AND user_id = ?',
                   (data['name'], data['dosage'], data['time'], med_id, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'updated'})

@app.route('/api/medicines/<int:med_id>', methods=['DELETE'])
def delete_medicine(med_id):
    if 'user_id' not in session:
        return jsonify({'status': 'unauthorized'}), 401
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM medicines WHERE id = ? AND user_id = ?', (med_id, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted'})

if __name__ == '__main__':
    app.run(debug=True)