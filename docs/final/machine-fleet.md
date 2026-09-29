# 12-Machine Simulated Factory Fleet Specification

The simulation models 12 heterogeneous industrial machines across varying mechanical mechanisms, operating frequencies, and protocol servers.

| Machine ID | Machine Type | Simulated Protocol | Key Observable Physical Sensors | Degradation / Fault Mechanism | Digital Twin / Management Parameters |
|---|---|---|---|---|---|
| **CNC-001** | CNC Machining Center | OPC UA | Spindle RPM, Vibration (3-axis), Spindle Temp, Feed Rate, Power (kW), Coolant Pressure | Tool wear accumulation, bearing thermal expansion | Spindle target RPM, feed rate override, state sync |
| **CNC-002** | CNC Lathe | Modbus TCP | Chuck RPM, Feed Speed, Main Motor Current, Cutting Temp, Vibration RMS | Insert wear, chuck imbalance, belt slippage | Chuck RPM setpoint, coolant toggle, calibration job |
| **ROB-001** | 6-Axis Industrial Robot | OPC UA | Joint Angles (1-6), Joint Temperatures, Motor Torques, End-Effector Payload, Cycle Time | Gearbox backlash, joint motor overheating | Kinematic mode setpoint, speed scaling, restart job |
| **ROB-002** | Spot/Arc Welding Robot | MQTT | Weld Current, Arc Voltage, Tip Temperature, Gas Flow Rate, Wire Feed Speed | Tip degradation, gas flow blockage, arc instability | Weld current target, wire feed speed setpoint |
| **CON-001** | Industrial Conveyor | Modbus TCP | Belt Speed, Motor Current, Belt Tension, Pulley Bearing Temp, Photoeye Jam Sensor | Belt stretch, roller bearing seizure, package jam | Belt target speed, reverse direction, emergency stop |
| **PRS-001** | Industrial Press | Modbus TCP | Press Force (kN), Hydraulic Pressure, Ram Displacement, Oil Temp, Cycle Count | Hydraulic seal leakage, valve clogging, pressure loss | Force limit setpoint, cycle interval, seal check job |
| **IMM-001** | Injection Molding Machine | OPC UA | Barrel Zone Temps (1-4), Clamping Force, Injection Pressure, Mold Temp, Shot Volume | Heater band failure, nozzle blockage, cooling degradation | Zone temperature targets, injection speed setpoint |
| **CMP-001** | Air Compressor | Modbus TCP | Discharge Pressure, Intake Pressure, Oil Temp, Vibration RMS, Motor Power | Air filter clogging, valve leakage, oil degradation | Target cutoff pressure, unload timer setpoint |
| **PMP-001** | Industrial Pump | MQTT | Flow Rate, Inlet/Outlet Pressure, Motor Temp, Vibration RMS, Cavitation Index | Impeller cavitation, mechanical seal wear, bearing failure | Target RPM, discharge valve position setpoint |
| **VIS-001** | Vision Inspection Station | OPC UA | Camera Frame Rate, Exposure Time, Lighting Lux, Processing Latency, Defect Rate | Illumination degradation, lens contamination, latency spike | Exposure time, frame rate setpoint, re-zero calibration |
| **AGV-001** | Autonomous Mobile Robot | MQTT | Battery SoC %, Wheel Velocities, Motor Currents, LiDAR Range, Navigation Error | Battery capacity degradation, wheel traction loss | Speed limit, navigation goal, battery recharge job |
| **CHL-001** | Industrial Chiller | Modbus TCP | Supply/Return Water Temp, Compressor Power, Refrigerant Pressure, Flow Rate | Condenser fouling, refrigerant leak, compressor wear | Target setpoint temp, flow rate minimum |

*Note: Protocol assignments (Modbus TCP, OPC UA, MQTT) represent simulation architecture design choices to validate multi-protocol interoperability.*
