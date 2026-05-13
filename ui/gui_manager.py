# ui/gui_manager.py
import pygame
import sys
import os
import time

from ui.constants import *
from ui.display_handler import DisplayHandler
from ui.round_history import RoundHistory

class GUIManager:
    def __init__(self):
        self.state = None  # Referenca na GameState iz engine-a
        
        self.round_history = RoundHistory()
        self.display_handler = DisplayHandler(self) 
        
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        
        self.slike_karata = {}
        self.slike_karata_velike = {}
        self.poledina = None
        self.ucitaj_slike()
        
        # Varijable za hvatanje klikova
        self.mis_pozicija = (0, 0)
        self.rects = []
        self.dugmici_licitacije = []
        self.dugme_potvrdi_skart = None

        self.prikaz_odnetih = None 
        self.gomilice_rects = {}
        
        self.resetuj_ui_elemente()

        # Mehanizam za sinhronizaciju sa HumanGUIAgent-om
        self.ceka_se_unos = False
        self.tip_unosa = None
        self.dozvoljeni_potezi = []
        self.odluka_igraca = None

    def povezi_sa_stanjem(self, state):
        """Povezuje GUI sa stanjem partije iz Engine-a."""
        self.state = state

    def ucitaj_slike(self):
        """Tvoj stari kod za učitavanje slika - prekopiran 1 na 1"""
        path_male = os.path.join("ui", "assets", "Karte", "Male")
        path_velike = os.path.join("ui", "assets", "Karte", "Velike")
        
        try:
            self.poledina = pygame.image.load(os.path.join(path_male, "2B.png")).convert_alpha()
            self.poledina_velika = pygame.image.load(os.path.join(path_velike, "2B.png")).convert_alpha()
        except Exception as e: 
            print(f"GREŠKA pri učitavanju poleđine (2B.png): {e}")

        # Ovaj deo simulira tvoj spil da bismo napravili imena slika (isto kao u tvom starom gui.py)
        boje = ['Pik', 'Karo', 'Herc', 'Tref']
        vrednosti = ['7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        sve_karte = [f"{v} {b}" for b in boje for v in vrednosti]

        for karta in sve_karte:
            v, b = karta.split()
            boje_map = {'Herc': 'H', 'Karo': 'D', 'Pik': 'S', 'Tref': 'C'}
            vred_map = {'7': '7', '8': '8', '9': '9', '10': 'T', 'J': 'J', 'Q': 'Q', 'K': 'K', 'A': 'A'}
            ime = f"{vred_map[v]}{boje_map[b]}.png"
            
            try:
                self.slike_karata[karta] = pygame.image.load(os.path.join(path_male, ime)).convert_alpha()
                self.slike_karata_velike[karta] = pygame.image.load(os.path.join(path_velike, ime)).convert_alpha()
            except Exception as e: 
                print(f"GREŠKA pri učitavanju slike '{ime}' za kartu {karta}: {e}")

    def trazi_unos_od_igraca(self, stanje_kopija, tip_unosa, dozvoljeni_potezi):
        """
        Poziva HumanGUIAgent. Ovde čistimo stare vizuelne elemente 
        i čekamo novi klik.
        """
        self.dugmici_licitacije = []
        self.rects = []
        self.odluka_igraca = None
        
        self.tip_unosa = tip_unosa
        self.dozvoljeni_potezi = dozvoljeni_potezi
        
        # KLJUČNA PROMENA: Talon ide pravo u prozor za škart na početku!
        if tip_unosa == "skart":
            self.karte_za_skart = list(stanje_kopija.talon)
            
        self.ceka_se_unos = True
        
        # Engine thread ovde pauzira
        while self.ceka_se_unos:
            time.sleep(0.05) 
            
        return self.odluka_igraca
    

    def loop(self):
        """Glavna Pygame petlja koja se vrti na glavnom threadu."""
        from ui.input_handler import InputHandler # Importujemo ovde da izbegnemo cirkularne importe
        
        clock = pygame.time.Clock()
        input_handler = InputHandler()
        
        # Varijable potrebne za vizuelni deo škarta
        self.karte_za_skart = []
        
        while True:
            clock.tick(60)
            self.mis_pozicija = pygame.mouse.get_pos()

            # Event loop za miša i prozor
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # Ovde ćemo ubaciti i scroll za istoriju kasnije
                if event.type == pygame.MOUSEBUTTONDOWN:
                    input_handler.handle_click(pygame.mouse.get_pos(), self)

            # --- VIZUELNI DEO ---
            if self.state is not None:
                # DODATO: Sinhronizujemo poene sa Engine-om svaki frejm
                if hasattr(self, 'engine_ref'):
                    self.osvezi_podatke_iz_enginea(self.engine_ref.scoring, self.engine_ref.zavrsene_runde)
                
                with self.state.lock:
                    self.display_handler.osvezi_ekran(self.screen)

    def osvezi_podatke_iz_enginea(self, engine_scoring, engine_istorija_rundi):
        """Sinhronizuje stanje rezultata i istoriju. Detektuje početak nove runde."""
        self.scoring = engine_scoring
        
        # PROVERA ZA RESET UI-JA
        if self.state and self.state.faza == "FAZA_IZBORA" and not self.state.istorija_licitacije:
            if self.bot_poruke.get(1, "") != "" or self.dugmici_licitacije:
                self.resetuj_ui_elemente()

        if len(self.round_history.rounds) < len(engine_istorija_rundi):
            nova_runda = engine_istorija_rundi[-1]
            
            self.round_history.zabelezi_rundu(
                nosilac_id=nova_runda.get("nosilac", 0),
                adut=nova_runda.get("adut", "Refa"),
                vrednost=nova_runda.get("vrednost", 0),
                direktna_igra=nova_runda.get("direktna_igra", False),
                kontra=nova_runda.get("kontra", False),
                zvanje_tip=nova_runda.get("zvanje_tip"),
                zvanje_igrac=nova_runda.get("zvanje_igrac"),
                stihovi_po_igracu=nova_runda.get("stihovi_po_igracu", {}),
                rezultat=nova_runda.get("rezultat", {}),
                stihovi_lista=nova_runda.get("stihovi", []),
                pocetne_ruke=nova_runda.get("pocetne_ruke", [[], [], []]),
                pocetni_talon=nova_runda.get("pocetni_talon", [])
            )
            
            # MAGIJA ZA REFU: Ako je refa, dodaj red za refu!
            if nova_runda.get("is_refa"):
                self.round_history.dodaj_refa_red()
            else:
                self.round_history.zabelezi_score_snapshot(self.scoring)
                # Ako je runda "skinula" nečiju refu, precrtaj tu refu!
                if nova_runda.get("odigrano_pod_refom"):
                    self.round_history.oznaci_refu_odigranom(nova_runda["nosilac"])

    def resetuj_ui_elemente(self):
        """Čisti sve vizuelne elemente koji ne treba da se vuku iz prošle runde."""
        self.mis_pozicija = (0, 0)
        self.rects = []
        self.dugmici_licitacije = []
        self.dugme_potvrdi_skart = None
        self.istorija_scroll = 0
        
        # Bot komunikacija (oblačići iznad botova)
        self.bot_poruke = {1: "", 2: ""}
        self.vreme_bot_poruke = {1: 0, 2: 0}
        
        # Tajmeri (ako ih koristiš za animacije ili delay)
        self.bot_timer = 0
        self.bot_licitacija_timer = 0
        
        # Skartiranje i pregled
        self.karte_za_skart = []
        self.prikaz_odnetih = None 
        self.gomilice_rects = {}