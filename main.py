# main.py
import pygame
import threading
import time
from engine.game_loop import GameLoop
from agents.heuristic_bot import HeuristicBot
from agents.human_gui_agent import HumanGUIAgent
from ui.gui_manager import GUIManager
from agents.napredni_bot import NapredniBot


def run_engine(engine):
    """Beskonačna petlja koja vrti runde jednu za drugom."""
    while True:
        if engine.state.faza == "KRAJ_PARTIJE":
            print("Glavna petlja zaustavljena. Engine čeka na restart ili novu partiju.")
            break

        engine.play_round()
        time.sleep(0.5)

def main():
    pygame.init()
    
    gui = GUIManager()
    
    igrac = HumanGUIAgent(agent_id=0, ime="Ja", input_callback=gui.trazi_unos_od_igraca)
    bot1 = NapredniBot(agent_id=1, ime="Kafanski Bot 1")
    bot2 = NapredniBot(agent_id=2, ime="Kafanski Bot 2")
    
    agenti = [igrac, bot1, bot2]
    
    engine = GameLoop(agents=agenti)
    gui.povezi_sa_stanjem(engine.state)
    
    gui.engine_ref = engine
    gui.scoring = engine.scoring
    gui.round_history.zabelezi_score_snapshot(engine.scoring)
    
    # PROMENJENO: Cilj thread-a je run_engine funkcija
    engine_thread = threading.Thread(target=run_engine, args=(engine,), daemon=True)
    engine_thread.start()
    
    gui.loop()

if __name__ == "__main__":
    main()