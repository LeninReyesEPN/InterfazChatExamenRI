# Despliegue: AWS Amplify (frontend) + AWS EC2 (backend)

- **Frontend**: desplegado en **AWS Amplify**, apuntando al repo de GitHub. Amplify hace el
  build de Next.js automáticamente en cada push.
- **Backend**: instancia **EC2** (`t3.micro`, capa gratuita), corriendo la API FastAPI como
  servicio `systemd`, expuesta a internet vía **Cloudflare Tunnel** (HTTPS gratis, sin
  necesidad de dominio propio ni certificados).

## 1. Instancia EC2

- AMI: Ubuntu Server 24.04 LTS.
- Tipo: `t3.micro` (capa gratuita).
- Almacenamiento: **30 GB** (el default de 8GB no alcanza para `torch`+`sentence-transformers`+`faiss`).
- Security Group: solo puerto **22** (SSH). No se necesita abrir 80/443 — el túnel de Cloudflare
  hace la conexión de adentro hacia afuera.

## 2. Preparar el sistema

```bash
ssh -i tu-key.pem ubuntu@<IP_PUBLICA_EC2>

# Swap (la instancia tiene ~1GB de RAM, ajustado para el modelo de embeddings)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

sudo apt-get update -y
sudo apt-get install -y python3-venv python3-pip
```

## 3. Backend

```bash
mkdir -p ~/examen-ri-backend/backend
# Sube el código (rsync/scp) y backend/data/corpus.json + qrels.json desde tu máquina.

cd ~/examen-ri-backend
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install --upgrade pip

# IMPORTANTE: instalar torch CPU-only primero — si dejas que sentence-transformers lo resuelva
# solo, pip trae la variante con CUDA (varios GB de librerías NVIDIA innecesarias en un servidor
# sin GPU).
pip install torch --index-url https://download.pytorch.org/whl/cpu
grep -v '^torch$' backend/requirements.txt > /tmp/reqs_no_torch.txt
pip install -r /tmp/reqs_no_torch.txt
```

Crea `backend/.env` (nunca se sube al repo):

```
GEMINI_API_KEY=tu-clave-real
CORS_ORIGINS=https://tu-app.amplifyapp.com,http://localhost:3000
```

## 4. Cloudflare Tunnel (HTTPS sin dominio propio)

```bash
curl -L -o cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/cloudflared
```

Esto es un "quick tunnel" gratuito de Cloudflare: genera una URL pública
`https://<palabras-random>.trycloudflare.com` con HTTPS válido, sin necesitar cuenta ni dominio.

**Limitación importante**: la URL **cambia cada vez que el proceso de `cloudflared` se
reinicia** (reboot de la instancia, crash, actualización). Cada vez que eso pase hay que:
1. Leer la nueva URL en `/home/ubuntu/cloudflared.log`.
2. Actualizar `NEXT_PUBLIC_API_URL` en Amplify con la nueva URL y volver a desplegar.

## 5. Servicios systemd (persisten ante reinicios/crashes)

Copia `deploy/examen-ri-backend.service` y `deploy/cloudflared-tunnel.service` a la instancia:

```bash
sudo cp examen-ri-backend.service cloudflared-tunnel.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now examen-ri-backend
sudo systemctl enable --now cloudflared-tunnel
```

Revisa logs con `journalctl -u examen-ri-backend -f` o `tail -f /home/ubuntu/cloudflared.log`.

## 6. Frontend (AWS Amplify)

En **App settings → Environment variables** de Amplify:

| Variable | Valor |
|---|---|
| `NEXT_PUBLIC_API_URL` | la URL actual de `trycloudflare.com` (paso 4) |

`NEXT_PUBLIC_*` se hornea en el build — cualquier cambio requiere disparar un nuevo deploy en
Amplify para que tome efecto.

## 7. Verificación

```bash
curl https://<tu-url>.trycloudflare.com/api/health
# {"status":"healthy"}
```

Abre la URL de Amplify, envía una consulta y confirma que aparece la respuesta con el
acordeón de evidencias.
