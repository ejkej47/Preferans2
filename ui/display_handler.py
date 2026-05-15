import pygame
from ui.constants import *
from ui.components import UIComponents

class DisplayHandler:
    """Svo iscrtavanje UI elementa"""
    
    def __init__(self, gui):
        self.gui = gui
    
    def osvezi_ekran(self, screen):
        screen.fill(IPREF_SIVA)
        
        # Ako engine još nije poslao stanje, ne crtaj ništa
        if self.gui.state is None:
            pygame.display.flip()
            return
            
        # 1. Crtamo panele (okvire)
        self.nacrtaj_okvire_panela(screen)
        self.nacrtaj_istoriju_licitacije(screen)
        self.nacrtaj_info_box(screen)
        
        # 3. Ostali elementi (desni panel, karte, sto)
        self.nacrtaj_desni_panel(screen) # Rezultati
        self.nacrtaj_moje_karte(screen)
        self.nacrtaj_bot_karte(screen)
        self.nacrtaj_centralni_deo(screen)
        self.nacrtaj_gomilice(screen)
         
        self.nacrtaj_scoring(screen)
        self.nacrtaj_status_labele(screen)

        # Overlay za pregled odnetih karata
        if hasattr(self.gui, 'prikaz_odnetih') and self.gui.prikaz_odnetih is not None:
            self.nacrtaj_pregled_odnetih(screen)

        if hasattr(self.gui, 'round_history') and self.gui.round_history.show_round_overlay:
            self.nacrtaj_overlay_istorije_rundi(screen)

        pygame.display.flip()

    def nacrtaj_okvire_panela(self, screen):
        """Crtanje osnovnih kontejnera za UI"""
        UIComponents.nacrtaj_okvir(screen, "Istorija Licitacije", 10, 10, 180, 350)
        UIComponents.nacrtaj_okvir(screen, "", 10, 370, 180, 320)
        UIComponents.nacrtaj_okvir(screen, "", 810, 10, 180, 600)

    def nacrtaj_status_labele(self, screen):
        """Crta etikete u bojama: žuta (nosilac), zelena (prati), crvena (prolazi), plava (kontra)"""
        if self.gui.state is None:
            return

        # Pozicije etiketa blizu karata svakog igrača
        pozicije = {
            0: (700, 500),  # Ja (iznad mojih karata)
            1: (700, 8),                 # Bot 1 (ispod karata)
            2: (300, 8),                 # Bot 2 (ispod karata)
        }

        # ISPRAVLJENO: Koristimo self.gui.state
        stanje = self.gui.state.faza
        pobednik_id = self.gui.state.pobednik_licitacije
        adut = self.gui.state.adut if self.gui.state.adut else ""

        for pid, (x, y) in pozicije.items():
            labela = ""
            boja_pozadine = (200, 200, 200) # Default siva
            boja_teksta = CRNA
            
            # --- FAZA LICITACIJE ---
            if stanje in ["FAZA_IZBORA", "FAZA_LICITACIJE"]:
                msg = self.gui.bot_poruke.get(pid, "") if pid > 0 else ""
                # Za igrača izvlačimo iz zadnje poruke u istoriji licitacije koja je u state-u
                if pid == 0 and self.gui.state.istorija_licitacije:
                    zadnja = self.gui.state.istorija_licitacije[-1]
                    if zadnja.startswith("Ja:"): 
                        labela = zadnja.replace("Ja: ", "")
                else:
                    labela = msg
                
                if not labela: continue

            # --- FAZA IGRE (Ili dolaska) ---
            else:
                if pid == pobednik_id:
                    # NOSILAC - Žuta etiketa
                    labela = f"{adut}"
                    boja_pozadine = (255, 215, 0) # Zlatna
                else:
                    # PRATIOCI
                    odluka = None
                    if pid == 0:
                        odluka = self.gui.state.moj_izbor_zvanja
                    else:
                        # Indexi u igraci_koji_dolaze su 0, 1, 2
                        odluka_bool = self.gui.state.igraci_koji_dolaze.get(pid)
                        if odluka_bool is True: odluka = "dodjem"
                        elif odluka_bool is False: odluka = "ne_dodjem"

                    if self.gui.state.kontra_aktivan and odluka == "dodjem":
                        labela = "KONTRA!"
                        boja_pozadine = (40, 100, 220) # Plava
                        boja_teksta = BELA
                    elif odluka == "dodjem" or odluka == "zovem":
                        labela = "Dodjem" if odluka == "dodjem" else "Zovem"
                        boja_pozadine = (40, 150, 40) if odluka == "dodjem" else (40, 100, 220)
                        boja_teksta = BELA
                    elif odluka == "ne_dodjem":
                        labela = "Ne dodjem"
                        boja_pozadine = (180, 40, 40) # Crvena
                        boja_teksta = BELA
                    else:
                        continue # Još se nije izjasnio

            if labela:
                txt_surf = FONT_BOLD.render(labela, True, boja_teksta)
                rect_w = txt_surf.get_width() + 16
                rect_h = 24
                label_rect = pygame.Rect(x, y, rect_w, rect_h)
                
                pygame.draw.rect(screen, boja_pozadine, label_rect, border_radius=4)
                pygame.draw.rect(screen, CRNA, label_rect, 1, border_radius=4)
                screen.blit(txt_surf, (label_rect.x + 8, label_rect.y + (rect_h - txt_surf.get_height()) // 2))

    def nacrtaj_scoring(self, screen):
        """Prikazuje bula/supe box pored karata svakog igrača"""
        if self.gui.scoring is None:
            return
            
        scoring = self.gui.scoring
        redosled = {0: (2, 1), 1: (0, 2), 2: (1, 0)}
        
        # Pozicije usklađene da budu pored gomilica i karata
        pozicije = {
            0: (300, 500),
            1: (600, 165),
            2: (300, 165),
        }
        
        COL_W = 30
        H = 22
        
        for pid, (x, y) in pozicije.items():
            levo_id, desno_id = redosled[pid]
            vrednosti = [
                str(scoring.supe[pid][levo_id]),
                str(scoring.bula[pid]),
                str(scoring.supe[pid][desno_id])
            ]
            
            for i, val in enumerate(vrednosti):
                rx = x + i * (COL_W - 1)
                # Bula je plava sa zlatnim tekstom, supe su sive
                boja_poz = (60, 60, 180) if i == 1 else (220, 220, 220)
                boja_txt = ZLATNA if i == 1 else CRNA
                
                pygame.draw.rect(screen, boja_poz, (rx, y, COL_W, H), border_radius=2)
                pygame.draw.rect(screen, CRNA, (rx, y, COL_W, H), 1, border_radius=2)
                
                txt = FONT_SMALL.render(val, True, boja_txt)
                screen.blit(txt, (rx + (COL_W - txt.get_width()) // 2, y + (H - txt.get_height()) // 2))

    def nacrtaj_istoriju_licitacije(self, screen):
        # Čitamo iz STATE umesto iz GUI
        istorija = self.gui.state.istorija_licitacije
        ukupna_visina = len(istorija) * 22
        vidljiva_visina = 310
        
        # Podesi scroll (privremeno ćemo držati scroll na gui objektu jer je to UI stanje)
        if not hasattr(self.gui, 'istorija_scroll'):
            self.gui.istorija_scroll = 0
            
        if ukupna_visina <= vidljiva_visina:
            self.gui.istorija_scroll = 0

        povrsina_istorije = pygame.Surface((160, vidljiva_visina))
        povrsina_istorije.fill(BELA)
        
        for i, stavka in enumerate(istorija):
            txt = FONT_SMALL.render(stavka, True, CRNA)
            povrsina_istorije.blit(txt, (5, 5 + i * 22 + self.gui.istorija_scroll))
            
        screen.blit(povrsina_istorije, (20, 40))

    def nacrtaj_info_box(self, screen):
        st = self.gui.state
        panel_x = 10
        panel_y = 370
        panel_w = 180
        panel_h = 320

        pob_id = st.pobednik_licitacije
        odigravac = "Čeka se..."
        if pob_id is not None:
            odigravac = "Ja" if pob_id == 0 else f"Bot {pob_id}"
            
        kontrakt = st.adut if st.adut else "Licitacija..."
        
        prate_lista = []
        # Sada je igraci_koji_dolaze dictionary {0: True, 1: False...}
        for i in range(1, 3):
            if st.igraci_koji_dolaze.get(i) is True: 
                prate_lista.append(f"Bot {i}")
        if st.zvanje_tip in ["dodjem", "kontra"] or st.igraci_koji_dolaze.get(0) is True: 
            prate_lista.append("Ja")
            
        prate = ", ".join(prate_lista) if prate_lista else "Niko"
        vrednost = str(st.trenutna_licitacija_broj)

        # STATUS - zakucan za vrh
        y = panel_y + 8
        n_txt = FONT_BOLD.render("STATUS:", True, CRVENA_PANEL)
        screen.blit(n_txt, (panel_x + 10, y))
        y += 16
        
        poruka = st.poruka_za_ui
        if len(poruka) > 20:
            reci = poruka.split()
            prvi_red = " ".join(reci[:3])
            drugi_red = " ".join(reci[3:])
            screen.blit(FONT_SMALL.render(prvi_red, True, CRNA), (panel_x + 10, y))
            y += 14
            screen.blit(FONT_SMALL.render(drugi_red, True, CRNA), (panel_x + 10, y))
        else:
            screen.blit(FONT_SMALL.render(poruka, True, CRNA), (panel_x + 10, y))

        sep_y = panel_y + 60
        pygame.draw.line(screen, (150, 150, 150), (panel_x, sep_y), (panel_x + panel_w, sep_y), 1)

        stavke = [
            ("ODIGRAVAČ:", odigravac),
            ("KONTRAKT:", kontrakt),
            ("PRATE:", prate),
            ("VREDNOST:", vrednost)
        ]

        visina_stavke = 45  
        y_start = panel_y + panel_h - len(stavke) * visina_stavke

        for i, (naslov, vred) in enumerate(stavke):
            y = y_start + i * visina_stavke
            n_txt = FONT_BOLD.render(naslov, True, CRNA)
            screen.blit(n_txt, (panel_x + 10, y))

            if len(vred) > 20:
                reci = vred.split()
                prvi_red = " ".join(reci[:3])
                drugi_red = " ".join(reci[3:])
                screen.blit(FONT_SMALL.render(prvi_red, True, CRNA), (panel_x + 10, y + 18))
                screen.blit(FONT_SMALL.render(drugi_red, True, CRNA), (panel_x + 10, y + 33))
            else:
                screen.blit(FONT_SMALL.render(vred, True, CRNA), (panel_x + 10, y + 18))

            if i < len(stavke) - 1:
                pygame.draw.line(screen, (150, 150, 150), 
                            (panel_x, y + visina_stavke - 4), 
                            (panel_x + panel_w, y + visina_stavke - 4), 1)
                
    def nacrtaj_moje_karte(self, screen):
        """Moje karte sa mogućnostima izbora i hover efektom"""
        if self.gui.state is None:
            return
            
        if self.gui.tip_unosa == "skart":
            return
            
        self.gui.rects = []
        mis_pos = self.gui.mis_pozicija
        
        # ISPRAVKA: Na kraju runde ruka je prazna, koristimo pocetne_ruke da vidimo šta smo imali
        ruka_za_prikaz = self.gui.state.pocetne_ruke[0] if self.gui.state.faza == "KRAJ" else self.gui.state.ruke[0]
        
        validni = []
        if self.gui.state.faza == "IGRA" and self.gui.state.na_potezu == 0:
            prva = self.gui.state.karte_na_stolu[0][1] if self.gui.state.karte_na_stolu else None
            from engine.game_rules import GameRules
            validni = GameRules.validni_potezi(ruka_za_prikaz, prva, self.gui.state.adut)
            
        n = len(ruka_za_prikaz)
        if n == 0: return # Bezbednosna provera

        KARTA_W = 100
        razmak = 45
        ukupna_sirina = (n - 1) * razmak + KARTA_W
        start_x = (SCREEN_W - ukupna_sirina) // 2

        hoverovana_karta = None
        for i in reversed(range(n)):
            karta = ruka_za_prikaz[i]
            rect = pygame.Rect(start_x + i * razmak, 540, 100, 140)
            if rect.collidepoint(mis_pos):
                hoverovana_karta = karta
                break

        for i, karta in enumerate(ruka_za_prikaz):
            y_pos = 540
            
            if karta == hoverovana_karta and self.gui.state.faza == "IGRA" and self.gui.state.na_potezu == 0:
                if karta in validni:
                    y_pos -= 15  
            
            slika = self.gui.slike_karata_velike.get(karta)
            rect = pygame.Rect(start_x + i * razmak, y_pos, 100, 140)
            
            if slika:
                screen.blit(slika, rect)
                pygame.draw.rect(screen, CRNA, rect, 1, border_radius=3)
                
            self.gui.rects.append((rect, karta, 'ruka'))

    def nacrtaj_bot_karte(self, screen):
        st = self.gui.state
        pozicije = {2: (220, 10), 1: (580, 10)}
        
        for bot_id, (x, y) in pozicije.items():
            # AKO JE KRAJ: Crtamo prave karte umesto poledine
            if st.faza == "KRAJ":
                # ISPRAVKA: Čitamo iz pocetne_ruke jer je redovna ruka sada prazna
                ruka_bota = st.pocetne_ruke[bot_id] if hasattr(st, 'pocetne_ruke') else st.ruke[bot_id]
                for i, karta in enumerate(ruka_bota):
                    slika = self.gui.slike_karata.get(karta) 
                    if slika:
                        screen.blit(slika, (x + i * 15, y + 30))
            else:
                # Standardno crtanje poledine
                if self.gui.poledina:
                    for i in range(len(st.ruke[bot_id])): 
                        screen.blit(self.gui.poledina, (x + i * 15, y + 30))
            
            ime_tekst = f"Bot {bot_id}"
            if st.na_potezu == bot_id and st.faza != "KRAJ":
                ime_tekst += " (Razmišlja...)"
                
            ime_surf = FONT_BOLD.render(ime_tekst, True, CRNA)
            screen.blit(ime_surf, (x, y))

    def nacrtaj_centralni_deo(self, screen):
        """Centralni deo koji izbacuje pop-up prozor SAMO kad je igrač na potezu"""
        # 1. Zeleni sto crtamo isključivo kada smo u fazi igre
        if self.gui.state.faza == "IGRA":
            self.nacrtaj_karte_na_stolu(screen)

        if self.gui.state.faza == "KRAJ":
            self.nacrtaj_kraj_runde_prikaz(screen)
            return # Prekidamo dalje crtanje u ovom delu

        # 2. Ako engine ne traži naš unos, prekidamo (nema pop-up menija)
        if not self.gui.ceka_se_unos:
            return
            
        tip = self.gui.tip_unosa
        
        if tip == "licitacija":
            self.nacrtaj_faza_licitacije(screen)
        elif tip == "najava_igre":
            self.nacrtaj_faza_najave(screen)
        elif tip == "igra_iz_ruke":
            self.nacrtaj_genericke_dugmice(screen, "PRIJAVA IGRE", 40)
        if self.gui.tip_unosa == "potvrda_talona":
            self.nacrtaj_potvrdu_talona(screen)
        elif tip == "skart":
            self.nacrtaj_skartiranje(screen)
        elif tip == "izbor_aduta":
            self.nacrtaj_genericke_dugmice(screen, "ODABERI ADUTA", 30)
        elif tip in ["pratnja", "kontra", "najava"]:
            self.nacrtaj_genericke_dugmice(screen, "ODABERI POTEZ", 45)

    def nacrtaj_faza_licitacije(self, screen):
        w, h = 450, 280
        x = (SCREEN_W - w) // 2
        y = (SCREEN_H - h) // 2

        pygame.draw.rect(screen, BELA, (x, y, w, h), border_radius=4)
        pygame.draw.rect(screen, CRNA, (x, y, w, h), 2, border_radius=4)
        
        naslov = FONT_BOLD.render("TVOJ POTEZ U LICITACIJI", True, CRNA)
        screen.blit(naslov, (x + (w - naslov.get_width()) // 2, y + 15))

        self.gui.dugmici_licitacije = []
        nivo = self.gui.state.trenutna_licitacija_broj
        
        opcije_za_prikaz = []

        # 3. Dalje
        if "dalje" in self.gui.dozvoljeni_potezi:
            opcije_za_prikaz.append(("Dalje", "dalje"))

        # 1. Numerički potezi
        if "moje" in self.gui.dozvoljeni_potezi:
            opcije_za_prikaz.append((f"Moje {nivo}", "moje"))
        else:
            sledeci_broj = next((p for p in self.gui.dozvoljeni_potezi if isinstance(p, int)), None)
            if sledeci_broj:
                opcije_za_prikaz.append((f"Licitiram {sledeci_broj}", sledeci_broj))

        # 2. Specijalne igre
        for sp in ["igra", "betl", "sans"]:
            if sp in self.gui.dozvoljeni_potezi:
                opcije_za_prikaz.append((sp.capitalize(), sp))

        

        # --- DINAMIČKO RAČUNANJE VELIČINE I POZICIJE ---
        broj_opcija = len(opcije_za_prikaz)
        if broj_opcija == 0: return

        dostupna_visina = h - 50 - 20 # 50 za naslov, 20 za donju marginu
        razmak = 5
        
        # Visina dugmeta se menja u zavisnosti od toga koliko ih ima (max 60px)
        btn_h = min(60, (dostupna_visina - (broj_opcija - 1) * razmak) // broj_opcija)
        
        ukupna_visina_elemenata = broj_opcija * btn_h + (broj_opcija - 1) * razmak
        start_y = y + 50 + (dostupna_visina - ukupna_visina_elemenata) // 2

        # Crtanje dugmića
        for i, (txt, akcija) in enumerate(opcije_za_prikaz):
            dy = start_y + i * (btn_h + razmak)
            d = UIComponents.nacrtaj_dugme(screen, txt, x + 150, dy, 150, btn_h)
            self.gui.dugmici_licitacije.append((d, akcija))

    def nacrtaj_genericke_dugmice(self, screen, naslov_tekst, _razmak_ignore=0):
        # Treći parametar (_razmak_ignore) ostaje zbog poziva iz prethodnih funkcija, 
        # ali se više ne koristi jer sve računamo dinamički
        w, h = 450, 280
        x = (SCREEN_W - w) // 2
        y = (SCREEN_H - h) // 2

        pygame.draw.rect(screen, BELA, (x, y, w, h), border_radius=4)
        pygame.draw.rect(screen, CRNA, (x, y, w, h), 2, border_radius=4)
        
        naslov = FONT_BOLD.render(naslov_tekst, True, CRNA)
        screen.blit(naslov, (SCREEN_W//2 - naslov.get_width()//2, y + 15))
        
        self.gui.dugmici_licitacije = []
        
        broj_opcija = len(self.gui.dozvoljeni_potezi)
        if broj_opcija == 0: return

        # --- DINAMIČKO RAČUNANJE VELIČINE I POZICIJE ---
        dostupna_visina = h - 50 - 20 
        razmak = 5
        btn_h = min(65, (dostupna_visina - (broj_opcija - 1) * razmak) // broj_opcija)
        
        ukupna_visina_elemenata = broj_opcija * btn_h + (broj_opcija - 1) * razmak
        start_y = y + 50 + (dostupna_visina - ukupna_visina_elemenata) // 2
        
        for i, akcija in enumerate(self.gui.dozvoljeni_potezi):
            tekst = str(akcija).capitalize()
            if akcija is True: tekst = "Pratim"
            elif akcija is False: tekst = "Ne pratim"
                
            dy = start_y + i * (btn_h + razmak)
            d = UIComponents.nacrtaj_dugme(screen, tekst, x + 75, dy, 300, btn_h)
            self.gui.dugmici_licitacije.append((d, akcija))

    def nacrtaj_skartiranje(self, screen):
        self.gui.rects = []
        if self.gui.state is None:
            return

        karte_za_skart = self.gui.karte_za_skart
        
        # Sve karte koje igrač ima na raspolaganju (njegova ruka + talon)
        sve_karte = self.gui.state.ruke[0] + self.gui.state.talon
        # Prikazuju se u ruci samo one koje NISU odabrane za skart
        karte_u_ruci = [k for k in sve_karte if k not in karte_za_skart]

        # Sortiranje ruke da se lepo prepakuje svaki put kad pomeriš kartu
        red_boja = {'Pik': 0, 'Karo': 1, 'Tref': 2, 'Herc': 3}
        red_vrednosti = {'A': 0, 'K': 1, 'Q': 2, 'J': 3, '10': 4, '9': 5, '8': 6, '7': 7}
        karte_u_ruci.sort(key=lambda k: (red_boja[k.split()[1]], red_vrednosti[k.split()[0]]))

        # Centralni prozor — isti stil kao nacrtaj_potvrdu_talona
        w, h = 400, 250
        x = (SCREEN_W - w) // 2
        y = (SCREEN_H - h) // 2

        pygame.draw.rect(screen, BELA, (x, y, w, h), border_radius=8)
        pygame.draw.rect(screen, CRNA, (x, y, w, h), 2, border_radius=8)

        lbl = FONT_BOLD.render("ODABERI 2 KARTE ZA ŠKART", True, CRNA)
        screen.blit(lbl, (x + w // 2 - lbl.get_width() // 2, y + 20))

        # Slotovi za skart karte
        KARTA_W, KARTA_H = 100, 140
        slotovi_x = [x + 90 + i * 120 for i in range(2)]

        for i in range(2):
            x_pos = slotovi_x[i]
            y_pos = y + 50
            slot_rect = pygame.Rect(x_pos, y_pos, KARTA_W, KARTA_H)

            pygame.draw.rect(screen, (200, 200, 200), slot_rect, 2, border_radius=4)

            if i < len(karte_za_skart):
                karta = karte_za_skart[i]
                slika = self.gui.slike_karata_velike.get(karta)
                if slika:
                    screen.blit(slika, slot_rect)
                    pygame.draw.rect(screen, ZLATNA, slot_rect, 2, border_radius=4)
                self.gui.rects.append((slot_rect, karta, 'skart'))
            else:
                lbl_prazno = FONT_SMALL.render("prazno", True, (150, 150, 150))
                screen.blit(lbl_prazno, (x_pos + KARTA_W//2 - lbl_prazno.get_width()//2, y_pos + KARTA_H//2 - 8))

        # Dugme / info — isti stil kao nacrtaj_potvrdu_talona
        btn_y = y + h - 45
        if len(karte_za_skart) == 2:
            self.gui.dugme_potvrdi_skart = UIComponents.nacrtaj_dugme(
                screen, "✓ POTVRDI ŠKART",
                x + w//2 - 60, btn_y, 120, 35)
        else:
            self.gui.dugme_potvrdi_skart = None
            info = FONT_MSG.render("Klikni na kartu iz ruke da je odložiš", True, CRNA)
            screen.blit(info, (SCREEN_W//2 - info.get_width()//2, btn_y + 8))

        # Moje karte dole
        n = len(karte_u_ruci)
        RUKA_W, RUKA_H = 100, 140
        available_w = 480
        if n > 1:
            razmak = min(45, available_w // (n - 1))
        else:
            razmak = 0

        ukupna_sirina = (n - 1) * razmak + RUKA_W
        start_x = SCREEN_W // 2 - ukupna_sirina // 2
        y_ruka = 540

        # Hover logika
        mis_pos = self.gui.mis_pozicija
        hoverovana_karta = None
        for i in reversed(range(n)):
            rect = pygame.Rect(start_x + i * razmak, y_ruka, RUKA_W, RUKA_H)
            if rect.collidepoint(mis_pos):
                hoverovana_karta = karte_u_ruci[i]
                break

        for i, karta in enumerate(karte_u_ruci):
            y_pos = y_ruka
            if karta == hoverovana_karta:
                y_pos -= 15

            slika = self.gui.slike_karata_velike.get(karta)
            x_k = start_x + i * razmak
            rect = pygame.Rect(x_k, y_pos, RUKA_W, RUKA_H)

            if slika:
                screen.blit(slika, rect)
                pygame.draw.rect(screen, CRNA, rect, 1, border_radius=2)

            self.gui.rects.append((rect, karta, 'ruka'))

    def nacrtaj_potvrdu_talona(self, screen):
        """Overlay koji pokazuje igraču šta je bot dobio u talonu."""
        w, h = 400, 250
        x, y = (SCREEN_W - w) // 2, (SCREEN_H - h) // 2
        pygame.draw.rect(screen, BELA, (x, y, w, h), border_radius=8)
        pygame.draw.rect(screen, CRNA, (x, y, w, h), 2, border_radius=8)

        txt = FONT_BOLD.render(f"TALON ZA BOTA {self.gui.state.pobednik_licitacije}", True, CRNA)
        screen.blit(txt, (x + w // 2 - txt.get_width() // 2, y + 20))

        for i, karta in enumerate(self.gui.state.talon):
            rect = pygame.Rect(x + 90 + i * 120, y + 50, 100, 140)
            slika = self.gui.slike_karata_velike.get(karta)
            if slika: screen.blit(slika, rect)
            pygame.draw.rect(screen, ZLATNA, rect, 2, border_radius=4)

        self.gui.dugmici_licitacije = []
        d = UIComponents.nacrtaj_dugme(screen, "U REDU", x + w//2 - 60, y + h - 45, 120, 35)
        self.gui.dugmici_licitacije.append((d, "potvrdi_pregled"))

        
    def nacrtaj_karte_na_stolu(self, screen):
        sto_rect = pygame.Rect(350, 230, 300, 220)
        pygame.draw.rect(screen, TAMNO_ZELENA, sto_rect)
        pygame.draw.rect(screen, CRNA, sto_rect, 2)
        
        pozicije = {
            0: (sto_rect.centerx - 35, sto_rect.bottom - 110),
            1: (sto_rect.right - 90, sto_rect.top + 20),
            2: (sto_rect.left + 20, sto_rect.top + 20)
        }

        for p_id, karta in self.gui.state.karte_na_stolu:
            slika = self.gui.slike_karata.get(karta)
            if slika: 
                pos_x, pos_y = pozicije[p_id]
                rect = pygame.Rect(pos_x, pos_y, 70, 100)
                screen.blit(slika, rect)
                pygame.draw.rect(screen, CRNA, rect, 1, border_radius=3)
                
                vlasnik = "Ja" if p_id == 0 else f"B{p_id}"
                oznaka = FONT_SMALL.render(vlasnik, True, BELA)
                screen.blit(oznaka, (pos_x + 20, pos_y - 15))

    def nacrtaj_gomilice(self, screen):
        """Iscrtava gomilice osvojenih karata sa TAČNIM brojem štihova"""
        if self.gui.state.faza != "IGRA" or not self.gui.poledina: return
            
        mala_poledina = pygame.transform.smoothscale(self.gui.poledina, (35, 50))
        self.gui.gomilice_rects = {}
        pozi = {
                2: (220, 150), 
                1: (750, 150),
                0: (220, 480)
                }
        
        st = self.gui.state
        
        # --- LOGIKA ZA PRAVILNO BROJANJE ŠTIHOVA ---
        # Računamo koliko tačno igrača igra ovu rundu
        pratioci_koji_dolaze = [p for p in range(3) if p != st.pobednik_licitacije and st.igraci_koji_dolaze.get(p) is True]
        broj_aktivnih = 1 + len(pratioci_koji_dolaze)
        if st.adut == "Betl":
            broj_aktivnih = 3 # U Betlu svi uvek igraju
            
        for pid, pos in pozi.items():
            rect = pygame.Rect(pos[0], pos[1], 35, 50)
            self.gui.gomilice_rects[pid] = rect
            
            if st.poslednji_stih_pobednik == pid and len(st.odnete_karte[pid]) > 0:
                pygame.draw.rect(screen, (255, 215, 0), (pos[0]-4, pos[1]-4, 43, 58), 4, border_radius=6)
            
            screen.blit(mala_poledina, pos)
            
            # Sada se broj karata deli sa TAČNIM brojem igrača u igri (2 ili 3)
            broj_stihova = len(st.odnete_karte[pid]) // broj_aktivnih if broj_aktivnih > 0 else 0
            
            txt = FONT_BOLD.render(str(broj_stihova), True, BELA)
            pygame.draw.rect(screen, CRNA, (pos[0] + 8, pos[1] + 15, 20, 20), border_radius=3)
            screen.blit(txt, (pos[0] + 13, pos[1] + 16))

    def nacrtaj_pregled_odnetih(self, screen):
        """Polu-providni overlay koji pokazuje detalje šta je ko odneo"""
        s = pygame.Surface((SCREEN_W, SCREEN_H))
        s.set_alpha(220)
        s.fill((30, 30, 30))
        screen.blit(s, (0,0))
        
        p_id = self.gui.prikaz_odnetih
        st = self.gui.state
        karte = st.odnete_karte[p_id]
        
        # LOGIKA PRIKAZA PO PRAVILIMA:
        if p_id == 0:
            naslov_tekst = "Tvoje odnete karte"
            karte_za_prikaz = karte
            prikazujem_samo_kraj = False
        else:
            if st.poslednji_stih_pobednik == p_id and len(karte) > 0:
                naslov_tekst = f"Bot {p_id} - Poslednji odneti štih"
                karte_za_prikaz = karte[-3:]
                prikazujem_samo_kraj = True
            else:
                naslov_tekst = f"Bot {p_id} - Karte su zatvorene (nije nosilac poslednjeg štiha)!"
                karte_za_prikaz = [] 
                prikazujem_samo_kraj = True
                
        naslov = FONT_MSG.render(naslov_tekst, True, BELA)
        screen.blit(naslov, (SCREEN_W//2 - naslov.get_width()//2, 50))
        
        start_x = 100
        start_y = 120
        broj_aktivnih = 3 # Uprošćeno za Headless crtanje
        
        for stih_idx in range(len(karte_za_prikaz) // broj_aktivnih):
            stih = karte_za_prikaz[stih_idx * broj_aktivnih : stih_idx * broj_aktivnih + broj_aktivnih]
            
            if prikazujem_samo_kraj:
                x_offset = SCREEN_W // 2 - 100
                y_offset = 200
                je_poslednji = True
            else:
                x_offset = start_x + (stih_idx % 3) * 260
                y_offset = start_y + (stih_idx // 3) * 130
                je_poslednji = (stih_idx == (len(karte_za_prikaz)//3 - 1)) and (st.poslednji_stih_pobednik == p_id)
            
            if je_poslednji:
                pygame.draw.rect(screen, (255, 215, 0), (x_offset - 10, y_offset - 10, 220, 120), 3, border_radius=10)
            
            for i, k in enumerate(stih):
                slika = self.gui.slike_karata.get(k)
                if slika:
                    rect = pygame.Rect(x_offset + i*70, y_offset, 70, 100)
                    screen.blit(slika, rect)
                    pygame.draw.rect(screen, CRNA, rect, 1, border_radius=3)
        
        zatvori = FONT_SMALL.render("[ Klikni bilo gde za zatvaranje ]", True, ZLATNA)
        screen.blit(zatvori, (SCREEN_W//2 - zatvori.get_width()//2, SCREEN_H - 40))

    def nacrtaj_desni_panel(self, screen):
        rh = self.gui.round_history

        rh.tab_rects = []
        rh.details_button_rect = None

        tab_x = 811
        tab_y = 11
        tab_w = 178

        self.nacrtaj_score_tabove(screen, tab_x, tab_y, tab_w)
        
        tabela_x = 815
        tabela_y = tab_y + 35
        tabela_w = 170
        tabela_h = 560

        self.nacrtaj_score_tabelu(screen, tabela_x, tabela_y, tabela_w, tabela_h)

        dugme_x = 810
        dugme_y = 620
        dugme_w = 180
        dugme_h = 70

        self.nacrtaj_dugme_detalji_rundi(screen, dugme_x, dugme_y, dugme_w, dugme_h)

    def nacrtaj_score_tabove(self, screen, x, y, w):
        rh = self.gui.round_history
        tabovi = [(2, "Levi"), (0, "Ja"), (1, "Desni")]
        tab_w = w // 3

        for i, (pid, label) in enumerate(tabovi):
            trenutni_w = tab_w if i < 2 else w - (tab_w * 2)
            rect = pygame.Rect(x + i * tab_w, y, trenutni_w, 28)
            aktivan = rh.selected_score_player == pid
            boja = BELA if aktivan else (220, 220, 220)

            pygame.draw.rect(screen, boja, rect, border_top_left_radius=4 if i==0 else 0, border_top_right_radius=4 if i==2 else 0)
            pygame.draw.rect(screen, CRNA, rect, 1, border_top_left_radius=4 if i==0 else 0, border_top_right_radius=4 if i==2 else 0)

            txt = FONT_BOLD.render(label, True, CRVENA_PANEL) if aktivan else FONT_SMALL.render(label, True, CRNA)
            screen.blit(txt, (rect.x + (rect.w - txt.get_width()) // 2, rect.y + (rect.h - txt.get_height()) // 2))
            rh.tab_rects.append((rect, pid))
            
        pygame.draw.line(screen, CRNA, (x, y + 27), (x + w - 1, y + 27), 1)
        for rect, pid in rh.tab_rects:
            if rh.selected_score_player == pid:
                pygame.draw.line(screen, BELA, (rect.left + 1, rect.bottom - 1), (rect.right - 2, rect.bottom - 1), 2)

    def nacrtaj_score_tabelu(self, screen, x, y, w, h):
        rh = self.gui.round_history
        pid = rh.selected_score_player
        rows = rh.score_history.get(pid, [])
        levo_id, desno_id = rh.score_redosled(pid)

        col_w = w // 3
        row_h = 18

        headers = [rh.ime(levo_id), "Bula", rh.ime(desno_id)]
        header_rect = pygame.Rect(x, y, w - 2, row_h)
        pygame.draw.rect(screen, (220, 220, 220), header_rect)
        pygame.draw.rect(screen, CRNA, header_rect, 1)

        for i, header in enumerate(headers):
            txt = FONT_SMALL.render(header, True, CRNA)
            tx = x + i * col_w + (col_w - txt.get_width()) // 2
            screen.blit(txt, (tx, y + 2))

        y += row_h
        max_rows = max(1, (h - 20) // row_h)
        visible_rows = rows[-max_rows:]

        for row in visible_rows:
            row_rect = pygame.Rect(x, y, w - 2, row_h)
            pygame.draw.rect(screen, (245, 245, 245), row_rect)
            
            pygame.draw.line(screen, CRNA, (x, y), (x, y + row_h), 1) 
            pygame.draw.line(screen, CRNA, (x + w - 3, y), (x + w - 3, y + row_h), 1) 
            pygame.draw.line(screen, CRNA, (x, y + row_h - 1), (x + w - 3, y + row_h - 1), 1) 

            if row.get("is_refa"):
                bula_col_x = x + col_w
                line_start_x = bula_col_x + 6
                line_end_x = bula_col_x + col_w - 6
                line_y = y + row_h // 2
                
                pygame.draw.line(screen, CRNA, (line_start_x, line_y), (line_end_x, line_y), 2)
                refa_obj = row.get("refa_obj", {"odigrao": {0:False, 1:False, 2:False}})
                
                if refa_obj["odigrao"][levo_id]:
                    pygame.draw.line(screen, CRNA, (line_start_x, line_y - 6), (line_start_x, line_y + 6), 2)
                if refa_obj["odigrao"][desno_id]:
                    pygame.draw.line(screen, CRNA, (line_end_x, line_y - 6), (line_end_x, line_y + 6), 2)
                if refa_obj["odigrao"][pid]:
                    mid_x = (line_start_x + line_end_x) // 2
                    pygame.draw.line(screen, CRNA, (mid_x, line_y - 6), (mid_x, line_y + 6), 2)
            else:
                values = [row.get("supa_levo", 0), row.get("bula", 0), row.get("supa_desno", 0)]
                for i, value in enumerate(values):
                    boja_txt = CRVENA_PANEL if i == 1 else CRNA
                    txt = FONT_SMALL.render(str(value), True, boja_txt)
                    tx = x + i * col_w + (col_w - txt.get_width()) // 2
                    screen.blit(txt, (tx, y + 2))
            y += row_h

    def nacrtaj_dugme_detalji_rundi(self, screen, x, y, w, h):
        rh = self.gui.round_history
        rect = pygame.Rect(x, y, w, h)
        rh.details_button_rect = rect

        ima_rundi = len(rh.rounds) > 0
        boja_dugmeta = (205, 230, 245)
        boja_hover = (185, 215, 235)
        boja_teksta = (15, 30, 40) if ima_rundi else (105, 115, 120)

        mis_pos = pygame.mouse.get_pos()
        boja_final = boja_hover if rect.collidepoint(mis_pos) else boja_dugmeta

        pygame.draw.rect(screen, boja_final, rect, border_radius=5)
        pygame.draw.rect(screen, CRNA, rect, 1, border_radius=5)

        naslov = "DETALJI RUNDI"
        podnaslov = f"{len(rh.rounds)} završeno" if ima_rundi else "Još nema rundi"

        txt1 = FONT_BOLD.render(naslov, True, boja_teksta)
        txt2 = FONT_SMALL.render(podnaslov, True, boja_teksta)

        screen.blit(txt1, (rect.x + (rect.w - txt1.get_width()) // 2, rect.y + 11))
        screen.blit(txt2, (rect.x + (rect.w - txt2.get_width()) // 2, rect.y + 34))  

    def nacrtaj_overlay_istorije_rundi(self, screen):
        rh = self.gui.round_history
        s = pygame.Surface((SCREEN_W, SCREEN_H))
        s.set_alpha(225)
        s.fill((25, 25, 25))
        screen.blit(s, (0, 0))

        overlay = pygame.Rect(40, 35, 920, 630)
        pygame.draw.rect(screen, BELA, overlay, border_radius=6)
        pygame.draw.rect(screen, CRNA, overlay, 2, border_radius=6)

        self.nacrtaj_overlay_navigaciju(screen, overlay)

        runda = rh.aktivna_runda()
        if not runda:
            txt = FONT_MSG.render("Još nema završenih rundi.", True, CRNA)
            screen.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2, 330))
            return

        self.nacrtaj_overlay_info_runde(screen, runda, overlay.x + 20, overlay.y + 55)
        self.nacrtaj_overlay_rezultat_runde(screen, runda, overlay.x + 20, overlay.y + 165)
        self.nacrtaj_overlay_stihove(screen, runda, overlay.x + 20, overlay.y + 265)

    def nacrtaj_overlay_navigaciju(self, screen, overlay):
        rh = self.gui.round_history
        naslov = f"Runda {rh.active_round_index + 1} / {len(rh.rounds)}" if rh.rounds else "Istorija rundi"
        txt = FONT_MSG.render(naslov, True, CRVENA_PANEL)
        naslov_x = overlay.centerx - txt.get_width() // 2
        naslov_y = 47
        screen.blit(txt, (naslov_x, naslov_y))

        rh.overlay_prev_rect = pygame.Rect(naslov_x - 105, 45, 90, 26)
        rh.overlay_next_rect = pygame.Rect(naslov_x + txt.get_width() + 15, 45, 90, 26)
        rh.overlay_close_rect = pygame.Rect(925, 45, 24, 24)

        pygame.draw.rect(screen, (230, 230, 230), rh.overlay_prev_rect, border_radius=4)
        pygame.draw.rect(screen, CRNA, rh.overlay_prev_rect, 1, border_radius=4)
        txt_prev = FONT_SMALL.render("< Prethodna", True, CRNA)
        screen.blit(txt_prev, (rh.overlay_prev_rect.x + (rh.overlay_prev_rect.w - txt_prev.get_width()) // 2, rh.overlay_prev_rect.y + 5))

        pygame.draw.rect(screen, (230, 230, 230), rh.overlay_next_rect, border_radius=4)
        pygame.draw.rect(screen, CRNA, rh.overlay_next_rect, 1, border_radius=4)
        txt_next = FONT_SMALL.render("Sledeća >", True, CRNA)
        screen.blit(txt_next, (rh.overlay_next_rect.x + (rh.overlay_next_rect.w - txt_next.get_width()) // 2, rh.overlay_next_rect.y + 5))

        pygame.draw.rect(screen, (240, 200, 200), rh.overlay_close_rect, border_radius=4)
        pygame.draw.rect(screen, CRNA, rh.overlay_close_rect, 1, border_radius=4)
        txt_x = FONT_BOLD.render("X", True, CRNA)
        screen.blit(txt_x, (rh.overlay_close_rect.x + (rh.overlay_close_rect.w - txt_x.get_width()) // 2, rh.overlay_close_rect.y + 3))

    def nacrtaj_overlay_info_runde(self, screen, runda, x, y):
        rh = self.gui.round_history
        nosilac = rh.ime(runda["nosilac"])
        adut = runda["adut"]
        vrednost = runda["vrednost"]

        tipovi = []
        if runda["direktna_igra"]: tipovi.append("iz ruke")
        else: tipovi.append("sa talonom")

        if runda["kontra"]:
            if runda["zvanje_igrac"] is not None: tipovi.append(f"kontra: {rh.ime(runda['zvanje_igrac'])}")
            else: tipovi.append("kontra")

        if runda["zvanje_tip"] == "zovem":
            tipovi.append(f"zovem: {rh.ime(runda['zvanje_igrac'])}")

        dodatak = ", ".join(tipovi)

        linije = [
            f"Nosilac: {nosilac}",
            f"Igra: {adut} ({dodatak})",
            f"Vrednost: {vrednost}",
        ]

        trenutni_y = y
        for linija in linije:
            txt = FONT_BOLD.render(linija, True, CRNA)
            screen.blit(txt, (x, trenutni_y))
            trenutni_y += 24

        stihovi = runda["stihovi_po_igracu"]
        stih_txt = f"Štihovi: Ja {stihovi.get(0, 0)} | Levi {stihovi.get(2, 0)} | Desni {stihovi.get(1, 0)}"
        txt = FONT_BOLD.render(stih_txt, True, CRVENA_PANEL)
        screen.blit(txt, (x, trenutni_y))

        self.nacrtaj_overlay_pocetne_karte(screen, runda, x + 350, y)

    def nacrtaj_overlay_pocetne_karte(self, screen, runda, x, y):
        naslov = FONT_BOLD.render("Početne karte igrača i talon:", True, CRVENA_PANEL)
        screen.blit(naslov, (x, y))
        y += 38

        ruke = runda.get("pocetne_ruke", [[], [], []])
        talon = runda.get("pocetni_talon", [])
        redosled = [(0, "Ja"), (2, "Levi"), (1, "Desni")]

        def nacrtaj_mini(karta, dx, dy):
            v, b = karta.split()
            znak_mapa = {'Pik': '♠', 'Karo': '♦', 'Herc': '♥', 'Tref': '♣'}
            boja_znaka = {'Pik': CRNA, 'Karo': (220, 0, 0), 'Herc': (220, 0, 0), 'Tref': CRNA}
            
            txt_v = FONT_MSG.render(v, True, CRNA)
            txt_s = FONT_MSG.render(znak_mapa.get(b, b), True, boja_znaka.get(b, CRNA))
            
            box_w = 44
            box_h = 38
            box_rect = pygame.Rect(dx, dy - 8, box_w, box_h)
            
            pygame.draw.rect(screen, BELA, box_rect, border_radius=4)
            pygame.draw.rect(screen, (150, 150, 150), box_rect, 1, border_radius=4)
            
            ukupna_sirina = txt_v.get_width() + txt_s.get_width() + 2
            pocetni_x = box_rect.x + (box_w - ukupna_sirina) // 2
            tekst_y = box_rect.y + (box_h - txt_v.get_height()) // 2 + 1
            
            screen.blit(txt_v, (pocetni_x, tekst_y))
            screen.blit(txt_s, (pocetni_x + txt_v.get_width() + 2, tekst_y))
            return box_w + 6

        red_boja = {'Pik': 0, 'Karo': 1, 'Tref': 2, 'Herc': 3}
        red_vrednosti = {'A': 0, 'K': 1, 'Q': 2, 'J': 3, '10': 4, '9': 5, '8': 6, '7': 7}
        def sortiraj_niz(niz):
            return sorted(niz, key=lambda karta: (red_boja[karta.split()[1]], red_vrednosti[karta.split()[0]]))

        def nacrtaj_status_za_igraca(pid, x, y):
            pobednik_id = runda.get("nosilac")
            adut = runda.get("adut", "")
            kontra = runda.get("kontra", False)
            refa = runda.get("refa", False)
            zvanje_tip = runda.get("zvanje_tip")
            zvanje_igrac = runda.get("zvanje_igrac")

            if refa:
                labela = "Refa"
                boja_pozadine = (150, 0, 200)
                boja_teksta = BELA
            elif pid == pobednik_id:
                labela = f"{adut}"
                boja_pozadine = (255, 215, 0)
                boja_teksta = CRNA
            elif pid == zvanje_igrac and zvanje_tip == "kontra":
                labela = "Kontra"
                boja_pozadine = (40, 100, 220)
                boja_teksta = BELA
            elif pid == zvanje_igrac and zvanje_tip == "zovem":
                labela = "Zovem"
                boja_pozadine = (40, 100, 220)
                boja_teksta = BELA
            elif zvanje_tip in ("kontra", "zovem") and pid != pobednik_id and pid != zvanje_igrac:
                labela = f"Pozvan ({zvanje_tip})"
                boja_pozadine = (40, 100, 220)
                boja_teksta = BELA
            elif kontra and pid != pobednik_id:
                labela = "Kontra"
                boja_pozadine = (40, 100, 220)
                boja_teksta = BELA
            else:
                labela = "Ne prati"
                boja_pozadine = (180, 40, 40)
                boja_teksta = BELA

            txt_surf = FONT_BOLD.render(labela, True, boja_teksta)
            rect_w = txt_surf.get_width() + 16
            rect_h = 24
            label_rect = pygame.Rect(x, y, rect_w, rect_h)
            pygame.draw.rect(screen, boja_pozadine, label_rect, border_radius=4)
            pygame.draw.rect(screen, CRNA, label_rect, 1, border_radius=4)
            screen.blit(txt_surf, (label_rect.x + 8, label_rect.y + (rect_h - txt_surf.get_height()) // 2))


        for pid, ime in redosled:
            ime_txt = FONT_SMALL.render(f"{ime}: ", True, (100, 100, 100))

            pobednik_id = runda.get("nosilac")
            adut = runda.get("adut", "")
            kontra = runda.get("kontra", False)
            refa = runda.get("refa", False)
            zvanje_tip = runda.get("zvanje_tip")
            zvanje_igrac = runda.get("zvanje_igrac")

            if refa:
                labela_test = "Refa"
            elif pid == pobednik_id:
                labela_test = f"{adut}"
            elif pid == zvanje_igrac and zvanje_tip == "kontra":
                labela_test = "Kontra"
            elif pid == zvanje_igrac and zvanje_tip == "zovem":
                labela_test = "Zovem"
            elif zvanje_tip in ("kontra", "zovem") and pid != pobednik_id and pid != zvanje_igrac:
                labela_test = f"Pozvan"
            elif kontra and pid != pobednik_id:
                labela_test = "Kontra"
            else:
                labela_test = "Ne prati"

            status_sirina = FONT_BOLD.size(labela_test)[0] + 16
            status_x = x - status_sirina - 10
            nacrtaj_status_za_igraca(pid, status_x, y + 4)
            screen.blit(ime_txt, (x, y + 4))
            kart_x = x + 40
            for karta in sortiraj_niz(ruke[pid]):
                kart_x += nacrtaj_mini(karta, kart_x, y)
            y += 42

        ime_txt = FONT_SMALL.render("Talon: ", True, (100, 100, 100))
        screen.blit(ime_txt, (x, y + 4))
        kart_x = x + 40
        for karta in sortiraj_niz(talon):
            kart_x += nacrtaj_mini(karta, kart_x, y)
    

    def nacrtaj_overlay_rezultat_runde(self, screen, runda, x, y):
        rh = self.gui.round_history
        naslov = FONT_BOLD.render("Rezultat i promene:", True, CRVENA_PANEL)
        screen.blit(naslov, (x, y))
        y += 24

        rezultat = runda["rezultat"]
        for pid in (0, 2, 1):
            if pid not in rezultat:
                continue
            tekst = f"{rh.ime(pid)}: {rezultat[pid]}"
            tekst = tekst if len(tekst) <= 75 else tekst[:72] + "..."
            txt = FONT_SMALL.render(tekst, True, CRNA)
            screen.blit(txt, (x, y))
            y += 18

    def nacrtaj_overlay_stihove(self, screen, runda, x, y):
        naslov = FONT_BOLD.render("Štihovi:", True, CRVENA_PANEL)
        screen.blit(naslov, (x, y))
        y += 25

        stihovi = runda["stihovi"]
        leva_kolona = stihovi[:5]
        desna_kolona = stihovi[5:10]

        self.nacrtaj_kolonu_stihova(screen, leva_kolona, x, y)
        self.nacrtaj_kolonu_stihova(screen, desna_kolona, x + 455, y)

    def nacrtaj_kolonu_stihova(self, screen, stihovi, x, y):
        for stih in stihovi:
            self.nacrtaj_jedan_stih(screen, stih, x, y)
            y += 66 

    def nacrtaj_jedan_stih(self, screen, stih, x, y):
        rh = self.gui.round_history
        BOX_W, BOX_H, INDEX_W = 435, 58, 65

        rect = pygame.Rect(x, y, BOX_W, BOX_H)
        pygame.draw.rect(screen, (252, 252, 252), rect, border_radius=8)
        pygame.draw.rect(screen, CRNA, rect, 1, border_radius=8)

        pobednik = stih["pobednik"]
        naslov = f"Štih {stih['broj']}"
        txt_naslov = FONT_BOLD.render(naslov, True, (40, 40, 40))
        nx = x + (INDEX_W - txt_naslov.get_width()) // 2
        ny = y + (BOX_H - txt_naslov.get_height()) // 2
        screen.blit(txt_naslov, (nx, ny))

        pygame.draw.line(screen, (210, 210, 210), (x + INDEX_W, y + 8), (x + INDEX_W, y + BOX_H - 8), 1)

        trenutni_x = x + INDEX_W + 8
        ukupno = len(stih["karte"])
        razmak_izmedju = 15 

        for idx, (pid, karta) in enumerate(stih["karte"]):
            ime = rh.kratko_ime(pid)
            ime_txt = "Ja" if ime == "Ja" else ("Desni" if ime == "D" else ("Levi" if ime == "L" else ime))

            delovi = karta.split()
            v, b = delovi[0], (delovi[1] if len(delovi) > 1 else "")

            simboli = {'Pik': '♠', 'Karo': '♦', 'Herc': '♥', 'Tref': '♣'}
            boje = {'Pik': CRNA, 'Tref': CRNA, 'Karo': (220, 0, 0), 'Herc': (220, 0, 0)}
            
            txt_i = FONT_BOLD.render(f"{ime_txt} ", True, (80, 80, 80))
            txt_v = FONT_BIG.render(v, True, CRNA)
            txt_b = FONT_BIG.render(simboli.get(b, b), True, boje.get(b, CRNA))

            w_bloka = txt_i.get_width() + txt_v.get_width() + txt_b.get_width() + 8
            h_bloka = 46 
            y_bloka = y + (BOX_H - h_bloka) // 2
            rect_bloka = pygame.Rect(trenutni_x, y_bloka, w_bloka, h_bloka)

            if pid == pobednik:
                pygame.draw.rect(screen, (230, 255, 230), rect_bloka, border_radius=6)
                pygame.draw.rect(screen, (0, 160, 0), rect_bloka, 3, border_radius=6) 
            else:
                pygame.draw.rect(screen, BELA, rect_bloka, border_radius=6)
                pygame.draw.rect(screen, (150, 150, 150), rect_bloka, 1, border_radius=6)

            unutar_x, cy = trenutni_x + 4, y_bloka + h_bloka // 2
            screen.blit(txt_i, (unutar_x, cy - txt_i.get_height() // 2))
            unutar_x += txt_i.get_width()
            screen.blit(txt_v, (unutar_x, cy - txt_v.get_height() // 2))
            unutar_x += txt_v.get_width()
            screen.blit(txt_b, (unutar_x, cy - txt_b.get_height() // 2))

            trenutni_x += w_bloka

            if idx < ukupno - 1:
                str_txt = FONT_BOLD.render("→", True, (170, 170, 170))
                sx = trenutni_x + (razmak_izmedju - str_txt.get_width()) // 2
                sy = y + (BOX_H - str_txt.get_height()) // 2
                screen.blit(str_txt, (sx, sy))
                trenutni_x += razmak_izmedju

    def nacrtaj_faza_najave(self, screen):
        w, h = 450, 280
        x = (SCREEN_W - w) // 2
        y = (SCREEN_H - h) // 2
        pygame.draw.rect(screen, BELA, (x, y, w, h), border_radius=4)
        pygame.draw.rect(screen, CRNA, (x, y, w, h), 2, border_radius=4)
        self.gui.dugmici_licitacije = []

        naslov = FONT_BOLD.render("NAJAVI NIVO IGRE", True, CRNA)
        screen.blit(naslov, (SCREEN_W//2 - naslov.get_width()//2, y + 15))

        opcije = [
            ("Najavljujem 2 (Pik)", "najava_2"),
            ("Najavljujem 3 (Karo)", "najava_3"),
            ("Najavljujem 4 (Herc)", "najava_4"),
            ("Najavljujem 5 (Tref)", "najava_5")
        ]

        if self.gui.state and len(self.gui.state.aktivni_u_licitaciji) > 1:
            opcije.append(("Slabiji sam (Dalje)", "dalje"))

        # --- DINAMIČKO RAČUNANJE VELIČINE I POZICIJE ---
        broj_opcija = len(opcije)
        dostupna_visina = h - 50 - 15
        razmak = 10
        btn_h = min(40, (dostupna_visina - (broj_opcija - 1) * razmak) // broj_opcija)
        
        ukupna_visina_elemenata = broj_opcija * btn_h + (broj_opcija - 1) * razmak
        start_y = y + 50 + (dostupna_visina - ukupna_visina_elemenata) // 2

        for i, (txt, akcija) in enumerate(opcije):
            dy = start_y + i * (btn_h + razmak)
            boja_dugmeta = (230, 230, 230)
            d = UIComponents.nacrtaj_dugme(screen, txt, x + 75, dy, 300, btn_h, boja_dugmeta)
            self.gui.dugmici_licitacije.append((d, akcija))


    def nacrtaj_kraj_runde_prikaz(self, screen):
        st = self.gui.state
        
        # 1. DODATO: Crtamo zeleni sto ispod talona u fazi KRAJ
        sto_rect = pygame.Rect(350, 230, 300, 220)
        try:
            boja_stola = TAMNO_ZELENA
        except NameError:
            boja_stola = (34, 139, 34) # Backup zelena za svaki slučaj
            
        pygame.draw.rect(screen, boja_stola, sto_rect)
        pygame.draw.rect(screen, CRNA, sto_rect, 2)
        
        # Određujemo šta su bile karte u talonu/škartu
        karte_talona = st.odbacene_karte if st.odbacene_karte else st.talon
        
        # 2. Naslov iznad karata
        txt = FONT_BOLD.render("TALON OVE RUNDE:", True, ZLATNA)
        screen.blit(txt, (SCREEN_W//2 - txt.get_width()//2, 240))

        # 3. Crtanje te dve karte u centru table
        for i, karta in enumerate(karte_talona):
            slika = self.gui.slike_karata_velike.get(karta)
            if slika:
                rect = pygame.Rect(SCREEN_W//2 - 105 + i*110, 270, 100, 140)
                screen.blit(slika, rect)
                pygame.draw.rect(screen, CRNA, rect, 1, border_radius=4)

        # 4. Dugme "PODELI" pomereno blago ispod zelenog stola
        self.gui.dugmici_licitacije = [] 
        btn_w, btn_h = 200, 50
        btn_x = SCREEN_W // 2 - btn_w // 2
        btn_y = 460 
        
        d = UIComponents.nacrtaj_dugme(screen, "PODELI SLEDEĆU", btn_x, btn_y, btn_w, btn_h, (255,255,255))
        self.gui.dugmici_licitacije.append((d, "podeli"))