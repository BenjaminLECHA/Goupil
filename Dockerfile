# Utilise une image officielle Python comme base
FROM python:3.14-slim

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

# Route /health ajoutée dans app.py : vérifie la connexion DB (SELECT 1)
# et renvoie 503 si la base est injoignable.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health')" || exit 1

# Définit la commande par défaut pour le conteneur
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
