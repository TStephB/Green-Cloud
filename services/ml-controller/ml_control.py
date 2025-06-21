from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import joblib
import numpy as np

app = FastAPI()

# --- Middleware CORS pour autoriser les appels JS depuis navigateur ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En dev, autoriser toutes les origines
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Chargement des modèles ---
BASE_DIR     = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR     = os.path.join(BASE_DIR, 'data')
MODEL_DIR    = os.path.join(DATA_DIR, 'models', 'model_outputs')
SCALER_PATH  = os.path.join(MODEL_DIR, 'scaler.pkl')

scaler = joblib.load(SCALER_PATH)

FEATURE_NAMES = [
    'temperature',
    'humidity',
    'current',
    'pressure',
    'energy',
    'workload',
]

models = {}
for fname in os.listdir(MODEL_DIR):
    if not fname.endswith('.pkl') or fname == os.path.basename(SCALER_PATH):
        continue
    name = os.path.splitext(fname)[0]
    models[name] = joblib.load(os.path.join(MODEL_DIR, fname))

# --- Schéma des données entrantes ---
class Features(BaseModel):
    temperature: float
    humidity: float
    current: float
    pressure: float
    energy: float
    workload: float

# --- Endpoint de prédiction ---
@app.post("/predict")
def predict(features: Features):
    X = np.array([[getattr(features, f) for f in FEATURE_NAMES]])
    Xs = scaler.transform(X)
    results = {}
    for name, m in models.items():
        pred = int(m.predict(Xs)[0])
        prob = float(m.predict_proba(Xs)[0][1]) if hasattr(m, "predict_proba") else None
        results[name] = {"prediction": pred, "probability": prob}
    return results

# Lancer le serveur avec : cd services/ml-controller
# uvicorn ml_control:app --reload
