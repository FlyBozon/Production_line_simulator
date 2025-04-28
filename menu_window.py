import pygame
from production import ProductionLine, BackgroundProductionLine, Screw
from constants import *
import json
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('ProductionLineSimulator')


class MenuWindow:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Production Line Simulator")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 24)
        self.title_font = pygame.font.SysFont('Arial', 36, bold=True)
        self.small_font = pygame.font.SysFont('Arial', 18)

        self.background = BackgroundProductionLine()

        self.error_message = ""
        self.active_input = ""
        self.login_input = ""
        self.password_input = ""
        self.show_password = False
        
        self.load_user_database()

        self.running = True
        self.config = None
    
    def load_user_database(self):
        try:
            with open('users.json', 'r') as file:
                self.user_database = json.load(file)
            logger.info("User database loaded successfully")
        except FileNotFoundError:
            self.user_database = {
                "users": [
                    {"username": "admin", "password": "1234"},
                    {"username": "user", "password": "5678"}
                ]
            }
            with open('users.json', 'w') as file:
                json.dump(self.user_database, file, indent=4)
            logger.info("Created default user database")
        except json.JSONDecodeError:
            logger.error("Invalid JSON format in users database")
            self.user_database = {"users": []}

    def create_background(self):
        gradient_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(10 + 20 * ratio)
            g = int(10 + 30 * ratio)
            b = int(20 + 40 * ratio)
            color = (r, g, b)
            pygame.draw.line(gradient_surface, color, (0, y), (SCREEN_WIDTH, y))

        for _ in range(100):
            x = random.randint(0, SCREEN_WIDTH - 1)
            y = random.randint(0, SCREEN_HEIGHT - 1)
            brightness = random.randint(100, 200)
            size = random.randint(1, 3)
            color = (brightness, brightness, brightness)
            pygame.draw.circle(gradient_surface, color, (x, y), size)

        return gradient_surface
    
    def draw_text(self, text, x, y, selected=False, small=False, color=None):
        if color is None:
            color = (0, 255, 0) if selected else (255, 255, 255)
        font = self.small_font if small else self.font
        rendered = font.render(text, True, color)
        self.screen.blit(rendered, (x, y))
        return rendered
    
    def authenticate_user(self):
        for user in self.user_database.get("users", []):
            if user.get("username") == self.login_input and user.get("password") == self.password_input:
                logger.info(f"User {self.login_input} authenticated successfully")
                return True
        return False
    
    def render(self):
        current_time = time.time()
        self.background.update(current_time)
        self.background.draw(self.screen)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))

        title_text = "PRODUCTION LINE SIMULATOR"
        title_surface = self.title_font.render(title_text, True, (180, 200, 255))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 80))

        glow_surface = pygame.Surface((title_rect.width + 20, title_rect.height + 20), pygame.SRCALPHA)
        pulse = (math.sin(pygame.time.get_ticks() * 0.003) + 1) / 2
        glow_color = (100, 120, 255, int(100 + pulse * 100))
        pygame.draw.rect(glow_surface, glow_color, (10, 10, title_rect.width, title_rect.height), 5)
        self.screen.blit(glow_surface, (title_rect.x - 10, title_rect.y - 10))

        self.screen.blit(title_surface, title_rect)

        panel_width = 300
        panel_height = 180
        panel_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - panel_width // 2,
            SCREEN_HEIGHT // 2 - panel_height // 2,
            panel_width,
            panel_height
        )
        
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill((30, 30, 60, 180))
        self.screen.blit(panel_surface, panel_rect)
        pygame.draw.rect(self.screen, (100, 100, 200), panel_rect, 2)

        self.draw_text("Login:", panel_rect.x + 20, panel_rect.y + 20)
        login_box_rect = pygame.Rect(panel_rect.x + 20, panel_rect.y + 45, 260, 30)
        pygame.draw.rect(self.screen, (50, 50, 80), login_box_rect)
        pygame.draw.rect(self.screen, (150, 150, 255) if self.active_input == "login" else (100, 100, 150),
                         login_box_rect, 2)
        self.draw_text(self.login_input, login_box_rect.x + 10, login_box_rect.y + 5)

        self.draw_text("Password:", panel_rect.x + 20, panel_rect.y + 80)
        password_box_rect = pygame.Rect(panel_rect.x + 20, panel_rect.y + 105, 260, 30)
        pygame.draw.rect(self.screen, (50, 50, 80), password_box_rect)
        pygame.draw.rect(self.screen, (150, 150, 255) if self.active_input == "password" else (100, 100, 150),
                         password_box_rect, 2)
        
        display_password = self.password_input if self.show_password else "*" * len(self.password_input)
        self.draw_text(display_password, password_box_rect.x + 10, password_box_rect.y + 5)

        checkbox_rect = pygame.Rect(panel_rect.x + 20, panel_rect.y + 140, 20, 20)
        pygame.draw.rect(self.screen, (50, 50, 80), checkbox_rect)
        pygame.draw.rect(self.screen, (100, 100, 150), checkbox_rect, 2)
        
        if self.show_password:
            pygame.draw.line(self.screen, (255, 255, 255), 
                            (checkbox_rect.x + 5, checkbox_rect.y + 5), 
                            (checkbox_rect.x + 15, checkbox_rect.y + 15), 2)
            pygame.draw.line(self.screen, (255, 255, 255), 
                            (checkbox_rect.x + 15, checkbox_rect.y + 5), 
                            (checkbox_rect.x + 5, checkbox_rect.y + 15), 2)
        
        self.draw_text("Show password", checkbox_rect.x + 30, checkbox_rect.y + 1, small=True)

        self.login_box_rect = login_box_rect
        self.password_box_rect = password_box_rect
        self.checkbox_rect = checkbox_rect

        help_surface = pygame.Surface((SCREEN_WIDTH, 80), pygame.SRCALPHA)
        help_surface.fill((0, 0, 0, 150))
        self.screen.blit(help_surface, (0, SCREEN_HEIGHT - 80))

        self.draw_text("ENTER = Login", 50, SCREEN_HEIGHT - 70, small=True)
        self.draw_text("TAB = Switch between fields", 50, SCREEN_HEIGHT - 45, small=True)
                           
        if self.error_message:
            error_bg = pygame.Surface((300, 40), pygame.SRCALPHA)
            error_bg.fill((100, 0, 0, 180))
            error_rect = error_bg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
            self.screen.blit(error_bg, error_rect)

            error_text = self.small_font.render(self.error_message, True, (255, 150, 150))
            error_text_rect = error_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
            self.screen.blit(error_text, error_text_rect)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logger.info("Menu closed.")
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    if self.active_input == "login":
                        self.active_input = "password"
                    elif self.active_input == "password" or self.active_input is None:
                        self.active_input = "login"
                elif event.key == pygame.K_RETURN:
                    if self.authenticate_user():
                        logger.info("Starting game...")
                        self.error_message = ""
                        self.running = False
                    else:
                        self.error_message = "Invalid username or password!"
                        logger.warning(f"Failed login attempt: {self.login_input}")
                elif self.active_input:
                    if event.key == pygame.K_BACKSPACE:
                        if self.active_input == "login":
                            self.login_input = self.login_input[:-1]
                        elif self.active_input == "password":
                            self.password_input = self.password_input[:-1]
                    else:
                        if self.active_input == "login" and event.unicode.isprintable():
                            self.login_input += event.unicode
                        elif self.active_input == "password" and event.unicode.isprintable():
                            self.password_input += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()

                if self.login_box_rect and self.login_box_rect.collidepoint(mouse_pos):
                    self.active_input = "login"
                elif self.password_box_rect and self.password_box_rect.collidepoint(mouse_pos):
                    self.active_input = "password"
                elif self.checkbox_rect and self.checkbox_rect.collidepoint(mouse_pos):
                    self.show_password = not self.show_password
                else:
                    self.active_input = None

    def menu_loop(self):
        while self.running:
            self.handle_events()
            self.render()
            pygame.display.flip()
            self.clock.tick(FPS)
