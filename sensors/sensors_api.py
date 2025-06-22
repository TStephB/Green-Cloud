from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import Adafruit_DHT
import board
import busio
import adafruit_bme280
import spidev
import math
import time
from pydantic import BaseModel
import uvicorn

# Configuration des capteurs
DHT22_PIN = 23
BME280_ADDRESS = 0x76
SCT013_CHANNEL = 0
API_PORT = 8000

# Initialisation des capteurs
try:
    # DHT22
    dht_sensor = Adafruit_DHT.DHT22
    
    # BME280
    i2c = busio.I2C(board.SCL, board.SDA)
    bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=BME280_ADDRESS)
    
    # SCT013 (via MCP3008)
    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 1350000
except Exception as e:
    print(f"ERREUR INITIALISATION CAPTEURS: {str(e)}")
    # Mode simulation si les capteurs ne sont pas disponibles
    SIMULATION_MODE = True
else:
    SIMULATION_MODE = False

app = FastAPI(title="API de Capteurs IoT", version="2.0.0")

# Autoriser les requêtes CORS (pour l'interface web)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SensorData(BaseModel):
    dht22: dict
    bme280: dict
    sct013: dict
    timestamp: str

def read_adc(channel):
    """Lit la valeur analogique d'un canal du MCP3008"""
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((adc[1] & 3) << 8) + adc[2]

def read_sct013(channel, calibration=0.0606):
    """Lit le courant RMS du capteur SCT013"""
    try:
        samples = 300
        somme_carre = 0.0
        vref = 3.3

        for _ in range(samples):
            valeur = read_adc(channel)
            tension = (valeur * vref) / 1023.0
            offset = tension - 1.65
            somme_carre += offset ** 2
            time.sleep(0.0001)

        tension_rms = math.sqrt(somme_carre / samples)
        return round(tension_rms * calibration, 3)
    except Exception as e:
        print(f"Erreur SCT013: {str(e)}")
        return None

def read_sensors():
    """Lit toutes les données des capteurs"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "dht22": {"temperature": None, "humidity": None},
        "bme280": {"temperature": None, "pressure": None, "humidity": None, "altitude": None},
        "sct013": {"current": None},
        "timestamp": timestamp
    }
    
    try:
        # Lecture DHT22
        if not SIMULATION_MODE:
            humidity, temperature = Adafruit_DHT.read_retry(dht_sensor, DHT22_PIN)
        else:
            humidity, temperature = 45.0 + time.time() % 10, 22.0 + time.time() % 5
        
        if humidity is not None and temperature is not None:
            data["dht22"]["temperature"] = round(temperature, 2)
            data["dht22"]["humidity"] = round(humidity, 2)
        
        # Lecture BME280
        if not SIMULATION_MODE:
            data["bme280"]["temperature"] = round(bme280.temperature, 2)
            data["bme280"]["pressure"] = round(bme280.pressure, 2)
            data["bme280"]["humidity"] = round(bme280.humidity, 2)
            data["bme280"]["altitude"] = round(bme280.altitude, 2)
        else:
            data["bme280"] = {
                "temperature": 22.5 + time.time() % 1,
                "pressure": 1013.25,
                "humidity": 50.0,
                "altitude": 100.0
            }
        
        # Lecture SCT013
        if not SIMULATION_MODE:
            data["sct013"]["current"] = read_sct013(SCT013_CHANNEL)
        else:
            data["sct013"]["current"] = round(1.5 + time.time() % 1, 3)
            
    except Exception as e:
        print(f"Erreur lecture capteurs: {str(e)}")
    
    return data

@app.get("/sensor-data", response_model=SensorData, summary="Obtenir toutes les données des capteurs")
def get_sensor_data():
    """Retourne les dernières lectures de tous les capteurs"""
    return read_sensors()

@app.get("/sensor-data/dht22", summary="Obtenir les données du DHT22")
def get_dht22_data():
    """Retourne les données de température et d'humidité du DHT22"""
    data = read_sensors()
    return {
        "temperature": data["dht22"]["temperature"],
        "humidity": data["dht22"]["humidity"],
        "timestamp": data["timestamp"]
    }

@app.get("/sensor-data/bme280", summary="Obtenir les données du BME280")
def get_bme280_data():
    """Retourne les données du BME280 (température, pression, humidité, altitude)"""
    data = read_sensors()
    return {
        "temperature": data["bme280"]["temperature"],
        "pressure": data["bme280"]["pressure"],
        "humidity": data["bme280"]["humidity"],
        "altitude": data["bme280"]["altitude"],
        "timestamp": data["timestamp"]
    }

@app.get("/sensor-data/sct013", summary="Obtenir les données du SCT013")
def get_sct013_data():
    """Retourne le courant mesuré par le capteur SCT013"""
    data = read_sensors()
    return {
        "current": data["sct013"]["current"],
        "timestamp": data["timestamp"]
    }

if __name__ == "__main__":
    print(f"API des capteurs démarrée sur http://0.0.0.0:{API_PORT}")
    print(f"Mode simulation: {'OUI' if SIMULATION_MODE else 'NON'}")
    uvicorn.run(app, host="0.0.0.0", port=API_PORT)