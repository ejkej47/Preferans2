# ui/input_handler.py
import pygame

class InputHandler:
    """Obrađuje klikove mišem samo kada je korisnik na potezu."""
    
    def handle_click(self, pos, gui):
        # 1. PRVO PROVERI DA LI JE KLIK NA ISTORIJU RUNDI (UI overlay i tabovi)
        # Ako jeste, handle_click će vratiti True i mi prekidamo dalju obradu.
        if gui.round_history.handle_click(pos):
            return
            
        # 2. Zatvaranje pop-upa za pregled odnetih karata
        if gui.prikaz_odnetih is not None:
            gui.prikaz_odnetih = None
            return

        # 3. Provera da li je kliknuto na nečiju gomilicu (odnetih karata na stolu)
        for pid, rect in gui.gomilice_rects.items():
            if rect.collidepoint(pos):
                gui.prikaz_odnetih = pid
                return

        # 4. Ako Engine trenutno ne čeka naš unos (npr. bot igra), ignoriši ostale klikove
        if not gui.ceka_se_unos:
            return

        # 2. Rešavanje klika u zavisnosti od toga šta Engine traži
        if gui.tip_unosa == "licitacija":
            self._handle_licitacija_klik(pos, gui)
            
        elif gui.tip_unosa == "igra_iz_ruke":
            self._handle_igra_iz_ruke_klik(pos, gui)

        elif gui.tip_unosa == "najava_igre":
            self._handle_genericki_dugmici(pos, gui)
            
        elif gui.tip_unosa == "skart":
            self._handle_skart_klik(pos, gui)
            
        elif gui.tip_unosa == "izbor_aduta":
            self._handle_izbor_aduta_klik(pos, gui)
            
        elif gui.tip_unosa in ["pratnja", "kontra", "najava"]:
            self._handle_genericki_dugmici(pos, gui)
            
        elif gui.tip_unosa == "igra_karta":
            self._handle_bacanje_karte(pos, gui)

        elif gui.tip_unosa == "potvrda_talona":
            for rect, akcija in gui.dugmici_licitacije:
                if rect.collidepoint(pos):
                    self._prosledi_odluku(gui, "ok")

        elif gui.tip_unosa == "kraj_runde":
            self._handle_genericki_dugmici(pos, gui)


    def _handle_licitacija_klik(self, pos, gui):
        """Proverava da li je kliknuto na neko od dugmadi za licitaciju."""
        for rect, akcija in gui.dugmici_licitacije:
            if rect.collidepoint(pos):
                if akcija in gui.dozvoljeni_potezi:
                    self._prosledi_odluku(gui, akcija)
                break

    def _handle_igra_iz_ruke_klik(self, pos, gui):
        for rect, akcija in gui.dugmici_licitacije:
            if rect.collidepoint(pos):
                if akcija in gui.dozvoljeni_potezi:
                    self._prosledi_odluku(gui, akcija)
                break

    def _handle_genericki_dugmici(self, pos, gui):
        """Univerzalna provera za jednostavne izbore (Pratim/Ne pratim, Može/Kontra)"""
        for rect, akcija in gui.dugmici_licitacije:
            if rect.collidepoint(pos):
                self._prosledi_odluku(gui, akcija)
                break

    def _handle_skart_klik(self, pos, gui):
        # 1. Dugme potvrdi
        if gui.dugme_potvrdi_skart and gui.dugme_potvrdi_skart.collidepoint(pos):
            if len(gui.karte_za_skart) == 2:
                # Odluka su dve karte koje smo skartirali
                odluka = list(gui.karte_za_skart) 
                gui.karte_za_skart = []
                self._prosledi_odluku(gui, odluka)
                return

        # 2. Pomeranje karata Ruka <-> Skart
        for rect, karta, tip in reversed(gui.rects):
            if rect.collidepoint(pos):
                if tip == 'skart':
                    gui.karte_za_skart.remove(karta)
                    # Vraćamo vizuelno u ruku
                elif tip == 'ruka':
                    if len(gui.karte_za_skart) < 2:
                        gui.karte_za_skart.append(karta)
                break

    def _handle_izbor_aduta_klik(self, pos, gui):
        for rect, boja in gui.dugmici_licitacije: # Ovde su dugmici napunjeni bojama
            if rect.collidepoint(pos):
                if boja in gui.dozvoljeni_potezi:
                    self._prosledi_odluku(gui, boja)
                break

    def _handle_bacanje_karte(self, pos, gui):
        """Kada Engine čeka da bacimo kartu na sto."""
        for rect, karta, tip in reversed(gui.rects):
            if rect.collidepoint(pos) and tip == 'ruka':
                if karta in gui.dozvoljeni_potezi:
                    self._prosledi_odluku(gui, karta)
                else:
                    print(f"Nevalidan potez! Dozvoljeno je: {gui.dozvoljeni_potezi}")
                break

    def _prosledi_odluku(self, gui, odluka):
        """Završava čekanje i budi Engine iz pauze."""
        gui.odluka_igraca = odluka
        gui.ceka_se_unos = False
        gui.tip_unosa = None