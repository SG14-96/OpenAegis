from typing import Any, Dict, List

from fastapi import APIRouter
from serial.tools import list_ports

router = APIRouter(prefix="/hardware", tags=["hardware"])


def _parse_port(port: Any) -> Dict[str, Any]:
    return {
        "device": port.device,
        "name": getattr(port, "name", None),
        "description": getattr(port, "description", None),
        "hwid": getattr(port, "hwid", None),
        "manufacturer": getattr(port, "manufacturer", None),
        "product": getattr(port, "product", None),
        "serial_number": getattr(port, "serial_number", None),
        "location": getattr(port, "location", None),
        "vid": getattr(port, "vid", None),
        "pid": getattr(port, "pid", None),
    }


@router.get("/ports")
def get_available_ports() -> Dict[str, List[Dict[str, Any]]]:
    ports = list_ports.comports()
    serial_ports: List[Dict[str, Any]] = []
    usb_ports: List[Dict[str, Any]] = []

    for port in ports:
        port_info = _parse_port(port)
        serial_ports.append(port_info)

        if port_info["vid"] is not None or port_info["pid"] is not None or (
            port_info["description"] and "USB" in port_info["description"].upper()
        ):
            usb_ports.append(port_info)

    return {
        "serial_ports": serial_ports,
        "usb_ports": usb_ports,
    }

@router.get("/info")
def get_hardware_info() -> Dict[str, Any]:
    # Placeholder for future hardware info retrieval logic
    return {
        "message": "Hardware info endpoint is under development."
    }