"""
Unit tests for Cloud & AWS Adapter Scaffolding.
Verifies that the cloud interfaces and AWS scaffold adapters import cleanly, default to disabled (AWS_ENABLED=false),
and execute safely without attempting live cloud connections or requiring AWS credentials.
"""

from cloud.aws.config import AWSConfig
from cloud.aws.iot_core import AWSIoTCoreAdapter
from cloud.aws.device_shadow import AWSIoTDeviceShadowAdapter
from cloud.aws.jobs import AWSIoTJobsAdapter
from cloud.aws.fleet_indexing import AWSIoTFleetIndexingAdapter
from cloud.interfaces.device_state import CloudDeviceStateInterface
from cloud.interfaces.jobs import CloudJobsInterface
from cloud.interfaces.fleet import CloudFleetIndexingInterface
from device_management.models import FleetDeviceRecord, ConnectivityState


def test_aws_config_default_disabled():
    cfg = AWSConfig()
    assert cfg.enabled is False
    assert cfg.region == "us-east-1"
    assert cfg.endpoint == ""


def test_aws_scaffold_interfaces_and_safe_stubs():
    cfg = AWSConfig(enabled=False)

    # IoT Core Adapter
    iot_adapter = AWSIoTCoreAdapter(cfg)
    assert iot_adapter.is_enabled is False
    assert iot_adapter.is_connected is False
    assert iot_adapter.connect() is False
    assert iot_adapter.publish_telemetry("topic", {"data": 1}) is False

    # Device Shadow Adapter
    shadow_adapter = AWSIoTDeviceShadowAdapter(cfg)
    assert isinstance(shadow_adapter, CloudDeviceStateInterface)
    assert shadow_adapter.is_enabled is False
    assert shadow_adapter.get_shadow("CNC-001") is None
    shadow_rec = shadow_adapter.update_desired_state("CNC-001", {"mode": "AUTO"})
    assert shadow_rec.desired_state == {"mode": "AUTO"}

    # Jobs Adapter
    jobs_adapter = AWSIoTJobsAdapter(cfg)
    assert isinstance(jobs_adapter, CloudJobsInterface)
    assert jobs_adapter.is_enabled is False
    stub_job = jobs_adapter.create_cloud_job("job_123", ["CNC-001"], {"cmd": "restart"})
    assert stub_job.job_id == "job_123"

    # Fleet Indexing Adapter
    fleet_adapter = AWSIoTFleetIndexingAdapter(cfg)
    assert isinstance(fleet_adapter, CloudFleetIndexingInterface)
    assert fleet_adapter.is_enabled is False
    dev = FleetDeviceRecord(machine_id="CNC-001", machine_type="CNC", protocol="OPC_UA", connectivity=ConnectivityState.ONLINE)
    assert fleet_adapter.index_thing(dev) is True
    assert fleet_adapter.search_things("protocol:OPC_UA") == []
