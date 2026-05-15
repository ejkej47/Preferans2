import os
import joblib
import pandas as pd
import warnings
from itertools import combinations
from agents.napredni_bot import NapredniBot
from engine.game_rules import GameRules

MODEL_PATH = "machine_learning/preferans_rf_model.pkl"
FEATURES_PATH = "machine_learning/model_features.pkl"

class MLBot(NapredniBot):
    # Statičke varijable za keširanje na nivou klase
    _cached_model = None
    _cached_features = None

    def __init__(self, agent_id, ime="ML Oracle Bot"):
        super().__init__(agent_id, ime)
        self.red_vrednosti = {'7': 0, '8': 1, '9': 2, '10': 3, 'J': 4, 'Q': 5, 'K': 6, 'A': 7}
        
        # Učitavamo model sa diska samo jednom po procesu!
        if MLBot._cached_model is None:
            if os.path.exists(MODEL_PATH) and os.path.exists(FEATURES_PATH):
                MLBot._cached_model = joblib.load(MODEL_PATH)
                MLBot._cached_model.n_jobs = 1  # Zadržavamo 1 da ne bi došlo do thrashing-a procesora
                MLBot._cached_features = joblib.load(FEATURES_PATH)
            else:
                print(f"⚠️ UPOZORENJE: Model nije pronađen na {MODEL_PATH}.")
                
        self.model = MLBot._cached_model
        self.model_features = MLBot._cached_features
        self.model_loaded = self.model is not None

    def _ekstrakcija_featurea(self, ruka, adut, nivo, iz_ruke=0, kontra=0):
        """Pretvara ruku u format koji ML model razume (identično kao u simulaciji)."""
        boje = {'Pik': [], 'Karo': [], 'Herc': [], 'Tref': []}
        for k in ruka:
            v, b = k.split()
            boje[b].append(v)
            
        asovi = sum(1 for b in boje.values() if 'A' in b)
        kraljevi = sum(1 for b in boje.values() if 'K' in b)
        dame = sum(1 for b in boje.values() if 'Q' in b)
        zandari = sum(1 for b in boje.values() if 'J' in b)
        desetke = sum(1 for b in boje.values() if '10' in b)
        
        aduti_karte = boje.get(adut, [])
        adut_duzina = len(aduti_karte)
        ima_adut_asa = 1 if 'A' in aduti_karte else 0
        ima_adut_kralja = 1 if 'K' in aduti_karte else 0
        ima_adut_damu = 1 if 'Q' in aduti_karte else 0
        
        # Štihovi (heuristika za model)
        stihovi = 0
        for b, vrednosti in boje.items():
            d = len(vrednosti)
            if 'A' in vrednosti: stihovi += 1
            if 'K' in vrednosti and d >= 2: stihovi += 1
            if 'Q' in vrednosti and d >= 3: stihovi += 1

        duzine = sorted([len(b) for b in boje.values()], reverse=True)
        
        data = {
            "iz_ruke": iz_ruke, "kontra": kontra,
            "pocetna_duzina_aduta": adut_duzina, "pocetni_stihovi": stihovi,
            "pocetni_asovi": asovi, "pocetni_kraljevi": kraljevi, "pocetne_dame": dame,
            "pocetni_zandari": zandari, "pocetne_desetke": desetke,
            "pocetni_adut_as": ima_adut_asa, "pocetni_adut_kralj": ima_adut_kralja,
            "pocetni_adut_dama": ima_adut_damu,
            "pocetni_asovi_sa_strane": asovi - ima_adut_asa,
            "pocetni_kraljevi_sa_strane": kraljevi - ima_adut_kralja,
            "pocetna_druga_duzina": duzine[1], "pocetna_treca_duzina": duzine[2],
            "pocetni_renonsi": sum(1 for d in duzine if d == 0),
            "pocetni_singlovi": sum(1 for d in duzine if d == 1),
            "talon_asovi": 0, "talon_kraljevi": 0, "talon_aduti": 0 # U trenutku igranja ne znamo šta je u talonu
        }

        # One-Hot Encoding za Aduta i Nivo
        for adut_ime in ['Pik', 'Karo', 'Herc', 'Tref']:
            data[f"adut_{adut_ime}"] = 1 if adut == adut_ime else 0
        for lvl in [2, 3, 4, 5, 6, 7]:
            data[f"nivo_licitacije_{lvl}"] = 1 if nivo == lvl else 0

        return [[data.get(feat, 0) for feat in self.model_features]]

    def proceni_sansu(self, ruka, adut, nivo):
        """Vraća šansu od 0.0 do 1.0 koristeći predict_proba ML modela."""
        if not self.model_loaded: return 0.0
        
        X = self._ekstrakcija_featurea(ruka, adut, nivo)
        
        # Ovde gasimo sklearn upozorenje jer mu svesno dajemo brzu listu bez imena
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # predict_proba[0][1] je šansa za ishod 1 (prolaz)
            return self.model.predict_proba(X)[0][1]
  
    

    def odluci_licitaciju(self, state, moguci_potezi):
        
        if not self.model_loaded: return "dalje"
        
        najbolji_ev_moj = -9999
        najbolja_igra = None
        
        ruka = state.ruke[self.id]
        
        vrednost_igre    = {'Pik': 4, 'Karo': 6, 'Herc': 8, 'Tref': 10}
        nivo_licitacije  = {'Pik': 2, 'Karo': 3, 'Herc': 4, 'Tref': 5}
        
        for adut in ['Pik', 'Karo', 'Herc', 'Tref']:
            nivo = nivo_licitacije[adut]
            v    = vrednost_igre[adut]
            
            sansa = self.proceni_sansu(ruka, adut, nivo)
            
            nagrada = v * 10
            kazna   = (v * 10) + (v * 5)  # bula + prosečne supe pri padu
            
            # PROMENA 1: faktor_rizika = 1.0 za sve boje (flat rizik po zahtevu)
            ev_moj = (sansa * nagrada) - ((1.0 - sansa) * kazna)
            
            if ev_moj > najbolji_ev_moj:
                najbolji_ev_moj = ev_moj
                najbolja_igra   = nivo

        # PROMENA 2: ev_dalje = čisto oportunitetni trošak, bez lažnih "supe kompenzacija"
        # Formula po arhitekturi Sekcija 2C: EV_Dalje = -1 * (šansa_prot * poeni_prot)
        # Deli sa 3 jer je to naš udeo u gubitku (bula nivelacija iz scoring.py)
        trenutna_licitacija = state.trenutna_licitacija_broj
        
        if trenutna_licitacija == 0:
            v_protivnika    = 6      # pretpostavljamo prosečnu igru (Karo)
            sansa_protivnika = 0.70  # NapredniBot prođe ~70% kad licitira
        else:
            v_protivnika    = trenutna_licitacija * 2
            # PROMENA 3: procenjujemo šansu protivnika na osnovu toga što je uopšte zvao
            # Ako je zvao visoko, verovatno ima dobru ruku — konzervativno 75%
            sansa_protivnika = 0.75

        ev_dalje = -(sansa_protivnika * v_protivnika * 10) / 3.0

        # Odluka
        if najbolji_ev_moj > ev_dalje:
            sledeci = next((p for p in moguci_potezi if isinstance(p, int)), None)
            if sledeci and sledeci <= najbolja_igra:
                return sledeci
            if "moje" in moguci_potezi and state.trenutna_licitacija_broj <= najbolja_igra:
                return "moje"
                
        return "dalje"

 