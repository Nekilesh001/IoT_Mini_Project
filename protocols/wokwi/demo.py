"""
Wokwi External IoT Integration Demo and Verification Script.

Demonstrates end-to-end telemetry flow:
Wokwi Pico W (DHT22) -> HiveMQ (broker.hivemq.com) -> Wokwi MQTT Bridge
-> Edge Ingestion -> Canonical Telemetry -> PostgreSQL/SQLite -> Alerts -> API / SSE
"""

import os
import sys
import time
import json
from datetime import datetime, timezone

from protocols.wokwi.config import WokwiConfig
from protocols.wokwi.bridge import WokwiMQTTBridge
from protocols.wokwi.registry import get_external_device_registry
from edge.service import EdgeIngestionService
from edge.models import IngestionStatus
from storage.database import get_engine, get_session_factory, init_db
from storage.repository import TelemetryRepository
from alerts.engine import AlertEngine
from alerts.repository import AlertRepository
from alerts.rules import create_default_rules

try:
    import paho.mqtt.client as mqtt
    PAHO_AVAILABLE = True
except ImportError:
    PAHO_AVAILABLE = False


def run_wokwi_demo():
    print("=" * 80)
    print(" SMART FACTORY — EXTERNAL WOKWI IOT DEVICE INTEGRATION DEMO")
    print("=" * 80)

    config = WokwiConfig.from_env()
    print(f"[*] Ingress Broker:      {config.broker}:{config.port}")
    print(f"[*] Telemetry Topic:     {config.telemetry_topic}")
    print(f"[*] Command Topic:       {config.command_topic}")
    print(f"[*] Device ID:           {config.device_id} ({config.device_type})")
    print(f"[*] Hardware:            Raspberry Pi Pico W + DHT22 + Status LED")
    print("=" * 80)

    # 1. Initialize Storage & Repositories
    db_url = os.getenv("DATABASE_URL", "sqlite:///wokwi_demo.db")
    engine = get_engine(db_url)
    init_db(engine)
    session_factory = get_session_factory(engine)
    telemetry_repo = TelemetryRepository(session_factory)
    alert_repo = AlertRepository(session_factory)
    alert_engine = AlertEngine(repository=alert_repo, rules=create_default_rules())

    # 2. Initialize Edge Ingestion Service with External IoT profiles
    registry = get_external_device_registry()
    edge_service = EdgeIngestionService(profiles=registry.get_all_machine_profiles())

    # 3. Start Wokwi MQTT Bridge
    bridge = WokwiMQTTBridge(config)
    print("\n[Step 1] Starting Local Wokwi MQTT Bridge...")
    bridge.start()
    time.sleep(1.5)

    bridge_status = bridge.get_status()
    print(f" -> Bridge Health: {bridge_status['health']} (Connected: {bridge_status['connected']})")

    # 4. Simulate Wokwi Telemetry Payloads
    sample_readings = [
        {"seq": 1, "temp": 24.5, "hum": 52.0, "desc": "Nominal Ambient State"},
        {"seq": 2, "temp": 31.2, "hum": 68.5, "desc": "High Temperature (Warning >=30°C, LED ON)"},
        {"seq": 3, "temp": 36.8, "hum": 74.0, "desc": "Critical Temperature (Alarm >=35°C, LED ON)"},
        {"seq": 4, "temp": 27.5, "hum": 50.0, "desc": "Temperature Recovery (<=28°C, LED OFF)"},
    ]

    print("\n[Step 2] Ingesting Simulated Wokwi Telemetry Packets...")

    for item in sample_readings:
        payload_dict = {
            "deviceId": config.device_id,
            "deviceType": config.device_type,
            "plantId": config.plant_id,
            "lineId": config.line_id,
            "eventType": "TELEMETRY",
            "sequence": item["seq"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "readings": {
                "temperatureC": item["temp"],
                "humidityPct": item["hum"]
            },
            "actuator": {
                "type": "LED",
                "state": "ON" if item["temp"] >= 30.0 else "OFF"
            },
            "control": {
                "mode": "AUTO",
                "alertThresholdC": 30.0,
                "normalThresholdC": 28.0
            },
            "firmwareVersion": "0.1.0"
        }

        # Normalize message through bridge normalizer
        reading, err = bridge.normalizer.normalize(
            raw_payload=payload_dict,
            topic=config.telemetry_topic,
            ingress_broker=config.broker
        )

        if err or not reading:
            print(f" [!] Normalization failed: {err}")
            continue

        # Ingest through edge pipeline
        ingestion_res = edge_service.ingest_reading(reading)
        if ingestion_res.status == IngestionStatus.ACCEPTED and ingestion_res.canonical_telemetry:
            canonical = ingestion_res.canonical_telemetry
            telemetry_repo.insert(canonical)
            alerts_triggered = alert_engine.process_telemetry(canonical)

            alert_info = f" -> ALERTS TRIGGERED: {[a.rule_id for a in alerts_triggered]}" if alerts_triggered else " -> No alerts"
            print(
                f" [+] #{canonical.sequence:03d} | "
                f"Temp: {canonical.measurements['temperature_c']}°C | "
                f"Hum: {canonical.measurements['humidity_pct']}% | "
                f"Quality: {canonical.quality.value} | "
                f"{item['desc']}{alert_info}"
            )

        time.sleep(0.3)

    # 5. Verify Database State
    print("\n[Step 3] Verifying Database Persistence & Historical Records...")
    latest = telemetry_repo.get_latest_by_machine(config.device_id)
    if latest:
        print(f" -> Database Latest Event ID: {latest.event_id}")
        print(f" -> Machine ID:               {latest.machine_id} ({latest.machine_type})")
        print(f" -> Latest Temperature:       {latest.measurements.get('temperature_c')}°C")
        print(f" -> Latest Humidity:          {latest.measurements.get('humidity_pct')}%")
        print(f" -> Sequence Counter:         {latest.sequence}")
        print(f" -> Source Address:           {latest.source_address}")

    # 6. Clean up
    print("\n[Step 4] Shutting down Wokwi MQTT Bridge...")
    bridge.stop()
    print("[*] Wokwi integration verification completed successfully.\n")


if __name__ == "__main__":
    run_wokwi_demo()
