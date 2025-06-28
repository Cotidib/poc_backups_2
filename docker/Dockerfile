FROM python:3.9-slim

# Instalar cliente MySQL y herramientas necesarias
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    wget \
    xz-utils \
    && wget https://downloads.mysql.com/archives/get/p/23/file/mysql-8.0.35-linux-glibc2.28-x86_64.tar.xz \
    && tar -xf mysql-8.0.35-linux-glibc2.28-x86_64.tar.xz \
    && cp mysql-8.0.35-linux-glibc2.28-x86_64/bin/mysqlbinlog /usr/local/bin/ \
    && chmod +x /usr/local/bin/mysqlbinlog \
    && rm -rf mysql-8.0.35-linux-glibc2.28-x86_64* \
    && apt-get remove -y wget xz-utils && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar archivos necesarios
COPY ../requirements.txt .
COPY ../src/ src/
COPY ../sql/ sql/

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Crear directorio para backups
RUN mkdir backups

CMD ["tail", "-f", "/dev/null"]