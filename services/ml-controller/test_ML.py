import time
import requests
from collect_data import read_dht22, read_bmp280, read_acs712

# Configuration
API_URL = "http://localhost:8000/predict"
INTERVAL = 10  # Secondes entre les mesures
SIMULATE_CURRENT = True

def collect_sensor_data():
    """Collecte les données des capteurs et calcule les métriques dérivées"""
    try:
        humidity, temperature = read_dht22()
        pressure = read_bmp280()
        current = read_acs712(simulate=SIMULATE_CURRENT)
        
        # Calcul des valeurs dérivées
        energy = current * 230 / 1000  # kW (supposant 230V)
        workload = min(max(current * 20, 0), 100)  # % (ex: 1A = 20% workload)
        
        return {
            "temperature": float(temperature),
            "humidity": float(humidity),
            "current": float(current),
            "pressure": float(pressure),
            "energy": float(energy),
            "workload": float(workload)
        }
    except Exception as e:
        print(f"Erreur capteurs: {str(e)}")
        return None

def predict_with_ml(sensor_data):
    """Envoie les données à l'API ML et retourne les prédictions"""
    try:
        response = requests.post(API_URL, json=sensor_data, timeout=5)
        if response.status_code == 200:
            return response.json()
        print(f"Erreur API: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Erreur connexion API: {str(e)}")
    return None

def main():
    """Boucle principale de collecte et prédiction"""
    print("Démarrage du système IoT/ML...")
    print(f"Configuration: Intervalle={INTERVAL}s, Simulation={SIMULATE_CURRENT}")
    
    while True:
        start_time = time.time()
        
        # 1. Collecte des données
        sensor_data = collect_sensor_data()
        if not sensor_data:
            time.sleep(INTERVAL)
            continue
            
        print("\nDonnées capteurs:")
        for k, v in sensor_data.items():
            print(f"- {k:12}: {v:.2f}")
        
        # 2. Prédiction ML
        predictions = predict_with_ml(sensor_data)
        if predictions:
            print("\nPrédictions ML:")
            for model, result in predictions.items():
                proba = result['probability'] or 'N/A'
                print(f"- {model:15}: {result['prediction']} (prob: {proba})")
        
        # 3. Gestion de l'intervalle
        elapsed = time.time() - start_time
        sleep_time = max(0, INTERVAL - elapsed)
        time.sleep(sleep_time)

if __name__ == "__main__":
    main()