
import spidev
import time
import math

# Initialisation du SPI
spi = spidev.SpiDev()
spi.open(0, 0)  # bus 0, device 0 (CE0)
spi.max_speed_hz = 1350000

def lire_adc(channel):
    """Lit la valeur analogique d'un canal MCP3008"""
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

def lire_courant(channel, calibration=60.6):
    """Calcule le courant RMS mesuré par le SCT-013"""
    samples = 1000
    somme_carre = 0
    
    for _ in range(samples):
        valeur = lire_adc(channel)
        tension = (valeur * 3.3) / 1023.0  # Conversion MCP3008 (10 bits)
        offset = tension - 1.65  # Le signal est centré autour de 1.65V
        somme_carre += offset * offset
        time.sleep(0.001)  # Petit délai pour échantillonner correctement

    tension_rms = math.sqrt(somme_carre / samples)
    courant = tension_rms * calibration
    return courant

# Boucle principale
canal_sct = 0  # Utiliser le canal 0 du MCP3008

while True:
    courant_mesure = lire_courant(canal_sct)
    print(f"Courant mesuré : {courant_mesure:.2f} A")
    time.sleep(1
