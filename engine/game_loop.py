# engine/game_loop.py
import time
from .state import GameState
from .deck import Deck
from .game_rules import GameRules
from engine.scoring import ScoringTable


class GameLoop:
    def __init__(self, agents, seed=None):
        """
        agents: lista od tačno 3 objekta koji nasleđuju BaseAgent
        """
        self.agents = agents
        self.deck = Deck(seed)
        self.state = GameState()
        self.scoring = ScoringTable(60)
        self.zavrsene_runde = []
        self.trenutni_stihovi = []

    def play_round(self):
        # 1. SPASI ONO ŠTO MORA DA PREŽIVI RUNDU (Rotaciju i Refe)
        sacuvan_prvi_licitant = getattr(self.state, 'prvi_licitant', 0)
        sacuvane_refe = getattr(self.state, 'refe', {0: 0, 1: 0, 2: 0}).copy()
        
        # 2. Resetuj sve ostalo (karte, štihove, bodove u trenutnoj rundi)
        self.state.__init__()
        self.trenutni_stihovi = []
        
        # 3. VRATI SPAŠENE VREDNOSTI
        self.state.prvi_licitant = sacuvan_prvi_licitant
        self.state.refe = sacuvane_refe
        
        self.deck.reset_spil()
        
        self._faza_deljenja()
        
        # DODATO: Postavljamo pravilnu listu aktivnih u licitaciji shodno rotaciji
        p1 = self.state.prvi_licitant
        self.state.aktivni_u_licitaciji = [p1, (p1 + 1) % 3, (p1 + 2) % 3]
        
        self._faza_licitacije()
        
        if self.state.faza == "KRAJ":
            return
            
        # SKARTIRANJE se poziva SAMO ako nije izglasana "Igra" iz ruke
        if self.state.faza == "SKARTIRANJE":
            self._faza_skartiranja_i_izbora()
            
        if self.state.faza != "IGRA": 
            self._faza_dolaska_i_zvanja()
            
        self._faza_igre()
        self._obracun()

    def _faza_licitacije(self):
        self.state.na_potezu = self.state.prvi_licitant
        self.state.poslednja_akcija = None
        self.state.igrac_imao_prvi_krug_licitacije = False
        self.state.igraci_imali_potez_licitacije = set()
        self.state.specijalna_igra_nivo = 0 
        
        igraci_koji_su_rekli_igra = []

        # --- ISPRAVLJENA PETLJA ---
        while True:
            # 1. Ako su svi odustali, prekidamo (ide se u Refu)
            if len(self.state.aktivni_u_licitaciji) == 0:
                break
                
            # 2. Ako je ostao samo 1 aktivan igrač, prekidamo SAMO ako je neko već nešto zvao.
            # Ako niko ništa nije zvao (poslednja_akcija je None), taj poslednji mora da se izjasni!
            if len(self.state.aktivni_u_licitaciji) == 1 and self.state.poslednja_akcija is not None:
                break

            # Prekid licitacije ako imamo izjednačenje u "Igra" (svi preostali su rekli Igra)
            svi_govorili = all(p in self.state.igraci_imali_potez_licitacije for p in self.state.aktivni_u_licitaciji)
            svi_rekli_igra = all(p in igraci_koji_su_rekli_igra for p in self.state.aktivni_u_licitaciji)
            if svi_govorili and self.state.specijalna_igra_nivo == 1 and svi_rekli_igra:
                break
                
            trenutni = self.state.na_potezu
            agent = self.agents[trenutni]
            
            # --- AUTO-IZBACIVANJE ---
            if self.state.specijalna_igra_nivo > 0:
                if trenutni in self.state.igraci_imali_potez_licitacije:
                    if self.state.specijalna_igra_nivo > 1 or trenutni not in igraci_koji_su_rekli_igra:
                        self.state.aktivni_u_licitaciji.remove(trenutni)
                        continue # Sledeca iteracija ce ga izbaciti ili zatvoriti petlju

            moguci = ["dalje"]
            nivo = self.state.trenutna_licitacija_broj
            zadnja = self.state.poslednja_akcija

            # Normalna licitacija brojevima
            if self.state.specijalna_igra_nivo == 0:
                if zadnja is None:
                    moguci.append(2)
                elif zadnja == "broj":
                    moguci.append("moje")
                elif zadnja == "moje":
                    if nivo < 7: moguci.append(nivo + 1)
            
            # Specijalne igre su dozvoljene SAMO u prvom krugu izjašnjavanja
            if trenutni not in self.state.igraci_imali_potez_licitacije:
                if self.state.specijalna_igra_nivo < 1: moguci.append("igra")
                if self.state.specijalna_igra_nivo < 2: moguci.append("betl")
                if self.state.specijalna_igra_nivo < 3: moguci.append("sans")

            moguci = list(set(moguci))
            
            if len(moguci) == 1 and moguci[0] == "dalje":
                odluka = "dalje"
            else:
                odluka = agent.odluci_licitaciju(self.state.kopiraj(), moguci)
                
            self.state.igraci_imali_potez_licitacije.add(trenutni)
            
            ime = "Ja" if trenutni == 0 else f"Bot {trenutni}"
            if odluka == "dalje":
                self.state.aktivni_u_licitaciji.remove(trenutni)
                msg = "Dalje"
            elif odluka == "moje":
                self.state.poslednja_akcija = "moje"
                msg = f"Moje {nivo}"
            elif isinstance(odluka, int):
                self.state.trenutna_licitacija_broj = odluka
                self.state.poslednja_akcija = "broj"
                msg = f"Licitiram {odluka}"
            else:
                self.state.poslednja_akcija = odluka
                msg = odluka.capitalize()
                mape = {"igra": 1, "betl": 2, "sans": 3}
                self.state.specijalna_igra_nivo = mape[odluka]
                self.state.specijalna_igra_igrac = trenutni
                if odluka == "igra":
                    igraci_koji_su_rekli_igra.append(trenutni)
            
            self.state.istorija_licitacije.append(f"{ime}: {msg}")
            self.state.poruka_za_ui = f"{ime} kaže: {msg}"
            
            if trenutni != 0: time.sleep(0.15) 
            if odluka == "sans": break # Sans se ne može prebiti, kraj odmah!
            
            self._sledeci_licitant()

        # --- NAKON PETLJE (Određivanje pobednika) ---
        if len(self.state.aktivni_u_licitaciji) == 0:
            self._svi_rekli_dalje()
        else:
            if self.state.specijalna_igra_nivo > 0:
                self.state.pobednik_licitacije = self.state.specijalna_igra_igrac
                # Ako je više ljudi reklo "Igra", idemo u Najavu. Ako si samo ti, ideš na Izbor Aduta!
                if self.state.specijalna_igra_nivo == 1 and len(self.state.aktivni_u_licitaciji) > 1:
                    self._faza_najave()
                else:
                    self.state.poslednja_akcija = "igra" if self.state.specijalna_igra_nivo == 1 else ("betl" if self.state.specijalna_igra_nivo == 2 else "sans")
                    self.state.faza = "SKARTIRANJE"
            else:
                self.state.pobednik_licitacije = self.state.aktivni_u_licitaciji[0]
                self.state.faza = "SKARTIRANJE"

    def _faza_najave(self):
        """Igrači najavljuju nivo igre iz ruke (2,3,4,5). Pitamo samo aktivne!"""
        self.state.faza = "FAZA_NAJAVA"
        self.state.poruka_za_ui = "Najava nivoa za igru iz ruke..."
        self.state.igra_dekleresi = {}
        
        # KLJUČNO: Pitamo samo one koji su ostali u licitaciji
        konkurenti = list(self.state.aktivni_u_licitaciji)
        
        for pid in konkurenti:
            agent = self.agents[pid]
            najava = agent.najavi_igru(self.state.kopiraj())
            ime = "Ja" if pid == 0 else f"Bot {pid}"
            
            # Bezbednosno čitanje vrednosti (radi i sa 2 i sa "najava_2")
            nivo = None
            if najava is not None and najava != "dalje":
                if str(najava).isdigit(): 
                    nivo = int(najava)
                elif "_" in str(najava): 
                    nivo = int(str(najava).split("_")[1]) 
            
            if nivo is not None:
                self.state.igra_dekleresi[pid] = nivo
                self.state.istorija_licitacije.append(f"{ime}: Najavljujem {nivo}")
            else:
                self.state.istorija_licitacije.append(f"{ime}: Slabiji sam (Dalje)")
                
            if pid != 0: time.sleep(0.1)
            
        # Obračun pobednika najave
        if not self.state.igra_dekleresi:
            pobednik = self.state.pobednik_licitacije
            najjaci_nivo = 2
        else:
            pobednik = max(self.state.igra_dekleresi.keys(), key=lambda k: self.state.igra_dekleresi[k])
            najjaci_nivo = self.state.igra_dekleresi[pobednik]
            
        mapa_boja = {2: "Pik", 3: "Karo", 4: "Herc", 5: "Tref"}
        self.state.adut = mapa_boja.get(najjaci_nivo, "Pik")
        self.state.pobednik_licitacije = pobednik 
        
        ko_nosi = "Ja" if pobednik == 0 else f"Bot {pobednik}"
        self.state.istorija_licitacije.append(f"{ko_nosi}: Nosi igru iz ruke ({self.state.adut})")
        self.state.direktna_igra = True
        
        self._napravi_krajnji_snapshot()
        self.state.faza = "FAZA_DOLASKA"

    def _faza_deljenja(self):
        ruke, talon = self.deck.podeli()
        for i in range(3):
            self.state.ruke[i] = GameRules.sortiraj_ruku(ruke[i])
            self.state.pocetne_ruke[i] = list(self.state.ruke[i])
        self.state.talon = talon
        self.state.pocetni_talon = list(talon)
        self.state.faza = "FAZA_LICITACIJE"


    def _svi_rekli_dalje(self):
        for i in range(3):
            self.state.refe[i] += 1
        self.state.istorija_licitacije.append("REFE - Svi su rekli dalje (novo deljenje)")
        self.state.poruka_za_ui = "Svi rekli dalje, pišu se refe."
        
        # 1. Očistimo stare štihove da ne bi UI "pamtio" gluposti
        self.trenutni_stihovi = []
        for i in range(3):
            self.state.odnete_karte[i] = []

        self.state.prvi_licitant = (self.state.prvi_licitant + 1) % 3
        
        # 2. Pakujemo lažnu rundu da bi GUI skapirao da je ovo "Refa runda"
        runda_info = {
            "is_refa": True, # KLJUČNO!
            "nosilac": 0, "adut": "Refa", "vrednost": 0,
            "direktna_igra": False, "kontra": False,
            "zvanje_tip": None, "zvanje_igrac": None,
            "stihovi_po_igracu": {0:0, 1:0, 2:0}, "rezultat": {0: "Svi rekli dalje", 1: "Svi rekli dalje", 2: "Svi rekli dalje"},
            "stihovi": [], "pocetne_ruke": self.state.pocetne_ruke, "pocetni_talon": self.state.pocetni_talon,
            "scoring_snapshot": self.scoring.get_stanje(),
            "odigrano_pod_refom": False
        }
        self.zavrsene_runde.append(runda_info)

        self.state.faza = "KRAJ"
        time.sleep(0.1) # Dam malo vremena igraču da vidi poruku pre mešanja

    def _faza_skartiranja_i_izbora(self):
        pid = self.state.pobednik_licitacije
        agent = self.agents[pid]
        zadnja = self.state.poslednja_akcija
        ime = "Ja" if pid == 0 else f"Bot {pid}"
        
        nivo = self.state.trenutna_licitacija_broj
        
        # SLUČAJ 1: BETL
        if zadnja == "betl":
            self.state.adut = "Betl"
            self.state.direktna_igra = True
            self.state.istorija_licitacije.append(f"{ime}: Igra BETL - svi igraju automatski")
            self.state.poruka_za_ui = "Igra se BETL! (svi igraju)"
            for i in range(3): self.state.igraci_koji_dolaze[i] = True
            self._napravi_krajnji_snapshot()
            self.state.faza = "FAZA_DOLASKA" 
            return
            
        # SLUČAJ 2: SANS
        if zadnja == "sans":
            self.state.adut = "Sans"
            self.state.direktna_igra = True
            self.state.istorija_licitacije.append(f"{ime}: Igra SANS")
            self.state.poruka_za_ui = "Igra se SANS! Boti deklarišu dolazak..."
            self._napravi_krajnji_snapshot()
            self.state.faza = "FAZA_DOLASKA"
            return
            
        # SLUČAJ 3: IGRA (IZ RUKE)
        if zadnja == "igra":
            self.state.direktna_igra = True
            self.state.poruka_za_ui = f"{ime} igra IZ RUKE. Bira aduta."
            validne_boje = ["Pik", "Karo", "Herc", "Tref"]
            
            self.state.faza = "IZBOR_ADUTA" # <--- OBAVEZNO DA GUI NACRTA NOVI EKRAN
            self.state.adut = agent.izaberi_aduta(self.state.kopiraj(), validne_boje)
            self.state.istorija_licitacije.append(f"{ime}: Igra iz ruke, adut {self.state.adut}")
            
            self._napravi_krajnji_snapshot()
            self.state.faza = "FAZA_DOLASKA"
            return
            
        # SLUČAJ 4: KLASIČNA IGRA SA TALONOM
        if pid == 0:
            self.state.poruka_za_ui = "Odaberi 2 karte za škart."
            skart = agent.skartiraj(self.state.kopiraj())
            sve = self.state.ruke[0] + self.state.talon
            for k in skart:
                if k in sve: sve.remove(k)
            self.state.ruke[0] = GameRules.sortiraj_ruku(sve)
            self.state.talon = []
            self.state.odbacene_karte = skart
        else:
            self.state.ruke[pid].extend(self.state.talon)
            self.state.talon = []
            self.state.ruke[pid] = GameRules.sortiraj_ruku(self.state.ruke[pid])
            self.state.poruka_za_ui = f"{ime} uzima talon i škartira."
            skart = agent.skartiraj(self.state.kopiraj())
            for k in skart: self.state.ruke[pid].remove(k)
            self.state.odbacene_karte = skart
            
        self.state.istorija_licitacije.append(f"{ime}: Škartirao 2 karte")
        
        # Izbor aduta
        nivo_na_boje = {
            2: ["Pik", "Karo", "Herc", "Tref", "Betl", "Sans"],
            3: ["Karo", "Herc", "Tref", "Betl", "Sans"],
            4: ["Herc", "Tref", "Betl", "Sans"],
            5: ["Tref", "Betl", "Sans"],
            6: ["Betl", "Sans"],
            7: ["Sans"],
        }
        validne_boje = nivo_na_boje.get(nivo, ["Sans"])
            
        self.state.faza = "IZBOR_ADUTA" # <--- OBAVEZNO DA GUI NACRTA NOVI EKRAN
        self.state.adut = agent.izaberi_aduta(self.state.kopiraj(), validne_boje)
        self.state.istorija_licitacije.append(f"{ime}: Adut je {self.state.adut}")
        self.state.faza = "FAZA_DOLASKA"
        
        self._napravi_krajnji_snapshot()

    def _faza_dolaska_i_zvanja(self):
        nosilac = self.state.pobednik_licitacije
        p1 = (nosilac + 1) % 3
        p2 = (nosilac + 2) % 3
        pratioci = [p1, p2]
        
        self.state.poruka_za_ui = "Faza dolaska: Da li pratite?"
        
        # 1. FAZA DOLASKA
        if self.state.adut == "Betl":
            for i in range(3):
                self.state.igraci_koji_dolaze[i] = True
        else:
            p1_id, p2_id = pratioci # Prvi i drugi pratilac po redu licitacije
            
            # Prvi se izjašnjava
            odluka1 = self.agents[p1_id].odluci_pratnju(self.state.kopiraj())
            self.state.igraci_koji_dolaze[p1_id] = odluka1
            self._zapisi_dolazak(p1_id, odluka1)
            if p1_id != 0: time.sleep(0.1)

            # Drugi se izjašnjava (njemu nudimo i opciju "Zovem" ako je prvi rekao "Ne")
            # Napomena: Agentu se u kopiji stanja šalje šta je prvi odlučio
            odluka2 = self.agents[p2_id].odluci_pratnju(self.state.kopiraj())
            
            if odluka2 == "zovem":
                self.state.igraci_koji_dolaze[p2_id] = True
                self.state.igraci_koji_dolaze[p1_id] = True # VRAĆAMO PRVOG U IGRU!
                self.state.zvanje_tip = "zovem"
                self.state.zvanje_igrac = p2_id
                self._zapisi_dolazak(p2_id, "Zovem")
            else:
                self.state.igraci_koji_dolaze[p2_id] = odluka2
                self._zapisi_dolazak(p2_id, "Dodjem" if odluka2 else "Ne dodjem")
                
            if p2_id != 0: time.sleep(0.1)

        dosli = [pid for pid in pratioci if self.state.igraci_koji_dolaze[pid] is True]

        if len(dosli) == 0:
            self.state.istorija_licitacije.append("Niko ne prati - pišu se bodovi automatski")
            self.state.faza = "IGRA" 
            return
            
        # 2. FAZA KONTRE
        self.state.faza = "FAZA_KONTRE"
        self.state.poruka_za_ui = "Može ili Kontra?"
        
        for pid in dosli:
            agent = self.agents[pid]
            odluka_kontra = agent.odluci_kontru(self.state.kopiraj())
            
            ime = "Ja" if pid == 0 else f"Bot {pid}"
            if odluka_kontra == "kontra":
                self.state.kontra_aktivan = True
                self.state.zvanje_tip = "kontra"
                self.state.zvanje_igrac = pid
                self.state.istorija_dolaska.append(f"{ime}: KONTRA!")
                self.state.istorija_licitacije.append(f"{ime}: KONTRA!")
                
                for i in pratioci: self.state.igraci_koji_dolaze[i] = True
                break 
            else:
                self.state.istorija_dolaska.append(f"{ime}: Može")
                self.state.istorija_licitacije.append(f"{ime}: Može")
            
            if pid != 0: time.sleep(0.1)
            
        self.state.faza = "IGRA"

    def _zapisi_dolazak(self, pid, msg_bool_or_str):
        ime = "Ja" if pid == 0 else f"Bot {pid}"
        if isinstance(msg_bool_or_str, bool):
            msg = "Dodjem" if msg_bool_or_str else "Ne dodjem"
        else:
            msg = msg_bool_or_str
        self.state.istorija_licitacije.append(f"{ime}: {msg}")
    
    def _faza_igre(self):
        pratioci = [pid for pid in range(3) if pid != self.state.pobednik_licitacije]
        ako_niko_ne_prati = all(self.state.igraci_koji_dolaze[pid] is False for pid in pratioci)
        if ako_niko_ne_prati: return

        aktivni_igraci = [self.state.pobednik_licitacije]
        for pid in pratioci:
            if self.state.igraci_koji_dolaze[pid] is True or self.state.adut == "Betl":
                aktivni_igraci.append(pid)
        aktivni_igraci.sort()

        broj_aktivnih = len(aktivni_igraci)
        self.state.na_potezu = self._prvi_za_sans(self.state.pobednik_licitacije, aktivni_igraci) if self.state.adut == "Sans" else self._prvi_na_potezu(aktivni_igraci)
        
        self.trenutni_stihovi = [] # Reset liste štihova za novu rundu
        broj_stihova = len(self.state.ruke[aktivni_igraci[0]])
        
        for stih_broj in range(broj_stihova):
            self.state.karte_na_stolu = []
            
            for _ in range(broj_aktivnih):
                trenutni_id = self.state.na_potezu
                agent = self.agents[trenutni_id]
                prva_karta = self.state.karte_na_stolu[0][1] if self.state.karte_na_stolu else None
                validne = GameRules.validni_potezi(self.state.ruke[trenutni_id], prva_karta, self.state.adut)
                
                karta = agent.odigraj_kartu(self.state.kopiraj(), validne)
                self.state.ruke[trenutni_id].remove(karta)
                self.state.karte_na_stolu.append((trenutni_id, karta))
                
                if trenutni_id != 0: time.sleep(0.1)
                self.state.na_potezu = self._sledeci_aktivni(trenutni_id, aktivni_igraci)
            
            time.sleep(0.25)
            pobednik_stiha = GameRules.ko_nosi_odnetak(self.state.karte_na_stolu, self.state.adut)
            
            # Snimanje stiha u listu za RoundHistory
            self.trenutni_stihovi.append({
                "broj": stih_broj + 1,
                "karte": list(self.state.karte_na_stolu),
                "pobednik": pobednik_stiha
            })
            
            karte_iz_stiha = [k for pid, k in self.state.karte_na_stolu]
            self.state.odnete_karte[pobednik_stiha].extend(karte_iz_stiha)
            self.state.poslednji_stih_pobednik = pobednik_stiha
            self.state.na_potezu = pobednik_stiha
            
            # --- ISPRAVLJENA LOGIKA ZA PREKID IGRE ---
            if self.state.adut == "Betl":
                # U Betlu nosilac pada čim odnese jedan jedini štih
                if pobednik_stiha == self.state.pobednik_licitacije:
                    msg = "NOSILAC JE PAO NA BETLU! (Uzeo je štih)"
                    self.state.istorija_licitacije.append(msg)
                    self.state.poruka_za_ui = msg
                    break
            else:
                # Za normalne igre (boje i Sans), nosilac pada uvek ako pratioci uzmu ukupno 5 štihova
                ukupno_pratioci = sum(len(self.state.odnete_karte[pid]) // broj_aktivnih for pid in pratioci)
                
                if ukupno_pratioci >= 5:
                    msg = f"NOSILAC JE PAO! Pratioci odneli 5 štihova."
                    self.state.istorija_licitacije.append(msg)
                    self.state.poruka_za_ui = msg
                    break

    def _obracun(self):
        aktivni = [pid for pid in range(3) if self.state.igraci_koji_dolaze[pid] is True]
        if self.state.pobednik_licitacije not in aktivni:
            aktivni.append(self.state.pobednik_licitacije)
            
        broj_aktivnih = len(aktivni) if len(aktivni) > 0 else 3
        stihovi_po_igracu = {pid: len(self.state.odnete_karte[pid]) // broj_aktivnih for pid in aktivni}
            
        nosilac = self.state.pobednik_licitacije
        pratioci_dosli = any(self.state.igraci_koji_dolaze.get(p) is True for p in range(3) if p != nosilac)
        
        if not pratioci_dosli and self.state.adut not in ["Betl"]:
            # Dodeljujemo mu fiktivnih 6 štihova da bi scoring.py video prolaz!
            stihovi_po_igracu[nosilac] = 6 

        igra_se_pod_refom = False
        if self.state.refe[nosilac] > 0:
            igra_se_pod_refom = True
            self.state.refe[nosilac] -= 1

        rezultat, vrednost = self.scoring.izracunaj_rundu(
            nosioac_id=nosilac, adut=self.state.adut, stihovi_po_igracu=stihovi_po_igracu,
            kontra=self.state.kontra_aktivan, refa=igra_se_pod_refom,
            direktna_igra=self.state.direktna_igra, zvanje_tip=self.state.zvanje_tip, zvanje_igrac=self.state.zvanje_igrac
        )
        
        runda_info = {
            "is_refa": False, # Obična runda nije refa
            "nosilac": nosilac, "adut": self.state.adut, "vrednost": vrednost,
            "direktna_igra": self.state.direktna_igra, "kontra": self.state.kontra_aktivan,
            "zvanje_tip": self.state.zvanje_tip, "zvanje_igrac": self.state.zvanje_igrac,
            "stihovi_po_igracu": stihovi_po_igracu, "rezultat": rezultat,
            "stihovi": list(self.trenutni_stihovi),
            "pocetne_ruke": self.state.pocetne_ruke, "pocetni_talon": self.state.pocetni_talon,
            "scoring_snapshot": self.scoring.get_stanje(),
            "odigrano_pod_refom": igra_se_pod_refom,
            "istorija_licitacije": list(self.state.istorija_licitacije)
        }
        self.zavrsene_runde.append(runda_info)
        
        zbir_bula = sum(self.scoring.bula.values())
        if zbir_bula <= 0:
            self.state.faza = "KRAJ_PARTIJE"
            skorovi = self.scoring.izracunaj_finalni_skor()
            msg = f"KRAJ IGRE! Skor: Ja {skorovi[0]} | B1 {skorovi[1]} | B2 {skorovi[2]}"
            self.state.poruka_za_ui = msg
            self.state.istorija_licitacije.append(msg)
        else:
            self.state.faza = "KRAJ"
            self.state.prvi_licitant = (self.state.prvi_licitant + 1) % 3

    # --- Pomoćne metode ---
    def _sledeci_licitant(self):
        trenutni = self.state.na_potezu
        for i in range(1, 4):
            kandidat = (trenutni + i) % 3
            if kandidat in self.state.aktivni_u_licitaciji:
                self.state.na_potezu = kandidat
                break

    def _sledeci_aktivni(self, trenutni, aktivni_igraci):
        idx = aktivni_igraci.index(trenutni)
        return aktivni_igraci[(idx + 1) % len(aktivni_igraci)]

    def _prvi_na_potezu(self, aktivni_igraci):
        """
        Vraća ID igrača koji prvi baca kartu. 
        U preferansu uvek kreće 'Prva ruka' (prvi licitant) ili prvi aktivni posle njega.
        """
        p = self.state.prvi_licitant
        # Tražimo prvog aktivnog igrača u krugu 0->1->2 počevši od onoga ko je delio/licitirao prvi
        for _ in range(3):
            if p in aktivni_igraci:
                return p
            p = (p + 1) % 3
        return self.state.prvi_licitant

    def _prvi_za_sans(self, nosilac_id, aktivni_igraci):
        levo_od = {0: 2, 2: 1, 1: 0}
        kandidat = levo_od[nosilac_id]
        for _ in range(3):
            if kandidat in aktivni_igraci and kandidat != nosilac_id:
                return kandidat
            kandidat = levo_od[kandidat]
        return nosilac_id

    def _napravi_krajnji_snapshot(self):
        self.state.pocetne_ruke = [list(self.state.ruke[i]) for i in range(3)]
        if self.state.odbacene_karte:
            self.state.pocetni_talon = list(self.state.odbacene_karte)
        else:
            self.state.pocetni_talon = list(self.state.talon)