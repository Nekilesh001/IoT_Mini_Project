"""
Wokwi MicroPython Firmware for Raspberry Pi Pico W + DHT22 + LED.
Device ID: IOT-SENSOR-001
Plant: PLANT_01, Line: LINE_A

Features:
- Wi-Fi connection with auto-retry
- NTP UTC time synchronization
- DHT22 temperature & humidity readings
- Local hysteresis control (LED ON if temp >= 30°C, OFF if temp <= 28°C)
- MQTT publish to broker.hivemq.com (QoS 1)
- Offline telemetry RAM buffering with auto-flush on reconnect
- Monotonically increasing sequence counter
- Subscribes to remote MQTT command topic
"""

import time
import json
import machine
import network
import dht
import ntptime
from umqtt.simple import MQTTClient

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
DEVICE_ID = "IOT-SENSOR-001"
DEVICE_TYPE = "ENVIRONMENT_SENSOR"
PLANT_ID = "PLANT_01"
LINE_ID = "LINE_A"
FIRMWARE_VERSION = "0.1.0"

# HiveMQ Public MQTT Broker
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_CLIENT_ID = f"wokwi-pico-{DEVICE_ID}"
MQTT_TELEMETRY_TOPIC = f"iot/plant/{PLANT_ID}/line/{LINE_ID}/device/{DEVICE_ID}/telemetry"
MQTT_COMMAND_TOPIC = f"iot/plant/{PLANT_ID}/line/{LINE_ID}/device/{DEVICE_ID}/commands"

# Wi-Fi Configuration (Wokwi uses 'Wokwi-GUEST')
WIFI_SSID = "Wokwi-GUEST"
WIFI_PASSWORD = ""

# Hardware Pins
DHT_PIN = 15
LED_PIN = 0  # External LED on GP0 (or machine.Pin("LED") on physical Pico W)

# Control & Thresholds
ALERT_THRESHOLD_C = 30.0
NORMAL_THRESHOLD_C = 28.0
CONTROL_MODE = "AUTO"  # "AUTO" or "MANUAL"

# Timing
POLL_INTERVAL_SECONDS = 2
MAX_OFFLINE_BUFFER_SIZE = 50

# ---------------------------------------------------------
# HARDWARE INITIALIZATION
# ---------------------------------------------------------
try:
    led = machine.Pin(LED_PIN, machine.Pin.OUT)
    led.value(0)
except Exception:
    led = machine.Pin("LED", machine.Pin.OUT)
    led.value(0)

sensor = dht.DHT22(machine.Pin(DHT_PIN))

# ---------------------------------------------------------
# STATE VARIABLES
# ---------------------------------------------------------
sequence_counter = 0
led_state = "OFF"
offline_buffer = []
mqtt_client = None
ntp_synced = False


