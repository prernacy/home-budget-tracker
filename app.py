from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS weeks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_name TEXT NOT NULL,
            budget REAL NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY (week_id) REFERENCES weeks (id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

with app.app_context():
    init_db()

@app.route('/')
def index():
    conn = get_db_connection()
    weeks = conn.execute('SELECT * FROM weeks').fetchall()
    
    weeks_data = []
    total_budget_all = 0
    total_spent_all = 0
    
    for w in weeks:
        expenses = conn.execute('SELECT * FROM expenses WHERE week_id = ?', (w['id'],)).fetchall()
        spent = sum(e['amount'] for e in expenses)
        budget = w['budget']
        diff = budget - spent
        
        total_budget_all += budget
        total_spent_all += spent
        
        weeks_data.append({
            'id': w['id'],
            'week_name': w['week_name'],
            'budget': budget,
            'spent': spent,
            'diff': diff,
            'expenses': expenses
        })
        
    conn.close()
    return render_template('index.html', weeks=weeks_data, total_budget=total_budget_all, total_spent=total_spent_all)

@app.route('/add_week', methods=['POST'])
def add_week():
    week_name = request.form['week_name']
    budget = float(request.form['budget'])
    conn = get_db_connection()
    conn.execute('INSERT INTO weeks (week_name, budget) VALUES (?, ?)', (week_name, budget))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete_week/<int:week_id>', methods=['POST'])
def delete_week(week_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM expenses WHERE week_id = ?', (week_id,))
    conn.execute('DELETE FROM weeks WHERE id = ?', (week_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/add_expense/<int:week_id>', methods=['POST'])
def add_expense(week_id):
    title = request.form['title']
    amount = float(request.form['amount'])
    conn = get_db_connection()
    conn.execute('INSERT INTO expenses (week_id, title, amount) VALUES (?, ?, ?)', (week_id, title, amount))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# --- NEW: UPDATE / EDIT EXPENSE ROUTE ---
@app.route('/edit_expense/<int:expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    conn = get_db_connection()
    if request.method == 'POST':
        title = request.form['title']
        amount = float(request.form['amount'])
        conn.execute('UPDATE expenses SET title = ?, amount = ? WHERE id = ?', (title, amount, expense_id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    
    expense = conn.execute('SELECT * FROM expenses WHERE id = ?', (expense_id,)).fetchone()
    conn.close()
    return render_template('edit_expense.html', expense=expense)

@app.route('/api/chart_data')
def chart_data():
    conn = get_db_connection()
    weeks = conn.execute('SELECT * FROM weeks').fetchall()
    labels = []
    budgets = []
    spent_list = []
    for w in weeks:
        expenses = conn.execute('SELECT SUM(amount) as total FROM expenses WHERE week_id = ?', (w['id'],)).fetchone()
        spent = expenses['total'] if expenses['total'] else 0.0
        labels.append(w['week_name'])
        budgets.append(w['budget'])
        spent_list.append(spent)
    conn.close()
    return jsonify({'labels': labels, 'budgets': budgets, 'spent': spent_list})

if __name__ == '_main_':
    app.run(debug=True)