from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from decimal import Decimal
from datetime import datetime
import logging
import uuid
import hashlib

app = Flask(__name__)
app.secret_key = 'Sarvesh@123'

db_config = {
    'user': 'root',
    'password': 'Sarvesh@123',
    'host': 'localhost',
    'database': 'ledger_db'
}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def login():
    return render_template('pages-login.html')

@app.route('/login', methods=['POST'])
def handle_login():
    username = request.form['username']
    password = request.form['password']
    
    hashed_password = hash_password(password)
    
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
        
        query = "SELECT id FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, hashed_password))
        user_id = cursor.fetchone()
        
        if user_id:
            session['user_id'] = user_id[0]
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials')
            return redirect(url_for('login'))

    except mysql.connector.Error as err:
        print(f"Error fetching user data: {err}")
        flash('Error fetching user data')
        return redirect(url_for('login'))

@app.route('/create_account')
def create_account():
    return render_template('pages-register.html')

@app.route('/create_user', methods=['POST'])
def create_user():
    username = request.form['username']
    password = request.form['password']
    hashed_password = hash_password(password)
    
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
        
        query = "INSERT INTO users (username, password) VALUES (%s, %s)"
        cursor.execute(query, (username, hashed_password))
        
        cnx.commit()
        cursor.close()
        cnx.close()
        
        flash('Account created successfully')
        return redirect(url_for('login'))

    except mysql.connector.Error as err:
        print(f"Error inserting user data: {err}")
        flash('Error inserting user data')
        return redirect(url_for('create_account'))

@app.route('/index')
def index():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()

        query_accounts_receivable = "SELECT SUM(amount) FROM accounts_receivable WHERE user_id = %s"
        cursor.execute(query_accounts_receivable, (user_id,))
        total_receivable = cursor.fetchone()[0] or 0

        query_accounts_payable = "SELECT SUM(amount) FROM accounts_payable WHERE user_id = %s"
        cursor.execute(query_accounts_payable, (user_id,))
        total_payable = cursor.fetchone()[0] or 0

        query_monthly_receivable = "SELECT MONTH(date) AS month, SUM(amount) FROM accounts_receivable WHERE user_id = %s GROUP BY MONTH(date)"
        cursor.execute(query_monthly_receivable, (user_id,))
        monthly_receivable = cursor.fetchall()

        query_monthly_payable = "SELECT MONTH(ap_date) AS month, SUM(amount) FROM accounts_payable WHERE user_id = %s GROUP BY MONTH(ap_date)"
        cursor.execute(query_monthly_payable, (user_id,))
        monthly_payable = cursor.fetchall()

        query_due_dates = """
            SELECT 'Accounts Receivable' AS type, due_date FROM accounts_receivable WHERE user_id = %s
            UNION
            SELECT 'Accounts Payable' AS type, due_date FROM accounts_payable WHERE user_id = %s
        """
        cursor.execute(query_due_dates, (user_id, user_id))
        due_dates = cursor.fetchall()

        cursor.close()
        cnx.close()

        def decimal_to_float(data):
            if isinstance(data, Decimal):
                return float(data)
            elif isinstance(data, (list, tuple)):
                return [decimal_to_float(item) for item in data]
            elif isinstance(data, dict):
                return {key: decimal_to_float(value) for key, value in data.items()}
            else:
                return data

        monthly_receivable_dict = {month: float(amount) for month, amount in monthly_receivable}
        monthly_payable_dict = {month: float(amount) for month, amount in monthly_payable}
        due_dates_dict = {type: [due_date.isoformat() for (type, due_date) in due_dates]}

        return render_template('index.html',
                               total_receivable=total_receivable,
                               total_payable=total_payable,
                               monthly_receivable=monthly_receivable_dict,
                               monthly_payable=monthly_payable_dict,
                               due_dates=due_dates_dict)

    except mysql.connector.Error as err:
        print(f"Error fetching data: {err}")
        return "Error fetching data"

@app.route('/messages')
def messages():
    return render_template('messages.html')

@app.route('/terms_and_conditions')
def terms_and_conditions():
    return render_template('pages-terms&conditions.html')

@app.route('/accounts_receivable_form')
def accounts_receivable_form():
    return render_template('accounts_receivable_form.html')

