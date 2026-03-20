# app.py
# The main Flask application. Handles all routes and login logic.
# Contains TWO versions of the login: vulnerable (SQLi possible) and secure (SQLi blocked).

import sqlite3
from flask import Flask, request, render_template

# Initialize the Flask app
# __name__ tells Flask where to look for templates and static files
app = Flask(__name__)


def get_db_connection():
    """
    Opens and returns a connection to the SQLite database.
    Called every time a login request is made.
    """
    conn = sqlite3.connect("users.db")
    # row_factory lets us access columns by name (e.g. row["username"])
    # instead of by index (e.g. row[0])
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    """
    Home route — renders the login form.
    The template (index.html) will let the user choose between
    vulnerable mode and secure mode.
    """
    return render_template("index.html")


@app.route("/login/vulnerable", methods=["POST"])
def login_vulnerable():
    """
    VULNERABLE login route — intentionally insecure.

    The SQL query is built by directly concatenating user input into the query string.
    This means an attacker can inject their own SQL and manipulate the query.

    Example attack input:
        username: ' OR '1'='1
        password: anything

    Resulting query:
        SELECT * FROM users WHERE username = '' OR '1'='1' AND password = 'anything'
    '1'='1' is always true → query returns all users → login succeeds.
    """
    username = request.form["username"]
    password = request.form["password"]

    # ❌ DANGEROUS: user input pasted directly into the query string
    # An attacker controls what goes inside the quotes
    query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(query)
        user = cursor.fetchone()  # fetchone() returns the first matching row, or None
    except Exception as e:
        # If the injected SQL causes a syntax error, catch it gracefully
        conn.close()
        return render_template("result.html",
                               success=False,
                               message=f"SQL Error: {str(e)}",
                               query=query,
                               mode="vulnerable")

    conn.close()

    if user:
        return render_template("result.html",
                               success=True,
                               message="Login successful! (Vulnerable mode)",
                               query=query,
                               mode="vulnerable")
    else:
        return render_template("result.html",
                               success=False,
                               message="Login failed. (Vulnerable mode)",
                               query=query,
                               mode="vulnerable")


@app.route("/login/secure", methods=["POST"])
def login_secure():
    """
    SECURE login route — parameterized queries used.

    Instead of pasting input into the query string, we pass it separately as parameters.
    The database driver handles escaping — user input is always treated as a literal value,
    never as SQL syntax.

    Same attack input (' OR '1'='1) now becomes a harmless string that simply
    won't match any username in the database.
    """
    username = request.form["username"]
    password = request.form["password"]

    # ✅ SAFE: The ? placeholders are filled in by the DB driver, not by string concatenation
    # User input cannot break out of the value context — it's never interpreted as SQL
    query = "SELECT * FROM users WHERE username = ? AND password = ?"

    conn = get_db_connection()
    cursor = conn.cursor()

    # The tuple (username, password) is passed separately — the DB handles the binding
    cursor.execute(query, (username, password))
    user = cursor.fetchone()

    conn.close()

    # For display purposes, show the query with the actual values substituted in
    display_query = "SELECT * FROM users WHERE username = ? AND password = ?"

    if user:
        return render_template("result.html",
                               success=True,
                               message="Login successful! (Secure mode)",
                               query=display_query,
                               mode="secure")
    else:
        return render_template("result.html",
                               success=False,
                               message="Login failed. (Secure mode)",
                               query=display_query,
                               mode="secure")


# Entry point — runs the Flask development server
# debug=True enables auto-reload on file changes and detailed error pages
if __name__ == "__main__":
    from database import init_db
    init_db()          # Initialize the DB every time the app starts
    app.run(debug=True)