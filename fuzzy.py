"""
fuzzy.py — Fuzzy Logic Inference Engine
=========================================
Estimates the shelf life of onions (in months) from:
  • Temperature  (°C)
  • Humidity     (%)
  • Gas concentration (ppm — CO2 / Ammonia via MQ135)

Membership functions and fuzzy rules are derived directly from:
  "Implementation of IoT and Fuzzy Logic Driven Real-Time Smart Storage
   Monitoring System" — IEEE Conference, IIT Mandi
  Authors: Rahul Prasad, Suman Raj, Akash Machireddy, Harshith Shahshni

Membership Ranges (from the paper):
──────────────────────────────────────────────────────────────
  Temperature:
    Good    → 0–10 °C   (cold storage, minimal losses)
    Poor    → 20–24 °C  (mold/fungal growth zone)
    Average → 27–34 °C  (ambient, acceptable)

  Humidity:
    Good    → 64–74 %
    Average → 45–53 %
    Poor    → 85–95 %

  Gas (CO2 + Ammonia ppm):
    Good    → 10–150 ppm
    Average → 180–500 ppm
    Poor    → 550–900 ppm

  Shelf Life Output (months):
    Good    → 4–8 months
    Average → 2–3 months
    Poor    → 0–1 months

Dependencies: numpy, scikit-fuzzy
Install: pip install scikit-fuzzy numpy
"""

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


# ═══════════════════════════════════════════════════════════════════════════════
#  1. UNIVERSE OF DISCOURSE
# ═══════════════════════════════════════════════════════════════════════════════

temperature = ctrl.Antecedent(np.arange(-10, 51, 1), "temperature")  # °C
humidity    = ctrl.Antecedent(np.arange(40, 111, 1), "humidity")     # %
gas         = ctrl.Antecedent(np.arange(0, 901, 1),  "gas")          # ppm
shelf_life  = ctrl.Consequent(np.arange(0, 9, 0.1),  "shelf_life")   # months


# ═══════════════════════════════════════════════════════════════════════════════
#  2. MEMBERSHIP FUNCTIONS  (trapezoidal — as depicted in paper Figs 3.35–3.38)
# ═══════════════════════════════════════════════════════════════════════════════

# — Temperature —
# Good  : blue  line  → 0–10 °C  (cold storage)
# Poor  : green line  → 20–24 °C (mold/fungal zone)
# Average: yellow line → 27–34 °C (ambient acceptable)
temperature["good"]    = fuzz.trapmf(temperature.universe, [-10, 0,  5,  10])
temperature["poor"]    = fuzz.trapmf(temperature.universe, [16,  20, 24, 28])
temperature["average"] = fuzz.trapmf(temperature.universe, [25,  27, 34, 40])

# — Humidity —
# Good    → 64–74 %
# Average → 45–53 %
# Poor    → 85–95 %
humidity["good"]    = fuzz.trapmf(humidity.universe, [60,  64, 74, 78])
humidity["average"] = fuzz.trapmf(humidity.universe, [42,  45, 53, 58])
humidity["poor"]    = fuzz.trapmf(humidity.universe, [80,  85, 95, 100])

# — Gas concentration (ppm) —
# Good    → 10–150 ppm
# Average → 180–500 ppm
# Poor    → 550–900 ppm
gas["good"]    = fuzz.trapmf(gas.universe, [0,   10,  150, 170])
gas["average"] = fuzz.trapmf(gas.universe, [160, 180, 500, 540])
gas["poor"]    = fuzz.trapmf(gas.universe, [530, 550, 900, 900])

# — Shelf Life output (months) —
# Good    → 4–8 months
# Average → 2–3 months
# Poor    → 0–1 months
shelf_life["good"]    = fuzz.trapmf(shelf_life.universe, [3.5, 4, 8,  8])
shelf_life["average"] = fuzz.trapmf(shelf_life.universe, [1.5, 2, 3,  3.5])
shelf_life["poor"]    = fuzz.trapmf(shelf_life.universe, [0,   0, 1,  1.5])


# ═══════════════════════════════════════════════════════════════════════════════
#  3. FUZZY RULES  (from Table 3.1 in the paper)
# ═══════════════════════════════════════════════════════════════════════════════
#
#  GAS & HUM \ TEMP   | Temp-P (Poor) | Temp-A (Avg) | Temp-G (Good)
#  ─────────────────────────────────────────────────────────────────────
#  Gas-P & Hum-P      |   Poor        |   Poor        |  Average
#  Gas-P & Hum-A      |   Poor        |   Poor        |  Average
#  Gas-P & Hum-G      |   Poor        |   Poor        |  Average
#  Gas-A & Hum-P      |   Poor        |   Poor        |  Good
#  Gas-A & Hum-A      |   Average     |   Average     |  Good
#  Gas-A & Hum-G      |   Average     |   Good        |  Good
#  Gas-G & Hum-P      |   Poor        |   Average     |  Good
#  Gas-G & Hum-A      |   Average     |   Good        |  Good
#  Gas-G & Hum-G      |   Average     |   Good        |  Good

