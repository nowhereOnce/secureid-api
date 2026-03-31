# Usa una imagen ligera de Python
FROM python:3.11-slim

# Evita que Python genere archivos .pyc y permite ver logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependencias del sistema
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    cmake \
    g++ \
    git \
    libgl1 \
    libglib2.0-0 \
    libxcb1 \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

# Instalamos setuptools ANTES que lo demás para que pkg_resources esté disponible
RUN pip install --no-cache-dir setuptools==70.0.0

# Instala dependencias de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código del proyecto
COPY . /app/
