import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

trenutni_folder = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(trenutni_folder, "preferans_ml_data.csv")
MODEL_PATH = os.path.join(trenutni_folder, "preferans_rf_model.pkl")
FEATURES_PATH = os.path.join(trenutni_folder, "model_features.pkl")

def analiziraj_podatke(fajl=DEFAULT_CSV):
    print(f"Učitavam podatke iz '{fajl}'...")
    
    # Lista kolona tačno kako ih simulacija izbacuje
    polja = [
        "igrac_id", "uloga", "nivo_licitacije", "adut", "iz_ruke", "kontra",
        "pocetni_asovi", "pocetni_kraljevi", "pocetne_dame", "pocetni_zandari", "pocetne_desetke",
        "pocetni_stihovi", "pocetna_duzina_aduta", 
        "pocetni_adut_as", "pocetni_adut_kralj", "pocetni_adut_dama",
        "pocetni_asovi_sa_strane", "pocetni_kraljevi_sa_strane",
        "pocetna_druga_duzina", "pocetna_treca_duzina", 
        "pocetni_renonsi", "pocetni_singlovi",
        "talon_asovi", "talon_kraljevi", "talon_aduti", 
        "zvanje_tip", "osvojeni_stihovi", "ishod"
    ]
    
    try:
        df = pd.read_csv(fajl)
    except FileNotFoundError:
        print(f"\n❌ GREŠKA: Fajl '{fajl}' nije pronađen! Generiši prvo podatke.")
        return

    # Čistimo podatke od Betla i Sansa
    df = df[~df['adut'].isin(['Betl', 'Sans'])]
    print(f"Broj validnih ruku u boji za analizu: {len(df)}")
    
    # ==========================================
    # ONE-HOT ENCODING: I za aduta i za nivo licitacije!
    # ==========================================
    # Ovo će napraviti kolone tipa: adut_Pik, adut_Tref..., nivo_licitacije_2, nivo_licitacije_3...
    df = pd.get_dummies(df, columns=['adut', 'nivo_licitacije'])
    
    # Prikupljamo sve generisane One-Hot kolone
    ohe_kolone_adut = [col for col in df.columns if col.startswith('adut_')]
    ohe_kolone_nivo = [col for col in df.columns if col.startswith('nivo_licitacije_')]
    
    print(f"Generisane kolone za adute: {ohe_kolone_adut}")
    print(f"Generisane kolone za nivo licitacije: {ohe_kolone_nivo}")
    
    # Svi naši osnovni parametri (BEZ nivo_licitacije i aduta jer su sada One-Hot)
    osnovni_features = [
        "iz_ruke", "kontra",
        "pocetna_duzina_aduta", "pocetni_stihovi",
        "pocetni_asovi", "pocetni_kraljevi", "pocetne_dame", "pocetni_zandari", "pocetne_desetke",
        "pocetni_adut_as", "pocetni_adut_kralj", "pocetni_adut_dama",
        "pocetni_asovi_sa_strane", "pocetni_kraljevi_sa_strane",
        "pocetna_druga_duzina", "pocetna_treca_duzina",
        "pocetni_renonsi", "pocetni_singlovi",
        "talon_asovi", "talon_kraljevi", "talon_aduti"
    ]
    
    # Spajamo sve feature
    features = osnovni_features + ohe_kolone_adut + ohe_kolone_nivo
    
    # Provera i čišćenje (brisemo redove kojima fali neki podatak)
    df = df.dropna(subset=features + ["ishod"])
    
    X = df[features]
    y = df["ishod"]
    
    # 80% za trening, 20% za test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("\nTreniram Elitni Random Forest model sa One-Hot Encodingom...")
    model = RandomForestClassifier(n_estimators=150, max_depth=12, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    # Čuvanje "mozga"
    joblib.dump(model, MODEL_PATH)
    joblib.dump(features, FEATURES_PATH)
    print(f"✅ Model uspešno sačuvan kao: preferans_rf_model.pkl")
    
    # Testiranje
    y_pred = model.predict(X_test)
    tacnost = accuracy_score(y_test, y_pred)
    print(f"\n🎯 Tačnost predviđanja modela: {tacnost * 100:.2f}%")
    print("-" * 50)
    
    # Rangiranje važnosti
    importances = model.feature_importances_
    feature_importance_df = pd.DataFrame({
        'Parametar': features,
        'Važnost (%)': importances * 100
    }).sort_values(by='Važnost (%)', ascending=False)
    
    print("\nŠTA GLAVNO REZULTUJE POBEDOM (Top 15 najbitnijih parametara):")
    print(feature_importance_df.head(15).to_string(index=False))
    
    # Grafikon
    top_features = feature_importance_df.head(15)
    plt.figure(figsize=(12, 8))
    plt.barh(top_features['Parametar'], top_features['Važnost (%)'], color='coral')
    plt.xlabel('Uticaj na prolaz/pad (%)')
    plt.title('Top 15 faktora za pobedu Nosioca u Preferansu (ML Analiza)')
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    analiziraj_podatke()