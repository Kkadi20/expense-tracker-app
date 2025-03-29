Expense Tracker App

  Overview

The Expense Tracker App is a simple yet powerful application that helps users track their expenses efficiently. The application allows users to add, view, and manage their expenses, providing insights into their spending habits.

 Features

 Add, edit, and delete expenses

 Categorize expenses (food, travel, shopping, etc.)

 View total expenses and spending trends
 
 Data persistence using a database

 API integration for currency conversion

local Setup (Run Application Locally)

Prerequisites

Ensure you have the following installed on your system:

Python 3.10+

Node.js & npm (if using React)

PostgreSQL (or SQLite)

Step 1: Clone the Repository

git clone https://github.com/Kkadi20/expense-tracker-app.git
cd expense-tracker-app

Step 2: Install Dependencies

pip install -r requirements.txt

Step 3: Run the Application

python expense-tracker-app.py  # using Flask/FastAPI


APIs Used

Challenges Faced & Solutions

 Database Migration Issues

Issue: Initial migrations were failing due to misconfigured database settings.

Solution: Used DEBUG=True to identify the issue, then fixed the database URI format.

 Acknowledgments

This app used Fast Price - Exchange rates API  and Open-source libraries such as flask 

Author 

The project is written by : Kadi Matou Koita 














