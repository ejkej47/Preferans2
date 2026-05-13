# engine/deck.py
import random

class Deck:
    def __init__(self, seed=None):
        self.boje = ['Pik', 'Karo', 'Herc', 'Tref']
        self.vrednosti = ['7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        self.seed = seed
        self.reset_spil()

    def reset_spil(self):
        if self.seed is not None:
            random.seed(self.seed)
            
        self.karte = [f"{v} {b}" for b in self.boje for v in self.vrednosti]
        random.shuffle(self.karte)

    def podeli(self):
        # Preferans deljenje: 5 svakome -> 2 talon -> 5 svakome
        ruke = [[], [], []]
        
        # Prvih 5
        ruke[0] = self.karte[0:5]
        ruke[1] = self.karte[5:10]
        ruke[2] = self.karte[10:15]
        
        # Talon
        talon = self.karte[15:17]
        
        # Drugih 5
        ruke[0].extend(self.karte[17:22])
        ruke[1].extend(self.karte[22:27])
        ruke[2].extend(self.karte[27:32])
        
        return ruke, talon