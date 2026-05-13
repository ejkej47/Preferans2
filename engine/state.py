# engine/state.py
import copy
import threading

class GameState:
    """
    Sadrži apsolutno sve informacije o trenutnom stanju partije.
    Ovo je jedini izvor istine koji će botovi i GUI čitati.
    """
    def __init__(self):
        self.lock = threading.RLock()

        self.faza = "FAZA_IZBORA" 
        self.na_potezu = 0
        self.prvi_licitant = 0 
        
        # Karte
        self.ruke = {0: [], 1: [], 2: []}
        self.talon = []
        self.odbacene_karte = []
        self.karte_na_stolu = [] 
        self.odnete_karte = {0: [], 1: [], 2: []}
        self.poslednji_stih_pobednik = None
        
        self.pocetne_ruke = [[], [], []]
        self.pocetni_talon = []
        
        # Licitacija
        self.aktivni_u_licitaciji = [0, 1, 2]
        self.trenutna_licitacija_broj = 2
        self.poslednja_akcija = None 
        self.pobednik_licitacije = None
        self.igra_dekleresi = {} 
        
        # Specijalne igre (Bitno za pamćenje nivoa)
        self.specijalna_igra_tip = None
        self.specijalna_igra_igrac = None
        self.specijalna_igra_nivo = 0
        
        # Zvanje i Adut
        self.adut = None
        self.igraci_koji_dolaze = {0: None, 1: None, 2: None} 
        self.moj_izbor_zvanja = None # Dodato iz starog GUI-a
        self.botovi_desili_odluku = {0: False, 1: False, 2: False}
        self.kontra_aktivan = False
        self.zvanje_tip = None 
        self.zvanje_igrac = None
        self.kontra_red = []
        self.kontra_index = 0
        self.direktna_igra = False
        
        # Obeležja poteza
        self.igraci_imali_potez_licitacije = set()
        self.igrac_imao_prvi_krug_licitacije = False
        
        # Skor i Istorija
        self.refe = {0: 0, 1: 0, 2: 0}
        self.istorija_licitacije = [] 
        self.istorija_dolaska = [] # Dodato za pregled ko je kako pratio
        self.poruka_za_ui = "Odaberi igru: Dalje, 2, Igra, Betl, Sans"

    def __getstate__(self):
        """Uklanja lock pre nego što se stanje iskopira (jer Lock ne može da se deepcopy-uje)"""
        state = self.__dict__.copy()
        if 'lock' in state:
            del state['lock']
        return state

    def __setstate__(self, state):
        """Kada se kopija napravi, dodeljuje joj novu, nezavisnu bravu"""
        self.__dict__.update(state)
        self.lock = threading.RLock()

    def kopiraj(self):
        with self.lock:
            return copy.deepcopy(self)