# syntax=docker/dockerfile:1

# Utilise une image officielle Python comme base
FROM python:3.14-slim@sha256:cea0e6040540fb2b965b6e7fb5ffa00871e632eef63719f0ea54bca189ce14a6 AS base

# Métadonnées OCI
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=main
LABEL org.opencontainers.image.title="Goupil" \
      org.opencontainers.image.description="Interface between Users and Developers" \
      org.opencontainers.image.source="https://github.com/BenjaminLECHA/Goupil" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.licenses="MIT"

# Définit le répertoire de travail dans le conteneur
WORKDIR /app

# Installe les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Utilisateur non-root
RUN groupadd --gid 1000 goupil \
    && useradd --uid 1000 --gid goupil --shell /usr/sbin/nologin --create-home goupil

# Copie les fichiers de l'application
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie le reste de l'application de manière ciblée
COPY --chown=goupil:goupil app.py constants.py forms.py mail.py models.py setup.py ./
COPY --chown=goupil:goupil controllers/ ./controllers/
COPY --chown=goupil:goupil templates/ ./templates/
COPY --chown=goupil:goupil static/ ./static/

# Répertoire pour le volume uploads, avec les bons droits avant de lâcher root
RUN mkdir -p /app/uploads && chown goupil:goupil /app/uploads

USER goupil

EXPOSE 5000

# Définit la commande par défaut pour le conteneur
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
