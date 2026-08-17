from __future__ import annotations

import socket

import psutil


def local_ip_for(manager_address: str) -> str:
    host = manager_address.rsplit(":", 1)[0]
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect((host, 1))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def collect_system_info(manager_address: str) -> dict:
    memory = psutil.virtual_memory()
    return {
        "hostname": socket.gethostname(),
        "ip": local_ip_for(manager_address),
        "cpu_count": psutil.cpu_count() or 0,
        "memory_mb": int(memory.total / (1024 * 1024)),
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": memory.percent,
    }
