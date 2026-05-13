import random
import time

# Gasimo sleep da simulacija proleti
time.sleep = lambda x: None

from engine.game_loop import GameLoop
from agents.napredni_bot import NapredniBot
from engine.game_rules import GameRules

def crtaj_kartu(karta_str, is_winner=False):
    """Generiše HTML i CSS za crtanje jedne karte."""
    v, b = karta_str.split()
    boja_klasa = "red" if b in ["Herc", "Karo"] else "black"
    simboli = {"Pik": "♠", "Karo": "♦", "Herc": "♥", "Tref": "♣"}
    
    border = "border: 3px solid #28a745; box-shadow: 0 0 5px #28a745;" if is_winner else "border: 1px solid #aaa;"
    
    return f'<div class="karta {boja_klasa}" style="{border}">{v}{simboli[b]}</div>'

def generisi_html_izvestaj(padovi, ime_fajla="padovi_izvestaj.html"):
    html = """
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #2c3e50; color: #ecf0f1; padding: 20px; }
            h1 { text-align: center; color: #e74c3c; }
            .runda { background: #ecf0f1; color: #2c3e50; border-radius: 12px; padding: 20px; margin-bottom: 40px; box-shadow: 0 8px 16px rgba(0,0,0,0.5); }
            .header { border-bottom: 2px solid #bdc3c7; padding-bottom: 10px; margin-bottom: 15px; }
            .red { color: #c0392b; }
            .black { color: #2c3e50; }
            .karta { display: inline-block; border-radius: 6px; padding: 6px 12px; margin: 3px; font-weight: bold; background: #fff; font-size: 16px; min-width: 25px; text-align: center;}
            .stihovi-grid { display: flex; flex-wrap: wrap; gap: 15px; margin-top: 20px; }
            .stih { border: 2px solid #bdc3c7; border-radius: 8px; padding: 10px; width: 45%; background: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .ruke-grid { margin-top: 20px; padding: 15px; background: #e8eaed; border-radius: 8px; }
            .bot-red { margin-bottom: 8px; }
            .info-panel { display: flex; gap: 30px; margin-top: 15px; }
            .info-box { background: #fff; padding: 15px; border-radius: 8px; border: 1px solid #bdc3c7; flex: 1; }
            .info-box h4 { margin-top: 0; color: #c0392b; border-bottom: 1px solid #ecf0f1; padding-bottom: 5px; }
            ul { margin: 0; padding-left: 20px; font-size: 14px; }
            ul li { margin-bottom: 4px; }
        </style>
    </head>
    <body>
    <h1>🔎 Lovac na Padove - Detaljna Analiza</h1>
    """
    
    if not padovi:
        html += "<h2 style='text-align:center; color:#2ecc71;'>Nema pronađenih padova! Bot je igrao savršeno.</h2>"
    
    for i, runda in enumerate(padovi):
        html += f'<div class="runda">'
        
        # --- LOGIKA IZ DISPLAY HANDLER-A ZA DETALJE IGRE ---
        nosilac_ime = f"Bot {runda['nosilac']}"
        adut = runda["adut"]
        vrednost = runda.get("vrednost", "?")
        
        tipovi = []
        if runda.get("direktna_igra"): tipovi.append("iz ruke")
        else: tipovi.append("sa talonom")

        if runda.get("kontra"):
            z_igrac = runda.get("zvanje_igrac")
            if z_igrac is not None: tipovi.append(f"kontra: Bot {z_igrac}")
            else: tipovi.append("kontra")

        if runda.get("zvanje_tip") == "zovem":
            z_igrac = runda.get("zvanje_igrac")
            tipovi.append(f"zovem: Bot {z_igrac}")

        dodatak = ", ".join(tipovi)
        igra_puna = f"{adut} ({dodatak})"
        
        stihovi = runda.get("stihovi_po_igracu", {})
        stih_txt = f"Bot 0: {stihovi.get(0, 0)} | Bot 1: {stihovi.get(1, 0)} | Bot 2: {stihovi.get(2, 0)}"
        
        rezultat = runda.get("rezultat", {})
        rez_txt = "<br>".join([f"Bot {pid}: {rez}" for pid, rez in rezultat.items() if "Pao" in rez or "Prošao" in rez])
        # --------------------------------------------------

        # HEADER I INFO PANELI
        html += f'<div class="header">'
        html += f'<h2>Pad #{i+1} | {runda["razlog_pada"]}</h2>'
        html += f'</div>'
        
        html += '<div class="info-panel">'
        
        # Leva kutija: Istorija Licitacije
        istorija = runda.get("istorija_licitacije", ["Istorija nije sačuvana u game_loop.py!"])
        html += '<div class="info-box"><h4>Istorija Licitacije</h4><ul>'
        for stavka in istorija:
            # Ulepšajmo prikaz: ako je nosilac pao na boju, da znamo kako
            stavka = stavka.replace("Ja:", "Bot 0:")
            html += f'<li>{stavka}</li>'
        html += '</ul></div>'
        
        # Desna kutija: Detalji runde
        html += f'<div class="info-box"><h4>Rezultat i Detalji</h4>'
        html += f'<p><strong>Nosilac:</strong> {nosilac_ime}</p>'
        html += f'<p><strong>Igra:</strong> {igra_puna}</p>'
        html += f'<p><strong>Vrednost:</strong> {vrednost}</p>'
        html += f'<p class="red"><strong>Štihovi:</strong> {stih_txt}</p>'
        html += f'<p style="margin-top:15px; border-top:1px solid #ecf0f1; padding-top:10px;"><strong>Promene:</strong><br>{rez_txt}</p>'
        html += '</div>'
        
        html += '</div>' # Kraj info-panela
        
        # POČETNE KARTE I TALON
        html += '<div class="ruke-grid"><h4>Početne karte igrača i Talon:</h4>'
        for pid in range(3):
            html += f'<div class="bot-red"><strong>Bot {pid}:</strong> '
            # Sortiramo ih po tvom algoritmu (Pik, Karo, Tref, Herc) radi lakšeg čitanja
            red_boja = {'Pik': 0, 'Karo': 1, 'Tref': 2, 'Herc': 3}
            red_vrednosti = {'A': 0, 'K': 1, 'Q': 2, 'J': 3, '10': 4, '9': 5, '8': 6, '7': 7}
            ruka_sort = sorted(runda["pocetne_ruke"][pid], key=lambda k: (red_boja[k.split()[1]], red_vrednosti[k.split()[0]]))
            for k in ruka_sort:
                html += crtaj_kartu(k)
            html += '</div>'
        
        html += f'<div class="bot-red" style="margin-top:10px;"><strong>Talon:</strong> '
        for k in runda["pocetni_talon"]:
            html += crtaj_kartu(k)
        html += '</div></div>'
        
        # ŠTIHOVI (Sa pobednicima)
        html += '<div class="stihovi-grid">'
        for stih in runda["stihovi"]:
            stih_lista = stih["karte"]
            pobednik_id = stih["pobednik"]
            
            html += f'<div class="stih"><strong style="color:#7f8c8d;">Štih {stih["broj"]}</strong><br><br>'
            for index, (pid, karta) in enumerate(stih_lista):
                is_win = (pid == pobednik_id)
                strelica = " ➔ " if index < len(stih_lista) - 1 else ""
                html += f'<span style="font-size:14px; color:#7f8c8d;">B{pid}:</span> {crtaj_kartu(karta, is_win)}{strelica}'
            html += '</div>'
        
        html += '</div></div>' # Kraj stihova i runde
        
    html += "</body></html>"
    
    with open(ime_fajla, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n[USPEH] Izveštaj je sačuvan! Otvorite '{ime_fajla}' u web pregledaču.")

def pokreni_lov(broj_rundi=200):
    print(f"Pokrećem engine. Tražim greške Naprednog bota u {broj_rundi} rundi...")
    padovi = []
    
    for iteracija in range(broj_rundi):
        agenti = [NapredniBot(0, "Bot 0"), NapredniBot(1, "Bot 1"), NapredniBot(2, "Bot 2")]
        engine = GameLoop(agents=agenti, seed=random.randint(1, 100000))
        engine.play_round()
        
        if not engine.zavrsene_runde: 
            continue
            
        runda = engine.zavrsene_runde[0]
        neko_pao = False
        razlog = ""
        
        for pid, rez in runda["rezultat"].items():
            if "Pao" in rez:
                if pid == runda["nosilac"]:
                    neko_pao = True
                    razlog = f"Glavni Pad: Bot {pid} je pao kao Nosilac! (Uzeo {runda['stihovi_po_igracu'].get(pid,0)} štihova)"
                elif runda.get("zvanje_igrac") == pid:
                    neko_pao = True
                    razlog = f"Agresivan Pad: Bot {pid} je pao jer je zvao '{runda['zvanje_tip']}'!"
                    
        if neko_pao:
            runda["razlog_pada"] = razlog
            padovi.append(runda)
            
    print(f"Pronađeno {len(padovi)} padova. Generišem vizuelizaciju...")
    generisi_html_izvestaj(padovi)

if __name__ == "__main__":
    pokreni_lov(200)