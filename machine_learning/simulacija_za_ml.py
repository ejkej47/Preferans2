import csv
import os
import sys
import time
import multiprocessing

# --- Povezivanje sa glavnim folderom ---
trenutni_folder = os.path.dirname(os.path.abspath(__file__))
glavni_folder = os.path.dirname(trenutni_folder)
sys.path.append(glavni_folder)

# Gasimo sleep za maksimalnu brzinu
time.sleep = lambda x: None 

from engine.game_loop import GameLoop
from agents.napredni_bot import NapredniBot

DEFAULT_CSV = os.path.join(trenutni_folder, "preferans_ml_data.csv")

def simuliraj_jednu_rundu(_):
    try:
        agenti = [NapredniBot(j) for j in range(3)]
        engine = GameLoop(agents=agenti)
        engine.play_round() 
        
        if not engine.zavrsene_runde:
            return None
            
        runda = engine.zavrsene_runde[0] 
        nosilac_id = runda["nosilac"]
        ishod_nosilac = 1 if "Prošao" in runda["rezultat"][nosilac_id] else 0 
        skorovi = engine.scoring.izracunaj_finalni_skor()
        neto_nosilac = skorovi[nosilac_id]
        
        # --- ULTIMATIVNA EKSTRAKCIJA PODATAKA ---
        def get_stats(ruka, adut):
            boje = {'Pik': [], 'Karo': [], 'Herc': [], 'Tref': []}
            for k in ruka:
                v, b = k.split()
                boje[b].append(v)
                
            asovi = sum(1 for b in boje.values() if 'A' in b)
            kraljevi = sum(1 for b in boje.values() if 'K' in b)
            dame = sum(1 for b in boje.values() if 'Q' in b)
            zandari = sum(1 for b in boje.values() if 'J' in b)
            desetke = sum(1 for b in boje.values() if '10' in b)
            
            # Detaljna analiza Aduta
            aduti_karte = boje.get(adut, [])
            adut_duzina = len(aduti_karte)
            ima_adut_asa = 1 if 'A' in aduti_karte else 0
            ima_adut_kralja = 1 if 'K' in aduti_karte else 0
            ima_adut_damu = 1 if 'Q' in aduti_karte else 0
            
            # Snaga isključivo sa strane (van aduta)
            asovi_sa_strane = asovi - ima_adut_asa
            kraljevi_sa_strane = kraljevi - ima_adut_kralja
            
            # Savršen oblik ruke (Shape)
            duzine_boja = sorted([len(b) for b in boje.values()], reverse=True)
            druga_duzina = duzine_boja[1] if len(duzine_boja) > 1 else 0
            treca_duzina = duzine_boja[2] if len(duzine_boja) > 2 else 0
            broj_renonsa = sum(1 for d in duzine_boja if d == 0)
            broj_singlova = sum(1 for d in duzine_boja if d == 1)
            
            # Kafanski štihovi (Kao dodatna heuristika modelu)
            stihovi = 0
            for b, vrednosti in boje.items():
                d = len(vrednosti)
                if 'A' in vrednosti: stihovi += 1
                if 'K' in vrednosti and d >= 2: stihovi += 1
                if 'Q' in vrednosti and d >= 3: stihovi += 1
                
            return {
                "asovi": asovi, "kraljevi": kraljevi, "dame": dame, "zandari": zandari, "desetke": desetke,
                "adut_duzina": adut_duzina, 
                "ima_adut_asa": ima_adut_asa, "ima_adut_kralja": ima_adut_kralja, "ima_adut_damu": ima_adut_damu,
                "asovi_sa_strane": asovi_sa_strane, "kraljevi_sa_strane": kraljevi_sa_strane,
                "stihovi": stihovi, 
                "druga_duzina": druga_duzina, "treca_duzina": treca_duzina,
                "broj_renonsa": broj_renonsa, "broj_singlova": broj_singlova
            }

        p_stats = get_stats(runda["pocetne_ruke"][nosilac_id], runda["adut"])
        t_stats = get_stats(runda["pocetni_talon"], runda["adut"])
        
        return {
            "igrac_id": nosilac_id,
            "uloga": "nosilac",
            "nivo_licitacije": runda["vrednost"],
            "adut": runda["adut"],
            "iz_ruke": 1 if runda["direktna_igra"] else 0,
            "kontra": 1 if runda["kontra"] else 0,
            
            # Bogati podaci o ruci
            "pocetni_asovi": p_stats["asovi"],
            "pocetni_kraljevi": p_stats["kraljevi"],
            "pocetne_dame": p_stats["dame"],
            "pocetni_zandari": p_stats["zandari"],
            "pocetne_desetke": p_stats["desetke"],
            "pocetni_stihovi": p_stats["stihovi"],
            
            # Detalji o Adutu
            "pocetna_duzina_aduta": p_stats["adut_duzina"],
            "pocetni_adut_as": p_stats["ima_adut_asa"],
            "pocetni_adut_kralj": p_stats["ima_adut_kralja"],
            "pocetni_adut_dama": p_stats["ima_adut_damu"],
            
            # Detalji o ne-adut bojama
            "pocetni_asovi_sa_strane": p_stats["asovi_sa_strane"],
            "pocetni_kraljevi_sa_strane": p_stats["kraljevi_sa_strane"],
            
            # Oblik (Shape)
            "pocetna_druga_duzina": p_stats["druga_duzina"],
            "pocetna_treca_duzina": p_stats["treca_duzina"],
            "pocetni_renonsi": p_stats["broj_renonsa"],
            "pocetni_singlovi": p_stats["broj_singlova"],
            
            # Talon podaci
            "talon_asovi": t_stats["asovi"],
            "talon_kraljevi": t_stats["kraljevi"],
            "talon_aduti": t_stats["adut_duzina"],
            
            "zvanje_tip": runda["zvanje_tip"] if runda["zvanje_tip"] else "nista",
            "osvojeni_stihovi": runda["stihovi_po_igracu"].get(nosilac_id, 0),
            "neto_nosilac": neto_nosilac,
            "ishod": ishod_nosilac
        }
    except Exception as e:
        return None

