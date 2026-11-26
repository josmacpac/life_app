#!/bin/sh
set -e

echo "=============================================="
echo "  life-app-docker — Iniciando entorno"
echo "=============================================="

# -------------------------------------------------------------------
# 1. Build del frontend (Vite) si no existe dist/
# -------------------------------------------------------------------
echo ""
echo "1/2 Verificando build del frontend..."

FRONT_DIR="/app/frontend"

if [ -d "$FRONT_DIR/dist" ] && [ -f "$FRONT_DIR/dist/index.html" ]; then
  echo "  → Frontend: dist/ ya existe, saltando build"
else
  echo "  → Frontend: ejecutando vite build..."
  if (
    cd "$FRONT_DIR"
    if [ ! -d "node_modules" ]; then
      echo "  → Frontend: npm install..."
      npm install --silent
    fi
    VITE_API_URL="${VITE_API_URL-http://localhost}" npm run build
  ); then
    echo "  → Frontend: build OK"
  else
    echo "  ⚠ Frontend: build FALLÓ (ver arriba); se servirá placeholder"
  fi
fi

# -------------------------------------------------------------------
# 2. Copiar archivos estáticos a directorios de Nginx
# -------------------------------------------------------------------
echo ""
echo "2/2 Copiando archivos a Nginx..."

if [ -d "$FRONT_DIR/dist" ]; then
  mkdir -p /usr/share/nginx/html/frontend
  cp -r "$FRONT_DIR/dist/." /usr/share/nginx/html/frontend/
  echo "  → Frontend: dist/ copiado a /usr/share/nginx/html/frontend/"
else
  mkdir -p /usr/share/nginx/html/frontend
  echo "<h1>life_app: build del frontend no disponible</h1>" > /usr/share/nginx/html/frontend/index.html
  echo "  → Frontend: placeholder creado"
fi

echo ""
echo "=============================================="
echo "  Entorno listo!"
echo "  → Frontend: http://localhost/"
echo "  → API:      http://localhost/api/"
echo "  → Health:   http://localhost/api/health"
echo "=============================================="
echo ""

# Ejecutar el comando principal (nginx)
exec "$@"
