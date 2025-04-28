import pygame
import sys
import math
import random
import logging
import json
import psutil
import threading
import time
from constants import *
from interaction import PresenceChecker
from menu_window import MenuWindow
from production import ProductionLine, BackgroundProductionLine, SystemMonitor, Screw


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('ProductionLineSimulator')

class Game:
    def __init__(self, username):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Production Line Simulator")
        self.clock = pygame.time.Clock()
        
        self.font = pygame.font.SysFont('Arial', 24)
        self.small_font = pygame.font.SysFont('Arial', 18)
        self.large_font = pygame.font.SysFont('Arial', 32)
        self.title_font = pygame.font.SysFont('Arial', 36, bold=True)
        
        self.system_monitor = SystemMonitor()
        self.production_line = ProductionLine(self.system_monitor)
        self.presence_checker = PresenceChecker(self)
        
        self.running = True
        self.paused = False
        self.username = username
        self.start_time = time.time()
        self.score = 0
        self.level = 1
        
        self.buttons = {
            'defective': pygame.Rect(SCREEN_WIDTH // 2 - 150, 430, 140, 40),
            'good': pygame.Rect(SCREEN_WIDTH // 2 + 10, 430, 140, 40),
        }
        self.extinguisher_button = pygame.Rect(SCREEN_WIDTH - 150, 150, 120, 50)
        
        self.monitor_thread = threading.Thread(target=self.monitor_system, daemon=True)
        self.monitor_thread.start()
    
    def monitor_system(self):
        while self.running:
            self.system_monitor.update_system_info()
            time.sleep(1)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if not self.presence_checker.alarm_active:
                    self.presence_checker.check_confirmation(event.key)
                
                if event.key == pygame.K_ESCAPE:
                    self.paused = not self.paused
                elif event.key == pygame.K_d:
                    if not self.paused:
                        self.production_line.mark_defective()
                elif event.key == pygame.K_g:
                    if not self.paused:
                        self.production_line.mark_good()
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not self.presence_checker.alarm_active:
                    self.presence_checker.reset_activity()
                
                mouse_pos = pygame.mouse.get_pos()
                
                self.production_line.select_screw(mouse_pos)
                
                if self.buttons['defective'].collidepoint(mouse_pos):
                    self.production_line.mark_defective()
                elif self.buttons['good'].collidepoint(mouse_pos):
                    self.production_line.mark_good()
                    
                if self.production_line.critical_failure and self.extinguisher_button.collidepoint(mouse_pos):
                    if self.production_line.fire_intensity < 4.0:
                        self.production_line.critical_failure = False
                        self.production_line.fire_particles = []
                        self.production_line.machine_health += 20
                        self.production_line.add_warning("Fire extinguished successfully!")
                    else:
                        self.production_line.add_warning("Fire too intense! Cannot extinguish!")
    
    def update(self):
        if self.paused:
            return
        
        system_info = self.system_monitor.update_system_info()
        
        current_time = time.time()
        self.production_line.update(current_time)
        
        should_logout = self.presence_checker.update()
        if should_logout:
            self.running = False
            logger.warning(f"User {self.username} logged out due to inactivity")
        
        self.score = (self.production_line.good_count * 10 + 
                     self.production_line.defective_count * 20 - 
                     self.production_line.missed_defects * 15 -
                     self.production_line.false_positives * 10)
        
        total_inspected = self.production_line.good_count + self.production_line.defective_count
        self.level = 1 + total_inspected // 20
        
        if self.level > 1:
            target_rate = min(1.0 + (self.level - 1) * 0.1, 2.0)
            self.production_line.production_rate = min(target_rate, self.production_line.production_rate + 0.01)
            logger.info(f"Level up to {self.level}! Production speed: {self.production_line.production_rate:.1f}x")
    
    def draw_fire_alarm(self):
        if self.production_line.critical_failure:
            flash_intensity = (math.sin(time.time() * 10) + 1) / 2
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 0, 0, int(100 * flash_intensity)))
            self.screen.blit(overlay, (0, 0))
            
            pulse_size = int(36 + flash_intensity * 8)
            alarm_font = pygame.font.SysFont('Arial', pulse_size, bold=True)
            alarm_text = alarm_font.render("CRITICAL FAILURE - FIRE DETECTED", True, (255, 255, 0))
            alarm_rect = alarm_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
            self.screen.blit(alarm_text, alarm_rect)

            if self.production_line.critical_failure:
                pygame.draw.rect(self.screen, (200, 50, 50), self.extinguisher_button)
                pygame.draw.rect(self.screen, (150, 30, 30), self.extinguisher_button, 3)
                extinguisher_text = self.font.render("EXTINGUISH", True, WHITE)
                extinguisher_rect = extinguisher_text.get_rect(center=self.extinguisher_button.center)
                self.screen.blit(extinguisher_text, extinguisher_rect)
            
            self.draw_text("EMERGENCY PROCEDURES ACTIVATED", SCREEN_WIDTH // 2 - 200, 200, color=(255, 200, 0))
            self.draw_text("SYSTEM WILL SHUT DOWN AUTOMATICALLY", SCREEN_WIDTH // 2 - 220, 230, color=(255, 200, 0))

            if hasattr(self.production_line, 'exploded') and self.production_line.exploded:
                time_since_explosion = time.time() - self.production_line.explosion_time
                
                if time_since_explosion < 3.0:
                    flash_alpha = max(0, 255 - int(time_since_explosion * 85))
                    flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                    
                    if time_since_explosion < 0.2:
                        flash_surface.fill((255, 255, 255, flash_alpha))
                    else:
                        flash_surface.fill((255, 0, 0, flash_alpha))
                        
                    self.screen.blit(flash_surface, (0, 0))
                    
                    explosion_size = int(72 * (1 - time_since_explosion/3))
                    explosion_font = pygame.font.SysFont('Arial', explosion_size, bold=True)
                    explosion_text = explosion_font.render("CATASTROPHIC FAILURE", True, (255, 255, 0))
                    text_rect = explosion_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                    self.screen.blit(explosion_text, text_rect)
    
    def draw_dashboard(self):
        panel_rect = pygame.Rect(50, 500, SCREEN_WIDTH - 100, 250)
        
        metrics_rect = pygame.Rect(panel_rect.x + 20, panel_rect.y + 20, 300, 210)
        pygame.draw.rect(self.screen, (30, 30, 50), metrics_rect)
        pygame.draw.rect(self.screen, (80, 80, 120), metrics_rect, 2)
        
        self.draw_text("SYSTEM DIAGNOSTICS", metrics_rect.x + 10, metrics_rect.y + 10, color=(200, 200, 255))
        
        temp_y = metrics_rect.y + 50
        self.draw_text(f"CPU Temp: {self.system_monitor.cpu_temp:.1f}°C", 
                      metrics_rect.x + 10, temp_y, small=True)
        
        bar_width = 200
        bar_height = 15
        bar_x = metrics_rect.x + 10
        bar_y = temp_y + 20
        pygame.draw.rect(self.screen, (50, 50, 70), (bar_x, bar_y, bar_width, bar_height))
        
        temp_ratio = min(1.0, max(0.0, self.system_monitor.cpu_temp / 100))
        temp_width = int(bar_width * temp_ratio)
        
        if temp_ratio < 0.5:
            r = int(255 * (temp_ratio * 2))
            g = 255
        else:
            r = 255
            g = int(255 * (2 - temp_ratio * 2))
        temp_color = (r, g, 0)
        
        pygame.draw.rect(self.screen, temp_color, (bar_x, bar_y, temp_width, bar_height))
        
        usage_y = bar_y + 30
        self.draw_text(f"CPU Usage: {self.system_monitor.cpu_usage:.1f}%", 
                      metrics_rect.x + 10, usage_y, small=True)
        
        usage_bar_y = usage_y + 20
        pygame.draw.rect(self.screen, (50, 50, 70), (bar_x, usage_bar_y, bar_width, bar_height))
        usage_width = int(bar_width * self.system_monitor.cpu_usage / 100)
        pygame.draw.rect(self.screen, (100, 100, 200), (bar_x, usage_bar_y, usage_width, bar_height))
        
        fan_y = usage_bar_y + 30
        self.draw_text(f"Fan Speed: {self.system_monitor.fan_speed} RPM", 
                      metrics_rect.x + 10, fan_y, small=True)
        
        ram_y = fan_y + 25
        self.draw_text(f"RAM Usage: {self.system_monitor.ram_usage:.1f}%", 
                      metrics_rect.x + 10, ram_y, small=True)
        
        stats_rect = pygame.Rect(metrics_rect.right + 20, panel_rect.y + 20, 300, 210)
        pygame.draw.rect(self.screen, (30, 30, 50), stats_rect)
        pygame.draw.rect(self.screen, (80, 80, 120), stats_rect, 2)
        
        self.draw_text("PRODUCTION STATISTICS", stats_rect.x + 10, stats_rect.y + 10, color=(200, 200, 255))
        
        stats_y = stats_rect.y + 50
        self.draw_text(f"Good Products: {self.production_line.good_count}", 
                      stats_rect.x + 10, stats_y, small=True, color=(100, 200, 100))
        
        self.draw_text(f"Defective Products: {self.production_line.defective_count}", 
                      stats_rect.x + 10, stats_y + 25, small=True, color=(200, 100, 100))
        
        self.draw_text(f"Missed Defects: {self.production_line.missed_defects}", 
                      stats_rect.x + 10, stats_y + 50, small=True, color=(200, 150, 50))
        
        self.draw_text(f"False Positives: {self.production_line.false_positives}", 
                      stats_rect.x + 10, stats_y + 75, small=True, color=(200, 150, 150))
        
        status_color = (100, 200, 100)
        if self.production_line.machine_status == "Critical Condition":
            status_color = (200, 50, 50)
        elif self.production_line.machine_status == "Maintenance Required":
            status_color = (200, 150, 50)
        elif self.production_line.machine_status == "Minor Issues":
            status_color = (150, 150, 50)
        
        self.draw_text(f"Machine Status: {self.production_line.machine_status}", 
                      stats_rect.x + 10, stats_y + 110, small=True, color=status_color)
        
        health_y = stats_y + 135
        self.draw_text(f"Machine Health:", stats_rect.x + 10, health_y, small=True)
        
        health_bar_y = health_y + 20
        pygame.draw.rect(self.screen, (50, 50, 70), (stats_rect.x + 10, health_bar_y, bar_width, bar_height))
        
        health_ratio = self.production_line.machine_health / 100
        health_width = int(bar_width * health_ratio)
        
        if health_ratio < 0.3:
            health_color = (200, 50, 50)
        elif health_ratio < 0.6:
            health_color = (200, 150, 50)
        else:
            health_color = (50, 200, 50)
            
        pygame.draw.rect(self.screen, health_color, (stats_rect.x + 10, health_bar_y, health_width, bar_height))
        
        score_rect = pygame.Rect(stats_rect.right + 20, panel_rect.y + 20, 
                               panel_rect.right - stats_rect.right - 40, 100)
        pygame.draw.rect(self.screen, (30, 30, 50), score_rect)
        pygame.draw.rect(self.screen, (80, 80, 120), score_rect, 2)
        
        score_text = self.large_font.render(f"SCORE: {self.score}", True, (200, 200, 255))
        self.screen.blit(score_text, (score_rect.x + 20, score_rect.y + 20))
        
        level_text = self.large_font.render(f"LEVEL: {self.level}", True, (200, 200, 255))
        self.screen.blit(level_text, (score_rect.x + 20, score_rect.y + 60))
        
        user_rect = pygame.Rect(score_rect.x, score_rect.bottom + 10, 
                              score_rect.width, 100)
        pygame.draw.rect(self.screen, (30, 30, 50), user_rect)
        pygame.draw.rect(self.screen, (80, 80, 120), user_rect, 2)
        
        self.draw_text(f"Operator: {self.username}", user_rect.x + 20, user_rect.y + 20, small=True)
        
        session_time = int(time.time() - self.start_time)
        hours = session_time // 3600
        minutes = (session_time % 3600) // 60
        seconds = session_time % 60
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.draw_text(f"Session Time: {time_str}", user_rect.x + 20, user_rect.y + 50, small=True)
        
        speed_text = f"Production Speed: {self.production_line.production_rate:.2f}x"
        self.draw_text(speed_text, user_rect.x + 20, user_rect.y + 70, small=True)

        instr_rect = pygame.Rect(20, SCREEN_HEIGHT - 60, SCREEN_WIDTH - 40, 40)
        pygame.draw.rect(self.screen, (30, 30, 50, 220), instr_rect)
        pygame.draw.rect(self.screen, (80, 80, 120), instr_rect, 2)
        
        self.draw_text("INSTRUCTIONS: Click on defective screws to remove them from the production line",
                instr_rect.x + 20, instr_rect.y + 10, small=True)
    
    def draw_warning_messages(self):
        for i, warning in enumerate(self.production_line.warning_messages[-3:]):
            age = pygame.time.get_ticks() - warning['time']
            alpha = int(255 * (1 - age / 5000))
            
            warning_surface = self.small_font.render(warning['message'], True, (255, 200, 50))
            warning_surface.set_alpha(alpha)
            self.screen.blit(warning_surface, (20, SCREEN_HEIGHT - 180 + i * 25))
    
    def draw_presence_warning(self):
        if self.presence_checker.warning_shown:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))
            
            warning_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 100, 400, 200)
            pygame.draw.rect(self.screen, (50, 50, 70), warning_rect)
            pygame.draw.rect(self.screen, (200, 50, 50), warning_rect, 3)
            
            warning_title = self.large_font.render("ATTENTION REQUIRED", True, (255, 100, 100))
            warning_title_rect = warning_title.get_rect(center=(SCREEN_WIDTH // 2, warning_rect.y + 40))
            self.screen.blit(warning_title, warning_title_rect)
            
            key_text = self.font.render(f"Press '{self.presence_checker.required_key}' to confirm presence", 
                                      True, WHITE)
            key_rect = key_text.get_rect(center=(SCREEN_WIDTH // 2, warning_rect.y + 100))
            self.screen.blit(key_text, key_rect)
            
            countdown = int(self.presence_checker.check_interval - 
                          (time.time() - self.presence_checker.last_activity_time))
            count_text = self.font.render(f"System logout in: {countdown} seconds", True, 
                                        (255, 150, 150))
            count_rect = count_text.get_rect(center=(SCREEN_WIDTH // 2, warning_rect.y + 150))
            self.screen.blit(count_text, count_rect)
    
    def draw_alarm(self):
        if self.presence_checker.alarm_active:
            flash_intensity = (math.sin(time.time() * 10) + 1) / 2
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 0, 0, int(100 * flash_intensity)))
            self.screen.blit(overlay, (0, 0))
            
            alarm_text = self.title_font.render("OPERATOR ABSENCE DETECTED", True, WHITE)
            alarm_rect = alarm_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(alarm_text, alarm_rect)
            
            logout_text = self.large_font.render("Logging out...", True, WHITE)
            logout_rect = logout_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            self.screen.blit(logout_text, logout_rect)
    
    def draw_text(self, text, x, y, selected=False, small=False, color=None):
        if color is None:
            color = (0, 255, 0) if selected else (255, 255, 255)
        font = self.small_font if small else self.font
        rendered = font.render(text, True, color)
        self.screen.blit(rendered, (x, y))
        return rendered
    
    def draw(self):
        self.screen.fill((20, 20, 35))
        
        self.production_line.draw(self.screen)
        
        self.draw_dashboard()
        
        self.draw_warning_messages()

        self.draw_fire_alarm()
        
        self.draw_presence_warning()
        
        self.draw_alarm()
        
        if self.paused:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))
            
            pause_text = self.title_font.render("PAUSED", True, WHITE)
            pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(pause_text, pause_rect)
            
            resume_text = self.font.render("Press ESC to resume", True, WHITE)
            resume_rect = resume_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            self.screen.blit(resume_text, resume_rect)
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
        
        return "logout"
