class RoundHistory:
    def __init__(self):
        self.selected_score_player = 0
        self.show_round_overlay = False
        self.active_round_index = 0

        self.current_tricks = []
        self.rounds = []
        self.score_history = {
            0: [],
            1: [],
            2: [],
        }

        self.tab_rects = []
        self.details_button_rect = None
        self.overlay_close_rect = None
        self.overlay_prev_rect = None
        self.overlay_next_rect = None

    def ime(self, pid):
        if pid == 0:
            return "Ja"
        if pid == 1:
            return "Desni"
        if pid == 2:
            return "Levi"
        return f"Igrač {pid}"

    def kratko_ime(self, pid):
        if pid == 0:
            return "Ja"
        if pid == 1:
            return "D"
        if pid == 2:
            return "L"
        return str(pid)

    def score_redosled(self, pid):
        redosled = {
            0: (2, 1),
            1: (0, 2),
            2: (1, 0),
        }
        return redosled[pid]

    def zabelezi_score_snapshot(self, scoring):
        for pid in (0, 1, 2):
            levo_id, desno_id = self.score_redosled(pid)
            self.score_history[pid].append({
                "levo_id": levo_id,
                "desno_id": desno_id,
                "supa_levo": scoring.supe[pid][levo_id],
                "bula": scoring.bula[pid],
                "supa_desno": scoring.supe[pid][desno_id],
            })

    def resetuj_trenutnu_rundu(self):
        self.current_tricks = []

    def zabelezi_stih(self, karte_na_stolu, pobednik):
        self.current_tricks.append({
            "broj": len(self.current_tricks) + 1,
            "karte": list(karte_na_stolu),
            "pobednik": pobednik,
        })

    def zabelezi_rundu(
        self,
        nosilac_id,
        adut,
        vrednost,
        direktna_igra,
        kontra,
        zvanje_tip,
        zvanje_igrac,
        stihovi_po_igracu,
        rezultat,
        stihovi_lista=None,  # DODATO: Prima listu iz engine-a
        pocetne_ruke=None,
        pocetni_talon=None
    ):
        runda = {
            "broj": len(self.rounds) + 1,
            "nosilac": nosilac_id,
            "adut": adut,
            "vrednost": vrednost,
            "direktna_igra": direktna_igra,
            "kontra": kontra,
            "zvanje_tip": zvanje_tip,
            "zvanje_igrac": zvanje_igrac,
            "stihovi_po_igracu": dict(stihovi_po_igracu),
            "rezultat": dict(rezultat),
            "stihovi": stihovi_lista if stihovi_lista else [], # DODATO
            "pocetne_ruke": pocetne_ruke if pocetne_ruke else [[], [], []],
            "pocetni_talon": pocetni_talon if pocetni_talon else []
        }

        self.rounds.append(runda)
        self.active_round_index = len(self.rounds) - 1

    def aktivna_runda(self):
        if not self.rounds:
            return None

        self.active_round_index = max(
            0,
            min(self.active_round_index, len(self.rounds) - 1)
        )

        return self.rounds[self.active_round_index]

    def prethodna_runda(self):
        if self.rounds:
            self.active_round_index = max(0, self.active_round_index - 1)

    def sledeca_runda(self):
        if self.rounds:
            self.active_round_index = min(len(self.rounds) - 1, self.active_round_index + 1)

    def otvori_overlay(self):
        if self.rounds:
            self.active_round_index = len(self.rounds) - 1
        self.show_round_overlay = True

    def zatvori_overlay(self):
        self.show_round_overlay = False

    def handle_click(self, pos):
        if self.show_round_overlay:
            if self.overlay_close_rect and self.overlay_close_rect.collidepoint(pos):
                self.zatvori_overlay()
                return True

            if self.overlay_prev_rect and self.overlay_prev_rect.collidepoint(pos):
                self.prethodna_runda()
                return True

            if self.overlay_next_rect and self.overlay_next_rect.collidepoint(pos):
                self.sledeca_runda()
                return True

            return True

        for rect, pid in self.tab_rects:
            if rect.collidepoint(pos):
                self.selected_score_player = pid
                return True

        if self.details_button_rect and self.details_button_rect.collidepoint(pos):
            self.otvori_overlay()
            return True

        return False
    
    def dodaj_refa_red(self):
        """Dodaje specijalan red za refu u istoriju skorova svih igrača"""
        # Objekat se deli, pa kada se updejtuje kod jednog, videće se kod svih
        refa_obj = {"odigrao": {0: False, 1: False, 2: False}}
        for pid in (0, 1, 2):
            self.score_history[pid].append({
                "is_refa": True,
                "refa_obj": refa_obj
            })

    def oznaci_refu_odigranom(self, pid):
        """Kada igrač odigra igru pod refom, obeležava njegov deo refe vizuelno"""
        # Tražimo prvu najstariju refu koja nije odigrana od strane ovog igrača
        if not self.score_history[0]: 
            return
            
        for row in self.score_history[0]: # Gledamo bilo čiju listu jer dele isti refa_obj
            if row.get("is_refa"):
                if not row["refa_obj"]["odigrao"][pid]:
                    row["refa_obj"]["odigrao"][pid] = True
                    break