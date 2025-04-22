# sensors.py
import Adafruit_DHT
import smbus2
import bme280
import random
import os

# ==== CONFIGURATION DES CAPTEURS ====

# DHT22
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = int(os.getenv("DHT_PIN", 4))  # GPIO 4 (Physique pin 7)

# BMP280 (via I2C)
I2C_PORT = 1
BMP280_ADDRESS = 0x76
bus = smbus2.SMBus(I2C_PORT)
calibration_params = bme280.load_calibration_params(bus, BMP280_ADDRESS)


# ==== FONCTIONS DE MESURE ====

def read_dht22():
    """Retourne l'humidité (%) et la température (°C) mesurées par le DHT22"""
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    return humidity, temperature


def read_bmp280():
    """Retourne la pression atmosphérique (hPa) mesurée par le BMP280"""
    data = bme280.sample(bus, BMP280_ADDRESS, calibration_params)
    return data.pressure


def read_acs712(simulate=True):
    """Retourne un courant simulé (ou réel si tu ajoutes un ADC comme MCP3008)"""
    if simulate:
        return round(random.uniform(0.5, 4.5), 2)
    else:
        # À implémenter avec lecture ADC (ex: MCP3008)
        raise NotImplementedError("Lecture réelle non encore implémentée")
