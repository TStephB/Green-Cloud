import Adafruit_DHT
import time

# Définir le modèle du capteur et le numéro du GPIO connecté
capteur = Adafruit_DHT.DHT22
gpio_pin = 4  # Remplacer par le GPIO connecté à ton capteur

while True:
    humidite, temperature = Adafruit_DHT.read_retry(capteur, gpio_pin)

    if humidite is not None and temperature is not None:
        print(f'Température : {temperature:.1f}°C, Humidité : {humidite:.1f}%')
    else:
        print('Échec de la lecture du capteur. Réessayer !')

    # Attendre 2 secondes avant la prochaine lecture
    time.sleep(2)

