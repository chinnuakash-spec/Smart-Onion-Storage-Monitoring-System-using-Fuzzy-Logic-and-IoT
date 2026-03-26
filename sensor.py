"""
sensor.py — Smart Storage Monitoring System
=============================================
Reads real-time data from:
  • DHT11  — Temperature & Humidity (GPIO pin 4)
  • MQ135  — CO2 & Ammonia gas concentration (via ADC, GPIO pin 21 digital)

Then:
  1. Passes readings to fuzzy.py to estimate shelf life
  2. POSTs the data (including shelf life) to the Django API for DB storage

Hardware: Raspberry Pi 3 B+
Run: python sensor.py

Authors: Rahul Prasad, Suman Raj, Akash Machireddy, Harshith Shahshni
IEEE Conference — IIT Mandi
"""

import time
import requests
import Adafruit_DHT
import RPi.GPIO as GPIO
from fuzzy import get_shelf_life

# ─── CONFIG ────────────────────────────────────────────────────────────────────
DHT_SENSOR  = Adafruit_DHT.DHT11
DHT_PIN     = 4           # GPIO4 → DHT11 data pin
GAS_PIN     = 21          # GPIO21 → MQ135 digital output

DEVICE_ID   = "Device 1"
SERVER_URL  = "http://127.0.0.1:8000/store/"  # Django POST endpoint
POLL_EVERY  = 30          # seconds between readings

# ─── GPIO SETUP ────────────────────────────────────────────────────────────────
GPIO.setmode(GPIO.BCM)
GPIO.setup(GAS_PIN, GPIO.IN)


def read_dht11():
    """
    Read temperature (°C) and humidity (%) from DHT11.
    Returns (temperature, humidity) or (None, None) on failure.
    """
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    if humidity is not None and temperature is not None:
        return round(temperature, 1), round(humidity, 1)
    return None, None


def read_gas_ppm():
    """
    Read gas concentration from MQ135.
    Digital pin: HIGH = clean air (True), LOW = gas detected (False).
    We also approximate a CO2+Ammonia ppm from digital state.

    Note: For analog PPM, connect AOUT to an ADC (e.g. MCP3008 via SPI).
    Here we use the digital output for a threshold-based detection.
    Returns approximate ppm value.
    """
    gas_detected = not GPIO.input(GAS_PIN)   # LOW = gas present
    if gas_detected:
        # Gas detected — return an elevated representative value
        return 450.0   # ppm (can be refined with ADC for true analog reading)
    else:
        # Clean air — baseline CO2
        return 150.0   # ppm


def post_to_server(payload: dict) -> bool:
    """Send sensor data + shelf life to Django REST endpoint."""
    try:
        response = requests.post(SERVER_URL, json=payload, timeout=10)
        print(f"[Server] {response.status_code} — {response.text[:80]}")
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"[Server] POST failed: {e}")
        return False


def main():
    print("=" * 50)
    print("  E-Smart Storage — Sensor Monitor")
    print("=" * 50)

    while True:
        temperature, humidity = read_dht11()

        if temperature is None:
            print("[DHT11] Read failed, retrying next cycle...")
            time.sleep(POLL_EVERY)
            continue

        gas_ppm = read_gas_ppm()

        # Fuzzy logic — estimate shelf life in months
        shelf_life_months = get_shelf_life(temperature, humidity, gas_ppm)

        print(
            f"[Sensor] Temp={temperature}°C | "
            f"Humidity={humidity}% | "
            f"Gas={gas_ppm}ppm | "
            f"Shelf Life≈{shelf_life_months:.2f} months"
        )

        payload = {
            "device_id":    DEVICE_ID,
            "temperature":  temperature,
            "humidity":     humidity,
            "gas_ppm":      gas_ppm,
            "shelf_life":   round(shelf_life_months, 2),
        }

        post_to_server(payload)
        time.sleep(POLL_EVERY)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Sensor] Stopped by user.")
        GPIO.cleanup()
