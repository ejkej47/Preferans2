import random
from .napredni_bot import NapredniBot
from engine.game_rules import GameRules

class PimcBot(NapredniBot):
    def __init__(self, agent_id, ime="PIMC Bot"):
        super().__init__(agent_id, ime)
        self.memo = {}

    def _daj_validne(self, ruka, na_stolu, adut):
        """Ultra-brza provera legalnih karata za Minimax stablo"""
        if not na_stolu: return list(ruka)
        prva_boja = na_stolu[0][1].split()[1]
        boja = [k for k in ruka if k.split()[1] == prva_boja]
        if boja: return boja
        
        if adut not in ["Betl", "Sans"]:
            aduti = [k for k in ruka if k.split()[1] == adut]
            if aduti: return aduti
            
        return list(ruka)

    def _minimax(self, ruke, na_stolu, na_potezu, nosilac, adut, alpha, beta):
        # 1. Provera kraja (nema više karata)
        if not ruke[na_potezu]:
            return 0

        # 2. Keširanje (Transposition Table - ubrzava algoritam 100x)
        state_key = (ruke[0], ruke[1], ruke[2], tuple(na_stolu), na_potezu)
        if state_key in self.memo:
            return self.memo[state_key]

        validne = self._daj_validne(ruke[na_potezu], na_stolu, adut)
        is_nosilac = (na_potezu == nosilac)

        # NOSILAC MAKSIMIZUJE SVOJ SKOR
        if is_nosilac:
            best_val = -1
            for karta in validne:
                novi_sto = list(na_stolu) + [(na_potezu, karta)]
                nova_ruka = tuple(k for k in ruke[na_potezu] if k != karta)
                nove_ruke = {p: (nova_ruka if p == na_potezu else ruke[p]) for p in range(3)}
                
                if len(novi_sto) == 3:
                    pobednik = GameRules.ko_nosi_odnetak(novi_sto, adut)
                    bod = 1 if pobednik == nosilac else 0
                    val = bod + self._minimax(nove_ruke, [], pobednik, nosilac, adut, alpha, beta)
                else:
                    val = self._minimax(nove_ruke, novi_sto, (na_potezu + 1) % 3, nosilac, adut, alpha, beta)

                best_val = max(best_val, val)
                alpha = max(alpha, best_val)
                if beta <= alpha: break # Alfa-Beta seča
                
            self.memo[state_key] = best_val
            return best_val
            
        # PRATIOCI MINIMIZUJU SKOR NOSIOCA (Saradjuju!)
        else:
            best_val = 99
            for karta in validne:
                novi_sto = list(na_stolu) + [(na_potezu, karta)]
                nova_ruka = tuple(k for k in ruke[na_potezu] if k != karta)
                nove_ruke = {p: (nova_ruka if p == na_potezu else ruke[p]) for p in range(3)}
                
                if len(novi_sto) == 3:
                    pobednik = GameRules.ko_nosi_odnetak(novi_sto, adut)
                    bod = 1 if pobednik == nosilac else 0
                    val = bod + self._minimax(nove_ruke, [], pobednik, nosilac, adut, alpha, beta)
                else:
                    val = self._minimax(nove_ruke, novi_sto, (na_potezu + 1) % 3, nosilac, adut, alpha, beta)

                best_val = min(best_val, val)
                beta = min(beta, best_val)
                if beta <= alpha: break # Alfa-Beta seča
                
            self.memo[state_key] = best_val
            return best_val

    def odigraj_kartu(self, state, validne_karte):
        # Ako imamo samo jednu legalnu kartu, nema šta da se misli!
        if len(validne_karte) == 1:
            return validne_karte[0]

        moje_karte = state.ruke[self.id]
        na_stolu = state.karte_na_stolu.copy()
        adut = state.adut
        nosilac = state.pobednik_licitacije

        SVE_KARTE = [f"{v} {b}" for v in ['7', '8', '9', '10', 'J', 'Q', 'K', 'A'] for b in ['Pik', 'Karo', 'Herc', 'Tref']]

        # 1. Šta sve pouzdano znamo da je otišlo iz špila?
        vidljive_karte = set(moje_karte)
        for _, k in na_stolu: vidljive_karte.add(k)
        for karte in state.odnete_karte.values():
            for k in karte: vidljive_karte.add(k)

        nepoznate_karte = list(set(SVE_KARTE) - vidljive_karte)
        ostali_igraci = [p for p in range(3) if p != self.id]
        
        # Koliko karata u ruci drži svaki od protivnika tačno u ovom trenutku?
        fali_karata = {}
        for p in ostali_igraci:
            igrao_u_ovom_stihu = any(pid == p for pid, _ in na_stolu)
            fali_karata[p] = len(moje_karte) - (1 if igrao_u_ovom_stihu else 0)

        rezultati = {k: 0 for k in validne_karte}
        
        # Dinamički broj simulacija: Na početku manje (da ne zablokira), na kraju više (brza matematika)
        karte_do_kraja = len(moje_karte)
        if karte_do_kraja >= 8: num_samples = 4
        elif karte_do_kraja >= 5: num_samples = 8
        else: num_samples = 15

        self.memo.clear()

        # 2. PIMC PETLJA - Istraživanje "Paralelnih Univerzuma"
        for _ in range(num_samples):
            # DETERMINIZATOR: Izmišljamo nasumičnu podelu nepoznatih karata
            random.shuffle(nepoznate_karte)
            simulirane_ruke = {self.id: tuple(moje_karte)}
            idx = 0
            for p in ostali_igraci:
                treba = fali_karata[p]
                simulirane_ruke[p] = tuple(nepoznate_karte[idx:idx+treba])
                idx += treba

            # MINIMAX SOLVER: Igramo do kraja za svaki validan potez
            for karta in validne_karte:
                novi_sto = na_stolu + [(self.id, karta)]
                nova_ruka = tuple(k for k in moje_karte if k != karta)
                sim_ruke = simulirane_ruke.copy()
                sim_ruke[self.id] = nova_ruka

                if len(novi_sto) == 3:
                    pobednik = GameRules.ko_nosi_odnetak(novi_sto, adut)
                    sledeci = pobednik
                    nosilac_dobio = 1 if pobednik == nosilac else 0
                    sto_za_dalje = []
                else:
                    sledeci = (self.id + 1) % 3
                    nosilac_dobio = 0
                    sto_za_dalje = novi_sto

                score = nosilac_dobio + self._minimax(sim_ruke, sto_za_dalje, sledeci, nosilac, adut, -1, 99)
                rezultati[karta] += score

        # 3. BIRANJE NAJBOLJE KARTE
        # Nosilac bira kartu sa najvećim prosekom. Pratioci biraju kartu sa NAJMANJIM prosekom (kvare nosiocu)!
        if self.id == nosilac:
            najbolja = max(rezultati, key=rezultati.get)
        else:
            najbolja = min(rezultati, key=rezultati.get)

        return najbolja