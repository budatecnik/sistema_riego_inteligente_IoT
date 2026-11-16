# Inventario de migración a Codex — SRI_IOT

Fecha de inspección: 2026-11-16  
Repositorio: https://github.com/budatecnik/sistema_riego_inteligente_IoT  
Rama de referencia: `main`  
Rama de preparación: `codex/migration-prep`  
Último commit visible durante el inventario: `07df06d` — integración de Docker y Splunk (2026-06-16).

## 1. Estado del repositorio

- Repositorio público, no archivado.
- Rama principal: `main`; durante la inspección solo se encontró esa rama.
- Tamaño informado por GitHub: aproximadamente 22 KB.
- Se creó `codex/migration-prep` desde `main` para aislar la preparación.
- No se modificó `main`.
- En el nivel raíz se observaron: `.gitignore`, `Dockerfile`, `README.md`, `backend/`, `docker-compose.yml`, `firmware/`, un archivo llamado `os` y `requirements.txt`.

## 2. Arquitectura y tecnologías observadas

| Capa | Implementación observada |
|---|---|
| Edge | ESP32 con Arduino/C++ |
| Sensores | DHT22, entrada de luz digital y sensor de humedad de suelo analógico |
| Mensajería | MQTT; PubSubClient en ESP32 y Paho MQTT en Python |
| API | FastAPI + Uvicorn |
| Persistencia | SQLite + SQLAlchemy |
| Visualización | HTML/JavaScript en `backend/static/index.html`; módulo gráfico Python con Matplotlib |
| Observabilidad | Logging rotativo y servicio Splunk declarado |
| Infraestructura | Dockerfile y Docker Compose |

Flujo pretendido según README: ESP32 → broker MQTT → FastAPI → SQLite → dashboard.

## 3. Archivos y módulos identificados

- `backend/main.py`: aplicación FastAPI, cliente MQTT, endpoints `/datos-actuales`, `/hora` y `/historial`, logging y persistencia.
- `backend/database.py`: motor y sesiones SQLAlchemy con SQLite.
- `backend/modelos.py`: modelo `Lectura`.
- `backend/graficador.py`: gráfica local Matplotlib/TkAgg.
- `backend/static/index.html`: dashboard web.
- `firmware/firmware.ino`, `firmware1_2.ino`, `firmware2.ino`: tres variantes de firmware; falta identificar cuál está desplegada.
- `Dockerfile`, `docker-compose.yml`: despliegue raíz.
- `backend/docker-compose.yml`: segunda composición histórica/alternativa.
- `requirements.txt`: FastAPI, Uvicorn, SQLAlchemy, Paho MQTT y tzdata.

## 4. Hallazgos y riesgos que bloquean una migración segura

### CRÍTICO — credenciales versionadas
Durante la inspección se detectaron credenciales reales o aparentemente reales en archivos versionados: una contraseña Wi-Fi en el firmware y una contraseña de Splunk en la composición raíz. El repositorio está marcado como público.

Acciones inmediatas:
1. Rotar la contraseña Wi-Fi afectada y actualizar el firmware/dispositivos autorizados.
2. Rotar la credencial de Splunk y revisar accesos/logs.
3. Revisar el historial Git completo: las credenciales pueden seguir accesibles en commits anteriores aunque se edite el archivo actual.
4. Migrar secretos a variables de entorno/secret manager y archivos locales ignorados por Git.
5. Evaluar limpieza del historial solo después de coordinar a todos los colaboradores y preservar una copia de respaldo. La rotación no debe esperar a la reescritura del historial.

No se reproducen aquí los valores secretos.

### ALTO — incompatibilidad de topic MQTT
El firmware principal publica en `iot/esp32/datos`, mientras que el backend se suscribe a `esp32/sensores`. Tal como están esos archivos, productor y consumidor no comparten topic y no se garantiza recepción de telemetría.

No cambiarlo automáticamente: confirmar primero qué firmware está cargado y qué topic utiliza el broker en el entorno real.

### ALTO — discrepancia de payload y persistencia
- El firmware envía `humedad_suelo` como lectura analógica cruda.
- El backend la trata como humedad porcentual en visualización/logs.
- El modelo declara `timestamp`, pero el constructor de `Lectura` en `main.py` no lo asigna.
- El firmware incluye timestamp NTP, pero el backend genera su propio timestamp para memoria y no persiste ese campo en el registro.
- La clave MQTT de temperatura/humedad parece coincidir (`temperatura`, `humedad`), pero hay que validar todos los campos y tipos con muestras reales.

### ALTO — configuración de despliegue
- El Dockerfile ejecuta `backend.main:app` desde el contexto raíz; validar imports y estructura en un build real.
- La composición raíz usa imágenes con etiqueta `latest` para Mosquitto y Splunk; fijar versiones en una tarea independiente.
- No se observa configuración de autenticación MQTT ni TLS en los fragmentos inspeccionados.
- La composición raíz publica puertos de MQTT, Splunk y API. Revisar exposición de red y credenciales antes de cualquier despliegue.
- Hay dos archivos Compose con configuraciones diferentes; determinar cuál es el despliegue vigente.
- La ruta de SQLite es relativa; validar el volumen y la persistencia real del archivo de base de datos.

### MEDIO — calidad y mantenibilidad
- No se identificó directorio de tests ni configuración CI en el árbol raíz inspeccionado.
- Hay tres variantes de firmware sin documento que identifique versión estable.
- `graficador.py` selecciona backend gráfico TkAgg, posiblemente incompatible con contenedores headless.
- CORS permite todos los orígenes, métodos y headers.
- La estrategia de reintento MQTT del backend y del firmware necesita pruebas de reconexión y manejo de mensajes.
- README describe nombres de carpetas/servicios que no coinciden completamente con el árbol actual y marca Docker como “in progress” pese a existir configuración Docker.

## 5. Plan de preparación para Codex

1. Conectar el repositorio en Codex y abrir la rama `codex/migration-prep`.
2. Leer `AGENTS.md` y este inventario como contexto inicial.
3. Crear un entorno local aislado; no conectar inicialmente a hardware ni a servicios productivos.
4. Obtener una copia completa del repositorio e historial Git; verificar que no falten archivos binarios, secretos locales o datos fuera de Git.
5. Confirmar firmware activo, broker, topic, payload, pines, calibración y despliegue Compose real.
6. Resolver exposición de credenciales antes de usar el sistema en red.
7. Añadir pruebas automatizadas del contrato MQTT, modelo de datos y endpoints.
8. Corregir documentación y reproducibilidad del entorno en PRs pequeños.
9. Validar build Docker, API, broker simulado, persistencia y dashboard.
10. Revisar el PR de preparación antes de integrar a `main`.

## 6. Pendientes de confirmación del responsable

- ¿Es este repositorio el SRI_IOT correcto?
- ¿Qué variante de firmware está instalada en el ESP32?
- ¿El sistema activo utiliza el Compose raíz o `backend/docker-compose.yml`?
- ¿Cuál es el topic MQTT real en producción?
- ¿El sensor de humedad de suelo debe convertirse a porcentaje mediante calibración?
- ¿Splunk está activo y expuesto a una red externa?
- ¿Hay datos SQLite, configuraciones, diagramas o documentación fuera de Git que deban preservarse?

## 7. Alcance de esta preparación

Esta rama incorpora instrucciones de trabajo para Codex e inventario técnico. No cambia código de firmware/backend, no altera la rama `main`, no rota credenciales y no ejecuta despliegues. La migración a Codex requiere que el usuario inicie sesión en Codex con la cuenta/plan Pro y autorice el acceso al repositorio.
