"""
FastAPI Route Handlers for External IoT Devices (Wokwi Pico W & Environmental Sensors).
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.dependencies import (
    get_telemetry_repository,
    get_api_config,
)
from storage.repository import TelemetryRepository
from protocols.wokwi.config import WokwiConfig
from protocols.wokwi.registry import get_external_device_registry
from protocols.wokwi.models import ExternalDeviceProfile

router = APIRouter(prefix="/api/iot-devices", tags=["External IoT Devices"])


class IoTDeviceSummary(BaseModel):
    device_id: str
    device_type: str
    device_class: str
    plant_id: str
    line_id: str
    description: str
    hardware: str
    firmware_version: str
    ingress_broker: str
    telemetry_topic: str
    command_topic: str
    connection_status: str  # "ONLINE", "STALE", "OFFLINE"
    last_seen: Optional[str] = None
    latest_temperature_c: Optional[float] = None
    latest_humidity_pct: Optional[float] = None
    latest_sequence: Optional[int] = None
    actuator_state: Optional[Dict[str, Any]] = None
    control_state: Optional[Dict[str, Any]] = None


class CommandRequest(BaseModel):
    command: str = Field(..., description="Command name: SET_LED, SET_MODE, SET_THRESHOLDS")
    state: Optional[str] = Field(None, description="LED state: ON or OFF")
    mode: Optional[str] = Field(None, description="Control mode: AUTO or MANUAL")
    alert_threshold_c: Optional[float] = Field(None, description="High temp alert threshold in °C")
    normal_threshold_c: Optional[float] = Field(None, description="Normal temp recovery threshold in °C")


def _compute_connection_status(event_time: Optional[datetime], max_stale_seconds: float = 15.0) -> str:
    if not event_time:
        return "OFFLINE"
    
    now = datetime.now(timezone.utc)
    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=timezone.utc)
        
    diff = (now - event_time).total_seconds()
    if diff <= max_stale_seconds:
        return "ONLINE"
    elif diff <= max_stale_seconds * 4:
        return "STALE"
    return "OFFLINE"


@router.get("", response_model=List[IoTDeviceSummary])
def list_external_iot_devices(
    repo: TelemetryRepository = Depends(get_telemetry_repository),
):
    """
    List all external IoT devices with their latest telemetry readings,
    live connection status, and hardware profile.
    """
    registry = get_external_device_registry()
    devices = registry.list_devices()
    result = []

    for dev in devices:
        latest = repo.get_latest_by_machine(dev.device_id)
        
        last_seen = None
        temp_c = None
        hum_pct = None
        seq = None
        actuator = None
        control = None
        conn_status = "OFFLINE"

        if latest:
            last_seen = latest.event_time.isoformat() if latest.event_time else None
            conn_status = _compute_connection_status(latest.event_time)
            seq = latest.sequence
            meas = latest.measurements or {}
            temp_c = meas.get("temperature_c", meas.get("temperatureC"))
            hum_pct = meas.get("humidity_pct", meas.get("humidityPct"))
            
            # Extract metadata if available
            raw = latest.raw_payload or {}
            actuator = raw.get("actuator")
            control = raw.get("control")

        summary = IoTDeviceSummary(
            device_id=dev.device_id,
            device_type=dev.device_type,
            device_class=dev.device_class.value,
            plant_id=dev.plant_id,
            line_id=dev.line_id,
            description=dev.description,
            hardware=dev.hardware,
            firmware_version=dev.firmware_version,
            ingress_broker=dev.ingress_broker,
            telemetry_topic=dev.telemetry_topic,
            command_topic=dev.command_topic,
            connection_status=conn_status,
            last_seen=last_seen,
            latest_temperature_c=temp_c,
            latest_humidity_pct=hum_pct,
            latest_sequence=seq,
            actuator_state=actuator,
            control_state=control,
        )
        result.append(summary)

    return result


@router.get("/{device_id}", response_model=IoTDeviceSummary)
def get_external_iot_device(
    device_id: str,
    repo: TelemetryRepository = Depends(get_telemetry_repository),
):
    """Retrieve metadata and latest status for a specific external IoT device."""
    registry = get_external_device_registry()
    dev = registry.get_device(device_id)
    if not dev:
        raise HTTPException(status_code=404, detail=f"External IoT device '{device_id}' not found.")

    latest = repo.get_latest_by_machine(dev.device_id)
    last_seen = None
    temp_c = None
    hum_pct = None
    seq = None
    actuator = None
    control = None
    conn_status = "OFFLINE"

    if latest:
        last_seen = latest.event_time.isoformat() if latest.event_time else None
        conn_status = _compute_connection_status(latest.event_time)
        seq = latest.sequence
        meas = latest.measurements or {}
        temp_c = meas.get("temperature_c", meas.get("temperatureC"))
        hum_pct = meas.get("humidity_pct", meas.get("humidityPct"))
        raw = latest.raw_payload or {}
        actuator = raw.get("actuator")
        control = raw.get("control")

    return IoTDeviceSummary(
        device_id=dev.device_id,
        device_type=dev.device_type,
        device_class=dev.device_class.value,
        plant_id=dev.plant_id,
        line_id=dev.line_id,
        description=dev.description,
        hardware=dev.hardware,
        firmware_version=dev.firmware_version,
        ingress_broker=dev.ingress_broker,
        telemetry_topic=dev.telemetry_topic,
        command_topic=dev.command_topic,
        connection_status=conn_status,
        last_seen=last_seen,
        latest_temperature_c=temp_c,
        latest_humidity_pct=hum_pct,
        latest_sequence=seq,
        actuator_state=actuator,
        control_state=control,
    )


@router.get("/{device_id}/history")
def get_external_iot_history(
    device_id: str,
    limit: int = Query(50, ge=1, le=500),
    repo: TelemetryRepository = Depends(get_telemetry_repository),
):
    """Retrieve historical canonical telemetry points for an external IoT device."""
    registry = get_external_device_registry()
    if not registry.get_device(device_id):
        raise HTTPException(status_code=404, detail=f"External IoT device '{device_id}' not found.")

    records = repo.get_history_by_machine(device_id, limit=limit)
    return [
        {
            "eventId": r.event_id,
            "timestamp": r.event_time.isoformat() if r.event_time else None,
            "sequence": r.sequence,
            "quality": r.quality,
            "temperature_c": (r.measurements or {}).get("temperature_c"),
            "humidity_pct": (r.measurements or {}).get("humidity_pct"),
            "operatingState": r.operating_state,
        }
        for r in records
    ]


@router.get("/bridge/status")
def get_bridge_status():
    """Retrieve operational status and metrics for the Wokwi HiveMQ MQTT bridge."""
    cfg = WokwiConfig.from_env()
    return {
        "enabled": cfg.enabled,
        "broker": cfg.broker,
        "port": cfg.port,
        "telemetry_topic": cfg.telemetry_topic,
        "command_topic": cfg.command_topic,
        "device_id": cfg.device_id,
    }