def connect_wifi():
    """Connect to Wi-Fi network with retry."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print(f"[WiFi] Connecting to '{WIFI_SSID}'...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        retries = 0
        while not wlan.isconnected() and retries < 15:
            time.sleep(0.5)
            retries += 1
            print(".", end="")
        print()

    if wlan.isconnected():
        print(f"[WiFi] Connected! IP: {wlan.ifconfig()[0]}")
        return True
    else:
        print("[WiFi] Failed to connect.")
        return False


def sync_ntp():
    """Synchronize RTC with NTP server."""
    global ntp_synced
    try:
        ntptime.settime()
        ntp_synced = True
        print("[NTP] UTC time synchronized successfully.")
    except Exception as e:
        print(f"[NTP] NTP sync failed: {e}")
        ntp_synced = False


def get_iso_timestamp():
    """Generate ISO-8601 UTC timestamp string."""
    t = time.gmtime()
    # Format: YYYY-MM-DDTHH:MM:SSZ
    return f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"


def on_mqtt_command(topic, msg):
    """Handle incoming command messages from MQTT."""
    global led_state, CONTROL_MODE, ALERT_THRESHOLD_C, NORMAL_THRESHOLD_C
    try:
        data = json.loads(msg.decode())
        print(f"[CMD] Received command: {data}")
        
        cmd_type = data.get("command")
        if cmd_type == "SET_LED":
            target = str(data.get("state", "OFF")).upper()
            if target == "ON":
                led.value(1)
                led_state = "ON"
            else:
                led.value(0)
                led_state = "OFF"
            CONTROL_MODE = "MANUAL"
            print(f"[CMD] LED set to {led_state} (Manual Mode)")

        elif cmd_type == "SET_MODE":
            CONTROL_MODE = str(data.get("mode", "AUTO")).upper()
            print(f"[CMD] Control mode set to {CONTROL_MODE}")

        elif cmd_type == "SET_THRESHOLDS":
            if "alertThresholdC" in data:
                ALERT_THRESHOLD_C = float(data["alertThresholdC"])
            if "normalThresholdC" in data:
                NORMAL_THRESHOLD_C = float(data["normalThresholdC"])
            print(f"[CMD] Updated thresholds: Alert={ALERT_THRESHOLD_C}°C, Normal={NORMAL_THRESHOLD_C}°C")

    except Exception as e:
        print(f"[CMD] Error processing command: {e}")


def connect_mqtt():
    """Connect to HiveMQ broker and subscribe to command topic."""
    global mqtt_client
    try:
        print(f"[MQTT] Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
        mqtt_client = MQTTClient(
            client_id=MQTT_CLIENT_ID,
            server=MQTT_BROKER,
            port=MQTT_PORT,
            keepalive=60,
        )
        mqtt_client.set_callback(on_mqtt_command)
        mqtt_client.connect()
        mqtt_client.subscribe(MQTT_COMMAND_TOPIC)
        print(f"[MQTT] Connected and subscribed to '{MQTT_COMMAND_TOPIC}'")
        return True
    except Exception as e:
        print(f"[MQTT] Connection failed: {e}")
        mqtt_client = None
        return False


def flush_offline_buffer():
    """Flush cached telemetry messages to MQTT broker."""
    global offline_buffer, mqtt_client
    if not offline_buffer or not mqtt_client:
        return

    print(f"[Buffer] Flushing {len(offline_buffer)} cached messages to MQTT...")
    failed = []
    for item in offline_buffer:
        try:
            payload_str = json.dumps(item)
            mqtt_client.publish(MQTT_TELEMETRY_TOPIC, payload_str)
        except Exception:
            failed.append(item)

    offline_buffer = failed
    if not offline_buffer:
        print("[Buffer] All cached telemetry sent successfully.")


def build_telemetry_payload(temp_c, hum_pct):
    """Construct standard Wokwi telemetry payload dictionary."""
    global sequence_counter, led_state, CONTROL_MODE
    sequence_counter += 1

    return {
        "deviceId": DEVICE_ID,
        "deviceType": DEVICE_TYPE,
        "plantId": PLANT_ID,
        "lineId": LINE_ID,
        "eventType": "TELEMETRY",
        "sequence": sequence_counter,
        "timestamp": get_iso_timestamp(),
        "readings": {
            "temperatureC": round(temp_c, 2),
            "humidityPct": round(hum_pct, 2),
        },
        "actuator": {
            "type": "LED",
            "state": led_state,
        },
        "control": {
            "mode": CONTROL_MODE,
            "alertThresholdC": ALERT_THRESHOLD_C,
            "normalThresholdC": NORMAL_THRESHOLD_C,
        },
        "firmwareVersion": FIRMWARE_VERSION,
    }


def main():
    """Main firmware execution loop."""
    global led_state, mqtt_client

    print("=" * 60)
    print(f" WOKWI ENVIRONMENT SENSOR NODE: {DEVICE_ID}")
    print(f" Hardware: Raspberry Pi Pico W + DHT22")
    print(f" Target Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print("=" * 60)

    # Initial Network setup
    if connect_wifi():
        sync_ntp()
        connect_mqtt()

    while True:
        try:
            # 1. Read physical DHT22 sensor
            sensor.measure()
            temp_c = sensor.temperature()
            hum_pct = sensor.humidity()

            # 2. Local Hysteresis Control
            if CONTROL_MODE == "AUTO":
                if temp_c >= ALERT_THRESHOLD_C and led_state == "OFF":
                    led.value(1)
                    led_state = "ON"
                    print(f"[*] Hysteresis Trigger: Temp={temp_c:.1f}°C >= {ALERT_THRESHOLD_C}°C -> LED ON")
                elif temp_c <= NORMAL_THRESHOLD_C and led_state == "ON":
                    led.value(0)
                    led_state = "OFF"
                    print(f"[*] Hysteresis Recovery: Temp={temp_c:.1f}°C <= {NORMAL_THRESHOLD_C}°C -> LED OFF")

            # 3. Build Telemetry Payload
            payload = build_telemetry_payload(temp_c, hum_pct)
            payload_str = json.dumps(payload)

            print(
                f"[Telemetry #{payload['sequence']:04d}] "
                f"Temp: {temp_c:.1f}°C | Humidity: {hum_pct:.1f}% | LED: {led_state}"
            )

            # 4. Check Wi-Fi & MQTT Connectivity
            wlan = network.WLAN(network.STA_IF)
            if not wlan.isconnected():
                connect_wifi()

            if wlan.isconnected() and mqtt_client is None:
                connect_mqtt()

            # 5. Publish to MQTT or Buffer in RAM
            published = False
            if mqtt_client:
                try:
                    # Check for incoming commands
                    mqtt_client.check_msg()
                    # Publish telemetry
                    mqtt_client.publish(MQTT_TELEMETRY_TOPIC, payload_str)
                    published = True
                    # Flush any previously cached offline messages
                    flush_offline_buffer()
                except Exception as pub_err:
                    print(f"[MQTT] Publish failed ({pub_err}). Buffering message.")
                    mqtt_client = None

            if not published:
                if len(offline_buffer) < MAX_OFFLINE_BUFFER_SIZE:
                    offline_buffer.append(payload)
                    print(f"[Buffer] Message #{payload['sequence']} buffered offline ({len(offline_buffer)} items).")
                else:
                    print(f"[Buffer] Buffer full, dropped oldest message.")
                    offline_buffer.pop(0)
                    offline_buffer.append(payload)

        except OSError as e:
            print(f"[DHT22] Failed to read sensor: {e}")
        except Exception as ex:
            print(f"[MainLoop] Unexpected error: {ex}")

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
