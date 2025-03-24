#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import datetime
import requests

app = Flask(__name__, template_folder="templates")

# Currency API URL for fetching exchange rates
API_KEY = '652192adb22c4fae65307ae1' 
API_URL = f'https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD'

# Initialize the SQLite database and create the expenses table if it doesn't exist
def init_db():
    """Initializes the SQLite database and creates the expenses table if it doesn't exist."""
    with sqlite3.connect("expenses.db") as conn:
        cur = conn.cursor()
        # Create a table for storing expenses
        cur.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                currency TEXT NOT NULL DEFAULT 'USD',
                date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()


# Fetch exchange rate for a given currency from the external API
import requests

API_KEY = '652192adb22c4fae65307ae1'  # Your API key
API_URL = f'https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD'

# Fetch exchange rate for a given currency from the external API
def get_exchange_rate(currency):
    try:
        response = requests.get(API_URL)
        data = response.json()

        # Check if the response contains conversion rates
        if "conversion_rates" in data:
            rate = data["conversion_rates"].get(currency.upper())
            if rate:
                return rate  # Return the exchange rate
            else:
                print(f"Currency {currency} not found in API response.")
                return None
        else:
            print(f"API error: {data}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None


# Home Page - Show the list of expenses from the database
@app.route("/")
def home():
    """Displays the list of expenses from the database on the home page."""
    with sqlite3.connect("expenses.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, description, amount, category, currency, date FROM expenses ORDER BY date DESC")
        expenses = cur.fetchall()
    # Render the 'index.html' template and pass the expenses data to it
    return render_template("index.html", expenses=expenses)

# Add a new expense to the database
@app.route("/add", methods=["POST"])
def add_expense():
    """Adds a new expense to the database based on user input from the form."""
    description = request.form["description"]
    amount = float(request.form["amount"])  # Convert amount to a float
    category = request.form["category"]
    currency = request.form.get("currency", "USD").upper()  # Default to USD if no currency is selected

    with sqlite3.connect("expenses.db") as conn:
        cur = conn.cursor()
        # Insert the new expense into the database
        cur.execute("INSERT INTO expenses (description, amount, category, currency, date) VALUES (?, ?, ?, ?, ?)",
                    (description, amount, category, currency, datetime.datetime.now()))
        conn.commit()

    # Redirect to the home page after adding the expense
    return redirect(url_for("home"))


# Convert all expenses to a different currency
@app.route("/convert")
def convert_expenses():
    currency = request.args.get('currency', 'USD').upper()  # Default to USD if no currency is provided
    rate = get_exchange_rate(currency)

    if not rate:
        return jsonify({"error": "Invalid currency or API issue"}), 400  # Handle failure if rate not found

    with sqlite3.connect("expenses.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, description, amount, category, currency, date FROM expenses ORDER BY date DESC")
        expenses = cur.fetchall()

    converted_expenses = [
        {
            "id": exp[0],
            "description": exp[1],
            "amount": round(exp[2] * rate, 2),  # Convert the amount
            "category": exp[3],
            "currency": currency,  # Updated currency symbol
            "date": exp[5]
        }
        for exp in expenses
    ]

    return render_template("index.html", expenses=converted_expenses)

   
# Delete an expense from the database by its ID
@app.route("/delete/<int:expense_id>")
def delete_expense(expense_id):
    """Deletes an expense from the database by its ID."""
    with sqlite3.connect("expenses.db") as conn:
        cur = conn.cursor()
        # Delete the expense from the database by its ID
        cur.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()

    # Redirect to the home page after deleting the expense
    return redirect(url_for("home"))

if __name__ == "__main__":
    # Initialize the database when the app starts
    init_db()
    # Run the Flask application
    app.run(debug=True)

