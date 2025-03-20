import sqlite3
from datetime import datetime

# Initialize database and create tables
def initialize_db():
    conn = sqlite3.connect('finance_app.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        type TEXT CHECK(type IN ('Income', 'Expense')) NOT NULL,
        date TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category TEXT NOT NULL,
        limit_amount REAL NOT NULL,
        month_year TEXT NOT NULL,
        UNIQUE(user_id, category, month_year),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    conn.commit()
    conn.close()

# User registration
def register_user(username, password):
    try:
        conn = sqlite3.connect('finance_app.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        print("User registered successfully!")
    except sqlite3.IntegrityError:
        print("Username already taken. Please try again.")
    finally:
        conn.close()

# User authentication
def authenticate_user(username, password):
    conn = sqlite3.connect('finance_app.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

# Add transaction
def add_transaction(user_id, amount, category, type):
    conn = sqlite3.connect('finance_app.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO transactions (user_id, amount, category, type) VALUES (?, ?, ?, ?)',
                   (user_id, amount, category, type))
    conn.commit()
    conn.close()
    print("Transaction added successfully!")
    check_budget_exceed(user_id, category)

# View transactions
def view_transactions(user_id):
    conn = sqlite3.connect('finance_app.db')
    cursor = conn.cursor()
    cursor.execute('SELECT amount, category, type, date FROM transactions WHERE user_id = ?', (user_id,))
    transactions = cursor.fetchall()
    conn.close()
    if transactions:
        print("\nYour Transactions:")
        for t in transactions:
            print(f"{t[3]} - {t[2]}: {t[1]} ({t[0]})")
    else:
        print("No transactions found.")

# Generate financial reports
def generate_financial_reports(user_id):
    conn = sqlite3.connect('finance_app.db')
    cursor = conn.cursor()
    
    # Monthly report
    current_month = datetime.now().strftime('%Y-%m')
    cursor.execute('''
        SELECT type, SUM(amount) 
        FROM transactions 
        WHERE user_id = ? AND strftime('%Y-%m', date) = ?
        GROUP BY type
    ''', (user_id, current_month))
    monthly_report = dict(cursor.fetchall())

    # Yearly report
    current_year = datetime.now().strftime('%Y')
    cursor.execute('''
        SELECT type, SUM(amount) 
        FROM transactions 
        WHERE user_id = ? AND strftime('%Y', date) = ?
        GROUP BY type
    ''', (user_id, current_year))
    yearly_report = dict(cursor.fetchall())
    
    conn.close()
    
    print("\nMonthly Report:")
    print(f"Income: {monthly_report.get('Income', 0)}")
    print(f"Expenses: {monthly_report.get('Expense', 0)}")
    print(f"Savings: {monthly_report.get('Income', 0) - monthly_report.get('Expense', 0)}")

    print("\nYearly Report:")
    print(f"Income: {yearly_report.get('Income', 0)}")
    print(f"Expenses: {yearly_report.get('Expense', 0)}")
    print(f"Savings: {yearly_report.get('Income', 0) - yearly_report.get('Expense', 0)}")

# Set budget
def set_budget(user_id, category, limit_amount):
    month_year = datetime.now().strftime('%Y-%m')
    conn = sqlite3.connect('finance_app.db')
    cursor = conn.cursor()

    # Check if budget already exists
    cursor.execute('''
        SELECT id FROM budgets 
        WHERE user_id = ? AND category = ? AND month_year = ?
    ''', (user_id, category, month_year))
    budget_id = cursor.fetchone()

    if budget_id:
        # Update existing budget
        cursor.execute('''
            UPDATE budgets
            SET limit_amount = ?
            WHERE user_id = ? AND category = ? AND month_year = ?
        ''', (limit_amount, user_id, category, month_year))
        print(f"Budget updated for {category} to {limit_amount}.")
    else:
        # Insert new budget
        cursor.execute('''
            INSERT INTO budgets (user_id, category, limit_amount, month_year)
            VALUES (?, ?, ?, ?)
        ''', (user_id, category, limit_amount, month_year))
        print(f"Budget set for {category} at {limit_amount}.")

    conn.commit()
    conn.close()

# Check if budget is exceeded
def check_budget_exceed(user_id, category):
    month_year = datetime.now().strftime('%Y-%m')
    conn = sqlite3.connect('finance_app.db')
    cursor = conn.cursor()
    
    # Get total expenses for the category in the current month
    cursor.execute('''
        SELECT SUM(amount) FROM transactions 
        WHERE user_id = ? AND category = ? AND type = 'Expense' 
        AND strftime('%Y-%m', date) = ?
    ''', (user_id, category, month_year))
    total_expense = cursor.fetchone()[0] or 0

    # Get budget limit
    cursor.execute('''
        SELECT limit_amount FROM budgets 
        WHERE user_id = ? AND category = ? AND month_year = ?
    ''', (user_id, category, month_year))
    budget_limit = cursor.fetchone()

    if budget_limit and total_expense > budget_limit[0]:
        print(f"⚠️ Alert: You have exceeded your budget limit of {budget_limit[0]} for {category}! Total spent: {total_expense}")

    conn.close()

# Main program loop
def main():
    initialize_db()
    print("Welcome to the Personal Finance Management App!")
    
    user_id = None
    while True:
        print("\n1. Register")
        print("2. Login")
        print("3. Add Transaction")
        print("4. View Transactions")
        print("5. Generate Financial Reports")
        print("6. Set Budget")
        print("7. Exit")
        choice = input("Choose an option: ")
        
        if choice == '1':
            username = input("Enter a username: ")
            password = input("Enter a password: ")
            register_user(username, password)
        elif choice == '2':
            username = input("Enter your username: ")
            password = input("Enter your password: ")
            user_id = authenticate_user(username, password)
            if user_id:
                print("Login successful! Welcome,", username)
            else:
                print("Invalid credentials. Please try again.")
        elif choice == '3':
            if user_id:
                amount = float(input("Enter amount: "))
                category = input("Enter category (e.g., Food, Rent, Salary): ")
                type = input("Enter type (Income/Expense): ")
                add_transaction(user_id, amount, category, type)
            else:
                print("Please login first.")
        elif choice == '4':
            if user_id:
                view_transactions(user_id)
            else:
                print("Please login first.")
        elif choice == '5':
            if user_id:
                generate_financial_reports(user_id)
            else:
                print("Please login first.")
        elif choice == '6':
            if user_id:
                category = input("Enter category: ")
                limit_amount = float(input("Enter budget limit: "))
                set_budget(user_id, category, limit_amount)
            else:
                print("Please login first.")
        elif choice == '7':
            print("Exiting...")
            break
        else:
            print("Invalid option. Please choose again.")

if __name__ == "__main__":
    main()