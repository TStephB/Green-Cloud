import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pickle
import os

# === Paramètres depuis variables d’environnement (pour la conteneurisation) ===
DATASET_PATH = os.getenv("DATASET_PATH", "data/models/dataset/Dataset_IoT_-_Data_Center.csv")
MODEL_PATH = os.getenv("MODEL_PATH", "data/models/RF_model.pkl")
SCALER_PATH = os.getenv("SCALER_PATH", "data/models/scaler.pkl")

# === Lecture du dataset ===
print(f"📂 Lecture du fichier dataset : {DATASET_PATH}")
df = pd.read_csv(DATASET_PATH)

# === Features et target ===
X = df[['temperature', 'humidity', 'current', 'pressure']]
y = df['energy_consumption']

# === Standardisation ===
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# === Sauvegarde du scaler ===
with open(SCALER_PATH, 'wb') as f:
    pickle.dump(scaler, f)
print(f"✅ Scaler sauvegardé : {SCALER_PATH}")

# === Séparation train/test ===
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# === Entraînement ===
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# === Sauvegarde du modèle ===
with open(MODEL_PATH, 'wb') as f:
    pickle.dump(model, f)
print(f"✅ Modèle sauvegardé : {MODEL_PATH}")