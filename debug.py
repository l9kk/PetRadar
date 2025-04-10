import os
import sys
import platform
import socket
import json
import uvicorn
from fastapi import FastAPI

debug_app = FastAPI(title="Debug App")


@debug_app.get("/")
async def debug_info():
    """Return diagnostic information"""
    env_vars = {
        k: v
        for k, v in os.environ.items()
        if not any(secret in k.lower() for secret in ["key", "secret", "pass", "token"])
    }

    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = "Unable to determine"

    diagnostic_info = {
        "system": {
            "platform": platform.platform(),
            "python_version": sys.version,
            "hostname": hostname,
            "local_ip": local_ip,
        },
        "network": {
            "can_connect_to_internet": check_internet_connection(),
            "hostname_resolution": check_hostname_resolution(),
        },
        "environment": env_vars,
        "ports": check_port_availability(
            [8000, 8080, int(os.environ.get("PORT", 8000))]
        ),
    }

    return diagnostic_info


def check_internet_connection():
    """Check if we can connect to a public DNS server"""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except:
        return False


def check_hostname_resolution():
    """Check if hostname resolution works"""
    try:
        socket.gethostbyname("google.com")
        return True
    except:
        return False


def check_port_availability(ports):
    """Check if ports are available"""
    results = {}
    for port in ports:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("0.0.0.0", port))
            s.close()
            results[port] = "available"
        except:
            results[port] = "in use or unavailable"
    return results


if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8000))

    print(f"Starting debug server on port {port}")
    uvicorn.run("debug:debug_app", host="0.0.0.0", port=port, reload=False)
