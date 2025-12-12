import sqlite3
from datetime import datetime

DB_FILENAME = "vehicules_finance.db"

conn = sqlite3.connect(DB_FILENAME)
cursor = conn.cursor()

# ------------------------------
# Création tables
# ------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS finance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matricule TEXT,
    date TEXT,
    designation TEXT,
    versement REAL,
    depense REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS entretien (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    date_echeance TEXT
)
""")

conn.commit()

# ------------------------------
# Ajouter utilisateur existant
# ------------------------------
try:
    cursor.execute("INSERT INTO users(username,password) VALUES(?,?)", ("admin","1234"))
except sqlite3.IntegrityError:
    pass  # utilisateur existe déjà

# ------------------------------
# Ajouter données Finance de ton Tkinter
# Remplace ou ajoute ici toutes les données existantes
# ------------------------------
finance_data = [
    ("ABC-123","01-12-2025","Carburant",100,0),
    ("XYZ-456","05-12-2025","Entretien",0,50),
    ("DEF-789","10-12-2025","Assurance",0,75),
    ("GHI-321","11-12-2025","Peinture",0,120),
    ("JKL-654","12-12-2025","Réparation moteur",0,200)
]

for f in finance_data:
    cursor.execute("INSERT INTO finance(matricule,date,designation,versement,depense) VALUES(?,?,?,?,?)", f)

# ------------------------------
# Ajouter données Entretien de ton Tkinter
entretien_data = [
    ("Vidange","15-12-2025"),
    ("Papier","20-12-2025"),
    ("Contrôle technique","25-12-2025"),
    ("Révision générale","30-12-2025")
]

for e in entretien_data:
    cursor.execute("INSERT INTO entretien(type,date_echeance) VALUES(?,?)", e)

conn.commit()
conn.close()

print(f"{DB_FILENAME} créé avec toutes les données !")
