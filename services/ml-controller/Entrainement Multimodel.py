import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import pickle

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
from sklearn.inspection import permutation_importance

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import LinearSVC
from sklearn.neighbors import KNeighborsClassifier

# === Chargement du dataset ===
df = pd.read_csv("data/models/dataset/Dataset_-_Fan_Activation_Logic.csv")  
X = df.drop(columns=["fan_on"])
y = df["fan_on"]

# === Création du dossier de sortie ===
os.makedirs("data/models/model_outputs", exist_ok=True)

# === Standardisation ===
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Sauvegarde du scaler
with open("data/models/model_outputs/scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)

# === Séparation train/test ===
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)

# === Liste des modèles à tester ===
models = {
    "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42),
    "GradientBoosting": GradientBoostingClassifier(),
    "LogisticRegression": LogisticRegression(max_iter=10000),
    "LinearSVC": LinearSVC(max_iter=10000),
    "KNN": KNeighborsClassifier(),
    "DecisionTree": DecisionTreeClassifier()
}

# === Entraînement, évaluation et visualisation ===
results = []

for name, model in models.items():
    print(f"🔧 Entraînement du modèle : {name}")
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    results.append((name, acc))

    # Sauvegarde du modèle
    with open(f"data/models/model_outputs/{name}.pkl", "wb") as f:
        pickle.dump(model, f)

    # === Importance des variables (permutation) ===
    try:
        print(f"📊 Calcul importance des features : {name}")
        result = permutation_importance(
            model, X_test, y_test, n_repeats=10, random_state=42
        )
        perm_df = pd.DataFrame({
            "feature": X.columns,
            "importance_mean": result.importances_mean,
            "importance_std": result.importances_std
        }).sort_values(by="importance_mean", ascending=True)

        # Graphique
        plt.figure(figsize=(8, 5))
        plt.barh(
            perm_df["feature"],
            perm_df["importance_mean"],
            xerr=perm_df["importance_std"],
            color="skyblue"
        )
        plt.xlabel("Importance (permutation)")
        plt.title(f"Importance des variables - {name}")
        plt.tight_layout()
        plt.savefig(f"data/models/model_outputs/permutation_importance_{name}.png")
        plt.close()

    except Exception as e:
        print(f"⚠️ Erreur lors de l’analyse des features pour {name} :", e)

# === Résumé des performances ===
df_results = pd.DataFrame(results, columns=["Modèle", "Accuracy"]).sort_values(by="Accuracy", ascending=False)
df_results.to_csv("data/models/model_outputs/comparaison_modeles.csv", index=False)
print("\n🎯 Résultats comparatifs :")
print(df_results)