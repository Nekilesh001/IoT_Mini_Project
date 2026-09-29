"""
Service for Factory Summary and Machine Overview metadata.
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone
from storage.repository import TelemetryRepository
from simulator.core.domain import MachineProfile
from api.schemas.factory import (
    FactorySummaryResponse,
    StateCountSummary,
    HealthCountSummary,
)
from api.schemas.machine import (
    MachineOverviewItem,
    MachineDetailResponse,
    SignalMetadataItem,
)
from api.schemas.health import ProtocolHealthItem, ProtocolHealthSummary


class FactoryService:
    def __init__(self, repository: TelemetryRepository, profiles: Dict[str, MachineProfile]):
        self._repo = repository
        self._profiles = profiles

    def get_factory_summary(self) -> FactorySummaryResponse:
        total_machines = len(self._profiles)
        states = {"RUNNING": 0, "IDLE": 0, "STARTING": 0, "STOPPING": 0, "MAINTENANCE": 0, "OFF": 0}
        healths = {"HEALTHY": 0, "WARNING": 0, "CRITICAL": 0}
        total_records = 0
        latest_event_time = None

        protocol_machines: Dict[str, List[str]] = {"MODBUS_TCP": [], "OPC_UA": [], "MQTT": []}
        protocol_last_seen: Dict[str, Optional[str]] = {"MODBUS_TCP": None, "OPC_UA": None, "MQTT": None}

        for machine_id, profile in self._profiles.items():
            proto_name = profile.protocol_metadata.value if hasattr(profile.protocol_metadata, "value") else str(profile.protocol_metadata)
            if proto_name not in protocol_machines:
                protocol_machines[proto_name] = []
            protocol_machines[proto_name].append(machine_id)

            rec_count = self._repo.count_by_machine(machine_id)
            total_records += rec_count

            latest = self._repo.get_latest_by_machine(machine_id)
            if latest:
                st = latest.operating_state.upper()
                hl = latest.health_state.upper()
                if st in states:
                    states[st] += 1
                if hl in healths:
                    healths[hl] += 1

                t_str = latest.event_time.isoformat() if latest.event_time else None
                if t_str and (latest_event_time is None or t_str > latest_event_time):
                    latest_event_time = t_str

                if t_str:
                    curr_ls = protocol_last_seen.get(proto_name)
                    if curr_ls is None or t_str > curr_ls:
                        protocol_last_seen[proto_name] = t_str
            else:
                states["OFF"] += 1
                healths["HEALTHY"] += 1

        protocol_items = [
            ProtocolHealthItem(
                protocol=proto,
                status="ONLINE" if protocol_last_seen.get(proto) else "STANDBY",
                endpoint="127.0.0.1:5020" if proto == "MODBUS_TCP" else ("opc.tcp://127.0.0.1:4840" if proto == "OPC_UA" else "127.0.0.1:1883"),
                assigned_machines=protocol_machines.get(proto, []),
                last_seen=protocol_last_seen.get(proto)
            )
            for proto in ["MODBUS_TCP", "OPC_UA", "MQTT"]
        ]

        return FactorySummaryResponse(
            total_machines=total_machines,
            states=StateCountSummary(
                running=states["RUNNING"],
                idle=states["IDLE"],
                starting=states["STARTING"],
                stopping=states["STOPPING"],
                maintenance=states["MAINTENANCE"],
                off=states["OFF"]
            ),
            health=HealthCountSummary(
                healthy=healths["HEALTHY"],
                warning=healths["WARNING"],
                critical=healths["CRITICAL"]
            ),
            protocols=protocol_items,
            total_telemetry_records=total_records,
            latest_event_time=latest_event_time
        )

    def get_all_machines(self) -> List[MachineOverviewItem]:
        items = []
        for machine_id, profile in sorted(self._profiles.items()):
            latest = self._repo.get_latest_by_machine(machine_id)
            proto_str = profile.protocol_metadata.value if hasattr(profile.protocol_metadata, "value") else str(profile.protocol_metadata)
            mtype_str = profile.machine_type.value if hasattr(profile.machine_type, "value") else str(profile.machine_type)

            if latest:
                # Pick 2-4 key measurements dynamically for cards
                key_meas = dict(list(latest.measurements.items())[:4]) if latest.measurements else {}
                items.append(MachineOverviewItem(
                    machine_id=machine_id,
                    machine_type=mtype_str,
                    protocol=proto_str,
                    plant_id=profile.plant_id,
                    line_id=profile.line_id,
                    operating_state=latest.operating_state,
                    health_state=latest.health_state,
                    quality=latest.quality,
                    sequence=latest.sequence,
                    latest_event_time=latest.event_time.isoformat() if latest.event_time else None,
                    key_measurements=key_meas
                ))
            else:
                items.append(MachineOverviewItem(
                    machine_id=machine_id,
                    machine_type=mtype_str,
                    protocol=proto_str,
                    plant_id=profile.plant_id,
                    line_id=profile.line_id,
                    operating_state="OFF",
                    health_state="HEALTHY",
                    quality="GOOD",
                    sequence=0,
                    latest_event_time=None,
                    key_measurements={}
                ))
        return items

    def get_machine_detail(self, machine_id: str) -> Optional[MachineDetailResponse]:
        profile = self._profiles.get(machine_id)
        if not profile:
            return None

        latest = self._repo.get_latest_by_machine(machine_id)
        proto_str = profile.protocol_metadata.value if hasattr(profile.protocol_metadata, "value") else str(profile.protocol_metadata)
        mtype_str = profile.machine_type.value if hasattr(profile.machine_type, "value") else str(profile.machine_type)

        signals = [
            SignalMetadataItem(
                name=s.name,
                signal_type=s.signal_type.value if hasattr(s.signal_type, "value") else str(s.signal_type),
                unit=s.unit,
                min_value=float(s.min_value) if s.min_value is not None else None,
                max_value=float(s.max_value) if s.max_value is not None else None,
                nominal_value=s.nominal_value,
                description=s.description
            )
            for s in profile.signals
        ]

        if latest:
            return MachineDetailResponse(
                machine_id=machine_id,
                machine_type=mtype_str,
                protocol=proto_str,
                plant_id=profile.plant_id,
                line_id=profile.line_id,
                operating_state=latest.operating_state,
                health_state=latest.health_state,
                quality=latest.quality,
                sequence=latest.sequence,
                latest_event_time=latest.event_time.isoformat() if latest.event_time else None,
                latest_ingestion_time=latest.ingestion_time.isoformat() if latest.ingestion_time else None,
                source_endpoint=latest.endpoint,
                source_address=latest.source_address,
                signals=signals,
                current_measurements=latest.measurements or {},
                current_derived=latest.derived or {}
            )
        else:
            return MachineDetailResponse(
                machine_id=machine_id,
                machine_type=mtype_str,
                protocol=proto_str,
                plant_id=profile.plant_id,
                line_id=profile.line_id,
                operating_state="OFF",
                health_state="HEALTHY",
                quality="GOOD",
                sequence=0,
                latest_event_time=None,
                latest_ingestion_time=None,
                source_endpoint=None,
                source_address=None,
                signals=signals,
                current_measurements={},
                current_derived={}
            )

    def get_protocol_health_summary(self) -> ProtocolHealthSummary:
        summary = self.get_factory_summary()
        online_count = sum(1 for p in summary.protocols if p.status == "ONLINE")
        return ProtocolHealthSummary(
            protocols=summary.protocols,
            total_protocols=len(summary.protocols),
            online_protocols=online_count
        )
