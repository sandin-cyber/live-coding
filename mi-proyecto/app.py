import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'clave_secreta_para_el_proyecto'

# 1. CONFIGURACIÓN DE LA BASE DE DATOS
def init_db():
    with sqlite3.connect('database.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT UNIQUE,
                      password TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS notes
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      content TEXT,
                      fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY(user_id) REFERENCES users(id))''')
init_db()

# 2. RUTAS DE AUTENTICACIÓN
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = generate_password_hash(request.form.get('password'))
        try:
            with sqlite3.connect('database.db') as conn:
                conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                return redirect(url_for('login'))
        except:
            flash("Error: El nombre de usuario ya está cogido.")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        with sqlite3.connect('database.db') as conn:
            user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('dashboard'))
        flash("Usuario o contraseña incorrectos.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# 3. RUTAS DE LAS NOTAS
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect('database.db') as conn:
        # Pedimos content(0), id(1) y fecha(2)
        user_notes = conn.execute("SELECT content, id, fecha FROM notes WHERE user_id = ? ORDER BY fecha DESC", 
                                 (session['user_id'],)).fetchall()
    return render_template('dashboard.html', notes=user_notes)

@app.route('/add_note', methods=['POST'])
def add_note():
    if 'user_id' in session:
        content = request.form.get('content')
        if content:
            with sqlite3.connect('database.db') as conn:
                conn.execute("INSERT INTO notes (user_id, content) VALUES (?, ?)", (session['user_id'], content))
    return redirect(url_for('dashboard'))

@app.route('/delete_note/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    if 'user_id' in session:
        with sqlite3.connect('database.db') as conn:
            # SEGURIDAD: Solo borra si la nota es del usuario logueado
            conn.execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, session['user_id']))
    return redirect(url_for('dashboard'))

# 4. PARCHE DE SEGURIDAD (Flecha atrás)
@app.after_request
def add_header(response):
    # Dice al navegador que no guarde nada en caché
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == '__main__':
    app.run(debug=True)