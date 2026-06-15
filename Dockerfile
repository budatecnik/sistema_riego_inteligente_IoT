# 1. Imagen base de Python
FROM python:3.10-slim

# 2. Carpeta de trabajo dentro del contenedor
WORKDIR /app

# 3. Copiar los requerimientos e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar TODO el contenido de iot_server al contenedor
COPY . .

# 5. SOLUCIÓN COMPLETA DE IMPORTACIONES:
# Le decimos a Uvicorn que se posicione virtualmente adentro de la carpeta 'backend'
# ... resto del Dockerfile igual ...

# Cambiamos "main:app" por "backend.main:app" y removemos --app-dir
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
