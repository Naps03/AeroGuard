#include <Wire.h>
#include <SensirionI2CScd4x.h>
#include <WiFi.h>
#include <PubSubClient.h>

const char* ssid = "WLAN-Name";   
const char* password = "WLAN-Passwort"; 
const char* mqtt_server = "100.81.219.149";   
const int mqtt_port = 1883;   

SensirionI2CScd4x scd41;
WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastMsg = 0;

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
  while (!Serial) { delay(100); }
  
  client.setServer(mqtt_server, mqtt_port);

  Wire.begin(21, 22); // SDA = 21, SCL = 22 auf ESP32
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

  unsigned long now = millis();

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

        String co2Str = String(co2);
        String tempStr = String(temperature, 1);
        String humStr = String(humidity, 1);

        client.publish("aeroguard/co2", co2Str.c_str());
        client.publish("aeroguard/temp", tempStr.c_str());
        client.publish("aeroguard/hum", humStr.c_str());
      }
    }
  }  
    delay(100); 
}