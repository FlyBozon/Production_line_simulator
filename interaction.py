import pygame
import time
import random

class PresenceChecker:
    def __init__(self, game):
        self.game = game
        self.last_activity_time = time.time()
        self.check_interval = 30
        self.warning_time = 20
        self.warning_shown = False
        self.confirmation_key = random.choice([pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f])
        self.confirmation_keys = {
            pygame.K_a: "A",
            pygame.K_s: "S",
            pygame.K_d: "D",
            pygame.K_f: "F"
        }
        self.required_key = self.confirmation_keys[self.confirmation_key]
        self.alarm_active = False
    
    def update(self):
        current_time = time.time()
        inactive_time = current_time - self.last_activity_time
        
        if inactive_time > self.check_interval:
            self.alarm_active = True
            return True
        
        elif inactive_time > self.warning_time and not self.warning_shown:
            self.warning_shown = True
            self.confirmation_key = random.choice(list(self.confirmation_keys.keys()))
            self.required_key = self.confirmation_keys[self.confirmation_key]
        
        return False
    
    def reset_activity(self):
        self.last_activity_time = time.time()
        self.warning_shown = False
        self.alarm_active = False
    
    def check_confirmation(self, key):
        if self.warning_shown and key == self.confirmation_key:
            self.reset_activity()
            return True
        return False
