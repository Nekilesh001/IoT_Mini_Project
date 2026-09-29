# Phase 9 Architecture — Local Device State, Fleet & Job Management

## 1. Overview & Architectural Principles

Phase 9 implements a **Local-First Device Management System** with clean abstract adapter interfaces designed for seamless future AWS IoT Core and hybrid cloud integration.

```mermaid
flowchart TD
    subgraph Management ["Device Management Service (Facade)"]
        Shadow[DeviceShadowManager]
        Fleet[FleetManager]
        Jobs[JobManager]
        Cmd[CommandHandler]
    end

    subgraph Backends ["Abstract Backend Interfaces"]
        DSB[DeviceStateBackend]
        FB[FleetBackend]
        JB[JobBackend]
        AB[AuditBackend]
    end

    subgraph Storage ["Local SQLite / PostgreSQL Persistence"]
        T_Shadow[(device_shadow)]
        T_Fleet[(fleet_devices)]
        T_Jobs[(management_jobs)]
        T_Attempts[(job_attempts)]
        T_Audit[(management_audit)]
    end

    subgraph CloudScaffold ["Cloud Scaffolding (Disabled by Default)"]
        AWS_Shadow[AWSIoTDeviceShadowAdapter]
        AWS_Jobs[AWSIoTJobsAdapter]
        AWS_Fleet[AWSIoTFleetIndexingAdapter]
        AWS_Core[AWSIoTCoreAdapter]
    end

    Shadow --> DSB
    Fleet --> FB
    Jobs --> JB
    Cmd --> Shadow
    Cmd --> Jobs

    DSB --> T_Shadow
    FB --> T_Fleet
    JB --> T_Jobs
    JB --> T_Attempts
    AB --> T_Audit

    DSB -.-> AWS_Shadow
    FB -.-> AWS_Fleet
    JB -.-> AWS_Jobs
```

## 2. Core Separation Principles

1. **Protocol & Engine Agnosticism**: Downstream machine simulation and ingestion operate independently of configuration and management job workflows.
2. **Local-First Independence**: All Device Shadow state, fleet metadata indexing, job rollouts, retries, and audit history function 100% locally on SQLite and PostgreSQL.
3. **No Direct Cloud Coupling**: Domain entities and application services never import `boto3` or cloud client SDKs directly.
4. **Optimistic Concurrency & Audit Trails**: Every state change increments version tags and emits structured audit logs.
