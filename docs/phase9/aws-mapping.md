# Future AWS IoT Mapping & Adapter Architecture

## 1. Mapping Overview

| Local Subsystem | Local Implementation | Future AWS IoT Service | Adapter Scaffold Module |
| :--- | :--- | :--- | :--- |
| **Digital Twin / State** | `DeviceShadowState` | AWS IoT Device Shadow | `cloud/aws/device_shadow.py` |
| **Fleet Inventory** | `LocalFleetBackend` | AWS IoT Fleet Indexing / Registry | `cloud/aws/fleet_indexing.py` |
| **Rollouts & Jobs** | `LocalJobBackend` | AWS IoT Jobs | `cloud/aws/jobs.py` |
| **Message Broker** | Local MQTT Event Bus | AWS IoT Core MQTT | `cloud/aws/iot_core.py` |

## 2. Scaffold Safety & Boundaries

- **`AWS_ENABLED=false`**: All cloud adapters check `AWSConfig.enabled` and operate in safe local fallback mode when false.
- **Zero Cloud Credentials**: No AWS secret keys, access keys, or STS tokens are required or loaded.
- **Abstract Cloud Interfaces**: Application code strictly references `CloudDeviceStateInterface`, `CloudJobsInterface`, and `CloudFleetIndexingInterface`.
