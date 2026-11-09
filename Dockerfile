# Imagen del Observatorio de Inteligencia Turística - Grupo 5
FROM python:3.13-slim

WORKDIR /app

# Dependencias (capa cacheable)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código fuente y dashboard
COPY src/ ./src/
COPY app/ ./app/

# Los datos NO se copian a la imagen (confidencialidad).
# Se montan por volumen: docker compose up
# El dashboard ejecuta el ETL automáticamente si no existen datos procesados.

EXPOSE 8501

CMD ["streamlit", "run", "app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
