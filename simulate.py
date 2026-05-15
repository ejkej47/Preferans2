import time
import multiprocessing
from tabulate import tabulate
from engine.game_loop import GameLoop
from agents.napredni_bot import NapredniBot
from agents.ml_bot import MLBot

# --- PODEŠAVANJA ---
BROJ_RUNDI = 5000  
MAX_PROCESA = multiprocessing.cpu_count()

def worker_simulacija(seed):
    """Izvršava jednu rundu i vraća detaljne statistike sa ekonomijom."""
    agenti = [
        MLBot(0, "ML Oracle"),
        NapredniBot(1, "Napredni_1"),
        NapredniBot(2, "Napredni_2")
    ]
    
    time.sleep = lambda x: None
    
    engine = GameLoop(agents=agenti, seed=seed)
    engine.play_round()
    
    if not engine.zavrsene_runde:
        return None
        
    runda = engine.zavrsene_runde[0]
    if runda.get("is_refa"): return "REFA"
    
    nosilac = runda["nosilac"]
    finalni_skorovi = engine.scoring.izracunaj_finalni_skor()
    
    stats = []
    for i in range(3):
        is_nosilac = (i == nosilac)
        
        # Logika Nosioca
        nosilac_prosao = 1 if is_nosilac and "Prošao" in runda["rezultat"][i] else 0
        nosilac_pao = 1 if is_nosilac and "Pao" in runda["rezultat"][i] else 0
        
        # OVO JE POPRAVLJENO: Logika Pratioca
        pratio = 1 if not is_nosilac and bool(engine.state.igraci_koji_dolaze.get(i)) else 0
        pratilac_prosao = 1 if pratio and "Prošao" in runda["rezultat"][i] else 0
        pratilac_pao = 1 if pratio and "Pao" in runda["rezultat"][i] else 0
        
        # Ekonomija (samo za ovu rundu, pošto je GameLoop uvek svež)
        bula_diff = engine.scoring.bula[i] - 60  # Minus je dobro (spustio se), Plus je loše (pao)
        supe_date = sum(engine.scoring.supe[i].values())
        supe_primljene = sum(engine.scoring.supe[p][i] for p in range(3) if p != i)
        
        stats.append({
            "id": i,
            "nosilac": 1 if is_nosilac else 0,
            "n_prosao": nosilac_prosao,
            "pratio": pratio,
            "p_prosao": pratilac_prosao,
            "neto_skor": finalni_skorovi[i],
            "bula_diff": bula_diff,
            "supe_date": supe_date,
            "supe_prim": supe_primljene,
            "lic_nivo": runda["vrednost"] if is_nosilac else 0
        })
    return stats

def pokreni_test():
    print(f"🚀 Duel: 1x ML Oracle vs 2x Napredni Bot ({BROJ_RUNDI} rundi)")
    
    gs = {i: {
        "score": 0, "n_count": 0, "n_win": 0, "n_net": 0, 
        "p_count": 0, "p_win": 0, "p_net": 0, "tudjih_igara": 0,
        "bula_neto": 0, "supe_date": 0, "supe_prim": 0
    } for i in range(3)}
    
    refas = 0
    start = time.time()

    with multiprocessing.Pool(MAX_PROCESA) as pool:
        for i, r in enumerate(pool.imap_unordered(worker_simulacija, range(BROJ_RUNDI), chunksize=50)):
            if r == "REFA": 
                refas += 1
            elif r: 
                for p in r:
                    pid = p["id"]
                    gs[pid]["score"] += p["neto_skor"]
                    gs[pid]["bula_neto"] += p["bula_diff"]
                    gs[pid]["supe_date"] += p["supe_date"]
                    gs[pid]["supe_prim"] += p["supe_prim"]
                    
                    if p["nosilac"]:
                        gs[pid]["n_count"] += 1
                        gs[pid]["n_win"] += p["n_prosao"]
                        gs[pid]["n_net"] += p["neto_skor"]
                    else:
                        gs[pid]["tudjih_igara"] += 1
                        gs[pid]["p_count"] += p["pratio"]
                        gs[pid]["p_win"] += p["p_prosao"]
                        gs[pid]["p_net"] += p["neto_skor"]
            
            if i % 10 == 0 or i == BROJ_RUNDI - 1:
                procenat = ((i + 1) / BROJ_RUNDI) * 100
                bar = "█" * int(procenat / 4) + "-" * (25 - int(procenat / 4))
                print(f"\r|{bar}| {procenat:.1f}% ({i+1}/{BROJ_RUNDI})", end="", flush=True)

    print("\n")
    ispisi_izvestaj(gs, refas, time.time() - start)

def ispisi_izvestaj(gs, refe, duration):
    validne = BROJ_RUNDI - refe
    imena = {0: "ML Oracle", 1: "Napredni 1", 2: "Napredni 2"}
    
    # Prva tabela: Osnovna statistika
    h_main = ["Bot", "Total Score", "Lic. %", "Nosilac WR%", "Pratnja %", "Pratnja WR%", "Net/Nos", "Net/Prat"]
    rows_main = []
    
    # Druga tabela: Detaljna Ekonomija
    h_econ = ["Bot", "Bula Neto", "Supe Date (Drugima)", "Supe Primljene"]
    rows_econ = []
    
    for i in range(3):
        n = gs[i]["n_count"]
        p_rounds = gs[i]["tudjih_igara"]
        
        lic_proc = (n / validne) * 100 if validne > 0 else 0
        n_wr = (gs[i]["n_win"] / n * 100) if n > 0 else 0
        
        prat_proc = (gs[i]["p_count"] / p_rounds * 100) if p_rounds > 0 else 0
        p_wr = (gs[i]["p_win"] / gs[i]["p_count"] * 100) if gs[i]["p_count"] > 0 else 0
        
        avg_nos = (gs[i]["n_net"] / n) if n > 0 else 0
        avg_prat = (gs[i]["p_net"] / gs[i]["p_count"]) if gs[i]["p_count"] > 0 else 0
        
        rows_main.append([
            imena[i], f"{gs[i]['score']:,}", f"{lic_proc:.1f}%", f"{n_wr:.1f}%",
            f"{prat_proc:.1f}%", f"{p_wr:.1f}%", f"{avg_nos:+.1f}", f"{avg_prat:+.1f}"
        ])
        
        # Bula neto: Minus je dobar u preferansu, stavljamo ga ovako da bude jasno
        rows_econ.append([
            imena[i], f"{gs[i]['bula_neto']:+}", f"{gs[i]['supe_date']:,}", f"{gs[i]['supe_prim']:,}"
        ])

    print("\n" + "="*95)
    print(f" GLAVNA STATISTIKA (Trajanje: {duration:.2f}s | Refe: {refe} | Odigrano: {validne})")
    print("="*95)
    print(tabulate(rows_main, headers=h_main, tablefmt="grid"))
    
    print("\n" + "="*56)
    print(" EKONOMIJA BOTOVA (Bule i Supe)")
    print("="*56)
    print(tabulate(rows_econ, headers=h_econ, tablefmt="grid"))
    print("="*56)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    pokreni_test()