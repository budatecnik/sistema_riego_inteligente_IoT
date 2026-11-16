# AGENTS.md — SRI_IOT

## Propósito
Este repositorio implementa un sistema IoT de monitoreo ambiental y de suelo basado en ESP32, MQTT, FastAPI, SQLite y contenedores Docker. Mantener la continuidad técnica, la seguridad y la trazabilidad es prioritario.

## Idioma y comunicación
- Responder y documentar en español, salvo que el usuario solicite otro idioma.
- Explicar cambios con precisión, indicando archivos afectados, motivos, riesgos y pruebas ejecutadas.
- No afirmar que algo fue probado si no se ejecutó realmente.

## Reglas de trabajo
1. Antes de modificar, inspeccionar la estructura, los archivos relacionados y el historial Git.
2. Trabajar en ramas de tarea; no hacer commits directos a `main` ni reescrituras de historial sin autorización explícita.
3. Mantener cambios pequeños, reversibles y enfocados. No refactorizar módulos no relacionados.
4. No cambiar pines, cableado, polaridades, calibraciones, topics MQTT, payloads ni comportamiento del firmware sin explicar el impacto y obtener confirmación cuando afecte dispositivos físicos.
5. Antes de cambiar contratos MQTT, comparar productor (firmware) y consumidor (backend), documentar el contrato y proponer compatibilidad/migración.
6. No eliminar archivos históricos de firmware hasta determinar cuál versión está desplegada y cuál es la fuente de verdad.
7. Preservar datos persistentes y volúmenes Docker. Nunca ejecutar operaciones destructivas sobre bases de datos, volúmenes o dispositivos reales sin autorización.
8. Añadir o actualizar pruebas para cambios funcionales. Si no hay entorno de hardware, usar mocks/simulaciones y declarar sus límites.
9. Mantener README y documentación alineados con la implementación real, no con una arquitectura aspiracional.

## Seguridad obligatoria
- Nunca copiar, mostrar, registrar ni commitear contraseñas, tokens, claves privadas, credenciales Wi-Fi, secretos MQTT ni credenciales de servicios.
- Leer secretos desde variables de entorno o archivos locales ignorados por Git; proporcionar `.env.example` solo con valores ficticios.
- Si se detectan credenciales en el historial o en archivos versionados, detener la exposición: recomendar revocación/rotación inmediata y limpieza del historial como tarea separada y coordinada. Borrar un secreto del último commit no lo invalida.
- No usar `latest` en servicios críticos sin justificarlo; fijar versiones/digests en una tarea controlada.
- Restringir CORS y puertos según el entorno; no abrir servicios de administración a redes no confiables.
- No imprimir payloads que puedan contener información sensible.

## Arquitectura observada
- Firmware ESP32 en Arduino/C++ dentro de `firmware/`.
- Backend Python/FastAPI dentro de `backend/`.
- Comunicación MQTT mediante Paho MQTT en backend y PubSubClient en ESP32.
- Persistencia SQLite mediante SQLAlchemy.
- Contenedores Docker y Mosquitto; la composición raíz también declara Splunk.
- Dashboard web en `backend/static/`.

## Validación
- Inspeccionar dependencias y comandos reales antes de ejecutar.
- Para Python: compilar/importar módulos y ejecutar pruebas disponibles; no inventar que existen tests.
- Para Docker: validar sintaxis/configuración sin levantar servicios de producción ni publicar puertos externamente.
- Para firmware: revisar compatibilidad de bibliotecas, pines y contrato MQTT; compilar solo si toolchain y placa están disponibles.
- Registrar los comandos ejecutados y sus resultados.

## Contexto de migración
Consultar `docs/MIGRATION_INVENTORY.md` antes de planificar cambios. La rama de preparación es `codex/migration-prep`; la rama principal de referencia es `main`.
