# Phase 7: ML Dataset Report

## 1. Dataset Overview
- **Dataset ID**: `DS-SIM-42-3600`
- **Source**: Deterministic Factory Simulator
- **Total Samples**: `3,600`
- **Total Machines**: `12` (AGV-001, CHL-001, CMP-001, CNC-001, CNC-002, CON-001, IMM-001, PMP-001, PRS-001, ROB-001, ROB-002, VIS-001)
- **Temporal Range**: `2026-01-01 08:00:01+00:00` to `2026-01-01 08:05:00+00:00`

## 2. Chronological Split Distribution
- **Training Set (60%)**: `2,160` samples
- **Validation Set (20%)**: `720` samples
- **Test Set (20%)**: `720` samples
- **Anomaly Prevalence**: `8.42%`

## 3. Feature Matrix
- **Engineered Features**: `1019` features
- **Rolling Windows**: `[5, 15, 30]` samples
- **Ground-Truth Target Leakage Status**: **ZERO LEAKAGE DETECTED** (Validated against whitelist)
