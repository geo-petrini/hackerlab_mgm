from typing import Dict, Any, Set, Optional
from docker import DockerClient

def extract_host_ports(container) -> Dict[str, Any]:
    """
    Estrae i mapping porta host dai NetworkSettings.Ports (quando disponibili).
    Ritorna un dizionario simile a c.attrs["NetworkSettings"]["Ports"].
    """
    ports = container.attrs.get("NetworkSettings", {}).get("Ports", {})
    return ports or {}

def used_ports_from_bindings(client: DockerClient) -> Set[int]:
    used: Set[int] = set()
    for c in client.containers.list(all=True):
        ports = extract_host_ports(c)
        if not ports:
            continue
        for _, mappings in ports.items():
            if mappings is None:
                continue
            for bind in mappings:
                host_port = bind.get("HostPort")
                if host_port and host_port.isdigit():
                    used.add(int(host_port))
    return used

def used_ports_from_names(client: DockerClient, prefix: str) -> Set[int]:
    """
    Fallback robusto: se i bindings non sono esposti/visibili,
    prova a ricavare le porte dal nome 'prefix<porta>' (es. 'hlab_10001').
    """
    used: Set[int] = set()
    for c in client.containers.list(all=True, filters={"name": prefix}):
        name = c.name or ""
        if name.startswith(prefix):
            suffix = name[len(prefix):]
            if suffix.isdigit():
                used.add(int(suffix))
    return used

def get_used_ports(client: DockerClient, prefix: str) -> Set[int]:
    # Combina entrambi i metodi (bindings + nome)
    return used_ports_from_bindings(client) | used_ports_from_names(client, prefix)

def get_free_port(client: DockerClient, port_min: int, port_max: int, prefix: str) -> Optional[int]:
    used = get_used_ports(client, prefix)
    for p in range(port_min, port_max + 1):
        if p not in used:
            return p
    return None

def compute_url_for_container(container, public_host: str = "localhost") -> Optional[str]:
    """
    Tenta di costruire una URL a partire dal primo HostPort disponibile.
    Altrimenti prova a ricavare dal nome se segue lo schema prefix<porta>.
    """
    ports = extract_host_ports(container)
    # Prova dai bindings
    for _, mappings in ports.items():
        if not mappings:
            continue
        host_port = mappings[0].get("HostPort")
        if host_port:
            return f"http://{public_host}:{host_port}"
    # Fallback dal nome
    name = container.name or ""
    # Se termina con cifre, assumiamo che sia la porta
    acc = []
    for ch in reversed(name):
        if ch.isdigit():
            acc.append(ch)
        else:
            break
    if acc:
        port = "".join(reversed(acc))
        return f"http://{public_host}:{port}"
    return None