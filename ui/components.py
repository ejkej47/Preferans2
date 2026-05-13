import pygame
from ui.constants import *

class UIComponents:
    @staticmethod
    def nacrtaj_okvir(screen, naslov, x, y, w, h):
        """Crta beli panel sa tankim crnim okvirom i crvenim naslovom"""
        pygame.draw.rect(screen, BELA, (x, y, w, h), border_radius=4)
        pygame.draw.rect(screen, CRNA, (x, y, w, h), 1, border_radius=4)
        
        if naslov:
            txt = FONT_SMALL.render(naslov, True, CRVENA_PANEL)
            screen.blit(txt, (x + 5, y + 2))

    @staticmethod
    def nacrtaj_dugme(screen, tekst, x, y, w, h, boja=(230,230,230)):
        mis_pos = pygame.mouse.get_pos()
        rect = pygame.Rect(x, y, w, h)
        
        boja_final = HOVER_PLAVA if rect.collidepoint(mis_pos) else boja
        
        pygame.draw.rect(screen, boja_final, rect, border_radius=4)
        pygame.draw.rect(screen, CRNA, rect, 1, border_radius=4)

        txt = FONT_SMALL.render(tekst, True, CRNA)
        screen.blit(txt, (x + 10, y + (h - txt.get_height()) // 2))

        return rect