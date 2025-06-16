# NE PAS NOMMER CE FICHIER "app.py"
import streamlit as st
import pandas as pd
import numpy as np
import shap
import matplotlib.pyplot as plt
import joblib
import sys, os

# Ajouter le chemin vers le service Utilisation_Model_Final
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'services')))

# Définition des répertoires de base
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DATASET_PATH = os.getenv(
    'DATASET_PATH',
    os.path.join(DATA_DIR, 'models', 'dataset', 'Dataset_-_Fan_Activation_Logic.csv')
)
MODEL_DIR = os.getenv(
    'MODEL_DIR',
    os.path.join(DATA_DIR, 'models', 'model_outputs')
)
SCALER_PATH = os.getenv(
    'SCALER_PATH',
    os.path.join(MODEL_DIR, 'scaler.pkl')
)

# Chargement du dataset et du scaler
df = pd.read_csv(DATASET_PATH)
TARGET_NAME = 'fan_on'
FEATURE_NAMES = [col for col in df.columns if col != TARGET_NAME]
scaler = joblib.load(SCALER_PATH)

# Découverte automatique des modèles
MODEL_OPTIONS = {
    os.path.splitext(f)[0]: os.path.join(MODEL_DIR, f)
    for f in os.listdir(MODEL_DIR)
    if f.endswith('.pkl') and f != os.path.basename(SCALER_PATH)
}

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Green Cloud - Efficacité Énergétique",
    page_icon="⚡",
    layout="wide"
)

