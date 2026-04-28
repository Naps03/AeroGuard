import sqlite3
import random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from iaq_score import calculate_iaq_index

#Letzte 10 CO2-Messungen
co2_history = [] 

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
    current_co2 = random.randint(1000, 2000) 
    
    prediction = calculate_co2_trend(current_co2)

    iaq = calculate_iaq_index(current_co2, 22.5, 45)
    
    return {
        "co2": current_co2,
        "temperature": 22.5,
        "humidity": 45,
        "iaq_score": round(iaq["score_global"], 1),
        "prediction_minutes": prediction
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
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM occupations")
    rows = cursor.fetchall()
    
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

def calculate_co2_trend(current_co2):
    global co2_history
    # Aktuelle Messung mit Uhrzeit in die Historie aufnehmen
    now = datetime.now()
    co2_history.append({"time": now, "value": current_co2})
    
    if len(co2_history) > 10:
        co2_history.pop(0)
    
    if len(co2_history) < 2:
        return None 

    start_vals = [d["value"] for d in co2_history[:3]]
    avg_start = sum(start_vals) / len(start_vals)
    time_start = co2_history[1]["time"]

    end_vals = [d["value"] for d in co2_history[-3:]]
    avg_end = sum(end_vals) / len(end_vals)
    time_end = co2_history[-2]["time"]

    time_diff = (time_end - time_start).total_seconds() / 60

    co2_diff = avg_end - avg_start

    if time_diff == 0 or co2_diff <= 0:
        return -1
    
    pente = co2_diff / time_diff 
    
    remaining_ppm = 1000 - current_co2
    if remaining_ppm <= 0:
        return 0
        
    minutes_to_alert = (remaining_ppm - avg_start) / pente
    if remaining_ppm > 0 and minutes_to_alert < 1:
        return 1 
    return round(minutes_to_alert)


init_db()
