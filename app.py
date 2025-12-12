#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
from datetime import datetime
from io import BytesIO
import openpyxl

app = Flask(__name__)
app.secret_key = "mananjina_secret"

DB_FILE = "vehicules_finance.db"

# ------------------------------
# Base de données
# ------------------------------
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ------------------------------
# Login / Inscription
# ------------------------------
@app.route('/', methods=['GET','POST'])
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, role FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            return render_template("login.html", error="Identifiants incorrects")
    return render_template("login.html")

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        role = request.form.get('role','client')
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)",(username,password,role))
            conn.commit()
        except sqlite3.IntegrityError:
            return render_template("register.html", error="Nom déjà utilisé")
        conn.close()
        return redirect(url_for('login'))
    return render_template("register.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ------------------------------
# Totaux finances
# ------------------------------
def calculate_totals():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(versement), SUM(depense) FROM finance")
    v, d = cursor.fetchone()
    conn.close()
    v = v or 0
    d = d or 0
    return {"versement": v, "depense": d, "reste": v - d}

# ------------------------------
# Dashboard
# ------------------------------
@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    role = session.get('role','client')
    search = request.args.get('search','').strip()
    conn = get_db()
    cursor = conn.cursor()

    # Rechercher finance
    if search:
        cursor.execute("""SELECT * FROM finance 
                          WHERE matricule LIKE ? OR designation LIKE ? 
                          ORDER BY id DESC""", (f"%{search}%", f"%{search}%"))
    else:
        cursor.execute("SELECT * FROM finance ORDER BY id DESC")
    finances = cursor.fetchall()

    # Entretiens
    cursor.execute("SELECT * FROM entretien ORDER BY id DESC")
    entretiens = cursor.fetchall()
    conn.close()

    totals = calculate_totals()
    alerts = check_alerts()  # Alertes entretien expiré
    return render_template("dashboard.html", finances=finances, entretiens=entretiens, totals=totals, role=role, search=search, alerts=alerts)

# ------------------------------
# Formulaires GET pour ajout
# ------------------------------
@app.route('/add_finance_form')
def add_finance_form():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("add_finance.html")

@app.route('/add_entretien_form')
def add_entretien_form():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("add_entretien.html")

# ------------------------------
# Finance CRUD
# ------------------------------
@app.route('/add_finance', methods=['POST'])
def add_finance():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    matricule = request.form['matricule'].strip()
    date = request.form['date'].strip()
    designation = request.form['designation'].strip()
    versement = float(request.form['versement'] or 0)
    depense = float(request.form['depense'] or 0)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO finance(matricule,date,designation,versement,depense) VALUES(?,?,?,?,?)",
                   (matricule,date,designation,versement,depense))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/edit_finance/<int:id>', methods=['GET','POST'])
def edit_finance(id):
    if 'user_id' not in session or session.get('role')!='admin':
        return redirect(url_for('dashboard'))
    conn = get_db()
    cursor = conn.cursor()
    if request.method=='POST':
        matricule = request.form['matricule'].strip()
        date = request.form['date'].strip()
        designation = request.form['designation'].strip()
        versement = float(request.form['versement'] or 0)
        depense = float(request.form['depense'] or 0)
        cursor.execute("UPDATE finance SET matricule=?,date=?,designation=?,versement=?,depense=? WHERE id=?",
                       (matricule,date,designation,versement,depense,id))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    cursor.execute("SELECT * FROM finance WHERE id=?",(id,))
    f = cursor.fetchone()
    conn.close()
    return render_template("edit_finance.html", f=f)

@app.route('/delete_finance/<int:id>')
def delete_finance(id):
    if 'user_id' not in session or session.get('role')!='admin':
        return redirect(url_for('dashboard'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM finance WHERE id=?",(id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

# ------------------------------
# Entretien CRUD
# ------------------------------
@app.route('/add_entretien', methods=['POST'])
def add_entretien():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    type_ent = request.form['type'].strip()
    date_ech = request.form['date_echeance'].strip()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO entretien(type,date_echeance) VALUES(?,?)",(type_ent,date_ech))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/edit_entretien/<int:id>', methods=['GET','POST'])
def edit_entretien(id):
    if 'user_id' not in session or session.get('role')!='admin':
        return redirect(url_for('dashboard'))
    conn = get_db()
    cursor = conn.cursor()
    if request.method=='POST':
        type_ent = request.form['type'].strip()
        date_ech = request.form['date_echeance'].strip()
        cursor.execute("UPDATE entretien SET type=?,date_echeance=? WHERE id=?",(type_ent,date_ech,id))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    cursor.execute("SELECT * FROM entretien WHERE id=?",(id,))
    e = cursor.fetchone()
    conn.close()
    return render_template("edit_entretien.html", e=e)

@app.route('/delete_entretien/<int:id>')
def delete_entretien(id):
    if 'user_id' not in session or session.get('role')!='admin':
        return redirect(url_for('dashboard'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM entretien WHERE id=?",(id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

# ------------------------------
# Export Excel
# ------------------------------
@app.route('/export_excel')
def export_excel():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM finance ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["ID","Matricule","Date","Désignation","Versement","Dépense"])
    for r in rows:
        ws.append([r['id'], r['matricule'], r['date'], r['designation'], r['versement'], r['depense']])
    
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return send_file(bio, download_name="finance.xlsx", as_attachment=True)

# ------------------------------
# Export CSV
# ------------------------------
@app.route('/export_csv')
def export_csv():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    import csv
    from io import StringIO
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM finance ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["ID","Matricule","Date","Désignation","Versement","Dépense"])
    for r in rows:
        writer.writerow([r['id'], r['matricule'], r['date'], r['designation'], r['versement'], r['depense']])
    output = BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    return send_file(output, download_name="finance.csv", as_attachment=True)

# ------------------------------
# Alertes entretien expiré
# ------------------------------
def check_alerts():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT type,date_echeance FROM entretien")
    rows = cursor.fetchall()
    today = datetime.now().date()
    alerts = []
    for r in rows:
        try:
            d = datetime.strptime(r['date_echeance'], "%d-%m-%Y").date()
            if d <= today:
                alerts.append(f"{r['type']} expiré le {d.strftime('%d-%m-%Y')}")
        except:
            continue
    conn.close()
    return alerts

# ------------------------------
# Lancer app
# ------------------------------
if __name__ == '__main__':
    app.run(debug=True)
