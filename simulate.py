import random
import time
import os
import concurrent.futures

# Gasimo sleep za brzinu (biće primenjeno na sve worker procese prilikom importa)
time.sleep = lambda x: None 

from engine.game_loop import GameLoop
from agents.heuristic_bot import HeuristicBot
from agents.napredni_bot import NapredniBot
from agents.pimc_bot import PimcBot

def analiziraj_ruku_za_statistiku(ruka, adut):
    aduti_count = asovi = drugi_kraljevi = trece_dame = 0
    karte_po_bojama = {'Pik': [], 'Karo': [], 'Herc': [], 'Tref': []}
    
    for k in ruka: karte_po_bojama[k.split()[1]].append(k.split()[0])
    if adut not in ["Betl", "Sans"]: aduti_count = len(karte_po_bojama.get(adut, []))
        
    for boja, vrednosti in karte_po_bojama.items():
        duzina = len(vrednosti)
        if 'A' in vrednosti: asovi += 1
        if 'K' in vrednosti and duzina >= 2: drugi_kraljevi += 1
        if 'Q' in vrednosti and duzina >= 3: trece_dame += 1
        
    return aduti_count, asovi, drugi_kraljevi, trece_dame

def dodaj_statistiku(target_dict, aduti, asovi, kraljevi, dame):
    target_dict["aduti"] += aduti; target_dict["asovi"] += asovi
    target_dict["kraljevi"] += kraljevi; target_dict["dame"] += dame

def _init_stats():
    """Kreira prazan rečnik za statistiku kako bi svaki proces imao svoj."""
    stats = {}
    for bot_id in range(1, 4):
        stats[bot_id] = {
            "skor": 0, "supe_zbir": 0,
            "nosilac": {"prosao": 0, "pao": 0, "prosao_stats": {"aduti": 0, "asovi": 0, "kraljevi": 0, "dame": 0}, "pao_stats": {"aduti": 0, "asovi": 0, "kraljevi": 0, "dame": 0}},
            "pratilac": {"igrao": 0, "prosao": 0, "pao": 0, "prosao_stats": {"aduti": 0, "asovi": 0, "kraljevi": 0, "dame": 0}, "pao_stats": {"aduti": 0, "asovi": 0, "kraljevi": 0, "dame": 0}},
            "zvanje": {"zovem_igrao": 0, "zovem_pao": 0, "kontra_igrao": 0, "kontra_pao": 0}
        }
    return stats

def _spoji_statistike(glavna, lokalna):
    """Spaja lokalnu statistiku iz workera u glavnu statistiku."""
    for bid in range(1, 4):
        glavna[bid]["skor"] += lokalna[bid]["skor"]
        glavna[bid]["supe_zbir"] += lokalna[bid]["supe_zbir"]
        
        # Nosilac
        for k in ["prosao", "pao"]:
            glavna[bid]["nosilac"][k] += lokalna[bid]["nosilac"][k]
        for k in ["aduti", "asovi", "kraljevi", "dame"]:
            glavna[bid]["nosilac"]["prosao_stats"][k] += lokalna[bid]["nosilac"]["prosao_stats"][k]
            glavna[bid]["nosilac"]["pao_stats"][k] += lokalna[bid]["nosilac"]["pao_stats"][k]
            
        # Pratilac
        for k in ["igrao", "prosao", "pao"]:
            glavna[bid]["pratilac"][k] += lokalna[bid]["pratilac"][k]
        for k in ["aduti", "asovi", "kraljevi", "dame"]:
            glavna[bid]["pratilac"]["prosao_stats"][k] += lokalna[bid]["pratilac"]["prosao_stats"][k]
            glavna[bid]["pratilac"]["pao_stats"][k] += lokalna[bid]["pratilac"]["pao_stats"][k]
            
        # Zvanje
        for k in ["zovem_igrao", "zovem_pao", "kontra_igrao", "kontra_pao"]:
            glavna[bid]["zvanje"][k] += lokalna[bid]["zvanje"][k]

