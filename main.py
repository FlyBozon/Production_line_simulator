import pygame
import sys
import logging
from game import Game
from menu_window import MenuWindow

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('ProductionLineSimulator')


def main():
    pygame.init()
    pygame.display.set_caption("Production Line Simulator")
    
    while True:
        menu = MenuWindow()
        menu.menu_loop()
        
        if menu.authenticate_user():
            game = Game(menu.login_input)
            result = game.run()
            
            if result == "logout":
                logger.info(f"User {menu.login_input} logged out")
                continue
            else:
                break
        else:
            break
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()