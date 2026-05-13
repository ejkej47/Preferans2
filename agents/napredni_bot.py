from .base_agent import BaseAgent
from engine.game_rules import GameRules

class NapredniBot(BaseAgent):
    def __init__(self, agent_id, ime="Pametni Bot"):
        super().__init__(agent_id, ime)
        self.red_vrednosti = {'7': 0, '8': 1, '9': 2, '10': 3, 'J': 4, 'Q': 5, 'K': 6, 'A': 7}

    def _snaga_karte(self, karta):
        v = karta.split()[0]
        return self.red_vrednosti[v]

    def _analiziraj_ruku(self, ruka):
        """
        Prava preferans logika: broji kafanske štihove i pronalazi dugu boju.
        Vraća: broj štihova, ime najduže boje, dužinu te boje, i rečnik rasporeda.
        """
        stihovi = 0
        karte_po_bojama = {'Pik': [], 'Karo': [], 'Herc': [], 'Tref': []}
        
        for k in ruka: 
            karte_po_bojama[k.split()[1]].append(k.split()[0])

        najduza_boja = "Pik"
        max_duzina = 0

        for boja, vrednosti in karte_po_bojama.items():
            duzina = len(vrednosti)
            if duzina > max_duzina:
                max_duzina = duzina
                najduza_boja = boja

            # Prava procena štihova (As, drugi Kralj, treća Dama)
            if 'A' in vrednosti: 
                stihovi += 1
            if 'K' in vrednosti and duzina >= 2: 
                stihovi += 1
            if 'Q' in vrednosti and duzina >= 3: 
                stihovi += 1

        return stihovi, najduza_boja, max_duzina, karte_po_bojama

    def odluci_licitaciju(self, state, moguci_potezi):
        stihovi, najduza_boja, max_duzina, karte_po_bojama = self._analiziraj_ruku(state.ruke[self.id])
        boje_nivoi = {'Pik': 2, 'Karo': 3, 'Herc': 4, 'Tref': 5}
        
        limit = 0
        broj_asova = sum(1 for v in karte_po_bojama.values() if 'A' in v)

        # NOVA, STEPENASTA LOGIKA ZA LICITACIJU (Poštovanje dužine aduta)
        imam_za_igru = False
        
        if max_duzina >= 6 and stihovi >= 2:
            imam_za_igru = True  # 6+ aduta je ODLIČNO: oprašta slabije karte sa strane
        elif max_duzina == 5 and stihovi >= 3:
            imam_za_igru = True  # 5 aduta je SUPER: standardna igra
        elif max_duzina == 4 and stihovi >= 4 and broj_asova >= 1:
            imam_za_igru = True  # 4 aduta je KNAP: MORA bar 1 Kec i jake karte sa strane
        elif max_duzina == 3 and stihovi >= 5 and broj_asova >= 2:
            imam_za_igru = True  # 3 aduta je LUDILO: igra se samo ako si krcat Asovima

        if imam_za_igru:
            limit = boje_nivoi.get(najduza_boja, 0)

        trenutni_broj = state.trenutna_licitacija_broj

        if "moje" in moguci_potezi and trenutni_broj <= limit:
            return "moje"
            
        sledeci_broj = next((p for p in moguci_potezi if isinstance(p, int)), None)
        if sledeci_broj and sledeci_broj <= limit:
            return sledeci_broj
            
        # Zategnut i Sans/Igra iz ruke
        if "sans" in moguci_potezi and stihovi >= 6 and broj_asova >= 2 and max_duzina <= 4: 
            return "sans"
            
        if "igra" in moguci_potezi and stihovi >= 7 and broj_asova >= 3: 
            return "igra"

        return "dalje"

    def _pametno_baci_najmanju(self, validne_karte, karte_po_bojama):
        """
        Ako ne može da nosi, bira kartu tako da čuva druge kraljeve i treće dame.
        Ako mora da škartira (nema boju/aduta), baca najmanju iz 'najružnije' boje.
        """
        boje_u_validnim = set(k.split()[1] for k in validne_karte)
        
        # Ako moramo da poštujemo boju, prosto dajemo najslabiju po vrednosti
        if len(boje_u_validnim) == 1:
            return min(validne_karte, key=self._snaga_karte)
            
        # Ako imamo pravo da bacimo bilo šta (npr. sečemo ili škartiramo)
        def ocena_lose_karte(karta):
            v, b = karta.split()
            boja_karte = karte_po_bojama[b]
            # Boja "vredi" i treba je čuvati ako u njoj spremamo As, Kralj ili Damu
            cuvam_jaku = any(j in boja_karte for j in ['A', 'K', 'Q'])
            
            # Rangiranje: 0 znači bacaj slobodno (nema jake), 1 znači čuvaj.
            # Zatim gledamo vrednost same karte (od 7 do A).
            return (1 if cuvam_jaku else 0, self._snaga_karte(karta))
            
        return min(validne_karte, key=ocena_lose_karte)

    def odluci_igru_iz_ruke(self, state):
        stihovi, _, max_duzina, _ = self._analiziraj_ruku(state.ruke[self.id])
        if stihovi >= 6 and max_duzina <= 4: return "sans"
        if stihovi >= 7: return "igra"
        return "dalje"

    def najavi_igru(self, state):
        if self.id not in state.aktivni_u_licitaciji: return None
        stihovi, najduza_boja, max_duzina, _ = self._analiziraj_ruku(state.ruke[self.id])
        
        boje_nivoi = {'Pik': 2, 'Karo': 3, 'Herc': 4, 'Tref': 5}
        moj_nivo = boje_nivoi.get(najduza_boja, 2)
        
        trenutni_max = max(state.igra_dekleresi.values()) if state.igra_dekleresi else 0
        if moj_nivo > trenutni_max and stihovi >= 6: 
            return moj_nivo
        return None

    def skartiraj(self, state):
        ruka = state.ruke[self.id]
        stihovi, najduza_boja, max_duzina, karte_po_bojama = self._analiziraj_ruku(ruka)
        
        def ocena_skarta(karta):
            v, b = karta.split()
            duzina_ove_boje = len(karte_po_bojama[b])
            
            # Pravilo 1: Nikad ne škartiraj iz najduže boje koju spremaš za aduta!
            if b == najduza_boja: return 100 
            
            # Pravilo 2: Ne bacaj sigurne štihove!
            if v == 'A': return 50
            if v == 'K' and duzina_ove_boje >= 2: return 40
            if v == 'Q' and duzina_ove_boje >= 3: return 30
            
            # Pravilo 3: Škartiraj iz najkraćih boja (idealno singlove)
            return duzina_ove_boje

        # Sortiramo i bacamo dve sa najmanjom ocenom
        sortirana = sorted(ruka, key=ocena_skarta)
        return sortirana[:2]

    def izaberi_aduta(self, state, validne_boje):
        _, najduza_boja, _, _ = self._analiziraj_ruku(state.ruke[self.id])
        if najduza_boja in validne_boje:
            return najduza_boja
        # Fallback ako nas je licitacija naterala iznad naše boje
        return validne_boje[0] if validne_boje else "Sans"

    def odluci_pratnju(self, state):
        ruka = state.ruke[self.id]
        adut = state.adut
        stihovi, _, max_duzina, karte_po_bojama = self._analiziraj_ruku(ruka)
        
        nosilac = state.pobednik_licitacije
        prvi_pratilac = (nosilac + 1) % 3
        partner_odustao = (self.id != prvi_pratilac and state.igraci_koji_dolaze.get(prvi_pratilac) is False)
        
        # --- 1. OSNOVNA PROCENA SNAGE (Scenario A - kada partner još nije pobegao) ---
        if adut in ["Betl", "Sans"]:
            imam_snagu = stihovi >= 2
        else:
            duzina_aduta = len(karte_po_bojama.get(adut, []))
            aduti_u_ruci = karte_po_bojama.get(adut, [])
            jaki_aduti = sum(1 for k in aduti_u_ruci if k in ['A', 'K', 'Q'])
            sigurni_stihovi_sa_strane = sum(1 for b, v in karte_po_bojama.items() if b != adut and 'A' in v)
            
            imam_snagu = False
            if duzina_aduta >= 4: imam_snagu = True
            elif duzina_aduta == 3 and (jaki_aduti >= 1 or sigurni_stihovi_sa_strane >= 1 or stihovi >= 1): imam_snagu = True
            elif duzina_aduta == 2 and ('A' in aduti_u_ruci or ('K' in aduti_u_ruci and sigurni_stihovi_sa_strane >= 1) or sigurni_stihovi_sa_strane >= 2): imam_snagu = True
            elif duzina_aduta == 1 and ('A' in aduti_u_ruci and sigurni_stihovi_sa_strane >= 1 or sigurni_stihovi_sa_strane >= 2): imam_snagu = True
            elif duzina_aduta == 0 and sigurni_stihovi_sa_strane >= 3: imam_snagu = True

        # --- 2. DONOŠENJE ODLUKE (Scenario B - šta ako je partner pobegao?) ---
        if imam_snagu:
            if partner_odustao:
                if adut not in ["Betl", "Sans"]:
                    duzina_aduta = len(karte_po_bojama.get(adut, []))
                    sigurni_stihovi_sa_strane = sum(1 for b, v in karte_po_bojama.items() if b != adut and 'A' in v)
                    ima_adut_asa = 'A' in aduti_u_ruci
                    
                    # STRATEGIJA 1: DOĐEM (Igram sam protiv nosioca, ne treba mi partner)
                    if duzina_aduta >= 4 or (stihovi >= 4 and duzina_aduta >= 2):
                        return True 
                        
                    # STRATEGIJA 2: ZOVEM (Ne smem sam, na silu vraćam partnera u igru)
                    elif duzina_aduta == 3 and (sigurni_stihovi_sa_strane >= 1 or ima_adut_asa):
                        return "zovem" 
                    elif duzina_aduta == 2 and (sigurni_stihovi_sa_strane >= 2 or (ima_adut_asa and sigurni_stihovi_sa_strane >= 1)):
                        return "zovem" 
                    elif duzina_aduta == 1 and sigurni_stihovi_sa_strane >= 2 and stihovi >= 3:
                        return "zovem"
                        
                    # STRATEGIJA 3: DALJE (Imam neku osnovnu snagu, ali nedovoljno da preživim, bežim i ja)
                    else:
                        return False 
                else:
                    # ZOVEM na Sans/Betl (Zategnuta pravila)
                    sigurni_asovi = sum(1 for b, v in karte_po_bojama.items() if 'A' in v)
                    if sigurni_asovi >= 2 or stihovi >= 4:
                        return "zovem"
                    return False
                    
            # Ako partner nije odustao (igra i on), i ja imam osnovnu snagu -> Pratim normalno
            return True 
            
        return False

    def odluci_kontru(self, state):
        ruka = state.ruke[self.id]
        adut = state.adut
        _, _, _, karte_po_bojama = self._analiziraj_ruku(ruka)
        
        if adut not in ["Betl", "Sans"]:
            duzina_aduta = len(karte_po_bojama.get(adut, []))
            sigurni_stihovi_sa_strane = sum(1 for b, v in karte_po_bojama.items() if b != adut and 'A' in v)
            
            # KONTRA ZATEGNUTA DO KRAJA (Gotovo zagarantovan pad nosioca)
            if duzina_aduta >= 5 and sigurni_stihovi_sa_strane >= 1: return "kontra"
            if duzina_aduta >= 4 and sigurni_stihovi_sa_strane >= 2: return "kontra"
            
        return "moze"

    def _da_li_je_igrao(self, igrac_id, na_stolu):
        """Proverava da li je određeni igrač već bacio kartu u trenutnom štihu."""
        return any(pid == igrac_id for pid, k in na_stolu)

    def odigraj_kartu(self, state, validne_karte):
        if len(validne_karte) == 1:
            return validne_karte[0]

        na_stolu = state.karte_na_stolu
        nosilac_igre = state.pobednik_licitacije
        _, _, _, karte_po_bojama = self._analiziraj_ruku(state.ruke[self.id])
        
        pratioci_u_igri = [p for p in range(3) if p != nosilac_igre and state.igraci_koji_dolaze.get(p) is True]
        imam_partnera = len(pratioci_u_igri) > 1
        igram_kroz_nosioca = ((self.id + 1) % 3) == nosilac_igre if imam_partnera else True

        # 1. PRVI SAM NA POTEZU (Otvaram štih)
        if not na_stolu:
            if self.id == nosilac_igre:
                if state.adut not in ["Betl", "Sans"]:
                    aduti_u_ruci = [k for k in validne_karte if k.split()[1] == state.adut]
                    bez_aduta = [k for k in validne_karte if k.split()[1] != state.adut]
                    
                    if aduti_u_ruci:
                        odigrane = self._odigrane_karte(state)
                        odigrani_aduti = [k for k in odigrane if k.split()[1] == state.adut]
                        # Pošto igramo sa 32 karte, uvek ima tačno 8 aduta u igri
                        ukupno_vidljivih_aduta = len(odigrani_aduti) + len(aduti_u_ruci)
                        
                        protivnici_imaju_adute = ukupno_vidljivih_aduta < 8
                        
                        if protivnici_imaju_adute:
                            moj_najjaci_adut = max(aduti_u_ruci, key=self._snaga_karte)
                            # Da li protivnik drži jačeg aduta od mog najjačeg?
                            protivnik_ima_jaceg = not self._je_gospodar(moj_najjaci_adut, state, state.ruke[self.id])
                            
                            if protivnik_ima_jaceg and bez_aduta:
                                # VELEMAJSTORSKI POTEZ: Ne vucem aduta da mu ga ne bih dao!
                                # Igram neku moju najdužu boju da ga nateram da on tog aduta potroši na SEČENJE.
                                najduza_boja = max(bez_aduta, key=lambda k: len(karte_po_bojama[k.split()[1]]))
                                karte_te_boje = [k for k in bez_aduta if k.split()[1] == najduza_boja.split()[1]]
                                return min(karte_te_boje, key=self._snaga_karte)
                            else:
                                # Moj adut je najjači (ili protivnici nemaju jačeg) -> VUČEM DA IH OČISTIM
                                return moj_najjaci_adut
                        else:
                            # PROTIVNICI SU OSTALI BEZ ADUTA!
                            # Nema razloga da trošim svoje. Igram sigurne štihove (Gospodare).
                            if bez_aduta:
                                gospodari = [k for k in bez_aduta if self._je_gospodar(k, state, state.ruke[self.id])]
                                if gospodari:
                                    return max(gospodari, key=self._snaga_karte)
                                # Inače bacam najjaču ne-adut kartu da probam da odnesem
                                return max(bez_aduta, key=self._snaga_karte)
                            else:
                                # Ostali su mi samo aduti u ruci
                                return min(aduti_u_ruci, key=self._snaga_karte)
                                
                # Za Sans/Betl uvek vuci najjače
                return max(validne_karte, key=self._snaga_karte)
            else:
                # PRATILAC VODI IGRU
                bez_aduta = [k for k in validne_karte if k.split()[1] != state.adut]
                if bez_aduta:
                    gospodari = [k for k in bez_aduta if self._je_gospodar(k, state, state.ruke[self.id])]
                    if gospodari: return max(gospodari, key=self._snaga_karte)
                        
                    if igram_kroz_nosioca and imam_partnera:
                        najduza_boja = max(bez_aduta, key=lambda k: len(karte_po_bojama[k.split()[1]]))
                        karte_te_boje = [k for k in bez_aduta if k.split()[1] == najduza_boja.split()[1]]
                        return min(karte_te_boje, key=self._snaga_karte)
                    else:
                        return self._pametno_baci_najmanju(bez_aduta, karte_po_bojama)
                else:
                    return min(validne_karte, key=self._snaga_karte)

        # 2. NEKO JE VEĆ ODIGRAO KARTU NA STO
        trenutni_pobednik = GameRules.ko_nosi_odnetak(na_stolu, state.adut)

        if imam_partnera and trenutni_pobednik != nosilac_igre and self.id != nosilac_igre:
            nosilac_igrao = self._da_li_je_igrao(nosilac_igre, na_stolu)
            if nosilac_igrao:
                return self._pametno_baci_najmanju(validne_karte, karte_po_bojama)
            else:
                karta_partnera = next(k for pid, k in na_stolu if pid == trenutni_pobednik)
                if not self._je_gospodar(karta_partnera, state, state.ruke[trenutni_pobednik]):
                    najveca_moja = max(validne_karte, key=self._snaga_karte)
                    if najveca_moja.split()[0] in ['A', 'K', 'Q', 'J', '10']:
                        return najveca_moja
                return self._pametno_baci_najmanju(validne_karte, karte_po_bojama)

        pobednicke = []
        for k in validne_karte:
            probni_sto = na_stolu + [(self.id, k)]
            if GameRules.ko_nosi_odnetak(probni_sto, state.adut) == self.id:
                pobednicke.append(k)

        if pobednicke:
            return min(pobednicke, key=self._snaga_karte)
        else:
            return self._pametno_baci_najmanju(validne_karte, karte_po_bojama)
        
    def _odigrane_karte(self, state):
        """Vraća set svih karata koje su do sada pale u ovoj rundi."""
        odigrane = set()
        for karte in state.odnete_karte.values():
            odigrane.update(karte)
        return odigrane

    def _je_gospodar(self, karta, state, ruka):
        """Proverava da li je karta trenutno NAJJAČA živa karta u svojoj boji."""
        v, b = karta.split()
        if v == 'A': return True # As je uvek gospodar
        
        odigrane = self._odigrane_karte(state)
        
        # Redosled od najjače naniže
        sve_vrednosti = ['A', 'K', 'Q', 'J', '10', '9', '8', '7']
        
        for jaca_v in sve_vrednosti:
            if jaca_v == v:
                break # Stigli smo do naše karte, nema jačih u igri
            
            jaca_karta = f"{jaca_v} {b}"
            # Ako jača karta nije ni u odigranim, ni u mojoj ruci, to je OPASNOST (nalazi se kod nekog drugog)
            if jaca_karta not in odigrane and jaca_karta not in ruka:
                return False
                
        return True