def simuliraj_iteraciju(seed):
    """Worker funkcija koja se izvršava na zasebnom jezgru za jedan random seed."""
    local_stats = _init_stats()
    odigrane_runde_lokalno = 0
    rotacije = [(1, 2, 3), (3, 1, 2), (2, 3, 1)]

    for rotacija in rotacije:
        agenti = [NapredniBot(seat, f"PBot {bid}") if bid == 1 else NapredniBot(seat, f"Bot {bid}") for seat, bid in enumerate(rotacija)]
        seat_to_bot = {s: b for s, b in enumerate(rotacija)}
        
        engine = GameLoop(agents=agenti, seed=seed)
        engine.play_round()
        
        if not engine.zavrsene_runde: continue
            
        odigrane_runde_lokalno += 1
        runda = engine.zavrsene_runde[0]
        skorovi = engine.scoring.izracunaj_finalni_skor() 
        
        for seat, rez in runda["rezultat"].items():
            bid = seat_to_bot[seat]
            local_stats[bid]["skor"] += skorovi[seat]
            
            levo = (seat + 1) % 3; desno = (seat + 2) % 3
            moje_supe = runda["scoring_snapshot"]["supe"][seat][levo] + runda["scoring_snapshot"]["supe"][seat][desno]
            local_stats[bid]["supe_zbir"] += moje_supe
            
            aduti, asovi, kr, dm = analiziraj_ruku_za_statistiku(runda["pocetne_ruke"][seat], runda["adut"])
            
            if seat == runda["nosilac"]:
                if "Prošao" in rez: 
                    local_stats[bid]["nosilac"]["prosao"] += 1; dodaj_statistiku(local_stats[bid]["nosilac"]["prosao_stats"], aduti, asovi, kr, dm)
                elif "Pao" in rez: 
                    local_stats[bid]["nosilac"]["pao"] += 1; dodaj_statistiku(local_stats[bid]["nosilac"]["pao_stats"], aduti, asovi, kr, dm)
            else:
                if "Prošao" in rez or "Pao" in rez: 
                    local_stats[bid]["pratilac"]["igrao"] += 1
                    if "Prošao" in rez: 
                        local_stats[bid]["pratilac"]["prosao"] += 1; dodaj_statistiku(local_stats[bid]["pratilac"]["prosao_stats"], aduti, asovi, kr, dm)
                    elif "Pao" in rez: 
                        local_stats[bid]["pratilac"]["pao"] += 1; dodaj_statistiku(local_stats[bid]["pratilac"]["pao_stats"], aduti, asovi, kr, dm)

            if seat == runda["zvanje_igrac"]:
                if runda["zvanje_tip"] == "zovem":
                    local_stats[bid]["zvanje"]["zovem_igrao"] += 1
                    if "Pao" in rez: local_stats[bid]["zvanje"]["zovem_pao"] += 1
                elif runda["zvanje_tip"] == "kontra":
                    local_stats[bid]["zvanje"]["kontra_igrao"] += 1
                    if "Pao" in rez: local_stats[bid]["zvanje"]["kontra_pao"] += 1

    return local_stats, odigrane_runde_lokalno

def pokreni_simulaciju(broj_rundi=1000):
    print(f"Pokrećem Paralelnu Simulaciju za {broj_rundi} rundi (ukupno {broj_rundi * 3} mečeva)...\n")
    
    global_stats = _init_stats()
    ukupno_odigrano = 0
    seeds = [random.randint(1, 1000000) for _ in range(broj_rundi)]

    pocetno_vreme = time.time()
    
    # Korišćenje svih dostupnih jezgara procesora za paralelno procesuiranje
    max_workers = os.cpu_count() or 4
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Mapiranje seeds niza na našu simulacionu funkciju
        rezultati = executor.map(simuliraj_iteraciju, seeds)
        
        # Prikupi i spoji rezultate iz svih thread-ova
        for lokalna_stat, odigrane in rezultati:
            _spoji_statistike(global_stats, lokalna_stat)
            ukupno_odigrano += odigrane

    zavrsno_vreme = time.time()
    print(f"Završeno za {zavrsno_vreme - pocetno_vreme:.2f} sekundi na {max_workers} jezgara.\n")
    _ispisi_rezultate(global_stats, ukupno_odigrano)

def _ispisi_rezultate(stats, odigrane_runde):
    print("="*105)
    print(f"{'GLAVNA STATISTIKA (Ukupno odigrano ruku: '+str(odigrane_runde)+')':^105}")
    print("="*105)
    print(f"{'BOT':<6} | {'SKOR':<6} | {'SUPE':<6} | {'NOSILAC (P/P/WR%)':<21} | {'PRATNJA (I/P/Fail%)':<21} | {'ZOVEM (I/P)':<13} | {'KONTRA (I/P)'}")
    print("-" * 105)
    
    for b in range(1, 4):
        s = stats[b]
        n_p, n_f = s["nosilac"]["prosao"], s["nosilac"]["pao"]; n_w = (n_p/(n_p+n_f)*100) if (n_p+n_f)>0 else 0
        pr_i, pr_f = s["pratilac"]["igrao"], s["pratilac"]["pao"]; pr_w = (pr_f/pr_i*100) if pr_i>0 else 0
        z_i, z_f = s["zvanje"]["zovem_igrao"], s["zvanje"]["zovem_pao"]
        k_i, k_f = s["zvanje"]["kontra_igrao"], s["zvanje"]["kontra_pao"]
        
        print(f"Bot {b:<2} | {s['skor']:<6} | {s['supe_zbir']:<6} | {f'{n_p}/{n_f} ({n_w:.1f}%)':<21} | {f'{pr_i}/{pr_f} ({pr_w:.1f}%)':<21} | {f'{z_i}/{z_f}':<13} | {f'{k_i}/{k_f}'}")
    print("="*105)

if __name__ == "__main__":
    pokreni_simulaciju(1500)