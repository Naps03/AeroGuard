import sqlite3
import json 
import threading 
import paho.mqtt.client as mqtt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from iaq_score import calculate_iaq_index

#Letzte 10 CO2-Messungen
co2_history = [] 

current_co2 = 400
current_temp = 22.0
current_hum = 45.0

# Daten aus dem Dashboard für den Belegungsplan
class Occupation(BaseModel):
    day: str
    start_time: str
    end_time: str
    label: str

app = FastAPI()
call_counter = 0
# Erstellung der Kommunikation zwischen FrontEnd & BackEnd
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

def on_connect(client, userdata, flags, rc):
    """ Cette fonction se déclenche dès que le backend se connecte à Mosquitto """
    if rc == 0:
        print("✅ Backend connecté avec succès au Broker Mosquitto !")
        # On s'abonne au pattern global 'aeroguard/#' pour écouter co2, temp, et hum en même temps
        client.subscribe("aeroguard/#")
    else:
        print(f"❌ Échec de connexion à Mosquitto, code erreur : {rc}")

def on_message(client, userdata, msg):
    """ Cette fonction s'exécute automatiquement dès que l'ESP32 publie une donnée """
    global current_co2, current_temp, current_hum, call_counter
    
    try:
        # Décoder la valeur brute reçue (qui arrive sous forme de texte)
        payload = msg.payload.decode("utf-8")
        topic = msg.topic

        # Dispatcher les données réelles selon le canal (Topic) d'origine
        if topic == "aeroguard/co2":
            current_co2 = int(payload)
        elif topic == "aeroguard/temp":
            current_temp = float(payload)
        elif topic == "aeroguard/hum":
            current_hum = float(payload)

        # Journalisation dans le terminal Python pour débugger
        print(f"📥 [MQTT] Réception sur {topic} -> {payload}")

        # --- SAUVEGARDE AUTOMATIQUE EN BASE DE DONNÉES ---
        # Comme l'ESP32 envoie 3 messages successifs (co2, temp, hum), 
        # on attend de recevoir les 3 (compteur à 3) pour faire une seule ligne propre en DB.
        if topic in ["aeroguard/co2", "aeroguard/temp", "aeroguard/hum"]:
            call_counter += 1
            if call_counter >= 3:
                # Calculer le score IAQ basé sur les vraies valeurs actuelles
                iaq = calculate_iaq_index(current_co2, current_temp, current_hum)
                save_to_db(current_co2, current_temp, current_hum, int(iaq["score_global"]))
                call_counter = 0
                print("💾 [DB] Enregistrement des données réelles effectué.")

    except Exception as e:
        print(f"❌ Erreur lors du traitement du message MQTT : {e}")

def start_mqtt_client():
    """ Fonction pour initialiser le client MQTT et le lancer dans un thread """
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    try:
        # Connexion au Mosquitto qui tourne sur ton PC en local (localhost)
        mqtt_client.connect("localhost", 1883, 60)
        # Démarre la boucle d'écoute en arrière-plan
        mqtt_client.loop_forever()
    except Exception as e:
        print(f"❌ Impossible de se connecter au Broker Mosquitto local : {e}")

# Lancement immédiat de Mosquitto dans un fil (thread) séparé de FastAPI
mqtt_thread = threading.Thread(target=start_mqtt_client, daemon=True)
mqtt_thread.start()

@app.get("/")
def read_root():
    return {"status": "AeroGuard Backend is running"}

@app.get("/api/sensor-test")
def get_sensor_test():
    global call_counter
    global  current_co2, current_temp, current_hum
    
    prediction = calculate_co2_trend(current_co2)

    iaq = calculate_iaq_index(current_co2, current_temp, current_hum)
    
    call_counter += 1
    if call_counter >= 2:
        save_to_db(current_co2, current_temp, current_hum, int(iaq["score_global"]))
        call_counter = 0
    return {
        "co2": current_co2,
        "temperature": current_temp,
        "humidity": current_hum,
        "iaq_score": round(iaq["score_global"], 1),
        "prediction_minutes": prediction
    }

@app.get("/api/history")
def get_history():
    try:
        conn = sqlite3.connect("aeroguard.db")
        # Zugriff auf die Datenbank
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Abholung der letzten 12 Messungen (ca. 1 Stunde Historie bei 5-Minuten-Intervallen)
        cursor.execute('''
            SELECT timestamp, co2, temperature, humidity, iaq_score 
            FROM measurements 
            ORDER BY id DESC 
            LIMIT 12
        ''')
        rows = cursor.fetchall()
        conn.close()

        history = []
        for row in rows:
            # Uhrzeitformat (HH:MM:SS)
            full_time = row['timestamp'].split(" ")[1] 
            
            history.append({
                "time": full_time,
                "co2": row['co2'],
                "temp": row['temperature'],
                "hum": row['humidity'],
                "iaq": row['iaq_score']
            })

        # On inverse la liste pour que le point le plus récent soit à droite du graphique
        return history[::-1]

    except Exception as e:
        print(f"❌ Erreur lecture historique: {e}")
        return []

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

def save_to_db(co2, temp, hum, iaq):
    conn = sqlite3.connect("aeroguard.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO measurements (co2, temperature, humidity, iaq_score) VALUES (?, ?, ?, ?)",
        (co2, temp, hum, iaq)
    )
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
