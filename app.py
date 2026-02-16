from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash
import sqlite3
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "users.db")
UPLOAD_DIR = os.path.join(APP_DIR, "uploads")

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

os.makedirs(UPLOAD_DIR, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            firstname TEXT,
            lastname TEXT,
            email TEXT,
            address TEXT,
            limerick_filename TEXT,
            limerick_wordcount INTEGER
        )
    """)
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT username, password, firstname, lastname, email, address,
                        limerick_filename, limerick_wordcount
                 FROM users WHERE username=?""", (username,))
    row = c.fetchone()
    conn.close()
    return row

def create_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

def update_details(username, firstname, lastname, email, address):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""UPDATE users
                 SET firstname=?, lastname=?, email=?, address=?
                 WHERE username=?""",
              (firstname, lastname, email, address, username))
    conn.commit()
    conn.close()

def update_limerick(username, filename, wordcount):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""UPDATE users
                 SET limerick_filename=?, limerick_wordcount=?
                 WHERE username=?""", (filename, wordcount, username))
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return redirect(url_for("register_page"))

# 4a) Registration page
@app.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Username and password are required.")
            return redirect(url_for("register_page"))

        try:
            create_user(username, password)
        except sqlite3.IntegrityError:
            flash("That username already exists.")
            return redirect(url_for("register_page"))

        session["username"] = username
        return redirect(url_for("details_page"))

    return render_template("register.html")

# 4b) Details page
@app.route("/details", methods=["GET", "POST"])
def details_page():
    if "username" not in session:
        return redirect(url_for("login_page"))

    if request.method == "POST":
        firstname = request.form.get("firstname", "").strip()
        lastname = request.form.get("lastname", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()

        update_details(session["username"], firstname, lastname, email, address)
        return redirect(url_for("profile_page"))

    return render_template("details.html")

# 4c) Display page
@app.route("/profile")
def profile_page():
    if "username" not in session:
        return redirect(url_for("login_page"))

    user = get_user(session["username"])
    return render_template("profile.html", user=user)

# 4d) Re-login page
@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        user = get_user(username)
        if not user or user[1] != password:
            flash("Invalid username or password.")
            return redirect(url_for("login_page"))

        session["username"] = username
        return redirect(url_for("profile_page"))

    return render_template("login.html")

@app.route("/logout")
def logout_page():
    session.pop("username", None)
    return redirect(url_for("login_page"))

# 4e) Upload Limerick.txt and word count
@app.route("/upload", methods=["POST"])
def upload_limerick():
    if "username" not in session:
        return redirect(url_for("login_page"))

    if "file" not in request.files:
        flash("No file part.")
        return redirect(url_for("profile_page"))

    f = request.files["file"]
    if f.filename == "":
        flash("No file selected.")
        return redirect(url_for("profile_page"))

    if f.filename.lower() != "limerick.txt":
        flash("Please upload the file named Limerick.txt")
        return redirect(url_for("profile_page"))

    save_name = f"{session['username']}_Limerick.txt"
    save_path = os.path.join(UPLOAD_DIR, save_name)
    f.save(save_path)

    with open(save_path, "r", encoding="utf-8", errors="ignore") as fp:
        text = fp.read()
    wordcount = len(text.split())

    update_limerick(session["username"], save_name, wordcount)
    return redirect(url_for("profile_page"))

@app.route("/download")
def download_limerick():
    if "username" not in session:
        return redirect(url_for("login_page"))

    user = get_user(session["username"])
    filename = user[6]
    if not filename:
        flash("No uploaded file found.")
        return redirect(url_for("profile_page"))

    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
