#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <SensirionI2CScd4x.h>
#include <Wire.h>

//MQTT-Parameter
const char* ssid = "WIFI_NAME";
const char* password = "WIFI_PASSWORT";
const char* mqtt_server = "COMPUTER_IP"; 
const int mqtt_port = 1883;
const char* mqtt_topic = "aeroguard/room1";

const int LDC2410_PIN = 13;

SensirionI2CScd4x scd41;
WiFiClient espClient;
PubSubClient client(espClient);
unsigned long lastMsg = 0;

void setup_wifi() {
  delay(10);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
  Serial.println("\nWi-Fi verbunden !");
}

void reconnect() {
  while (!client.connected()) {
    String clientId = "ESP32Client-AeroGuard-" + String(random(0, 1000));
    if (client.connect(clientId.c_str())) {
      Serial.println("verbunden !");
    } else {
      Serial.print("Verbindung fehlgeschlagen, rc=");
      Serial.print(client.state());
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);

  pinMode(LDC2410_PIN, INPUT);

  Wire.begin();
  scd41.begin(Wire);

  uint16_t error;
  char errorMessage[256];
  
  // Stoppen des SCD41, Falls eine Messung schon aktiv war
  error = scd41.stopPeriodicMeasurement();
  
  // Starten der periodeshen Messung von CO2/Temp/Hum
  error = scd41.startPeriodicMeasurement();
  if (error) {
    Serial.print("Erreur lors du démarrage du SCD41 : ");
    errorToString(error, errorMessage, 256);
    Serial.println(errorMessage);
  } else {
    Serial.println("Capteur SCD41 prêt et démarré !");
  }
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  
  if (now - lastMsg > 5000) {
    lastMsg = now;

    //Menschliche Präsenz (LDC2410)
    bool presence = (digitalRead(LDC2410_PIN) == HIGH);

    //Raumluftdaten (SCD41)
    uint16_t co2 = 0;
    float temperatur = 0.0;
    float feuchtigkeit = 0.0;
    bool dataReady = false;

    // Prüfen ob SCD41 neue Werte hat
    scd41.getDataReadyFlag(dataReady);

    //Erstellen der JSON & Senden
    StaticJsonDocument<128> doc;
    doc["co2"] = co2;
    doc["temperature"] = temperature;
    doc["humidity"] = humidity;
    doc["presence"] = presence;

    char buffer[128];
    serializeJson(doc, buffer);
    client.publish(mqtt_topic, buffer);
  }
}