# CSS personnalisé amélioré
st.markdown("""
<style>
.main { background-color: #F1F3F5; }
.stButton>button { color: white; background: #1976d2; border: none; border-radius: 8px; padding: 10px 16px; font-size: 15px; }
section[data-testid='stSidebar'] { background: #2e3b4e; padding: 16px; }
section[data-testid='stSidebar'] h1, h2, h3 { color: #37474f; }
.card { background-color: #bbdefb; border-left: 6px solid #0d47a1; color: #0d47a1; padding: 16px; border-radius: 8px; margin: 12px 0; }
.title-main { font-size: 2rem; color: #1565c0; margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)

# Initialisation de session_state
if not hasattr(st, 'session_state'):
    st.warning("⚠️ Veuillez lancer l'application avec `streamlit run app.py` pour activer session_state.")
    st.stop()
st.session_state.setdefault('logged_in', False)
st.session_state.setdefault('cas_history', [])
st.session_state.setdefault('sample_loaded', False)

# Page de connexion simplifiée
if not st.session_state.get('logged_in', False):
    st.title("🔐 Connexion Admin")
    user = st.text_input("Utilisateur")
    pwd = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        if user == "admin" and pwd == "1234":
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("Identifiants invalides.")
    st.stop()

# Barre latérale
st.sidebar.markdown("**Bienvenue, Admin**")
st.sidebar.markdown("## 🏠 Menu")
page = st.sidebar.radio(
    "Navigation", ["Dashboard", "Historique", "Métriques", "Assistant", "Aide", "FAQ"]
)
st.sidebar.markdown("---")
st.sidebar.markdown("### 🧠 Modèle ML")
model_name = st.sidebar.selectbox("Modèle", list(MODEL_OPTIONS.keys()))
model = joblib.load(MODEL_OPTIONS[model_name])

# Dashboard
if page == "Dashboard":
    st.markdown("<h2 class='title-main'>🔌 Prédiction d'Efficacité Énergétique</h2>", unsafe_allow_html=True)
    # Exemple de données
    sample = dict(zip(FEATURE_NAMES, [25.0, 40.0, 10.0, 1013.0, 500.0, 75.0]))
    if st.session_state['sample_loaded']:
        for k, v in sample.items(): st.session_state[k] = v
        st.session_state['sample_loaded'] = False

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Charger Exemple"):
            st.session_state['sample_loaded'] = True
            st.rerun()
        inputs = []
        for f in FEATURE_NAMES:
            default = st.session_state.get(f, sample.get(f, 0.0))
            val = st.number_input(f, value=float(default), format="%.2f", key=f)
            inputs.append(val)
        niveau = st.slider("Priorité du contrôle", 1, 5, 3)
        commentaire = st.text_area("Commentaire")
        st.progress(int(len(inputs) and sum(1 for i in inputs if i is not None) / len(inputs) * 100 or 0))
        if st.button("Enregistrer feedback"):
            st.toast("Feedback enregistré.")
            st.balloons()
    with col2:
        if st.button("Lancer la prédiction"):
            X = np.array(inputs).reshape(1, -1)
            Xs = scaler.transform(X)
            pred = model.predict(Xs)[0]
            prob = model.predict_proba(Xs)[0][1] if hasattr(model, 'predict_proba') else None
            # Affichage du résultat avec style
            result_label = f"Activation refroidissement à {pred*100:.1f}%" if pred else "Pas d'activation"
            prob_text = f"Confiance : {prob*100:.1f}%" if prob is not None else ""
            st.markdown(
                f"<div class='card'><h3>Résultat :</h3><p><strong>{result_label}</strong></p><p>{prob_text}</p></div>",
                unsafe_allow_html=True
            )
            st.balloons()
            # Historique
            rec = {f: inputs[i] for i, f in enumerate(FEATURE_NAMES)}
            rec.update({'prediction': int(pred), 'probability': float(prob)})
            st.session_state['cas_history'].append(rec)
            df_rec = pd.DataFrame([rec])
            st.download_button("📥 Télécharger résultat", df_rec.to_csv(index=False), "result.csv", "text/csv")
            # Interprétation SHAP
            try:
                df_sh = pd.read_csv(DATASET_PATH)
                explainer = shap.TreeExplainer(model)
                sv = explainer.shap_values(df_sh)
                st.subheader("🔎 Interprétation SHAP")

                # Vérifie si sv est une liste ou un seul tableau
                if isinstance(sv, list) and len(sv) == 2:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    shap.summary_plot(sv[1], df_sh, feature_names=df_sh.columns, plot_type="dot", show=False)
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.clf()
                else:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    shap.summary_plot(sv, df_sh, feature_names=df_sh.columns, plot_type="dot", show=False)
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.clf()


            except Exception as e:
                st.warning(f"Pas de SHAP disponible : {e}")

# Historique
elif page == "Historique":
    st.title("📋 Historique des Prédictions")
    if st.session_state['cas_history']:
        st.dataframe(pd.DataFrame(st.session_state['cas_history']))
    else:
        st.info("Aucune prédiction enregistrée.")

# Métriques
elif page == "Métriques":
    st.title("📊 Comparaison des Modèles")
    dfm = pd.read_csv(os.path.join(MODEL_DIR, 'comparaison_modeles.csv'))
    cols = st.columns(len(dfm))
    for (_, row), col in zip(dfm.iterrows(), cols):
        with col:
            fig, ax = plt.subplots()
            ax.pie([row['Accuracy'], 1-row['Accuracy']], labels=[f"{row['Accuracy']*100:.0f}%", ""], startangle=90, wedgeprops={'width':0.3,'edgecolor':'white'})
            ax.axis('equal')
            st.subheader(row['Modèle'])
            st.pyplot(fig)

# Assistant
elif page == "Assistant":
    st.title("💬 Assistant Energie")
    msg = st.chat_input("Posez une question sur l'efficacité énergétique...")
    if msg:
        with st.chat_message("assistant"):
            m = msg.lower()
            if "temp" in m:
                st.write("Pour réduire la température, optimisez la charge ou améliorez le refroidissement.")
            elif "charge" in m:
                st.write("Équilibrez les workloads pour éviter les surcharges.")
            else:
                st.write("Je suis en développement 🤖.")

# Aide
elif page == "Aide":
    st.title("❓ Aide")
    st.markdown("- Chargez ou saisissez vos mesures et lancez la prédiction.")
    st.markdown("- Consultez l'historique et les métriques.")

# FAQ
elif page == "FAQ":
    st.title("🙋‍♂️ FAQ")
    with st.expander("Comment les modèles sont-ils entraînés ?"):
        st.write("Sur des données historiques de mesures et de consommation.")
    with st.expander("Interprétation des diagrammes ?"):
        st.write("Part verte = accuracy, part grise = erreur.")
    st.markdown("Pour plus d'info, contactez l'équipe Green Cloud.")