def pokreni_turbo_simulaciju(broj_rundi=10000, fajl=DEFAULT_CSV):
    print(f"🚀 Pokrećem PARALELNU simulaciju {broj_rundi} rundi...")
    start_time = time.time()
    
    # SVA NOVA POLJA
    polja = [
        "igrac_id", "uloga", "nivo_licitacije", "adut", "iz_ruke", "kontra",
        "pocetni_asovi", "pocetni_kraljevi", "pocetne_dame", "pocetni_zandari", "pocetne_desetke",
        "pocetni_stihovi", "pocetna_duzina_aduta", 
        "pocetni_adut_as", "pocetni_adut_kralj", "pocetni_adut_dama",
        "pocetni_asovi_sa_strane", "pocetni_kraljevi_sa_strane",
        "pocetna_druga_duzina", "pocetna_treca_duzina", 
        "pocetni_renonsi", "pocetni_singlovi",
        "talon_asovi", "talon_kraljevi", "talon_aduti", 
        "zvanje_tip", "osvojeni_stihovi","neto_nosilac", "ishod"
    ]
    
    # BRISANJE STAROG FAJLA AKO POSTOJI ZBOG NOVIH KOLONA
    if os.path.isfile(fajl):
        os.remove(fajl)
        print(f"🗑️ Obrisao sam stari CSV fajl jer smo uveli masivne nove podatke.")
        
    with open(fajl, "w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=polja).writeheader()

    with multiprocessing.Pool() as pool:
        rezultati = []
        for i, res in enumerate(pool.imap_unordered(simuliraj_jednu_rundu, range(broj_rundi), chunksize=10)):
            if res:
                rezultati.append(res)
            
            if i % 50 == 0 or i == broj_rundi - 1:
                procenat = ((i + 1) / broj_rundi) * 100
                bar = "█" * int(procenat / 4) + "-" * (25 - int(procenat / 4))
                print(f"\r|{bar}| {procenat:.1f}% ({i+1}/{broj_rundi})", end="", flush=True)

        print("\n\n💾 Snimam podatke u CSV...")
        with open(fajl, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=polja)
            writer.writerows(rezultati)

    total_time = time.time() - start_time
    print(f"✅ Završeno za {total_time:.2f}s! Ukupno prikupljeno {len(rezultati)} zapisa.")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    pokreni_turbo_simulaciju(100000)