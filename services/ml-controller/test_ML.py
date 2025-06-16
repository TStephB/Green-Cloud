import os
import joblib
import numpy as np

# 1) Définissez ici votre dossier de modèles et de scaler
BASE_DIR     = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR     = os.path.join(BASE_DIR, 'data')
MODEL_DIR    = os.path.join(DATA_DIR, 'models', 'model_outputs')
SCALER_PATH  = os.path.join(MODEL_DIR, 'scaler.pkl')

# 2) Chargez le scaler
scaler = joblib.load(SCALER_PATH)

# 3) Définissez la liste des features dans l’ordre attendu par vos modèles
FEATURE_NAMES = [
    'temperature',
    'humidity',
    'current',
    'pressure',
    'energy',
    'workload',
]

# 4) Chargez tous les modèles .pkl dans MODEL_DIR (hors scaler)
models = {}
for fname in os.listdir(MODEL_DIR):
    if not fname.endswith('.pkl') or fname == os.path.basename(SCALER_PATH):
        continue
    name = os.path.splitext(fname)[0]
    models[name] = joblib.load(os.path.join(MODEL_DIR, fname))

# 5) Lecture des inputs utilisateur
print("Entrez les valeurs pour chaque feature :")
values = []
for feat in FEATURE_NAMES:
    val = input(f"  - {feat}: ")
    try:
        values.append(float(val))
    except ValueError:
        print("    ⚠️ valeur invalide, je prends 0.0")
        values.append(0.0)

# 6) Préparation du vecteur et mise à l'échelle
X = np.array(values).reshape(1, -1)
Xs = scaler.transform(X)

# 7) Prédiction et affichage
print("\nRésultats :")
for name, m in models.items():
    pred = m.predict(Xs)[0]
    if hasattr(m, "predict_proba"):
        prob = m.predict_proba(Xs)[0][1]
        print(f" - {name:20s} → prédiction : {pred}, probabilité {prob*100:5.1f}%")
    else:
        print(f" - {name:20s} → prédiction : {pred}")

