# ml_control/app.py
from flask import Flask, request, jsonify
import joblib
import numpy as np
import os

# Chemins
ARTIFACT_DIR = os.getenv("ARTIFACT_DIR", "model_outputs")
MODEL_PATH   = os.path.join(ARTIFACT_DIR, "RF_model.pkl")
SCALER_PATH  = os.path.join(ARTIFACT_DIR, "scaler.pkl")

# Chargement des artefacts
model  = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

app = Flask(__name__)

@app.get("/status")
def status():
    return jsonify({"status": "ok"})

@app.post("/predict")
def predict():
    """
    Attendu en JSON :
    {
        "temperature": 23.4,
        "humidity": 51.2,
        "cpu_load": 0.72,
        ...
    }
    L’ordre des features doit être cohérent avec l’entraînement.
    """
    try:
        data = request.get_json(force=True)
        # 1️⃣ transformer en vecteur
        ordered_keys = sorted(data.keys())        # même ordre qu’à l’entraînement
        x = np.array([data[k] for k in ordered_keys], dtype=float).reshape(1, -1)
        # 2️⃣ scaling identique à l’entraînement
        x_scaled = scaler.transform(x)
        # 3️⃣ prédiction
        y_pred = model.predict(x_scaled)[0]
        return jsonify({"prediction": float(y_pred)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)

