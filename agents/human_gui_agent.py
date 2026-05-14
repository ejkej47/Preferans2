# agents/human_gui_agent.py

class HumanGUIAgent:
    """
    Predstavlja tebe u Engine-u.
    Kada Engine zatraži potez, ovaj agent pauzira Engine thread
    i delegira zahtev GUI thread-u preko input_callback funkcije.
    """
    def __init__(self, agent_id, ime, input_callback):
        self.agent_id = agent_id
        self.ime = ime
        self.input_callback = input_callback

    def odluci_licitaciju(self, state_kopija, dozvoljeni_potezi):
        # Šaljemo signal GUI-ju da prikaže dugmiće za licitaciju
        return self.input_callback(state_kopija, "licitacija", dozvoljeni_potezi)

    def skartiraj(self, state_kopija):
        # GUI će prikazati prozor za škartiranje
        return self.input_callback(state_kopija, "skart", [])

    def izaberi_aduta(self, state_kopija, validne_boje):
        # GUI će prikazati dugmiće za izbor boje
        return self.input_callback(state_kopija, "izbor_aduta", validne_boje)

    def odluci_pratnju(self, state_kopija):
        # GUI će prikazati "Dodjem" / "Ne dodjem"
        # Očekujemo da GUI vrati boolean (True za dodjem, False za ne)
        # Ali pošto su tvoji dugmići stringovi "dodjem", mapiraćemo ovde:
        odluka_string = self.input_callback(state_kopija, "pratnja", ["dodjem", "ne dodjem"])
        return True if odluka_string == "dodjem" else False

    def odluci_kontru(self, state_kopija):
        # GUI će prikazati "Može" / "Kontra"
        return self.input_callback(state_kopija, "kontra", ["moze", "kontra"])

    def odigraj_kartu(self, state_kopija, dozvoljene_karte):
        # GUI će ti dozvoliti da klikneš samo na dozvoljene karte
        return self.input_callback(state_kopija, "igra_karta", dozvoljene_karte)
    
    def najavi_igru(self, state_kopija):
        # Ako u istoriji licitacije niko drugi nije rekao 'Igra', ne nudi se 'Dalje'
        opcije = ["najava_2", "najava_3", "najava_4", "najava_5"]
        
        # Proveravamo da li postoji realna konkurencija za Igru
        druge_igre = [s for s in state_kopija.istorija_licitacije if "Igra" in s and not s.startswith("Ja")]
        if druge_igre:
            opcije.append("dalje")
            
        odluka = self.input_callback(state_kopija, "najava_igre", opcije)
        if odluka == "dalje": return None
        return int(odluka.split("_")[1])
    
    def potvrdi_talon(self, state_kopija):
        # GUI će prikazati talon bota i čekati da klikneš "U REDU"
        return self.input_callback(state_kopija, "potvrda_talona", ["potvrdi_pregled"])
    
    def ceka_novu_ruku(self, state_kopija):
        # Šaljemo signal GUI-ju da prikaže dugme "PODELI"
        return self.input_callback(state_kopija, "kraj_runde", ["podeli"])