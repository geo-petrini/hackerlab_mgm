from flask import Flask, request, jsonify, render_template
import docker
import random

app = Flask(__name__)
client = docker.from_env()

IMAGE_NAME = "hackerlab:latest"        # esempio: python:3.10
PORT_RANGE = (10000, 19999)
CONTAINER_PREFIX = "hlab_"

def get_used_ports():
    used = set()

    for c in client.containers.list(all=True):
        ports = c.attrs.get("NetworkSettings", {}).get("Ports", {})

        if not ports:
            continue

        for container_port, mappings in ports.items():
            if mappings is None:
                continue

            for bind in mappings:
                host_port = bind.get("HostPort")
                if host_port and host_port.isdigit():
                    used.add(int(host_port))

    return used

def get_free_port():
    used_ports = get_used_ports()

    for port in range(PORT_RANGE[0], PORT_RANGE[1]):
        if port not in used_ports:
            return port

    return None


@app.get("/")
def index():
    return render_template("index.html")

@app.route("/create", methods=["POST"])
def create_containers():
    try:
        data = request.json
        count = data.get("count", 1)

        created = []

        for i in range(count):
            port = get_free_port()
            if port is None:
                return jsonify({"error": "No available ports in range"}), 400

            container = client.containers.run(
                IMAGE_NAME,
                name=f"{CONTAINER_PREFIX}{port}",
                detach=True,
                ports={"80/tcp": port}  # mappa la porta 80 dell'immagine
            )
            created.append({"id": container.id, "port": port})

        return jsonify({"created": created})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/list", methods=["GET"])
def list_containers():
    containers = client.containers.list(all=True, filters={"name": CONTAINER_PREFIX})
    result = []
    for c in containers:
        result.append({
            "id": c.id,
            "name": c.name,
            "status": c.status,
            "ports": c.ports,
            "url": f"http://localhost:{list(c.ports.values())[0][0]['HostPort']}" if c.ports else None
        })
    return jsonify(result)


@app.route("/delete", methods=["DELETE"])
def delete_containers():
    data = request.get_json(force=True, silent=True) or {}
    ids = data.get("ids", [])
    removed = []
    errors = []

    for cid in ids:
        try:
            container = client.containers.get(cid)
            container.stop()
            container.remove()
            removed.append(cid)
        except Exception as e:
            errors.append({"id": cid, "error": str(e)})

    status = 200 if removed else 400
    return jsonify({"removed": removed, "errors": errors}), status


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)