from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

def db():
    return sqlite3.connect('expense.db')

def norm(x):
    return x.strip().lower()

# ---------- INIT ----------
conn = db()
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS users (name TEXT UNIQUE)")

c.execute("""
CREATE TABLE IF NOT EXISTS expenses (
 payer TEXT,
 amount REAL,
 type TEXT
)
""")

c.execute("CREATE TABLE IF NOT EXISTS splits (user TEXT, share REAL)")

# ✅ NEW HISTORY TABLE
c.execute("""
CREATE TABLE IF NOT EXISTS history (
 payer TEXT,
 amount REAL,
 type TEXT
)
""")

conn.commit()
conn.close()

# ---------- ADD USER ----------
@app.route('/add_user', methods=['POST'])
def add_user():
    name = norm(request.json['name'])
    conn = db(); c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?)", (name,))
    except:
        pass
    conn.commit(); conn.close()
    return jsonify({'msg':'ok'})

# ---------- USERS ----------
@app.route('/users')
def users():
    conn = db(); c = conn.cursor()
    c.execute("SELECT name FROM users")
    data = [x[0].capitalize() for x in c.fetchall()]
    conn.close()
    return jsonify(data)

# ---------- ADD EXPENSE ----------
@app.route('/add_expense', methods=['POST'])
def add_expense():
    d = request.json

    payer = norm(d['payer'])
    amount = float(d['amount'])
    type_ = d.get('type', 'equal')

    participants = [norm(x) for x in d['participants'] if x.strip()!=""]

    conn = db(); c = conn.cursor()

    # auto-create users
    c.execute("SELECT name FROM users")
    existing = {x[0] for x in c.fetchall()}

    for u in participants + [payer]:
        if u not in existing:
            c.execute("INSERT INTO users VALUES (?)",(u,))

    # insert expense
    c.execute("INSERT INTO expenses VALUES (?,?,?)",(payer,amount,type_))

    # splits
    if type_ == "custom":
        for s in d['splits']:
            user = norm(s['user'])
            share = float(s['amount'])
            c.execute("INSERT INTO splits VALUES (?,?)",(user,share))
    else:
        split = amount / len(participants)
        for u in participants:
            c.execute("INSERT INTO splits VALUES (?,?)",(u,split))

    conn.commit(); conn.close()
    return jsonify({'msg':'ok'})

# ---------- CALCULATE ----------
def calc():
    conn = db(); c = conn.cursor()

    c.execute("SELECT name FROM users")
    users = [x[0] for x in c.fetchall()]
    bal = {u:0 for u in users}

    c.execute("SELECT payer,amount FROM expenses")
    for p,a in c.fetchall():
        bal[p]+=a

    c.execute("SELECT user,share FROM splits")
    for u,s in c.fetchall():
        bal[u]-=s

    conn.close()
    return bal

# ---------- BALANCE ----------
@app.route('/balances')
def balances():
    return jsonify(calc())

# ---------- SETTLE ----------
@app.route('/settle')
def settle():
    bal = calc()
    tx=[]

    while True:
        d=min(bal,key=bal.get)
        c=max(bal,key=bal.get)

        if round(bal[d],2)==0 and round(bal[c],2)==0:
            break

        amt=min(-bal[d],bal[c])

        tx.append({
            'from':d.capitalize(),
            'to':c.capitalize(),
            'amount':round(amt,2)
        })

        bal[d]+=amt
        bal[c]-=amt

    return jsonify(tx)

# ---------- RESET (NEW FEATURE) ----------
@app.route('/reset', methods=['POST'])
def reset():
    conn = db(); c = conn.cursor()

    # move to history
    c.execute("SELECT payer, amount, type FROM expenses")
    rows = c.fetchall()

    for r in rows:
        c.execute("INSERT INTO history VALUES (?,?,?)", r)

    # clear current session
    c.execute("DELETE FROM expenses")
    c.execute("DELETE FROM splits")

    conn.commit()
    conn.close()

    return jsonify({'msg':'reset done'})

# ---------- HISTORY ----------
@app.route('/history')
def history():
    conn = db(); c = conn.cursor()
    c.execute("SELECT payer, amount, type FROM history")
    data = c.fetchall()
    conn.close()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)