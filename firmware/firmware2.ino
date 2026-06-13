#include <WiFi.h>
#include <PubSubClient.h>
#include "DHT.h"
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"
#include <time.h>

// ---------------- WIFI ----------------
const char* ssid = "Marina";
const char* password = "miisa395am";

// ---------------- MQTT ----------------
const char* mqtt_server = "192.168.1.6";
const char* mqtt_topic = "iot/esp32/datos"; // Asegurate de que este sea tu tópico correcto

WiFiClient espClient;
PubSubClient client(espClient);

// ---------------- SENSORES ----------------
#define LUZ_PIN 4
#define DHTPIN 15
#define DHTTYPE DHT22
#define SUELO_PIN 34  // Pin analógico donde está conectado el sensor de humedad de suelo

DHT dht(DHTPIN, DHTTYPE);

// ---------------- BUFFER (RAM) ----------------
String buffer[50];
int bufferIndex = 0;

// ---------------- WIFI CONFIG ----------------
void conectarWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("📡 Conectando WiFi");
  int intentos = 0;
  while (WiFi.status() != WL_CONNECTED && intentos < 20) {
    delay(500);
    Serial.print(".");
    intentos++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi conectado");
    Serial.print("🌐 IP ESP32: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n❌ Fallo WiFi");
  }
}

// ---------------- MQTT CONFIG ----------------
void conectarMQTT() {
  while (!client.connected()) {
    Serial.print("🔄 Conectando a Broker MQTT...");
    if (client.connect("ESP32_Client")) {
      Serial.println("\n✅ Conectado al Broker MQTT");
    } else {
      Serial.print("❌ Fallo, rc=");
      Serial.print(client.state());
      Serial.println(" reintentando en 5 segundos");
      delay(5000);
    }
  }
}

void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); // Deshabilitar detector Brownout
  Serial.begin(115200);
  
  pinMode(LUZ_PIN, INPUT);
  pinMode(SUELO_PIN, INPUT); // Configurar pin del suelo como entrada
  
  dht.begin();
  conectarWiFi();
  client.setServer(mqtt_server, 1883);
}

void loop() {

  // ---------------- WIFI ----------------
  if (WiFi.status() != WL_CONNECTED) {

    Serial.println("⚠️ WiFi desconectado");
    conectarWiFi();
  }

  // ---------------- MQTT ----------------
  if (!client.connected()) {

    Serial.println("⚠️ MQTT desconectado");
    conectarMQTT();
  }

  // Mantener MQTT vivo
  client.loop();

  // ---------------- LEER DHT ----------------
  float t = dht.readTemperature();
  float h = dht.readHumidity();

  // ---------------- LEER LUZ ----------------
  bool luz = digitalRead(LUZ_PIN) == HIGH;

  // ---------------- LEER SUELO ----------------
  int valorCrudoSuelo = analogRead(SUELO_PIN);

  int porcentajeSuelo = map(
    valorCrudoSuelo,
    2560,
    900,
    0,
    100
  );

  porcentajeSuelo = constrain(
    porcentajeSuelo,
    0,
    100
  );

  // ---------------- VALIDAR DHT ----------------
  if (!isnan(t) && !isnan(h)) {

    // ---------------- JSON ----------------
    String json = "{";

    json += "\"temperatura\":";
    json += String(t, 2);
    json += ",";

    json += "\"humedad\":";
    json += String(h, 2);
    json += ",";

    json += "\"humedad_suelo\":";
    json += String(porcentajeSuelo);
    json += ",";

    json += "\"luz\":";
    json += (luz ? "true" : "false");

    json += "}";

    // ---------------- SERIAL ----------------
    Serial.println("\n----------------------");

    Serial.print("🌡 Temp: ");
    Serial.println(t);

    Serial.print("💧 Humedad: ");
    Serial.println(h);

    Serial.print("🌿 Suelo: ");
    Serial.print(porcentajeSuelo);
    Serial.println("%");

    Serial.println(json);

    // ---------------- PUBLICAR MQTT ----------------
    bool ok = client.publish(
      mqtt_topic,
      json.c_str()
    );

    if (ok) {

      Serial.println("📡 MQTT enviado OK");

    } else {

      Serial.println("❌ Error MQTT publish");
    }

  } else {

    Serial.println("⚠️ Error leyendo DHT22");
  }

  // ⚡ IMPORTANTE
  // Pequeño delay y no gigantesco
  for (int i = 0; i < 50; i++) {

    client.loop();
    delay(100);
  }
}
 