import os
import json
import logging
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session

# Importaciones de tus módulos locales
from backend.database import SessionLocal, engine
from backend.modelos import Base, Lectura

# ---------------- DB ----------------
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- CONFIGURACIÓN DE LOGS PARA SPLUNK ----------------
logger = logging.getLogger("iot_logger")
logger.setLevel(logging.INFO)

# RotatingFileHandler evita que el archivo crezca infinitamente (max 5MB por archivo)
file_handler = RotatingFileHandler("proyecto_iot.log", maxBytes=5000000, backupCount=3)

# Formato estándar para Splunk (Timestamp - Nivel - Mensaje)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# ---------------- MEMORIA LIVE (RAM) ----------------
datos_actuales = {
    "temperatura": 0,
    "humidity": 0,
    "humidity_suelo": 0,
    "luz": False,
    "timestamp": ""
}

# ---------------- MQTT CONFIG ----------------
# Ahora, si Docker no pasa la variable, por defecto buscará el DNS interno de la red Docker
BROKER = os.getenv("MQTT_HOST", "mqtt_broker")
PORT = int(os.getenv("MQTT_PORT", 1883))
TOPIC = "esp32/sensores"

# Configuración obligatoria usando la API v2 de Paho-MQTT
mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

# ---------------- CALLBACKS MQTT ----------------
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"✅ MQTT conectado exitosamente al broker: {BROKER}")
        client.subscribe(TOPIC)
    else:
        print(f"❌ Error de conexión MQTT. Código: {reason_code}")

def on_message(client, userdata, msg):
    global datos_actuales
    try:
        # Decodificar el mensaje entrante de la ESP32
        payload = msg.payload.decode()
        datos = json.loads(payload)

        fecha_hora_actual = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).strftime("%Y-%m-%d %H:%M:%S")

        # 1. Guardar en la variable global mapeando los datos recibidos (Memoria RAM)
        datos_actuales = {
            "temperatura": datos.get("temperatura", 0),
            "humedad": datos.get("humedad", 0),
            "humedad_suelo": datos.get("humedad_suelo", 0),
            "luz": datos.get("luz", False),
            "timestamp": fecha_hora_actual
        }

        # 2. PERSISTENCIA EN BASE DE DATOS
        db = SessionLocal()
        try:
            nueva_lectura = Lectura(
                temperatura=datos_actuales["temperatura"],
                humedad=datos_actuales["humedad"],
                humedad_suelo=datos_actuales["humedad_suelo"],
                luz=datos_actuales["luz"]
                # Nota: Si tu modelo 'Lectura' requiere un campo fecha o timestamp string, agrégalo aquí.
                # Ejemplo: fecha=datos_actuales["timestamp"]
            )
            db.add(nueva_lectura)
            db.commit()
        except Exception as db_err:
            logger.error(f"EVENT=DB_SAVE_ERROR msg='No se pudo guardar la lectura: {str(db_err)}'")
            print("⚠️ Error guardando en BD:", db_err)
        finally:
            db.close() # Cierre manual de la sesión (fuera de endpoints HTTP)

        # 3. LOG PARA SPLUNK
        logger.info(f"EVENT=MQTT_DATA_RECEIVED temp={datos_actuales['temperatura']} hum={datos_actuales['humedad']} suelo={datos_actuales['humedad_suelo']} luz={datos_actuales['luz']}")
        print("📥 Datos recibidos, guardados en BD y logueados exitosamente:", datos_actuales)

    except Exception as e:
        error_msg = f"EVENT=MQTT_ERROR msg='Error al procesar el mensaje: {str(e)}'"
        logger.error(error_msg)
        print("⚠️ Error procesando MQTT:", e)

# Asignación de callbacks
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# ---------------- MQTT LOOP ----------------
def mqtt_worker():
    while True:
        try:
            print(f"🔌 Intentando conectar al Broker MQTT en {BROKER}:{PORT}...")
            mqtt_client.connect(BROKER, PORT, 60)
            mqtt_client.loop_forever()
        except Exception as e:
            logger.error(f"EVENT=MQTT_CONNECTION_FAILED msg='{str(e)}'")
            print(f"⚠️ MQTT caído: {e} — Reintentando en 5 segundos...")
            try:
                mqtt_client.disconnect()
            except:
                pass
            time.sleep(5)

# ---------------- LIFESPAN (STARTUP / SHUTDOWN) ----------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- [STARTUP] Lo que corre al iniciar el servidor ---
    thread = threading.Thread(target=mqtt_worker, daemon=True)
    thread.start()

    logger.info("EVENT=SERVER_START status=SUCCESS msg='El backend de FastAPI encendio correctamente'")
    print("🚀 Backend iniciado y listo (Lifespan)")
    
    yield  # El servidor corre aquí
    
    # --- [SHUTDOWN] Lo que corre al apagar el servidor ---
    try:
        logger.info("EVENT=SERVER_SHUTDOWN")
        mqtt_client.disconnect()
        print("🛑 MQTT desconectado limpiamente")
    except Exception:
        pass

# ---------------- INSTANCIA DE FASTAPI ----------------
# Se coloca abajo de lifespan para evitar el NameError
app = FastAPI(lifespan=lifespan)

# ---------------- MIDDLEWARES ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- API ENDPOINTS ----------------
@app.get("/datos-actuales")
def datos():
    return datos_actuales

@app.get("/hora")
def hora():
    ahora = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires"))
    return {"hora": ahora.strftime("%H:%M:%S")}

@app.get("/historial")
def historial(db: Session = Depends(get_db)):
    # Trae las últimas 50 lecturas guardadas en la base de datos relacional
    datos_db = db.query(Lectura).order_by(Lectura.id.desc()).limit(50).all()
    return datos_db