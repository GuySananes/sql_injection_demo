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

def detect_injection_technique(username, password):
    """
    Analyzes the user input to identify which SQLi technique was used.
    Returns a short label and explanation for display in the result page.
    """
    combined = (username + " " + password).upper()

    if "--" in username or "#" in username:
        return {
            "technique": "Comment Injection",
            "explanation": (
                "The input used a SQL comment sequence (-- or #) to strip the rest of the query. "
                "Everything after the comment marker is ignored by the database engine, "
                "effectively nullifying the password check."
            )
        }
    elif "UNION" in combined:
        return {
            "technique": "UNION-Based Injection",
            "explanation": (
                "The input attempted a UNION-based injection to append a second SELECT statement "
                "and extract data from other tables. This technique can be used to dump "
                "the entire database schema and contents."
            )
        }
    elif "OR" in combined and ("1=1" in combined.replace(" ", "") or "'1'='1'" in combined.replace(" ", "")):
        return {
            "technique": "OR-Based Tautology (Classic)",
            "explanation": (
                "The input used a classic OR tautology — ' OR '1'='1. "
                "Since '1'='1' is always true, the WHERE clause evaluates to true for every row, "
                "returning all users and bypassing authentication."
            )
        }
    elif "OR" in combined or "AND" in combined:
        return {
            "technique": "Boolean-Based Injection",
            "explanation": (
                "The input manipulated the WHERE clause using a boolean condition (OR/AND). "
                "This altered the query logic to return rows that should not have matched."
            )
        }
    elif "SLEEP" in combined or "WAITFOR" in combined or "BENCHMARK" in combined:
        return {
            "technique": "Time-Based Blind Injection",
            "explanation": (
                "The input attempted a time-based blind injection. "
                "By injecting SLEEP() or WAITFOR DELAY, attackers can infer database "
                "structure from response delays even when no data is returned."
            )
        }
    else:
        return {
            "technique": "Unknown / Custom Payload",
            "explanation": (
                "The input contained characters or patterns that broke the expected query structure. "
                "Manual review of the executed query is needed to understand the full impact."
            )
        }

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
    Uses string concatenation to build the SQL query.
    Fetches ALL matching rows to demonstrate data leakage.
    """
    username = request.form["username"]
    password = request.form["password"]

    # ❌ DANGEROUS: user input pasted directly into the query string
    query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(query)
        # fetchall() returns every row the query matched — not just the first one.
        # This demonstrates that a successful injection leaks the entire table,
        # not just grants access to one account.
        rows = cursor.fetchall()
    except Exception as e:
        conn.close()
        return render_template("result.html",
                               success=False,
                               message=f"SQL Error: {str(e)}",
                               query=query,
                               mode="vulnerable",
                               technique=None,
                               leaked_rows=None)

    conn.close()

    # Detect which SQLi technique was used — drives the dynamic explanation
    injection_info = detect_injection_technique(username, password)

    if rows:
        return render_template("result.html",
                               success=True,
                               message="Login successful! (Vulnerable mode)",
                               query=query,
                               mode="vulnerable",
                               technique=injection_info,
                               leaked_rows=[dict(row) for row in rows])
    else:
        return render_template("result.html",
                               success=False,
                               message="Login failed. (Vulnerable mode)",
                               query=query,
                               mode="vulnerable",
                               technique=None,
                               leaked_rows=None)

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
                               mode="secure",
                               technique=None,
                               leaked_rows=None)
    else:
        return render_template("result.html",
                               success=False,
                               message="Login failed. (Secure mode)",
                               query=display_query,
                               mode="secure",
                               technique=None,
                               leaked_rows=None)

# Entry point — runs the Flask development server
# debug=True enables auto-reload on file changes and detailed error pages
if __name__ == "__main__":
    from database import init_db
    init_db()          # Initialize the DB every time the app starts
    app.run(debug=True)