# agents/heuristic_bot.py

import random
from .base_agent import BaseAgent
from engine.game_rules import GameRules

class HeuristicBot(BaseAgent):
    def __init__(self, agent_id, ime="Kafanski Bot"):
        super().__init__(agent_id, ime)
        self.vrednosti = {'7': 0, '8': 1, '9': 2, '10': 3, 'J': 4, 'Q': 5, 'K': 6, 'A': 7}

    def _karta_vrednost(self, karta):
        """Pomoćna metoda za sortiranje po jačini"""
        v = karta.split()[0]
        return self.vrednosti[v]

    def odluci_licitaciju(self, state, moguci_potezi):
        ruka = state.ruke[self.id]
        broj_asa = sum(1 for k in ruka if k.startswith("A"))
        max_limit = 2 + broj_asa
        
        trenutni_broj = state.trenutna_licitacija_broj

        # 1. Ako je "moje" jedina numerička opcija i imamo snage
        if "moje" in moguci_potezi:
            if trenutni_broj <= max_limit:
                return "moje"
            return "dalje"

        # 2. Ako treba da licitiramo novi broj (npr. početak ili nakon "moje")
        sledeci_broj = next((p for p in moguci_potezi if isinstance(p, int)), None)
        if sledeci_broj:
            if sledeci_broj <= max_limit:
                return sledeci_broj
            return "dalje"

        # 3. Specijalne igre (ako su dozvoljene)
        if "sans" in moguci_potezi and broj_asa >= 3: return "sans"
        if "betl" in moguci_potezi and broj_asa >= 2: return "betl"
        if "igra" in moguci_potezi and broj_asa >= 1: return "igra"

        return "dalje"

    def odluci_igru_iz_ruke(self, state):
        ruka = state.ruke[self.id]
        broj_asa = sum(1 for k in ruka if k.startswith("A"))
        
        if broj_asa >= 3: return "sans"
        if broj_asa >= 2: return "betl"
        if broj_asa >= 1: return "igra"
        return "dalje"

    def najavi_igru(self, state):
        """Bot najavljuje nivo na osnovu broja asova"""
        # Ako bot uopšte nije u licitaciji, ne treba da najavljuje ništa
        if self.id not in state.aktivni_u_licitaciji:
            return None
            
        ruka = state.ruke[self.id]
        asa = sum(1 for k in ruka if k.startswith("A"))
        moj_nivo = min(2 + asa, 5)
        
        # Ako je neko već najavio više, bot kaže dalje
        trenutni_max = max(state.igra_dekleresi.values()) if state.igra_dekleresi else 0
        if moj_nivo > trenutni_max:
            return moj_nivo
            
        return None

    def skartiraj(self, state):
        ruka = state.ruke[self.id]
        # Sortira karte od najslabije do najjače i izbaci dve najslabije
        sortirana = sorted(ruka, key=self._karta_vrednost)
        return sortirana[:2]

    def izaberi_aduta(self, state, validne_boje):
        ruka = state.ruke[self.id]
        brojac_boja = {boja: sum(1 for k in ruka if k.split()[1] == boja) for boja in validne_boje if boja not in ["Sans", "Betl"]}
        
        if not brojac_boja: 
            return "Sans" # Fallback
            
        # Vraća boju koje ima najviše u ruci
        return max(brojac_boja, key=brojac_boja.get)

    def odluci_pratnju(self, state):
        ruka = state.ruke[self.id]
        adut = state.adut
        
        adut_karte = sum(1 for k in ruka if k.split()[1] == adut) if adut not in ("Betl", "Sans") else 0
        # Bot prati ako ima bar 2 aduta ili dugačku boju
        return adut_karte >= 2 or len(ruka) >= 8

    def odluci_kontru(self, state):
        ruka = state.ruke[self.id]
        broj_asa = sum(1 for k in ruka if k.startswith("A"))
        if broj_asa >= 2:
            return "kontra"
        return "moze"

    def odigraj_kartu(self, state, validne_karte):
        if len(validne_karte) == 1:
            return validne_karte[0]

        na_stolu = state.karte_na_stolu
        nosilac_igre = state.pobednik_licitacije

        # 1. Prvi sam na potezu
        if not na_stolu:
            # Ako sam nosilac, vučem najjače. Ako nisam, vučem najmanju (da ne trošim adute)
            if self.id == nosilac_igre:
                return max(validne_karte, key=self._karta_vrednost)
            else:
                return min(validne_karte, key=self._karta_vrednost)

        # 2. Neko je već igrao
        trenutni_pobednik = GameRules.ko_nosi_odnetak(na_stolu, state.adut)

        # Ako moj partner nosi štih, nema potrebe da se trošim -> dajem najmanju
        if trenutni_pobednik != nosilac_igre and self.id != nosilac_igre:
            return min(validne_karte, key=self._karta_vrednost)

        # U suprotnom (nosilac trenutno nosi, ili sam ja nosilac a neko drugi vodi)
        # pokušavam da preotmem bacanjem najjače karte (ili forsiram nosioca da seče)
        return max(validne_karte, key=self._karta_vrednost)