
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Autoriser le Frontend (React) à communiquer avec le Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # On pourra restreindre plus tard
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "AeroGuard Backend is running"}

@app.get("/api/sensor-test")
def get_sensor_test():
    # Simulation de données pour tester la connexion
    return {
        "co2": 1100,
        "temperature": 30,
        "humidity": 48,
        "iaq_score": 90
    }
