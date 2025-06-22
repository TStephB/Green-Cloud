import time
import json
import threading
from pathlib import Path
import Adafruit_DHT
import board
import busio
import adafruit_bme280
import spidev
import math

# Configuration des capteurs
DHT22_PIN = 23
BME280_ADDRESS = 0x76
SCT013_CHANNEL = 0
DATA_FILE = Path("sensor_data.json")
UPDATE_INTERVAL = 5  # secondes

# Initialisation des capteurs
# DHT22
dht_sensor = Adafruit_DHT.DHT22

# BME280
i2c = busio.I2C(board.SCL, board.SDA)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=BME280_ADDRESS)

# SCT013 (via MCP3008)
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

# Données courantes
sensor_data = {
    "dht22": {"temperature": None, "humidity": None},
    "bme280": {"temperature": None, "pressure": None, "humidity": None, "altitude": None},
    "sct013": {"current": None},
    "timestamp": None
}

def read_dht22():
    """Lit les données du capteur DHT22"""
    try:
        humidity, temperature = Adafruit_DHT.read_retry(dht_sensor, DHT22_PIN)
        if humidity is not None and temperature is not None:
            return round(temperature, 2), round(humidity, 2)
    except Exception as e:
        print(f"Erreur DHT22: {str(e)}")
    return None, None

def read_bme280():
    """Lit les données du capteur BME280"""
    try:
        return {
            "temperature": round(bme280.temperature, 2),
            "pressure": round(bme280.pressure, 2),
            "humidity": round(bme280.humidity, 2),
            "altitude": round(bme280.altitude, 2)
        }
    except Exception as e:
        print(f"Erreur BME280: {str(e)}")
        return None

def read_adc(channel):
    """Lit la valeur analogique d'un canal du MCP3008"""
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((adc[1] & 3) << 8) + adc[2]

def read_sct013(channel, calibration=0.0606):
    """Lit le courant RMS du capteur SCT013"""
    try:
        samples = 300  # Réduit pour des performances temps réel
        somme_carre = 0.0
        vref = 3.3

        for _ in range(samples):
            valeur = read_adc(channel)
            tension = (valeur * vref) / 1023.0
            offset = tension - 1.65  # Signal centré à mi-tension
            somme_carre += offset ** 2
            time.sleep(0.0001)

        tension_rms = math.sqrt(somme_carre / samples)
        return round(tension_rms * calibration, 3)
    except Exception as e:
        print(f"Erreur SCT013: {str(e)}")
        return None

def update_sensor_data():
    """Met à jour les données des capteurs et les sauvegarde"""
    global sensor_data
    
    while True:
        try:
            # Lecture des capteurs
            dht_temp, dht_hum = read_dht22()
            bme_data = read_bme280()
            current = read_sct013(SCT013_CHANNEL)
            
            # Mise à jour des données
            sensor_data["dht22"]["temperature"] = dht_temp
            sensor_data["dht22"]["humidity"] = dht_hum
            
            if bme_data:
                sensor_data["bme280"] = bme_data
            
            sensor_data["sct013"]["current"] = current
            sensor_data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Sauvegarde dans le fichier JSON
            with open(DATA_FILE, 'w') as f:
                json.dump(sensor_data, f, indent=2)
                
            print(f"Données mises à jour à {sensor_data['timestamp']}")
            
        except Exception as e:
            print(f"Erreur majeure: {str(e)}")
        
        time.sleep(UPDATE_INTERVAL)

def start_collector():
    """Démarre le collecteur de données dans un thread séparé"""
    # Créer le fichier s'il n'existe pas
    if not DATA_FILE.exists():
        with open(DATA_FILE, 'w') as f:
            json.dump(sensor_data, f)
    
    # Démarrer le thread de collecte
    collector_thread = threading.Thread(target=update_sensor_data, daemon=True)
    collector_thread.start()
    print("Collecteur de données démarré...")
    return collector_thread

if __name__ == "__main__":
    start_collector()
    # Maintenir le programme actif
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArrêt du collecteur de données")
        spi.close()