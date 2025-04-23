# 🌱 GREEN-CLOUD — Microservices for Intelligent Mini Data Center

> Plateforme modulaire et conteneurisée pour superviser, prédire et contrôler un micro data center basé sur Raspberry Pi, capteurs IoT et modèles de machine learning.

---

## 🚀 Table des matières

1. [Contexte & Objectifs](#contexte--objectifs)  
2. [Architecture & Structure du dépôt](#architecture--structure-du-dépôt)  
3. [Prérequis](#prérequis)  
4. [Installation & Exécution en local](#installation--exécution-en-local)  
5. [Microservices détaillés](#microservices-détaillés)  
   - [frontend](#frontend)  
   - [data-collector](#data-collector)  
   - [ml-controller](#ml-controller)  
6. [Gestion des capteurs](#gestion-des-capteurs)  
7. [Dataset & Entraînement ML](#dataset--entraînement-ml)  
8. [Analyse d’importance de features](#analyse-dimportance-de-features)  
9. [Déploiement Docker & Kubernetes (à venir)](#déploiement-docker--kubernetes-à-venir)  
10. [Contributeurs](#contributeurs)  
11. [Licence](#licence)  

---

## Contexte & Objectifs

Les data centers consomment beaucoup d’énergie et génèrent de la chaleur. **GREEN-CLOUD** propose :

- 📡 Lecture en temps réel des capteurs (température, humidité, courant, pression…)  
- 🤖 Prédiction de la consommation énergétique et décision d’activer la ventilation (`fan_on`)  
- 💬 Fil d’actualité “mini-réseau social” pour les utilisateurs  
- 🌐 Interface web légère (Flask + Bootstrap)  
- 🐳 Architecture microservices prête pour Docker / Kubernetes  

---

## Architecture & Structure du dépôt

```
GREEN-CLOUD/
├── data/
│   ├── logs/                         # Journaux & mesures historiques
│   └── models/
│       ├── dataset/                  # CSV d’entraînement (fan_dataset.csv, etc.)
│       ├── scaler.pkl                # StandardScaler sauvegardé
│       └── *.pkl                     # Modèles entraînés (RandomForest.pkl, etc.)
├── k8s/                              # Manifests Kubernetes (placeholder)
├── sensors/                          # Scripts de lecture capteurs
│   ├── bmp280_reader.py
│   ├── dht22_reader.py
│   └── sct013_reader.py
├── services/
│   ├── frontend/                     # UI web Flask (templates/, static/, frontend.py)
│   ├── data-collector/               # API utilisateurs & posts (app.py)
│   ├── ml-controller/                # Entraînement & prédiction ML (train_xxx.py, service.py)
│   ├── fan-controller/               # Contrôle GPIO ventilateur (placeholder)
│   ├── sensor-visualizer/            # Dashboard des mesures (placeholder)
│   ├── green-meter/                  # Calcul d’empreinte carbone (placeholder)
│   └── workload-tester/              # Simulateur de charge CPU (placeholder)
├── docker-compose.yml                # Orchestration multi-services (à venir)
└── README.md                         # Ce fichier
```

---

## Prérequis

- **Python 3.8+**  
- **pip**  
- Capteurs connectés à un Raspberry Pi (DHT22, SCT-013 via ADC, BMP280)  
- (Optionnel) **Docker** & **kubectl** pour déploiement futur  

---

## Installation & Exécution en local

1. **Cloner le dépôt**  
   ```bash
   git clone https://github.com/username/GREEN-CLOUD.git
   cd GREEN-CLOUD
   ```

2. **Créer un environnement virtuel**  
   ```bash
   python -m venv venv
   source venv/bin/activate       # macOS/Linux
   venv\Scripts\activate.bat    # Windows
   ```

3. **Installer les dépendances**  
   ```bash
   pip install -r requirements.txt
   ```

4. **Lancer le service `data-collector`** (port **5001**)  
   ```bash
   cd services/data-collector
   python app.py
   ```

5. **Lancer le service `frontend`** (port **5000**)  
   ```bash
   cd services/frontend
   python frontend.py
   ```

6. **Visiter**  
   [http://localhost:5000](http://localhost:5000)  

---

## Microservices détaillés

### frontend

- **Langage** : Python / Flask  
- **Routes** :  
  - `GET /login`, `POST /login`  
  - `GET /register`, `POST /register`  
  - `GET /feed`, `POST /feed`  
  - `GET /sensors`, `/ml-control`, `/manual-control`, `/workflow`, `/load`, `/greenmeter`  
- **Dépend** : `data-collector` pour `/login`, `/register`, `/post`, `/posts`  
- **Templates** : Bootstrap 5, `templates/` & `static/`  

### data-collector

- **Langage** : Python / Flask  
- **Routes** :  
  - `POST /register` → stocke `data/users.json`  
  - `POST /login` → valide identifiants  
  - `POST /post` → stocke `data/posts.json`  
  - `GET /posts` → renvoie la liste des posts  
- **Données** : JSON files (`data/users.json`, `data/posts.json`)  

### ml-controller

- **Script d’entraînement** :  
  - `train_fan_models.py` → entraîne plusieurs classificateurs  
  - Sauvegarde `scaler.pkl` + `{model}.pkl` dans `data/models/`  
  - Génère `permutation_importance_{model}.png`  
- **Service de prédiction** (à implémenter) :  
  - `POST /predict-fan` ← reçoit mesures JSON, renvoie `{ "fan_on": true/false }`  

---

## Gestion des capteurs

Le dossier `sensors/` contient :
- **dht22_reader.py** → `read_dht22()` (température & humidité)  
- **bmp280_reader.py** → `read_bmp280()` (pression via I2C)  
- **sct013_reader.py** → `read_sct013()` (courant, nécessite ADC)  

Chaque service importe :
```python
from sensors import read_dht22, read_bmp280, read_sct013
```

---

## Dataset & Entraînement ML

- **Dataset** : `data/models/dataset/fan_dataset.csv` (300 échantillons simulés)  
- **Features** : `temperature, humidity, current, pressure, energy, workload`  
- **Target** : `fan_on` (0/1, règle logique “au moins 2 conditions vraies”)  
- **Script** : `services/ml-controller/train_fan_models.py`  
- **Modèles testés** : RandomForest, GradientBoosting, LogisticRegression, etc.  

---

## Analyse d’importance de features

- **Permutation Importance** : pour chaque modèle, graphique horizontal  
  - Généré dans `data/models/permutation_importance_{Model}.png`  
- **SHAP** : utilisation future dans un environnement CPU-only  

---

## Déploiement Docker & Kubernetes (à venir)

- **docker-compose.yml** orchestrera tous les services  
- **k8s/** contiendra les manifests (Deployments, Services)  
- Chaque microservice aura son propre `Dockerfile`  

---

## Contributeurs
- Stephane Bryand TONDE
- Sette TOURÉ  
- Youssef SERBOUTI  
- Mahmoud SANNOUNE  
- Mohamed Ali RABBAH  

---

## Licence

Ce projet est fourni à titre éducatif et prototypique. Réutilisation libre avec mention de l’auteur original.

