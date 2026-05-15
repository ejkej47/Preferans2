import os
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

trenutni_folder = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(trenutni_folder, "preferans_ml_data.csv")
MODEL_PATH = os.path.join(trenutni_folder, "preferans_rf_model.pkl")
FEATURES_PATH = os.path.join(trenutni_folder, "model_features.pkl")

def analiziraj_podatke(fajl=DEFAULT_CSV):
    print(f"Učitavam podatke iz '{fajl}'...")
    
    try:
        df = pd.read_csv(fajl)
    except FileNotFoundError:
        print(f"\n❌ GREŠKA: Fajl '{fajl}' nije pronađen!")
        return

    # --- ČIŠĆENJE PODATAKA (KLJUČNI DEO) ---
    # 1. Izbacujemo Refu - ona nam kvari statistiku jer nema pravog nosioca
    df = df[df['adut'] != 'Refa']
    
    # 2. Izbacujemo Betl i Sans za sada (kao što si već imao)
    df = df[~df['adut'].isin(['Betl', 'Sans'])]
    
    # 3. Filtriramo nivo licitacije da budu samo validni brojevi (2,3,4,5,6,7)
    validni_nivoi = [2, 3, 4, 5, 6, 7]
    df = df[df['nivo_licitacije'].isin(validni_nivoi)]
    
    print(f"Broj validnih odigranih ruku za trening: {len(df)}")

    # --- ONE-HOT ENCODING ---
    # Pretvaramo nivo_licitacije u string pre encodinga da ga pandas ne bi tretirao kao broj
    df['nivo_licitacije'] = df['nivo_licitacije'].astype(str)
    
    df = pd.get_dummies(df, columns=['adut', 'nivo_licitacije'])
    
    ohe_kolone = [col for col in df.columns if col.startswith(('adut_', 'nivo_licitacije_'))]
    
    osnovni_features = [
        "iz_ruke", "kontra", "pocetna_duzina_aduta", "pocetni_stihovi",
        "pocetni_asovi", "pocetni_kraljevi", "pocetne_dame", "pocetni_zandari", "pocetne_desetke",
        "pocetni_adut_as", "pocetni_adut_kralj", "pocetni_adut_dama",
        "pocetni_asovi_sa_strane", "pocetni_kraljevi_sa_strane",
        "pocetna_druga_duzina", "pocetna_treca_duzina",
        "pocetni_renonsi", "pocetni_singlovi",
        "talon_asovi", "talon_kraljevi", "talon_aduti"
    ]
    
    features = osnovni_features + ohe_kolone
    df = df.dropna(subset=features + ["ishod"])
    
    X = df[features]
    y = df["ishod"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("\nTreniram novi model bez šuma (bez Refa i 0 nivoa)...")
    model = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    joblib.dump(model, MODEL_PATH)
    joblib.dump(features, FEATURES_PATH)
    
    tacnost = accuracy_score(y_test, model.predict(X_test))
    print(f"🎯 Tačnost: {tacnost * 100:.2f}%")
    
    # Ispis važnosti
    importances = model.feature_importances_
    feat_imp = pd.DataFrame({'Parametar': features, 'Važnost (%)': importances * 100})
    print("\nTOP 10 STVARNIH FAKTORA ZA POBEDU:")
    print(feat_imp.sort_values(by='Važnost (%)', ascending=False).head(10).to_string(index=False))

if __name__ == "__main__":
    analiziraj_podatke()