"""
views.py — Django Views
========================
GET  /         → home page (renders index.html with latest reading)
GET  /data/    → returns latest SensorData as JSON (used by notify.py & frontend)
POST /store/   → receives sensor data from Raspberry Pi (sensor.py), saves to DB
"""

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from .models import SensorData


# ─── Home Page ─────────────────────────────────────────────────────────────────

def home(request):
    """Render the main dashboard with the 4 storage device cards."""
    latest = SensorData.objects.first()   # most recent reading (ordered by -timestamp)
    all_readings = SensorData.objects.all()[:50]
    return render(request, "smartstorage/index.html", {
        "latest":       latest,
        "all_readings": all_readings,
    })


# ─── GET: Real-time data API ───────────────────────────────────────────────────

@require_http_methods(["GET"])
def get_sensor_data(request):
    """
    Returns the most recent sensor reading as JSON.
    Used by notify.py and the frontend dashboard charts.
    """
    device_id = request.GET.get("device", None)
    qs = SensorData.objects.all()
    if device_id:
        qs = qs.filter(device_id=device_id)
    latest = qs.first()

    if not latest:
        return JsonResponse({"message": "No data yet"}, status=204)

    return JsonResponse({
        "device_id":   latest.device_id,
        "temperature": latest.temperature,
        "humidity":    latest.humidity,
        "gas_ppm":     latest.gas_ppm,
        "shelf_life":  latest.shelf_life,
        "condition":   latest.condition,
        "timestamp":   latest.timestamp.isoformat(),
    })


# ─── POST: Ingest sensor data from Raspberry Pi ───────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
def store_sensor_data(request):
    """
    Receives JSON payload from sensor.py running on the Raspberry Pi.
    Validates and saves to SQLite via Django ORM.

    Expected payload:
    {
        "device_id":  "Device 1",
        "temperature": 28.0,
        "humidity":    59.0,
        "gas_ppm":     317.0,
        "shelf_life":  4.32
    }
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    required = ["temperature", "humidity", "gas_ppm", "shelf_life"]
    missing  = [f for f in required if f not in data]
    if missing:
        return JsonResponse({"error": f"Missing fields: {missing}"}, status=422)

    try:
        record = SensorData.objects.create(
            device_id   = data.get("device_id", "Device 1"),
            temperature = float(data["temperature"]),
            humidity    = float(data["humidity"]),
            gas_ppm     = float(data["gas_ppm"]),
            shelf_life  = float(data["shelf_life"]),
        )
    except (ValueError, TypeError) as e:
        return JsonResponse({"error": str(e)}, status=422)

    return JsonResponse({
        "status":    "ok",
        "id":        record.id,
        "condition": record.condition,
    }, status=200)


# ─── Device-specific page ──────────────────────────────────────────────────────

def device_view(request, device_id):
    """Show latest reading for a specific storage device (Device 1–4)."""
    readings = SensorData.objects.filter(device_id=device_id)[:20]
    latest   = readings.first()
    return render(request, "smartstorage/device.html", {
        "device_id": device_id,
        "latest":    latest,
        "readings":  readings,
    })
