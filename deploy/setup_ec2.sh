#!/usr/bin/env bash
# Provisioning script for a fresh Ubuntu 22.04 EC2 t2.micro/t3.micro instance.
# Run from the repo root: ./deploy/setup_ec2.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

echo "== 1. Swapfile (2GB) para RAM limitada del t2/t3.micro =="
if [ ! -f /swapfile ]; then
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab
else
  echo "Swapfile ya existe, se omite."
fi

echo "== 2. Paquetes del sistema =="
sudo apt-get update -y
sudo apt-get install -y python3 python3-venv python3-pip nginx curl

if ! command -v node >/dev/null 2>&1; then
  echo "== 3. Node.js 20 =="
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y nodejs
else
  echo "Node.js ya instalado: $(node -v)"
fi

echo "== 4. Entorno virtual + dependencias del backend =="
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
deactivate

echo "== 5. Dependencias y build del frontend =="
npm install --no-audit --no-fund
if [ -f .env.production ]; then
  echo "Usando .env.production existente para el build (NEXT_PUBLIC_API_URL)."
else
  echo "ADVERTENCIA: no existe .env.production. Créalo con NEXT_PUBLIC_API_URL antes del build (ver DEPLOY.md)."
fi
npm run build

echo ""
echo "Listo. Siguientes pasos manuales (ver DEPLOY.md):"
echo "  1. Configura GEMINI_API_KEY en deploy/arxiv-rag-backend.service"
echo "  2. Copia los unit files a /etc/systemd/system/ y actívalos"
echo "  3. Configura nginx con deploy/nginx-arxiv-rag.conf"
