# agents/base_agent.py

class BaseAgent:
    """
    Osnovna klasa (Interface) koju svaki bot ili čovek mora da nasledi.
    Definiše koje sve odluke agent mora da donese tokom partije.
    Sve metode uvek dobijaju `state` (GameState objekat).
    """
    def __init__(self, agent_id, ime="Bot"):
        self.id = agent_id
        self.ime = ime

    def odluci_licitaciju(self, state, moguci_potezi):
        """Vraća string (npr. 'dalje', 'moje') ili int (broj koji licitira)."""
        raise NotImplementedError

    def odluci_igru_iz_ruke(self, state):
        """Kada se prijavljuje specijalna igra (Igra, Betl, Sans)."""
        raise NotImplementedError

    def najavi_igru(self, state):
        """Kada pobedi sa 'Igra', prijavljuje nivo koji najavljuje (int) ili 0 za 'dalje'."""
        raise NotImplementedError

    def skartiraj(self, state):
        """Vraća listu od tačno dve karte (stringovi) koje izbacuje iz ruke."""
        raise NotImplementedError

    def izaberi_aduta(self, state, validne_boje):
        """Vraća izabranu boju (string)."""
        raise NotImplementedError

    def odluci_pratnju(self, state):
        """Vraća boolean: True (prati/dolazi) ili False (ne prati)."""
        raise NotImplementedError

    def odluci_kontru(self, state):
        """Vraća string: 'moze', 'kontra', 'zovem', itd."""
        raise NotImplementedError

    def odigraj_kartu(self, state, validne_karte):
        """Bira i vraća kartu (string) koju baca na sto."""
        raise NotImplementedError
    
    def potvrdi_talon(self, state):
        """Pauzira igru dok se talon ne pregleda."""
        raise NotImplementedError
    
    def ceka_novu_ruku(self, state):
        """Metoda koja zaustavlja engine na kraju runde."""
        raise NotImplementedError