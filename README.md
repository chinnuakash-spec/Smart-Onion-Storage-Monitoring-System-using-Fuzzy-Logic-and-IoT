# 🌱 E-Smart Storage — IoT & Fuzzy Logic Driven Onion Storage Monitoring System

> **IEEE Conference Publication — IIT Mandi**  
> *"Implementation of IoT and Fuzzy Logic Driven Real-Time Smart Storage Monitoring System"*  
> **Authors:** Rahul Prasad · Suman Raj · Akash Machireddy · Harshith Shahshni  
> **DOI:** [10.1109/10724998](https://ieeexplore.ieee.org/document/10724998/)

---

## 📌 Overview

India is the world's second-largest onion producer, yet 30–35% of harvested onions are lost due to improper storage. This project implements a **real-time IoT-based monitoring and alert system** for onion storage facilities that:

- Continuously measures **temperature**, **humidity**, and **gas concentration (CO₂ + Ammonia)** via DHT11 and MQ135 sensors on a Raspberry Pi 3 B+
- Applies a **Mamdani-type fuzzy inference system** to predict the **estimated shelf life** in months
- Sends automated **Email (Gmail) and SMS (Twilio) alerts** when shelf life drops below 1 month
- Provides a **real-time web dashboard** (Django + HTML/CSS) accessible remotely via VNC or browser

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────┐
│           ONION STORAGE UNIT                 │
│                                              │
│   DHT11 ──┐                                  │
│           ├──► Raspberry Pi 3 B+ ──► Django  │
│  MQ135 ───┤       (GPIO / ADC)     (SQLite)  │
│  (via ADC)┘                                  │
└──────────────────────────────────────────────┘
                        │
           ┌────────────┼───────────────┐
           ▼            ▼               ▼
       fuzzy.py      Dashboard       notify.py
   (shelf life)    (HTML/CSS)    (Email + SMS)
```

### Dependency Chart (from paper Fig 3.39)

```
               Django Framework
              (GET + POST API, SQLite)
                       │
     ┌─────────────────┼───────────────────┐
     ▼                 ▼                   ▼
 fuzzy.py          sensor.py           notify.py         Html/CSS
 Estimates         1. Reads sensors    1. Fetches data   1. Fetch via GET API
 shelf life        2. Invokes fuzzy    2. Sends mail/SMS 2. Displays on website
 from T, H, Gas    3. POSTs to DB
```

---

## 🔬 Fuzzy Logic Design

### Input Variables & Membership Functions

| Variable | Good | Average | Poor |
|---|---|---|---|
| Temperature | 0–10 °C (cold storage) | 27–34 °C (ambient) | 20–24 °C (mold zone) |
| Humidity | 64–74 % | 45–53 % | 85–95 % |
| Gas (MQ135 ppm) | 10–150 ppm | 180–500 ppm | 550–900 ppm |

### Output Variable

| Shelf Life | Range |
|---|---|
| Good | 4–8 months |
| Average | 2–3 months |
| Poor | 0–1 months |

### Fuzzy Rules (Table 3.1)

| Gas & Humidity | Temp Poor | Temp Average | Temp Good |
|---|---|---|---|
| Gas-P & Hum-P | Poor | Poor | Average |
| Gas-P & Hum-A | Poor | Poor | Average |
| Gas-P & Hum-G | Poor | Poor | Average |
| Gas-A & Hum-P | Poor | Poor | Good |
| Gas-A & Hum-A | Average | Average | Good |
| Gas-A & Hum-G | Average | Good | Good |
| Gas-G & Hum-P | Poor | Average | Good |
| Gas-G & Hum-A | Average | Good | Good |
| Gas-G & Hum-G | Average | Good | Good |

---

## 🛠️ Hardware Components

| Component | Purpose |
|---|---|
| Raspberry Pi 3 B+ | Main processing unit — Wi-Fi, GPIO, Django server |
| DHT11 Sensor | Temperature (0–50 °C) & Humidity (20–90%) |
| MQ135 Gas Sensor | CO₂ and Ammonia detection |
| ADC Converter | Converts MQ135 analog signal to digital for Raspberry Pi |
| Micro SD Card (≥16 GB) | Raspberry Pi OS storage |
| Jumper Wires + Breadboard | Circuit connections |
| 5V Power Supply | System power |

### Wiring

```
DHT11  VCC   → 3.3V  (Pin 1)
DHT11  DATA  → GPIO4 (Pin 7)
DHT11  GND   → GND

MQ135  VCC   → 5V    (Pin 2)
MQ135  DOUT  → GPIO21 (Pin 40)   ← digital detection
MQ135  AOUT  → ADC → SPI (GPIO9/10/11/8) ← for analog PPM
MQ135  GND   → GND
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/smart-storage-iot.git
cd smart-storage-iot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up the Django Server

```bash
# Run migrations to create SQLite database
python manage.py makemigrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Start the server
python manage.py runserver 0.0.0.0:8000
```

Dashboard: **http://localhost:8000**  
Admin panel: **http://localhost:8000/admin**

### 4. Set Up Raspberry Pi

**Install Raspberry Pi OS** using Raspberry Pi Imager, then:

```bash
# Install sensor libraries
pip install Adafruit_DHT
# RPi.GPIO is pre-installed on Raspberry Pi OS

# Install fuzzy logic
pip install scikit-fuzzy numpy requests
```

**Configure credentials:**
```bash
cp .env.example .env
# Edit .env with your Gmail and Twilio credentials
```

**Run sensor + notification scripts:**
```bash
# Terminal 1 — Read sensors and POST to Django
python hardware/sensor.py

# Terminal 2 — Poll API and send alerts
python hardware/notify.py
```

---

## 📁 Project Structure

```
smart-storage-iot/
├── hardware/
│   ├── sensor.py       # Reads DHT11 + MQ135, invokes fuzzy, POSTs to Django
│   ├── fuzzy.py        # Fuzzy inference engine (shelf life in months)
│   └── notify.py       # Polls GET API, sends Gmail + Twilio SMS alerts
│
├── smartstorage/       # Django app
│   ├── models.py       # SensorData model (SQLite)
│   ├── views.py        # GET /data/, POST /store/, home page
│   ├── urls.py         # URL routing
│   └── templates/
│       └── smartstorage/
│           ├── index.html   # E-Smart Storage homepage
│           └── device.html  # Per-device reading page
│
├── esmartstorage/      # Django project config
│   ├── settings.py
│   └── urls.py
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 📡 API Reference

| Method | URL | Description |
|---|---|---|
| `GET` | `/` | Dashboard homepage |
| `GET` | `/data/` | Latest reading as JSON |
| `GET` | `/data/?device=Device+1` | Reading for specific device |
| `POST` | `/store/` | Ingest data from Raspberry Pi |
| `GET` | `/device/<id>/` | Device-specific info page |
| `GET` | `/admin/` | Django admin panel |

**POST `/store/` payload:**
```json
{
  "device_id":  "Device 1",
  "temperature": 28.0,
  "humidity":    59.0,
  "gas_ppm":     317.0,
  "shelf_life":  4.32
}
```

---

## 📊 Sample Results (from paper Fig 4.2)

| Device | Temp (°C) | Humidity (%) | Gas (ppm) | Estimated Shelf Life |
|---|---|---|---|---|
| Device 1 | 28.0 | 59.0 | 317.0 | **4.32 months** (Good) |

---

## 🔔 Alert System

Alerts trigger via **Email and SMS** when estimated shelf life **< 1 month**.

- Email via **Gmail SMTP** (`smtplib`, port 587 with TLS)
- SMS via **Twilio** Python SDK

Example alert message:
> *"Dear User, Estimated shelf-life of stored onion is only 23 days. Thus it requires immediate actions. Thanks."*

---

## 🧪 Testing APIs with Postman

**GET request** — Verify latest data:
```
GET http://raspberrypi.local:8000/data/
```

**POST request** — Simulate sensor data:
```
POST http://raspberrypi.local:8000/store/
Content-Type: application/json

{ "device_id": "Device 1", "temperature": 28, "humidity": 59, "gas_ppm": 317, "shelf_life": 4.32 }
```

---

## 📄 Publication

> **"Implementation of IoT and Fuzzy Logic Driven Real-Time Smart Storage Monitoring System"**  
> Rahul Prasad, Suman Raj, Akash Machireddy, Harshith Shahshni  
> *IEEE Conference — IIT Mandi, 2024*  
> DOI: [10.1109/10724998](https://ieeexplore.ieee.org/document/10724998/)

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.
