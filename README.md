# Hackerlab Manager

Piccolo web app per la creazione di container Docker basati sull'immagine HackerLab sviluppata da Filippo Finke nel 2019 presso il CPT di Trevano, sezione SAMT Info.

## Struttura del progetto

```
project/
│
├─ app/
│  ├─ __init__.py         # create_app() + Config + dotenv
│  ├─ api.py              # Blueprint con le routes
│  ├─ utils.py            # helper porte e parsing
│  ├─ templates/
│  │   └─ index.html      # tua UI
│  └─ static/
│      └─ main.js         # tua logica JS
│
├─ run.py                 # avvio in locale (debug)
├─ requirements.txt
├─ .env                   # variabili d'ambiente (vedi esempio)
├─ Dockerfile             # opzionale
└─ docker-compose.yml     # opzionale
```

## Configurazione

Impostare le seguenti variabili d'ambiente
**Immagine docker da usare per gli studenti**

`IMAGE_NAME=hackerlab:latest`

**Prefisso per i container creati**

`CONTAINER_PREFIX=hlab_`

**Porta interna esposta dall'immagine (verrà pubblicata sull'host)**

`TARGET_PORT=80`

**Range porte host**

`PORT_MIN=10000`
`PORT_MAX=19999`

**Host pubblico usato per costruire le URL in /list**

`PUBLIC_HOST=localhost`

**Flask debug**

`FLASK_DEBUG=true`

### File .env di esempio
```
# Immagine docker da usare per gli studenti
IMAGE_NAME=hackerlab:latest

# Prefisso per i container creati
CONTAINER_PREFIX=hlab_

# Porta interna esposta dall'immagine (verrà pubblicata sull'host)
TARGET_PORT=80

# Range porte host
PORT_MIN=10000
PORT_MAX=19999

# Host pubblico usato per costruire le URL in /list
PUBLIC_HOST=localhost

# Flask debug
FLASK_DEBUG=true
```

### Logo
Image generated via MS Copilot