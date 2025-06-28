FROM python:3.9-slim

# Instalar dependencias del sistema incluyendo mariadb-client para mariadb-binlog
RUN apt-get update && \
    apt-get install -y mariadb-client && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar archivos necesarios
COPY requirements.txt .
COPY backup_completo.py .
COPY backup_incremental.py .
COPY db_config.py .
COPY db_utils.py .
COPY disaster_simulator.py .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Crear directorio para backups
RUN mkdir backups

CMD ["tail", "-f", "/dev/null"] 