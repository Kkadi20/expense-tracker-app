#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import datetime
import requests
import schedule
import time
import threading
import redis


app = Flask(__name__, template_folder="templates")

# Initialize the SQLite database and create necessary tables
def init_db():
    """Initializes the SQLite database and creates tables for expenses and budgets."""
    with sqlite3.connect("expenses.db") as conn:
        cur = conn.cursor()
        # Create expenses table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                currency TEXT NOT NULL DEFAULT 'USD',
                date TEXT DEFAULT CURRENT_TIMESTAMP,
                recurring INTEGER DEFAULT 0 -- 0: Non-recurring, 1: Recurring
            )
        ''')
        # Create budget table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS budget (
                category TEXT PRIMARY KEY,
                amount REAL NOT NULL
            )
        ''')
        conn.commit()

# Currency Exchange API Details
API_KEY = 'e4d962c480msh81c080e0b9b1642p141641jsnc8a3703e3f64'
API_URL = 'https://fast-price-exchange-rates.p.rapidapi.com/api/v1/convert'

# Initialize Redis
cache = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def get_exchange_rate(currency):
    """Fetch exchange rate with caching"""
    cache_key = f"exchange_rate:{currency}"

    # Check if exchange rate is cached
    cached_rate = cache.get(cache_key)
    if cached_rate:
        print("Cache hit!")  # Debugging
        return float(cached_rate)  # Use cached value

    print("Cache miss!")  # Debugging
    API_URL = f"https://api.exchangerate-api.com/v4/latest/USD"
    
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
        
        if currency in data["rates"]:
            rate = data["rates"][currency]
            
            # Cache the rate for 5 minutes
            cache.setex(cache_key, 300, rate)
            return rate
    except requests.RequestException:
        return None


@app.route("/")
def home():
    """Displays the home page with a list of expenses."""
    with sqlite3.connect("expenses.db") as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM expenses ORDER BY date DESC")
        expenses = [dict(row) for row in cur.fetchall()]
    return render_template("index.html", expenses=expenses)

@app.route("/add", methods=["POST"])
def add_expense():
    """Adds a new expense to the database."""
    description = request.form["description"]
    amount = float(request.form["amount"])
    category = request.form["category"]
    currency = request.form.get("currency", "USD").upper()
    recurring = int(request.form.get("recurring", 0))

    with sqlite3.connect("expenses.db") as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO expenses (description, amount, category, currency, date, recurring) VALUES (?, ?, ?, ?, ?, ?)",
                    (description, amount, category, currency, datetime.datetime.now().isoformat(), recurring))
        conn.commit()

    return redirect(url_for("home"))

@app.route("/convert")
def convert_expenses():
    """Converts and displays expenses in a selected currency."""
    currency = request.args.get('currency', 'USD').upper()
    rate = get_exchange_rate(currency)
    if not rate:
        return jsonify({"error": "Invalid currency or API issue"}), 400

    with sqlite3.connect("expenses.db") as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM expenses ORDER BY date DESC")
        expenses = [dict(row) for row in cur.fetchall()]
    
    for exp in expenses:
        exp["amount"] = round(float(exp["amount"]) * rate, 2)
        exp["currency"] = currency
    
    return render_template("index.html", expenses=expenses)

@app.route("/delete/<int:expense_id>")
def delete_expense(expense_id):
    """Deletes an expense by ID."""
    with sqlite3.connect("expenses.db") as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
    return redirect(url_for("home"))

@app.route("/set-budget", methods=["POST"])
def set_budget():
    """Sets a budget for a specific category."""
    category = request.form["category"]
    amount = float(request.form["amount"])
    with sqlite3.connect("expenses.db") as conn:
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO budget (category, amount) VALUES (?, ?)", (category, amount))
        conn.commit()
    return redirect(url_for("home"))

@app.route("/budget-alerts")
def budget_alerts():
    """Checks if spending exceeds the budget and returns alerts."""
    alerts = []
    with sqlite3.connect("expenses.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
        category_spendings = dict(cur.fetchall())
        cur.execute("SELECT * FROM budget")
        budgets = dict(cur.fetchall())
    for category, budget in budgets.items():
        if category_spendings.get(category, 0) > budget:
            alerts.append(f"Warning: You have exceeded the budget for {category}")
    return jsonify({"alerts": alerts})
def process_recurring_expenses():
    """Automatically adds recurring expenses."""
    with sqlite3.connect("expenses.db") as conn:
        cur = conn.cursor()

        cur.execute("SELECT description, amount, category, currency FROM expenses WHERE recurring = 1")
        recurring_expenses = cur.fetchall()

        for exp in recurring_expenses:
            cur.execute(
                "INSERT INTO expenses (description, amount, category, currency, date, recurring) VALUES (?, ?, ?, ?, ?, 1)",
                (exp[0], exp[1], exp[2], exp[3], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )

        conn.commit()


# Schedule recurring expense processing every 24 hours
schedule.every().day.at("00:00").do(process_recurring_expenses)

def run_scheduler():
    """Runs the scheduler in a separate thread."""
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_scheduler, daemon=True).start()
    app.run(debug=True)
