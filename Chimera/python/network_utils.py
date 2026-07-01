import urllib.request
import json
import socket

from config import (
    LM_STUDIO_BASE_URL,
    LM_STUDIO_MODELS_ENDPOINT,
    logger,
)


def check_lm_studio_health(timeout: int = 5) -> bool:
    """Check if LM Studio API is healthy and reachable.

    Args:
        timeout: Request timeout in seconds

    Returns:
        True if LM Studio is reachable and healthy, False otherwise
    """
    try:
        req = urllib.request.Request(LM_STUDIO_MODELS_ENDPOINT)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                return isinstance(data, dict)
            return False
    except Exception:
        logger.warning(f"LM Studio API health check failed at {LM_STUDIO_MODELS_ENDPOINT}")
        return False


def check_network_connectivity(host: str, port: int, timeout: int = 3) -> bool:
    """Check network connectivity to a specific host and port.

    Args:
        host: Hostname or IP address
        port: Port number
        timeout: Connection timeout in seconds

    Returns:
        True if connection successful, False otherwise
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        return result == 0
    except Exception:
        return False
    finally:
        sock.close()