rules = [
    # Gas-P rows
    ctrl.Rule(gas["poor"]    & humidity["poor"]    & temperature["poor"],    shelf_life["poor"]),
    ctrl.Rule(gas["poor"]    & humidity["poor"]    & temperature["average"], shelf_life["poor"]),
    ctrl.Rule(gas["poor"]    & humidity["poor"]    & temperature["good"],    shelf_life["average"]),
    ctrl.Rule(gas["poor"]    & humidity["average"] & temperature["poor"],    shelf_life["poor"]),
    ctrl.Rule(gas["poor"]    & humidity["average"] & temperature["average"], shelf_life["poor"]),
    ctrl.Rule(gas["poor"]    & humidity["average"] & temperature["good"],    shelf_life["average"]),
    ctrl.Rule(gas["poor"]    & humidity["good"]    & temperature["poor"],    shelf_life["poor"]),
    ctrl.Rule(gas["poor"]    & humidity["good"]    & temperature["average"], shelf_life["poor"]),
    ctrl.Rule(gas["poor"]    & humidity["good"]    & temperature["good"],    shelf_life["average"]),
    # Gas-A rows
    ctrl.Rule(gas["average"] & humidity["poor"]    & temperature["poor"],    shelf_life["poor"]),
    ctrl.Rule(gas["average"] & humidity["poor"]    & temperature["average"], shelf_life["poor"]),
    ctrl.Rule(gas["average"] & humidity["poor"]    & temperature["good"],    shelf_life["good"]),
    ctrl.Rule(gas["average"] & humidity["average"] & temperature["poor"],    shelf_life["average"]),
    ctrl.Rule(gas["average"] & humidity["average"] & temperature["average"], shelf_life["average"]),
    ctrl.Rule(gas["average"] & humidity["average"] & temperature["good"],    shelf_life["good"]),
    ctrl.Rule(gas["average"] & humidity["good"]    & temperature["poor"],    shelf_life["average"]),
    ctrl.Rule(gas["average"] & humidity["good"]    & temperature["average"], shelf_life["good"]),
    ctrl.Rule(gas["average"] & humidity["good"]    & temperature["good"],    shelf_life["good"]),
    # Gas-G rows
    ctrl.Rule(gas["good"]    & humidity["poor"]    & temperature["poor"],    shelf_life["poor"]),
    ctrl.Rule(gas["good"]    & humidity["poor"]    & temperature["average"], shelf_life["average"]),
    ctrl.Rule(gas["good"]    & humidity["poor"]    & temperature["good"],    shelf_life["good"]),
    ctrl.Rule(gas["good"]    & humidity["average"] & temperature["poor"],    shelf_life["average"]),
    ctrl.Rule(gas["good"]    & humidity["average"] & temperature["average"], shelf_life["good"]),
    ctrl.Rule(gas["good"]    & humidity["average"] & temperature["good"],    shelf_life["good"]),
    ctrl.Rule(gas["good"]    & humidity["good"]    & temperature["poor"],    shelf_life["average"]),
    ctrl.Rule(gas["good"]    & humidity["good"]    & temperature["average"], shelf_life["good"]),
    ctrl.Rule(gas["good"]    & humidity["good"]    & temperature["good"],    shelf_life["good"]),
]


# ═══════════════════════════════════════════════════════════════════════════════
#  4. CONTROL SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

_storage_ctrl = ctrl.ControlSystem(rules)
_storage_sim  = ctrl.ControlSystemSimulation(_storage_ctrl)


# ═══════════════════════════════════════════════════════════════════════════════
#  5. PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def get_shelf_life(temperature_c: float,
                   humidity_pct: float,
                   gas_ppm: float) -> float:
    """
    Run fuzzy inference and return estimated shelf life in months.

    Parameters
    ----------
    temperature_c : float — storage temperature in °C
    humidity_pct  : float — relative humidity in %
    gas_ppm       : float — gas concentration in ppm (CO2 + Ammonia, MQ135)

    Returns
    -------
    float — estimated shelf life in months (0.0 – 8.0)
    """
    # Clip inputs to universe bounds
    t = float(np.clip(temperature_c, -10, 50))
    h = float(np.clip(humidity_pct,   40, 110))
    g = float(np.clip(gas_ppm,         0, 900))

    _storage_sim.input["temperature"] = t
    _storage_sim.input["humidity"]    = h
    _storage_sim.input["gas"]         = g
    _storage_sim.compute()

    return round(float(_storage_sim.output["shelf_life"]), 2)


def classify(shelf_months: float) -> str:
    """Return 'Good', 'Average', or 'Poor' label from shelf life value."""
    if shelf_months >= 4:
        return "Good"
    elif shelf_months >= 2:
        return "Average"
    return "Poor"


# ─── Quick Test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cases = [
        (5,   70, 80,  "Cold storage (optimal)"),
        (30,  67, 120, "Ambient, good conditions"),
        (22,  88, 400, "Mold-zone humidity+gas"),
        (22,  90, 700, "High gas, poor humidity"),
    ]
    print(f"\n{'='*65}")
    print(f"  Fuzzy Shelf Life Prediction")
    print(f"{'='*65}")
    for t, h, g, label in cases:
        sl = get_shelf_life(t, h, g)
        print(f"  {label}")
        print(f"    T={t}°C  H={h}%  Gas={g}ppm → {sl} months ({classify(sl)})\n")
    print("="*65)
