# syntax=docker/dockerfile:1

# Utilise une image officielle Python comme base
FROM python:3.14-slim@sha256:cea0e6040540fb2b965b6e7fb5ffa00871e632eef63719f0ea54bca189ce14a6 AS base

# Définit le répertoire de travail dans le conteneur
WORKDIR /app

# Installe les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copie les fichiers de l'application
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie le reste de l'application
COPY . .

# Définit la commande par défaut pour le conteneur
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
