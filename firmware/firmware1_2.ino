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
const char* mqtt_topic = "esp32/sensores"; // Asegurate de que este sea tu tópico correcto

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
  if (WiFi.status() != WL_CONNECTED) {
    conectarWiFi();
  }
  
  if (!client.connected()) {
    conectarMQTT();
  }
  client.loop();

  // 1. Leer los sensores ambientales
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  bool luz = digitalRead(LUZ_PIN) == LOW;

  // 2. Leer humedad de suelo y aplicar calibración real
  int valorCrudoSuelo = analogRead(SUELO_PIN);
  // Al aire = 2560 (0%), Sumergido = 900 (100%)
  int porcentajeSuelo = map(valorCrudoSuelo, 2560, 900, 0, 100);
  // Restringir el valor entre 0 y 100 para evitar desbordes por pequeñas fluctuaciones
  porcentajeSuelo = constrain(porcentajeSuelo, 0, 100);

  // Validar lecturas del DHT antes de armar el JSON
  if (!isnan(t) && !isnan(h)) {
    // 3. Armar JSON con el porcentaje calibrado del suelo
    String json = "{";
    json += "\"temperatura\":" + String(t, 2) + ",";
    json += "\"humedad\":" + String(h, 2) + ",";
    json += "\"humedad_suelo\":" + String(porcentajeSuelo) + ",";
    json += "\"luz\":" + String(luz ? "true" : "false");
    json += "}";

    // Imprimir por Monitor Serie para control local
    Serial.println("----------------------");
    Serial.print("Valor Crudo Sensor Suelo: "); Serial.println(valorCrudoSuelo);
    Serial.println(json);

    // 4. Enviar datos por MQTT
    if (client.publish(mqtt_topic, json.c_str())) {
      Serial.println("📡 MQTT enviado OK");
    } else {
      Serial.println("❌ Error al enviar por MQTT");
    }
  } else {
    Serial.println("⚠️ Error al leer el sensor DHT22");
  }

  delay(5000); // Espera de 5 segundos entre lecturas
}