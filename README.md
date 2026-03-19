# SQL Injection Demo

A web application that demonstrates a SQL injection attack and its mitigation.
Built with Python, Flask, and SQLite.

---

## What It Does

- Presents a login form with two modes: **Vulnerable** and **Secure**
- In **Vulnerable mode**: the login query is built by string concatenation — a SQL injection attack bypasses authentication entirely
- In **Secure mode**: parameterized queries are used — the same attack is blocked
- After each login attempt, the app displays the SQL query that ran and explains what happened

---

## Setup

### Prerequisites
- Python 3.8+
- pip

### Install dependencies
```bash
git clone https://github.com/GuySananes/sql_injection_demo.git
cd sql_injection_demo
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run
```bash
python app.py
```

Then open your browser at: `http://127.0.0.1:5000`

The database is initialized automatically on startup.

---

## Demonstrating the Attack

1. Open the app in your browser
2. Make sure **Vulnerable Mode** is selected (red toggle)
3. Enter the following and click Login:
   - Username: `' OR '1'='1`
   - Password: anything
4. Login succeeds without valid credentials — the injected SQL manipulates the query
5. Switch to **Secure Mode** (green toggle) and repeat the same input
6. Login fails — the parameterized query treats the input as a literal string, not SQL

---

## Project Structure
```
sql_injection_demo/
├── app.py              # Flask app — vulnerable and secure login routes
├── database.py         # Database initialization and test user seeding
├── requirements.txt    # Python dependencies
├── templates/
│   ├── index.html      # Login form with mode toggle
│   └── result.html     # Login result + SQL query display
└── README.md
```

---

## How the Vulnerability Works

**Vulnerable query (string concatenation):**
```python
query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
```

With input `' OR '1'='1`, the query becomes:
```sql
SELECT * FROM users WHERE username = '' OR '1'='1' AND password = 'anything'
```
`'1'='1'` is always true → returns all users → login succeeds.

**Secure query (parameterized):**
```python
cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
```
User input is passed separately — the database treats it as a literal value, never as SQL syntax.

---

## Test Credentials

| Username | Password |
|----------|----------|
| admin    | password123 |