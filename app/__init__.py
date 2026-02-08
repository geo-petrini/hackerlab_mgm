import os
from flask import Flask
from dotenv import load_dotenv
import docker

def _env_int(name: str, default: int) -> int:
    val = os.getenv(name, None)
    if val is None:
        return int(default)
    try:
        return int(val)
    except ValueError:
        raise ValueError(f"Variabile d'ambiente {name} non è un intero valido: {val}")

class Config:
    # Caricata dopo load_dotenv() in create_app
    IMAGE_NAME = os.getenv("IMAGE_NAME", "hackerlab:latest")
    CONTAINER_PREFIX = os.getenv("CONTAINER_PREFIX", "hlab_")
    TARGET_PORT = _env_int("TARGET_PORT", 80)   # porta esposta all’interno dell’immagine
    PORT_MIN = _env_int("PORT_MIN", 10000)
    PORT_MAX = _env_int("PORT_MAX", 10012)
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
    # Se vuoi personalizzare l'host per la URL esposta in /list
    PUBLIC_HOST = os.getenv("PUBLIC_HOST", "localhost")

def create_app() -> Flask:
    # Carica .env se presente
    load_dotenv()

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # Ricarica Config dopo load_dotenv (per leggere i nuovi env)
    app.config.from_object(Config)

    # Validazione minima
    if app.config["PORT_MIN"] >= app.config["PORT_MAX"]:
        raise ValueError("PORT_MIN deve essere < PORT_MAX")

    # Istanzia Docker client una volta
    try:
        client = docker.from_env()
        # Prova una chiamata leggera per validare accesso
        _ = client.version()
    except Exception as e:
        raise RuntimeError(f"Impossibile connettersi a Docker: {e}")

    app.config["DOCKER_CLIENT"] = client

    # Registra Blueprint
    from .api import api_bp
    app.register_blueprint(api_bp)

    return app