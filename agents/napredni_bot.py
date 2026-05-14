from .base_agent import BaseAgent
from engine.game_rules import GameRules

class NapredniBot(BaseAgent):
    def __init__(self, agent_id, ime="Pametni Bot"):
        super().__init__(agent_id, ime)
        self.red_vrednosti = {'7': 0, '8': 1, '9': 2, '10': 3, 'J': 4, 'Q': 5, 'K': 6, 'A': 7}
        self.nema_karte = {0: set(), 1: set(), 2: set()}

    def _snaga_karte(self, karta):
        v = karta.split()[0]
        return self.red_vrednosti[v]
    
    def _azuriraj_znanje_o_protivnicima(self, state):
        """Analizira prošle štihove i zaključuje koje karte protivnici nemaju."""
        # Prolazimo kroz sve odigrane štihove u ovoj rundi
        for stih in state.istorija_licitacije: # Pretpostavljamo da state ima pristup štihovima
             # U realnosti koristimo state.odnete_karte ili runda_info['stihovi']
             pass
             
        # Efikasniji način: gledamo karte koje su upravo na stolu pre nego što ih neko odnese
        if not state.karte_na_stolu: return
        
        prvi_id, prva_karta = state.karte_na_stolu[0]
        v_prve, b_prve = prva_karta.split()
        
        trenutno_najaca_v = v_prve
        
        for pid, karta in state.karte_na_stolu[1:]:
            v, b = karta.split()
            # Ako je igrač odgovorio na boju, a nije bacio jaču od trenutne
            if b == b_prve:
                if self.red_vrednosti[v] < self.red_vrednosti[trenutno_najaca_v]:
                    # Zaključujemo da nema ništa jače od trenutno najjače na stolu
                    sve_vrednosti = ['A', 'K', 'Q', 'J', '10', '9', '8', '7']
                    for jaca_v in sve_vrednosti:
                        if self.red_vrednosti[jaca_v] <= self.red_vrednosti[trenutno_najaca_v]:
                            break
                        self.nema_karte[pid].add(f"{jaca_v} {b}")
                else:
                    trenutno_najaca_v = v

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

    def _planirani_adut(self, state, ruka):
        """Procenuje koji bi adut bio najbolji s obzirom na nivo licitacije."""
        stihovi, _, _, karte_po_bojama = self._analiziraj_ruku(ruka)
        nivo = state.trenutna_licitacija_broj
        
        # Nivoi i dozvoljene boje (isto kao u engine-u)
        nivo_na_boje = {
            2: ["Pik", "Karo", "Herc", "Tref"],
            3: ["Karo", "Herc", "Tref"],
            4: ["Herc", "Tref"],
            5: ["Tref"]
        }
        dozvoljene = nivo_na_boje.get(nivo, ["Sans"])
        
        najbolja = dozvoljene[0]
        max_d = -1
        
        for b in dozvoljene:
            if b in ["Betl", "Sans"]: continue
            d = len(karte_po_bojama.get(b, []))
            if d > max_d:
                max_d = d
                najbolja = b
        return najbolja
    
    def odluci_licitaciju(self, state, moguci_potezi):
        stihovi, _, _, karte_po_bojama = self._analiziraj_ruku(state.ruke[self.id])
        boje_nivoi = {'Pik': 2, 'Karo': 3, 'Herc': 4, 'Tref': 5}
        
        # FIX: Proveravamo limit za SVAKU boju koju imamo u ruci
        # Bot sada traži najveći mogući nivo do kog sme da ide na osnovu dozvoljenih boja
        limit = 0
        broj_asova = sum(1 for v in karte_po_bojama.values() if 'A' in v)
        
        for boja, karte in karte_po_bojama.items():
            duzina = len(karte)
            moze_ovu_boju = False
            
            # Stepenasta logika snage: što je kraći adut, treba nam više asova/štihova
            if duzina >= 6 and stihovi >= 2: 
                moze_ovu_boju = True 
            elif duzina == 5 and stihovi >= 3: 
                moze_ovu_boju = True 
            elif duzina == 4 and stihovi >= 4 and broj_asova >= 1: 
                moze_ovu_boju = True 
            elif duzina == 3 and stihovi >= 5 and broj_asova >= 2: 
                moze_ovu_boju = True 

            if moze_ovu_boju:
                boja_limit = boje_nivoi.get(boja, 0)
                if boja_limit > limit:
                    limit = boja_limit

        trenutni_broj = state.trenutna_licitacija_broj

        # 1. Odgovaranje sa "Moje" ako smo već u licitaciji i limit dozvoljava
        if "moje" in moguci_potezi and trenutni_broj <= limit:
            return "moje"
            
        # 2. Podizanje licitacije na sledeći broj
        sledeci_broj = next((p for p in moguci_potezi if isinstance(p, int)), None)
        if sledeci_broj and sledeci_broj <= limit:
            return sledeci_broj
            
        # 3. Specijalne igre (Sans i Igra iz ruke) - zategnuti uslovi
        max_duzina = max(len(k) for k in karte_po_bojama.values())
        
        if "sans" in moguci_potezi and stihovi >= 6 and broj_asova >= 2 and max_duzina <= 4: 
            return "sans"
            
        if "igra" in moguci_potezi and stihovi >= 7 and broj_asova >= 3: 
            return "igra"

        # 4. Ako ništa ne prolazi, kažemo Dalje
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
        # KLJUČNO: Bot prvo odlučuje šta će mu biti adut, pa tek onda škartira!
        planirani_adut = self._planirani_adut(state, ruka)
        _, _, _, karte_po_bojama = self._analiziraj_ruku(ruka)
        
        def ocena_skarta(karta):
            v, b = karta.split()
            duzina_ove_boje = len(karte_po_bojama[b])
            
            # Štitimo boju koju ZAISTA planiramo da zovemo
            if b == planirani_adut: return 1000 
            
            if v == 'A': return 500
            if v == 'K' and duzina_ove_boje >= 2: return 400
            if v == 'Q' and duzina_ove_boje >= 3: return 300
            return duzina_ove_boje

        sortirana = sorted(ruka, key=ocena_skarta)
        return sortirana[:2]
    

    def izaberi_aduta(self, state, validne_boje):
        _, _, _, karte_po_bojama = self._analiziraj_ruku(state.ruke[self.id])
        
        najbolja_boja = None
        max_d = -1
        
        # Tražimo najdužu boju, ali ISKLJUČIVO među onima koje smemo da zovemo!
        for boja in validne_boje:
            if boja in ["Betl", "Sans"]:
                continue
            duzina = len(karte_po_bojama.get(boja, []))
            if duzina > max_d:
                max_d = duzina
                najbolja_boja = boja
                
        # Ako imamo validnu boju, igramo nju (npr. našao je onaj sakriveni Tref!)
        if najbolja_boja and max_d > 0:
            return najbolja_boja
            
        # Očajnički potez: Ako su nam sve dozvoljene boje potpuno prazne (0 karata)
        if "Sans" in validne_boje:
            return "Sans"
            
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
                    # Sam ide samo ako ima 4+ aduta, ili ako je apsolutni monstrum (4+ štiha uz 3 aduta)
                    if duzina_aduta >= 4 or (stihovi >= 4 and duzina_aduta >= 3) or (stihovi >= 5 and duzina_aduta >= 2):
                        return True 
                        
                    # STRATEGIJA 2: ZOVEM (Na silu vraćam partnera u igru)
                    # TVOJA LOGIKA: Imam ~3 stabilna štiha (Kec, Kec, dugi Kralj) ali mi treba pomoć
                    
                    # Sa 3 aduta: MORA da ima Adutskog Keca ILI bar 1 Kec sa strane
                    # (Samo stihovi od trece dame nisu dovoljni da opravdaju zvanje!)
                    elif duzina_aduta == 4 and (ima_adut_asa or sigurni_stihovi_sa_strane >= 1):
                        return "zovem"

                    # Sa 2 aduta: MORA Adutski Kec + 1 Kec sa strane, ILI 2 Keca sa strane
                    # Adutski Kec ALONE nije dovoljan — treba i podrska sa strane!
                    elif duzina_aduta == 3 and (sigurni_stihovi_sa_strane >= 2 or (ima_adut_asa and sigurni_stihovi_sa_strane >= 1)):
                        return "zovem"

                    # Sa 1 adutom: samo uz 2 Keca sa strane i ukupno 3 štiha
                    elif duzina_aduta == 2 and sigurni_stihovi_sa_strane >= 3 and stihovi >= 3:
                        return "zovem"

                    # STRATEGIJA 3: DALJE (Imam neku osnovnu snagu, ali nedovoljno da preživim, bežim i ja)
                    else:
                        return False 
                else:
                    # ZOVEM na Sans/Betl (Ekstremno zategnuto)
                    sigurni_asovi = sum(1 for b, v in karte_po_bojama.items() if 'A' in v)
                    if sigurni_asovi >= 3 or stihovi >= 5:
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

        if len(state.odnete_karte[0]) + len(state.odnete_karte[1]) + len(state.odnete_karte[2]) == 0:
            self.nema_karte = {0: set(), 1: set(), 2: set()}

        # Ažuriraj znanje na osnovu karata koje su trenutno na stolu ili u istoriji
        self._azuriraj_znanje_o_protivnicima(state)

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
                        ukupno_vidljivih_aduta = len(odigrani_aduti) + len(aduti_u_ruci)
                        
                        if ukupno_vidljivih_aduta < 8: # Protivnici imaju adute
                            moj_najjaci_adut = max(aduti_u_ruci, key=self._snaga_karte)
                            protivnik_ima_jaceg = not self._je_gospodar(moj_najjaci_adut, state, state.ruke[self.id])

                            if protivnik_ima_jaceg and bez_aduta:
                                # VELEMAJSTORSKI POTEZ: Forsiramo dugu boju
                                najduza_boja = max(bez_aduta, key=lambda k: len(karte_po_bojama[k.split()[1]])).split()[1]
                                karte_te_boje = sorted([k for k in bez_aduta if k.split()[1] == najduza_boja], 
                                                     key=self._snaga_karte, reverse=True)
                                
                                # FIX: Primeni Safety Lead i unutar Velemajstorskog poteza!
                                if self._je_gospodar(karte_te_boje[0], state, state.ruke[self.id]):
                                    return karte_te_boje[0] # Baci gospodara ako ga imaš
                                elif len(karte_te_boje) >= 2:
                                    return karte_te_boje[1] # Baci DRUGU NAJJAČU (Dama iz K-Q-8)
                                return karte_te_boje[-1]
                            else:
                                return moj_najjaci_adut
                        else:
                            # PROTIVNICI NEMAJU ADUTA - Igramo agresivno obične boje
                            if bez_aduta:
                                gospodari = [k for k in bez_aduta if self._je_gospodar(k, state, state.ruke[self.id])]
                                if gospodari: return max(gospodari, key=self._snaga_karte)
                                
                                # Safety Lead ovde
                                for b in set(k.split()[1] for k in bez_aduta):
                                    u_boji = sorted([k for k in bez_aduta if k.split()[1] == b], key=self._snaga_karte, reverse=True)
                                    if len(u_boji) >= 2 and not self._je_gospodar(u_boji[0], state, state.ruke[self.id]):
                                        return u_boji[1]
                                return max(bez_aduta, key=self._snaga_karte)
                            return min(aduti_u_ruci, key=self._snaga_karte)
                return max(validne_karte, key=self._snaga_karte)

            else:
                # PRATILAC OTVARA ŠTIH
                bez_aduta = [k for k in validne_karte if k.split()[1] != state.adut]
                if bez_aduta:
                    # PRIORITET 1: Gospodari
                    gospodari = [k for k in bez_aduta if self._je_gospodar(k, state, state.ruke[self.id])]
                    if gospodari: return max(gospodari, key=self._snaga_karte)

                    # PRIORITET 2: Safety Lead (Tvoj zahtev - mora biti pre "kroz nosioca")
                    for b in set(k.split()[1] for k in bez_aduta):
                        u_boji = sorted([k for k in bez_aduta if k.split()[1] == b], key=self._snaga_karte, reverse=True)
                        if len(u_boji) >= 2 and not self._je_gospodar(u_boji[0], state, state.ruke[self.id]):
                            return u_boji[1]

                    # PRIORITET 3: Igram kroz nosioca (ako nisam imao Safety Lead)
                    if igram_kroz_nosioca and imam_partnera:
                        najduza_boja = max(bez_aduta, key=lambda k: len(karte_po_bojama[k.split()[1]])).split()[1]
                        return min([k for k in bez_aduta if k.split()[1] == najduza_boja], key=self._snaga_karte)

                    return self._pametno_baci_najmanju(bez_aduta, karte_po_bojama)
                return min(validne_karte, key=self._snaga_karte)

        # 2. NEKO JE VEĆ ODIGRAO KARTU NA STO (Logika odgovaranja - ostaje ista i tačna)
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

        pobednicke = [k for k in validne_karte if GameRules.ko_nosi_odnetak(na_stolu + [(self.id, k)], state.adut) == self.id]
        if pobednicke: return min(pobednicke, key=self._snaga_karte)
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
        if v == 'A': return True
        
        odigrane = self._odigrane_karte(state)
        sve_vrednosti = ['A', 'K', 'Q', 'J', '10', '9', '8', '7']
        
        for jaca_v in sve_vrednosti:
            if jaca_v == v: break
            
            jaca_karta = f"{jaca_v} {b}"
            
            # Karta je i dalje opasnost ako postoji igrač koji je možda ima
            mozda_je_kod_nekog = False
            for protivnik_id in [p for p in range(3) if p != self.id]:
                # Ako jača karta nije pala, nije kod mene, I nismo zaključili da je taj protivnik nema
                if (jaca_karta not in odigrane and 
                    jaca_karta not in ruka and 
                    jaca_karta not in self.nema_karte[protivnik_id]):
                    mozda_je_kod_nekog = True
                    break
            
            if mozda_je_kod_nekog:
                return False
                
        return True
    
    def potvrdi_talon(self, state):
        return True
    
    def ceka_novu_ruku(self, state):
        return True # Bot ne čeka, on je spreman odmah