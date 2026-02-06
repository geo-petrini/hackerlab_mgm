from flask import Flask, request, jsonify, render_template
import docker
import random

app = Flask(__name__)
client = docker.from_env()

IMAGE_NAME = "hackerlab:latest"        # esempio: python:3.10
PORT_RANGE = (10000, 19999)
CONTAINER_PREFIX = "hlab_"


def get_free_port():
    used_ports = set()

    for c in client.containers.list(all=True):
        ports = c.attrs["NetworkSettings"]["Ports"]
        if not ports:
            continue

        for container_port, bindings in ports.items():
            if bindings:
                for bind in bindings:
                    host_port = bind.get("HostPort")
                    if host_port:
                        try:
                            used_ports.add(int(host_port))
                        except ValueError:
                            pass

    for port in range(PORT_RANGE[0], PORT_RANGE[1]):
        if port not in used_ports:
            return port

    return None


@app.get("/")
def index():
    return render_template("index.html")

@app.post("/create")
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


@app.get("/list")
def list_containers():
    containers = client.containers.list(all=True, filters={"name": CONTAINER_PREFIX})
    result = []
    for c in containers:
        result.append({
            "id": c.id,
            "name": c.name,
            "status": c.status,
            "ports": c.ports
        })
    return jsonify(result)


@app.post("/delete")
def delete_containers():
    data = request.json
    ids = data.get("ids", [])
    removed = []

    for cid in ids:
        try:
            container = client.containers.get(cid)
            container.stop()
            container.remove()
            removed.append(cid)
        except:
            pass

    return jsonify({"removed": removed})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)