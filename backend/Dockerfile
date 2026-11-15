# Groundy API — imagen de produccion para Cloud Run
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

# Dependencias (capa cacheable)
COPY api/requirements.txt /app/api/requirements.txt
RUN pip install -r /app/api/requirements.txt

# Codigo y el unico dato que el motor lee en runtime
COPY src/ /app/src/
COPY api/ /app/api/
COPY data/crop_requirements.csv /app/data/crop_requirements.csv

# La llave de GEE NO va en la imagen: se monta por Secret Manager en /secrets/gee_key.json
# Cloud Run inyecta $PORT
CMD exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1
