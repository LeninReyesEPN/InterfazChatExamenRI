# Despliegue en AWS EC2 (t2.micro / t3.micro, capa gratuita)

Este documento describe cómo desplegar **backend (FastAPI) + frontend (Next.js)** en una sola
instancia EC2 de la capa gratuita, con `nginx` enrutando por path. No requiere contenedores.

> Nota: yo (Claude) no tengo acceso a tu cuenta de AWS y no ejecuto estos pasos por ti — esta guía
> y los scripts de `deploy/` son para que tú los corras en tu propia instancia.

## 0. Por qué esta arquitectura

- Un `t2.micro`/`t3.micro` tiene **1 GB de RAM**. `sentence-transformers` + `torch` + `faiss` +
  el proceso de Next.js compiten por esa memoria, así que:
  - Se agrega un **swapfile de 2 GB** (paso 2) — sin esto, el proceso de embeddings o el build de
    Next.js pueden morir por out-of-memory.
  - El **build de Next.js se hace una sola vez** (`npm run build` + `next start`), nunca se corre
    `next dev` en producción (usa mucha más RAM).
  - El backend descarga el corpus y construye el índice FAISS **una vez** en el primer arranque
    (`~4000 papers`, tarda un par de minutos); en arranques siguientes reutiliza los archivos ya
    generados en `backend/data/`.

## 1. Crear la instancia EC2

- AMI: Ubuntu Server 22.04 LTS (capa gratuita).
- Tipo: `t3.micro` o `t2.micro`.
- Security Group: abre los puertos
  - `22` (SSH, solo desde tu IP),
  - `80` (HTTP, `0.0.0.0/0`) — es el único puerto público que necesitas, nginx enruta todo desde ahí.
- Guarda la key pair (`.pem`) para conectarte por SSH.

## 2. Preparar el sistema (paquetes, swap)

Conéctate por SSH y ejecuta el script de aprovisionamiento (o los pasos manuales debajo):

```bash
ssh -i tu-key.pem ubuntu@<IP_PUBLICA_EC2>
```

Copia este repo a la instancia (por ejemplo con `git clone` a tu repo de GitHub, o `scp`), y luego:

```bash
cd ChatExamenRI
chmod +x deploy/setup_ec2.sh
./deploy/setup_ec2.sh
```

El script (`deploy/setup_ec2.sh`) hace lo siguiente:
1. Crea un swapfile de 2 GB si no existe (evita OOM en el `t2.micro`/`t3.micro`).
2. Instala Python 3, `python3-venv`, Node.js 20, `nginx`.
3. Crea el virtualenv del backend e instala `backend/requirements.txt`.
4. Instala dependencias de Node y corre `npm run build` del frontend.

## 3. Variables de entorno

**Backend** — crea `/etc/systemd/system/arxiv-rag-backend.service` a partir de
`deploy/arxiv-rag-backend.service` (incluido en este repo) y edita la línea `Environment=GEMINI_API_KEY=...`
con tu clave real. **Nunca** subas esta clave al repositorio; solo vive en el archivo de servicio de
systemd en la instancia (o mejor, en un archivo `backend/.env` con permisos `600` que el servicio
cargue — ver comentario en el unit file).

**Frontend** — crea `ChatExamenRI/.env.production` (no versionado) con:

```
NEXT_PUBLIC_API_URL=http://<IP_PUBLICA_EC2>/api
```

y vuelve a correr `npm run build` después de fijarlo (Next.js *inlinea* las variables `NEXT_PUBLIC_*`
en el build, así que el build debe hacerse **después** de definir esta variable).

## 4. Servicios systemd (para que sobrevivan reinicios/crashes)

Copia los unit files de `deploy/` a `/etc/systemd/system/` y actívalos:

```bash
sudo cp deploy/arxiv-rag-backend.service /etc/systemd/system/
sudo cp deploy/arxiv-rag-frontend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now arxiv-rag-backend
sudo systemctl enable --now arxiv-rag-frontend
sudo systemctl status arxiv-rag-backend arxiv-rag-frontend
```

La primera vez que arranca `arxiv-rag-backend`, descarga el corpus y construye el índice FAISS —
puede tardar 1-3 minutos; revisa el progreso con:

```bash
journalctl -u arxiv-rag-backend -f
```

## 5. nginx (enrutamiento por path, un solo puerto público)

```bash
sudo cp deploy/nginx-arxiv-rag.conf /etc/nginx/sites-available/arxiv-rag
sudo ln -sf /etc/nginx/sites-available/arxiv-rag /etc/nginx/sites-enabled/arxiv-rag
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

Con esto, `http://<IP_PUBLICA_EC2>/` sirve el frontend y `http://<IP_PUBLICA_EC2>/api/...` proxyea
al backend FastAPI (puerto 8000 interno).

## 6. Verificación

```bash
curl http://<IP_PUBLICA_EC2>/api/health
# {"status":"healthy"}
```

Abre `http://<IP_PUBLICA_EC2>/` en el navegador, envía una consulta y confirma que aparece la
respuesta junto con el acordeón de evidencias. Pega esta URL en la Sección H del notebook
(`examen_rag_arxiv.ipynb`).

## 7. Mantener la instancia disponible durante la evaluación

- No detengas ni "hibernes" la instancia mientras dure el período de evaluación del examen.
- Un `t2.micro`/`t3.micro` de la capa gratuita no tiene límite de tiempo de uso continuo, solo un
  tope de horas-mes; revisa tu consumo en el dashboard de Free Tier de AWS para no exceder las 750
  horas/mes si tienes otras instancias corriendo en paralelo.
- Si reinicias la instancia (reboot), los servicios systemd (`enable`d) arrancan solos; nginx
  también. No necesitas volver a ejecutar nada manualmente.
