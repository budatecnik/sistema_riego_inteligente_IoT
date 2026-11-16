# Configuración de Codex para SRI_IOT

## Objetivo
Preparar un entorno Codex Cloud reproducible para inspeccionar, probar y modificar SRI_IOT sin conectar servicios productivos ni hardware durante la primera validación.

## Repositorio y rama inicial
- Repositorio: `budatecnik/sistema_riego_inteligente_IoT`
- Rama de preparación: `codex/migration-prep`
- Rama estable de referencia: `main`
- Instrucciones del agente: `AGENTS.md`
- Inventario y riesgos: `docs/MIGRATION_INVENTORY.md`

## Alta manual de Codex Cloud
1. Abrir ChatGPT con la misma cuenta que tiene Pro.
2. Iniciar una tarea nueva y elegir **Work in → Cloud** (o abrir Codex desde la superficie disponible).
3. En el selector de entorno, elegir **Create environment**.
4. Conectar GitHub si aparece el aviso y autorizar únicamente el repositorio SRI_IOT necesario.
5. Seleccionar `budatecnik/sistema_riego_inteligente_IoT` como repositorio.
6. Elegir **Get started** para que Codex inspeccione dependencias y prepare el entorno.
7. Revisar el informe de instalación; no proporcionar credenciales productivas.
8. Guardar/publicar el entorno solo después de revisar el script de instalación, los permisos, la red y las variables.
9. Iniciar una tarea nueva en ese entorno y seleccionar la rama `codex/migration-prep` si el selector de rama está disponible. En caso contrario, pedir explícitamente a Codex que haga checkout de esa rama.
10. Confirmar que Codex leyó `AGENTS.md` y `docs/MIGRATION_INVENTORY.md`.

## Configuración de entorno recomendada

### Runtime
- Python 3.10 (coincide con la imagen base del Dockerfile).
- Instalar dependencias Python con `python -m pip install -r requirements.txt`.
- Herramientas opcionales para tareas futuras: Docker CLI/Compose y toolchain ESP32/Arduino. No son necesarias para la primera revisión estática.

### Install script inicial sugerido
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m compileall -q backend
```

No arrancar Mosquitto, Splunk, FastAPI ni hardware real durante la instalación inicial. No ejecutar `docker compose up` hasta sanear credenciales, revisar puertos y decidir qué Compose es el vigente.

### Acceso de red
- Mantener acceso de red restringido al mínimo necesario para clonar GitHub e instalar paquetes.
- No habilitar acceso a LAN, broker MQTT, dispositivos ni servicios productivos para la primera etapa.
- No añadir secretos HTTP ni variables con credenciales a este entorno inicial.

## Primera tarea recomendada para Codex

Copiar este prompt en una nueva tarea de Codex Cloud:

> Trabaja en el repositorio SRI_IOT, rama codex/migration-prep. Lee primero AGENTS.md y docs/MIGRATION_INVENTORY.md. No modifiques archivos todavía. Realiza una auditoría reproducible: identifica el estado real del árbol, confirma qué variante de firmware publica en cada topic, compara todos los contratos MQTT con el backend, revisa el modelo SQLAlchemy y los dos archivos Docker Compose. Ejecuta únicamente validaciones estáticas seguras (instalación de dependencias, compileall y validación de sintaxis/configuración sin levantar servicios). No muestres ni copies secretos. Devuelve comandos ejecutados, resultados verificables, riesgos priorizados y un plan de PRs pequeños. No conectes hardware, redes privadas ni servicios productivos.

## Permisos de trabajo
- Primera sesión: lectura y ejecución de validaciones estáticas; sin cambios.
- Segunda etapa: permitir edición solo en la rama de preparación, con revisión de diff.
- No autorizar push a `main`, despliegues, borrado de datos, reescritura Git ni acceso a dispositivos sin aprobación explícita.

## Señales de aceptación del entorno
- Codex clona el repositorio correcto.
- Se encuentra en `codex/migration-prep`.
- Lee las instrucciones del agente y el inventario.
- Instala dependencias sin secretos.
- `python -m compileall -q backend` termina con código 0.
- No se ha iniciado ningún servicio productivo ni cambiado hardware.
- Los resultados y limitaciones quedan registrados en la tarea.
