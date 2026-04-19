import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Daten aus dem Dashboard für den Belegungsplan
class Occupation(BaseModel):
    day: str
    start_time: str
    end_time: str
    label: str

app = FastAPI()

# Erstellung der Kommunikation zwischen FrontEnd & BackEnd
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "AeroGuard Backend is running"}

@app.get("/api/sensor-test")
def get_sensor_test():
    # Simualtion der Sensordaten zum Test
    return {
        "co2": 1100,
        "temperature": 30,
        "humidity": 48,
        "iaq_score": 90
    }

# Initialiserung der Datenbank
def init_db():
    conn = sqlite3.connect("aeroguard.db")
    cursor = conn.cursor()
    # Sensordaten-Tabelle
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            co2 INTEGER,
            temperature REAL,
            humidity REAL,
            iaq_score INTEGER
        )
    ''')
    # Belegungsplan-Tabelle
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS occupations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT,
            start_time TEXT,
            end_time TEXT,
            label TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.post("/api/occupations")
def add_occupation(occ: Occupation):
    conn = sqlite3.connect("aeroguard.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO occupations (day, start_time, end_time, label) VALUES (?, ?, ?, ?)",
        (occ.day, occ.start_time, occ.end_time, occ.label)
    )
    conn.commit()
    conn.close()
    return {"message": "Kurs erfolgreich hinzugefügt!"}

@app.get("/api/occupations")
def get_occupations():
    conn = sqlite3.connect("aeroguard.db")
    # row_factory permet de transformer les résultats en dictionnaires Python (plus facile pour le JSON)
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM occupations")
    rows = cursor.fetchall()
    
    # On transforme les lignes de la DB en une liste de dictionnaires
    occupations = [dict(row) for row in rows]
    conn.close()
    return occupations

@app.delete("/api/occupations/{occ_id}")
def delete_occupation(occ_id: int):
    conn = sqlite3.connect("aeroguard.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM occupations WHERE id = ?", (occ_id,))
    conn.commit()
    conn.close()
    return {"message": "Cours supprimé avec succès"}

init_db()