@app.route('/add_accounts_receivable', methods=['POST'])
def add_accounts_receivable():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    date = request.form['date']
    description = request.form['description']
    amount = float(request.form['amount'])
    customer = request.form['customer']
    due_date = request.form['due_date']
    invoice_id = request.form.get('invoice_id', str(uuid.uuid4()))  
    
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
        
        query = """
            INSERT INTO accounts_receivable (user_id, date, description, amount, customer, due_date, invoice_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, date, description, amount, customer, due_date, invoice_id))
        
        cnx.commit()
        cursor.close()
        cnx.close()
        
        return redirect(url_for('finance_accounts_receivable'))

    except mysql.connector.Error as err:
        print(f"Error inserting data: {err}")
        return f"Error inserting data: {err}"

@app.route('/finance_accounts_receivable')
def finance_accounts_receivable():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
    
        query = "SELECT date, description, amount, customer, due_date FROM accounts_receivable WHERE user_id = %s"
        cursor.execute(query, (user_id,))
    
        receivable_entries = cursor.fetchall()
    
        cursor.close()
        cnx.close()
    
        return render_template('finance_accounts_receivable.html', receivable_entries=receivable_entries)
    
    except mysql.connector.Error as err:
        print(f"Error fetching accounts receivable data: {err}")
        return "Error fetching data"

@app.route('/accounts_payable_form')
def accounts_payable_form():
    return render_template('accounts_payable_form.html')

@app.route('/add_accounts_payable', methods=['POST'])
def add_accounts_payable():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    date = request.form['date']
    description = request.form['description']
    amount = float(request.form['amount'])
    vendor = request.form['vendor']
    due_date = request.form['due_date']
    
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
        
        query = """
            INSERT INTO accounts_payable (user_id, ap_date, description, amount, vendor, due_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, date, description, amount, vendor, due_date))
        
        cnx.commit()
        cursor.close()
        cnx.close()
        
        return redirect(url_for('finance_accounts_payable'))

    except mysql.connector.Error as err:
        print(f"Error inserting data: {err}")
        return "Error inserting data"

@app.route('/finance_accounts_payable')
def finance_accounts_payable():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
    
        query = "SELECT ap_date, description, amount, vendor, due_date FROM accounts_payable WHERE user_id = %s"
        cursor.execute(query, (user_id,))
    
        payable_entries = cursor.fetchall()
    
        cursor.close()
        cnx.close()
    
        return render_template('finance_accounts_payable.html', payable_entries=payable_entries)
    
    except mysql.connector.Error as err:
        print(f"Error fetching accounts payable data: {err}")
        return "Error fetching data"
    
@app.route('/finance_general_ledger')
def finance_general_ledger():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()

        # Fetch receivable entries for the logged-in user
        query_accounts_receivable = """
            SELECT date AS date, '' AS debit, amount AS credit, customer AS vendor_or_customer, due_date, '' AS balance
            FROM accounts_receivable
            WHERE user_id = %s
        """
        cursor.execute(query_accounts_receivable, (user_id,))
        receivable_entries = cursor.fetchall()

        # Fetch payable entries for the logged-in user
        query_accounts_payable = """
            SELECT ap_date AS date, amount AS debit, '' AS credit, vendor AS vendor_or_customer, due_date, '' AS balance
            FROM accounts_payable
            WHERE user_id = %s
        """
        cursor.execute(query_accounts_payable, (user_id,))
        payable_entries = cursor.fetchall()

        max_length = max(len(receivable_entries), len(payable_entries))

        cursor.close()
        cnx.close()

        return render_template('finance_general_ledger.html',
                               receivable_entries=receivable_entries,
                               payable_entries=payable_entries,
                               max_length=max_length)

    except mysql.connector.Error as err:
        print(f"Error retrieving data: {err}")
        return "Error fetching data"
    except Exception as e:
        print(f"Unexpected error: {e}")
        return "An unexpected error occurred"

@app.route('/cash_management_form')
def cash_management_form():
    return render_template('cash_management_form.html')

@app.route('/add_cash_management', methods=['POST'])
def add_cash_management():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    date = request.form['date']
    description = request.form['description']
    cash_inflow = float(request.form['cash_inflow'])
    cash_outflow = float(request.form['cash_outflow'])

    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()

        query = """
            INSERT INTO cash_management (user_id, date, description, cash_inflow, cash_outflow)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, date, description, cash_inflow, cash_outflow))

        cnx.commit()
        cursor.close()
        cnx.close()

        return redirect(url_for('finance_cash_management'))

    except mysql.connector.Error as err:
        print(f"Error inserting cash management data: {err}")
        return "Error inserting data"

@app.route('/finance_cash_management')
def finance_cash_management():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()

        query = "SELECT date, description, cash_inflow, cash_outflow FROM cash_management WHERE user_id = %s"
        cursor.execute(query, (user_id,))

        cash_entries = cursor.fetchall()

        cursor.close()
        cnx.close()

        return render_template('finance_cash_management.html', cash_entries=cash_entries)

    except mysql.connector.Error as err:
        print(f"Error fetching cash management data: {err}")
        return "Error fetching data"



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
