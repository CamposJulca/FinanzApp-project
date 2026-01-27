#!/bin/bash
set -e

echo "🚀 Inicializando estructura base de FinanzApp..."

# Archivos raíz
touch docker-compose.yml
touch .env

# Backend
mkdir -p backend/finanzapp
mkdir -p backend/transactions

touch backend/Dockerfile
touch backend/manage.py

touch backend/finanzapp/settings.py
touch backend/finanzapp/urls.py
touch backend/finanzapp/wsgi.py

touch backend/transactions/models.py
touch backend/transactions/views.py
touch backend/transactions/serializers.py
touch backend/transactions/services.py

# Frontend
mkdir -p frontend/src/components
mkdir -p frontend/src/pages
mkdir -p frontend/src/services

touch frontend/Dockerfile

# MongoDB
mkdir -p mongodb/data

echo "✅ Estructura de FinanzApp creada correctamente."
echo
echo "📂 Árbol generado:"
tree -a -L 4 || echo "(instala 'tree' para visualizar el árbol)"

