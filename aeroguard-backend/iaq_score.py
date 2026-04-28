import math

def get_co2_score(co2):
    #Score der CO2-Konzentration
    if co2 <= 800:
        return 100
    elif 800 < co2 <= 1000:
        return 100 - ((co2 - 800) / 200) * 20
    elif 1000 < co2 <= 2000:
        return 80 - ((co2 - 1000) / 1000) * 60
    elif 2000 < co2 <= 3000:
        return 20 - ((co2 - 2000) / 1000) * 20
    else: # CO2 > 3000
        return 0

def get_humidity_score(hr):
    #Score der Feuchtigkeit
    if 40 <= hr <= 60:
        return 100
    elif 30 <= hr < 40:
        return 60 + ((hr - 30) / 10) * 40
    elif 60 < hr <= 65:
        return 60 + ((65 - hr) / 5) * 40
    elif 20 <= hr < 30:
        return 20 + ((hr - 20) / 10) * 40
    elif 65 < hr <= 70:
        return 20 + ((70 - hr) / 5) * 40
    else: # hr < 20 ou hr > 70
        return 0

def get_temperature_score(t):
    #Score der Temperatur
    if 20 <= t <= 23:
        return 100
    elif 19 <= t < 20:
        return 70 + ((t - 19) / 1) * 30
    elif 23 < t <= 24:
        return 70 + ((24 - t) / 1) * 30
    elif 17 <= t < 19:
        return 30 + ((t - 17) / 2) * 40
    elif 24 < t <= 26:
        return 30 + ((26 - t) / 2) * 40
    elif 15 <= t < 17:
        return ((t - 15) / 2) * 30
    elif 26 < t <= 28:
        return ((28 - t) / 2) * 30
    else: # t < 15 ou t > 28
        return 0

def calculate_iaq_index(co2, temp, hum, weight_co2=0.5, weight_temp=0.25, weight_hum=0.25):
    s_co2 = get_co2_score(co2)
    s_temp = get_temperature_score(temp)
    s_hum = get_humidity_score(hum)
    
    iaq_final = (s_co2 * weight_co2) + (s_temp * weight_temp) + (s_hum * weight_hum)
    
    return {
        "score_global": round(iaq_final, 1),
        "details": {
            "co2": round(s_co2, 1),
            "temp": round(s_temp, 1),
            "hum": round(s_hum, 1)
        }
    }
