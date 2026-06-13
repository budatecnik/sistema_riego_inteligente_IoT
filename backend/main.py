from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from modelos import Base, Lectura
import paho.mqtt.client as mqtt
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import threading
import logging
from logging.handlers import RotatingFileHandler

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

# Formato estándar que a Splunk le encanta (Timestamp - Nivel - Mensaje)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modificalo en producción si es necesario
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- MEMORIA LIVE ----------------
datos_actuales = {
    "temperatura": 0,
    "humedad": 0,
    "humedad_suelo": 0,
    "luz": False,
    "timestamp": ""
}

# ---------------- MQTT CONFIG ----------------
BROKER = "127.0.0.1"
PORT = 1883
TOPIC = "esp32/sensores"
mqtt_client = mqtt.Client()

# ---------------- CALLBACKS MQTT ----------------
def on_connect(client, userdata, flags, rc):
    print("MQTT conectado con código:", rc)
    client.subscribe(TOPIC)

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

        # 2. 🚨 PERSISTENCIA EN BASE DE DATOS (Para que funcione el /historial)
        db = SessionLocal()
        try:
            nueva_lectura = Lectura(
                temperatura=datos_actuales["temperatura"],
                humedad=datos_actuales["humedad"],
                humedad_suelo=datos_actuales["humedad_suelo"],
                luz=datos_actuales["luz"]
                # Nota: Si tu modelo 'Lectura' requiere un campo fecha o timestamp string, agregalo aquí.
                # Ejemplo: fecha=datos_actuales["timestamp"]
            )
            db.add(nueva_lectura)
            db.commit()
        except Exception as db_err:
            logger.error(f"EVENT=DB_SAVE_ERROR msg='No se pudo guardar la lectura: {str(db_err)}'")
            print("⚠️ Error guardando en BD:", db_err)
        finally:
            db.close() # Cerramos manualmente la sesión ya que no estamos en un endpoint HTTP con Depends

        # 3. LÍNEA CLAVE PARA SPLUNK: Escribe la telemetría exacta en el archivo .log
        logger.info(f"EVENT=MQTT_DATA_RECEIVED temp={datos_actuales['temperatura']} hum={datos_actuales['humedad']} suelo={datos_actuales['humedad_suelo']} luz={datos_actuales['luz']}")
        print("📥 Datos recibidos, guardados en BD y logueados exitosamente:", datos_actuales)

    except Exception as e:
        error_msg = f"EVENT=MQTT_ERROR msg='Error al procesar el mensaje: {str(e)}'"
        logger.error(error_msg)
        print("⚠️ Error procesando MQTT:", e)

# Asignación correcta de los callbacks (fuera de las funciones)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# ---------------- MQTT LOOP ----------------
def mqtt_worker():
    import time
    while True:
        try:
            print("🔌 Intentando conectar al Broker MQTT...")
            mqtt_client.connect(BROKER, PORT, 60)
            mqtt_client.loop_forever()
        except Exception as e:
            logger.error(f"EVENT=MQTT_CONNECTION_FAILED msg='{str(e)}'")
            print(f"⚠️ MQTT caído: {e} — Reintentando en 5 segundos...")
            time.sleep(5)

# ---------------- STARTUP / SHUTDOWN ----------------
@app.on_event("startup")
def startup():
    # Iniciar el hilo de fondo para que MQTT no congele a FastAPI
    thread = threading.Thread(target=mqtt_worker, daemon=True)
    thread.start()

    # Log de "Prueba de vida" inicial: ni bien arranca el script escribe aquí
    logger.info("EVENT=SERVER_START status=SUCCESS msg='El backend de FastAPI encendio correctamente'")
    print("🚀 Backend iniciado y listo")

@app.on_event("shutdown")
def shutdown():
    try:
        logger.info("EVENT=SERVER_SHUTDOWN")
        mqtt_client.disconnect()
    except Exception:
        pass

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
