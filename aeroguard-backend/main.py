import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

init_db()
