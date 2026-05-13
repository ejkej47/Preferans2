# engine/game_rules.py

# KONSTANTE
BOJE = ['Pik', 'Karo', 'Herc', 'Tref']
VREDNOSTI = ['7', '8', '9', '10', 'J', 'Q', 'K', 'A']
JAČINA_KARTE = {v: i for i, v in enumerate(VREDNOSTI)} # 7=0, A=7

# Vrednosti igara (licitacija)
IGRE_VREDNOST = {
    'Pik': 2, 'Karo': 3, 'Herc': 4, 'Tref': 5, 
    'Betl': 0, 'Sans': 1 
}

class GameRules:
    """Statička klasa koja sadrži isključivo pravila preferansa."""

    @staticmethod
    def ko_nosi_odnetak(karte_na_stolu, adut):
        """
        karte_na_stolu: lista tuplova [(igrac_id, "Karta Boja"), ...]
        Vraća igrac_id koji nosi ovaj štih.
        """
        prvi_igrac, prva_karta = karte_na_stolu[0]
        v_prve, b_prve = prva_karta.split()
        
        pobednik_id = prvi_igrac
        najaca_karta = prva_karta
        
        for i_id, karta in karte_na_stolu[1:]:
            v_trenutna, b_trenutna = karta.split()
            v_najaca, b_najaca = najaca_karta.split()

            # Ako je bačen adut na običnu boju
            if b_trenutna == adut and b_najaca != adut:
                pobednik_id = i_id
                najaca_karta = karta
            # Ako su obe karte u istoj boji (obe adut ili obe ista obična boja)
            elif b_trenutna == b_najaca:
                if JAČINA_KARTE[v_trenutna] > JAČINA_KARTE[v_najaca]:
                    pobednik_id = i_id
                    najaca_karta = karta
            
        return pobednik_id

    @staticmethod
    def validni_potezi(ruka, prva_karta_na_stolu, adut):
        """
        Vraća listu karata koje igrač SME da baci po pravilima preferansa.
        """
        if not prva_karta_na_stolu:
            return ruka # Prvi igrač može bilo šta

        v_prve, b_prve = prva_karta_na_stolu.split()
        
        # 1. Mora da odgovori na boju
        na_boju = [k for k in ruka if k.split()[1] == b_prve]
        if na_boju:
            return na_boju
            
        # 2. Ako nema boju, mora da seče adutom
        if adut and adut != 'Sans' and adut != 'Betl':
            na_adut = [k for k in ruka if k.split()[1] == adut]
            if na_adut:
                return na_adut
                
        # 3. Ako nema ni boju ni adut, može bilo šta
        return ruka

    @staticmethod
    def izracunaj_vrednost_igre(nivo, boja):
        """Vraća osnovnu vrednost za bodovanje."""
        if boja == 'Betl': return 6 
        if boja == 'Sans': return 7
        return IGRE_VREDNOST.get(boja, 4)
    
    @staticmethod
    def sortiraj_ruku(ruka):
        red_boja = {'Pik': 0, 'Karo': 1, 'Tref': 2, 'Herc': 3}
        red_vrednosti = {'A': 0, 'K': 1, 'Q': 2, 'J': 3, '10': 4, '9': 5, '8': 6, '7': 7}
        return sorted(ruka, key=lambda k: (red_boja[k.split()[1]], red_vrednosti[k.split()[0]]))