from flask import Blueprint, current_app, jsonify, render_template, request
from docker.errors import NotFound
from .utils import get_free_port, compute_url_for_container, extract_host_ports

api_bp = Blueprint("api", __name__)

@api_bp.get("/")
def index():
    return render_template("index.html")

@api_bp.post("/create")
def create_containers():
    cfg = current_app.config
    client = cfg["DOCKER_CLIENT"]

    try:
        data = request.get_json(force=True, silent=True) or {}
        count = int(data.get("count", 1))
        if count < 1:
            return jsonify({"error": "Il parametro 'count' deve essere >= 1"}), 400
    except Exception:
        return jsonify({"error": "Body JSON non valido"}), 400

    created = []
    for _ in range(count):
        port = get_free_port(client, cfg["PORT_MIN"], cfg["PORT_MAX"], cfg["CONTAINER_PREFIX"])
        if port is None:
            return jsonify({"error": "Nessuna porta disponibile nel range"}), 400

        name = f"{cfg['CONTAINER_PREFIX']}{port}"

        # Se esiste un container con lo stesso nome (magari stoppato), proviamo a rimuoverlo prima
        existing = client.containers.list(all=True, filters={"name": f"^{name}$"})
        for ec in existing:
            try:
                if ec.status == "running":
                    ec.stop()
                ec.remove()
            except Exception:
                pass

        container = client.containers.run(
            cfg["IMAGE_NAME"],
            name=name,
            detach=True,
            ports={f"{cfg['TARGET_PORT']}/tcp": port},
        )

        created.append({
            "id": container.id,
            "name": container.name,
            "port": port,
        })

    return jsonify({"created": created})

@api_bp.get("/list")
def list_containers():
    cfg = current_app.config
    client = cfg["DOCKER_CLIENT"]
    containers = client.containers.list(all=True, filters={"name": cfg["CONTAINER_PREFIX"]})

    result = []
    for c in containers:
        # Ports robusto dai attrs (invece di c.ports che talvolta è vuoto)
        ports = extract_host_ports(c)
        url = compute_url_for_container(c, public_host=cfg["PUBLIC_HOST"])
        result.append({
            "id": c.id,
            "name": c.name,
            "status": c.status,
            "ports": ports,
            "url": url,
        })
    return jsonify(result)

@api_bp.delete("/delete")
def delete_containers():
    cfg = current_app.config
    client = cfg["DOCKER_CLIENT"]

    data = request.get_json(force=True, silent=True) or {}
    ids = data.get("ids", [])
    if not isinstance(ids, list):
        return jsonify({"error": "'ids' deve essere una lista"}), 400

    removed = []
    errors = []

    for cid in ids:
        try:
            c = client.containers.get(cid)
            if c.status == "running":
                c.stop()
            c.remove()
            removed.append(cid)
        except NotFound:
            # Considera già rimosso se non esiste
            removed.append(cid)
        except Exception as e:
            errors.append({"id": cid, "error": str(e)})

    status = 200 if removed else 400
    return jsonify({"removed": removed, "errors": errors}), status