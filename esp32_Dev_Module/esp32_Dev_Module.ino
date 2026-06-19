
#include <Wire.h>
#include <SensirionI2CScd4x.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ld2410.h>

const char* ssid = "Vodafone-1B54";   
const char* password = "EY36k2chKFRsnyry"; 
const char* mqtt_server = "192.168.0.94";   
const int mqtt_port = 1883;  

const int ledGrün = 13;
const int ledGelb = 12;
const int ledRot = 14;

SensirionI2CScd4x scd41;
WiFiClient espClient; 
PubSubClient client(espClient);
ld2410 radar;

unsigned long lastMsg = 0;
unsigned long lastPresenceTime = 0;
bool systemActive = false;            
const unsigned long TIMEOUT_SPARMODUS = 60000; //Wartezeit bis das System augeht, wenn niemand mehr im Raum ist

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Verbindung zur WLAN : ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WLAN verbunden!");
  Serial.print("ESP32 IP-Adresse : ");
  Serial.println(WiFi.localIP());
}

// Verbindung zum Broker
void reconnect() {
  while (!client.connected()) {
    Serial.print("Verbindung zum Mosquitto...");
    String clientId = "ESP32Client-AeroGuard";
    
    if (client.connect(clientId.c_str())) {
      Serial.println("Verbunden mit dem Broker !");
    } else {
      Serial.print("Verbindung mit dem Broker fehlgeschlagen, ErrorCode = ");
      Serial.print(client.state());
      Serial.println("5 Sekunden warten...");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(ledGrün, OUTPUT);
  pinMode(ledGelb, OUTPUT);
  pinMode(ledRot, OUTPUT);
  
  Serial2.begin(256000, SERIAL_8N1, 32, 27); 
    Serial.print("Initialisierung des LD2410C... ");
    if (radar.begin(Serial2)) {
      Serial.println("LD2410 Bereit !");
    } else {
      Serial.println("Fehler bei Initialisierung des SCD41");
    }

  setup_wifi();
  
  client.setServer(mqtt_server, mqtt_port);

  Wire.begin(25, 26); // SDA = 21, SCL = 22 auf ESP32
  scd41.begin(Wire);
  
  scd41.stopPeriodicMeasurement();
  uint16_t error = scd41.startPeriodicMeasurement();
  
  if (error) {
    Serial.print("Fehler bei Initialisierung des SCD41. Code : ");
    Serial.println(error);
  } else {
    Serial.println("SCD41 bereit");
  }
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  radar.read();
  bool menschPraesenz = radar.movingTargetDetected() || radar.stationaryTargetDetected();

  unsigned long now = millis();
  
  if (menschPraesenz) {
    lastPresenceTime = now;
    
    if (!systemActive) {
      systemActive = true;
      Serial.println("Menschliche Praesenz detektiert. Neu Starten des Aeroguard");
      client.publish("aeroguard/presence", "1");
    }
  } else {
    if (systemActive && (now - lastPresenceTime > TIMEOUT_SPARMODUS)) {
      systemActive = false;
      Serial.println("Leerer Raum seit 60s. Aktivierung des Sparmodus");
      offLEDs();
      client.publish("aeroguard/presence", "0");
    }
  }
  
  if (systemActive) {
    if (now - lastMsg > 5000) {
      lastMsg = now;
      uint16_t co2 = 0;
      float temp = 0.0, hum = 0.0;
      bool ready = false;
      
      uint16_t error = scd41.getDataReadyFlag(ready);
      
      if (!error && ready) {
        error = scd41.readMeasurement(co2, temp, hum);
        
        if (!error) {
          Serial.print("CO2: "); Serial.print(co2); Serial.print(" ppm\t");
          Serial.print("Temp: "); Serial.print(temp, 1); Serial.print(" °C\t");
          Serial.print("Hum: "); Serial.print(hum, 1); Serial.println(" %");

          steuernLEDs(co2);

          String co2Str = String(co2);
          String tempStr = String(temp, 1);
          String humStr = String(hum, 1);

          client.publish("aeroguard/co2", co2Str.c_str());
          client.publish("aeroguard/temp", tempStr.c_str());
          client.publish("aeroguard/hum", humStr.c_str());
        }
      }
    } 
  } else {
    if (now - lastMsg > 15000) {
      lastMsg = now;
      Serial.println("💤 Système en sommeil... En attente d'une présence.");
    }
  }
    delay(500); 
}

void steuernLEDs(uint16_t wertCO2) {
  if (wertCO2 < 800) {
    digitalWrite(ledGrün, HIGH);
    digitalWrite(ledGelb, LOW);
    digitalWrite(ledRot, LOW);
  } 
  else if (wertCO2 >= 800 && wertCO2 <= 1200) {
    digitalWrite(ledGrün, LOW);
    digitalWrite(ledGelb, HIGH);
    digitalWrite(ledRot, LOW);
  } 
  else {
    digitalWrite(ledGrün, LOW);
    digitalWrite(ledGelb, LOW);
    digitalWrite(ledRot, HIGH);
  }
}

void offLEDs() {
  digitalWrite(ledGrün, LOW);
  digitalWrite(ledGelb, LOW);
  digitalWrite(ledRot, LOW);
}