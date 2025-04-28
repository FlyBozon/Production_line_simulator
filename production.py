import pygame
import psutil
import random
from constants import *
from datetime import datetime
import math
import time

class SystemMonitor:
    def __init__(self, to_show = True):
        self.cpu_temp = 0
        self.cpu_usage = 0
        self.ram_usage = 0
        self.fan_speed = 0
        self.to_show = to_show
        if to_show:
            self.update_system_info()
        
    def update_system_info(self):
        self.cpu_usage = psutil.cpu_percent()
        
        memory = psutil.virtual_memory()
        self.ram_usage = memory.percent
        
        base_temp = 40
        usage_factor = self.cpu_usage / 100
        random_factor = random.uniform(-2, 2)
        self.cpu_temp = base_temp + (usage_factor * 40) + random_factor
        
        self.fan_speed = int(1000 + (self.cpu_temp - base_temp) * 50)
        
        if self.to_show:
            return {
                'cpu_temp': self.cpu_temp,
                'cpu_usage': self.cpu_usage,
                'ram_usage': self.ram_usage,
                'fan_speed': self.fan_speed
            }

class Screw:
    def __init__(self, x, system_monitor, speed_multiplier):
        self.x = x
        self.y = 350
        self.speed = 2 * speed_multiplier
        self.size = random.randint(18, 22)
        self.color = (180, 180, 180)
        self.selected = False
        self.inspected = False
        self.defective = self.determine_if_defective(system_monitor)
        self.defect_type = None
        if self.defective:
            self.defect_type = random.choice(['size', 'color', 'thread'])

        self.marked_for_removal = False
        self.removal_progress = 0
    
    def determine_if_defective(self, system_monitor):
        base_probability = 0.15
        
        modifier = getattr(system_monitor, 'defect_probability_modifier', 0)
        
        temp_factor = 0.005 * max(0, system_monitor.cpu_temp - 50)
        usage_factor = 0.002 * system_monitor.cpu_usage
        
        total_probability = base_probability + temp_factor + usage_factor + modifier
        return random.random() < min(0.70, total_probability)
    
    def update(self):
        if self.marked_for_removal:
            self.removal_progress += 1
            self.y += 5
            return self.removal_progress > 20
        else:
            self.x -= self.speed
            return self.x < -50
    
    def draw(self, screen):
        display_color = self.color
        if self.selected:
            display_color = (255, 255, 0)
        elif self.inspected:
            if self.defective:
                display_color = (255, 100, 100)
            else:
                display_color = (100, 255, 100)
        
        pygame.draw.circle(screen, display_color, (self.x, self.y), self.size // 2)
        
        body_length = self.size * 3
        body_width = self.size // 3
        body_rect = pygame.Rect(self.x - body_width // 2, self.y, body_width, body_length)
        pygame.draw.rect(screen, display_color, body_rect)
        
        thread_spacing = 4
        thread_width = int(body_width * 1.5)
        thread_start_x = self.x - thread_width // 2
        
        thread_defect = self.defective and self.defect_type == 'thread'
        
        for y_offset in range(self.size, body_length, thread_spacing):
            thread_y = self.y + y_offset
            
            if thread_defect and random.random() < 0.3:
                if random.random() < 0.5:
                    continue
                else:
                    thread_start_x = self.x - thread_width // 2 + random.randint(-2, 2)
                    
            pygame.draw.line(screen, DARK_GRAY, 
                            (thread_start_x, thread_y), 
                            (thread_start_x + thread_width, thread_y), 1)
        
        if self.defective and self.defect_type == 'size':
            if random.random() < 0.5:
                pygame.draw.circle(screen, (150, 150, 150), 
                                (self.x + random.randint(-3, 3), self.y + random.randint(-3, 3)), 
                                self.size // 4)
        
        if self.defective and self.defect_type == 'color':
            for _ in range(3):
                spot_x = self.x + random.randint(-self.size//2, self.size//2)
                spot_y = self.y + random.randint(0, body_length)
                spot_size = random.randint(2, 4)
                pygame.draw.circle(screen, (139, 69, 19), (spot_x, spot_y), spot_size)

class ProductionLine:
    def __init__(self, system_monitor, speed_multiplier=1.0, background_mode=False):
        self.screws = []
        self.system_monitor = system_monitor
        self.last_spawn_time = 0
        self.spawn_interval = 1.5
        self.conveyor_speed = 2
        self.production_rate = 1.0 * speed_multiplier
        self.selected_screw_index = -1
        self.good_count = 0
        self.defective_count = 0
        self.missed_defects = 0
        self.false_positives = 0
        self.temperature_warning = False
        self.machine_status = "Normal Operation"
        self.machine_health = 100
        self.warning_messages = []
        self.alert_active = False
        self.background_mode = background_mode
        self.fire_particles = []
        self.critical_failure = False
        
    def update(self, current_time):
        for screw in self.screws:
            screw.speed = self.conveyor_speed * self.production_rate
        
        if current_time - self.last_spawn_time > self.spawn_interval / self.production_rate:
            self.screws.append(Screw(SCREEN_WIDTH + 20, self.system_monitor, self.production_rate))
            self.last_spawn_time = current_time

        to_remove = []
        for i, screw in enumerate(self.screws):
            if screw.update():
                if not screw.marked_for_removal and screw.defective and not self.background_mode:
                    self.missed_defects += 1
                    self.add_warning(f"Missed defective product!")
                    self.machine_health = max(0, self.machine_health - 1.0)
                elif not screw.marked_for_removal and not screw.defective and not self.background_mode:
                    self.good_count += 1
                to_remove.append(i)
        
        for i in sorted(to_remove, reverse=True):
            self.screws.pop(i)

        if self.system_monitor.cpu_temp > 60 and not self.background_mode:
            self.temperature_warning = True
            if random.random() < 0.1:
                self.machine_health -= 0.2
                self.production_rate = max(0.7, self.production_rate - 0.01)
                self.add_warning("High temperature affecting production!")
        else:
            self.temperature_warning = False
        
        if self.missed_defects > 0 and random.random() < 0.05:
            self.machine_health -= 0.5
        
        if self.system_monitor.cpu_temp > 60:
            self.temperature_warning = True
            if random.random() < 0.1:
                self.machine_health -= 0.2
                self.production_rate = max(0.7, self.production_rate - 0.01)
                self.add_warning("High temperature affecting production!")
        else:
            self.temperature_warning = False
        
        if self.machine_health < 30:
            self.machine_status = "Critical Condition"
            self.alert_active = True
            if self.machine_health < 15 and not self.critical_failure:
                self.critical_failure = True
                self.start_fire_simulation()
        elif self.machine_health < 60:
            self.machine_status = "Maintenance Required"
        elif self.machine_health < 80:
            self.machine_status = "Minor Issues"
        else:
            self.machine_status = "Normal Operation"

        if self.critical_failure:
            self.update_fire_particles()

        self.defect_probability_modifier = min(1.0, 0.15 + (self.missed_defects * 0.01))
                
        current_time_ms = pygame.time.get_ticks()
        self.warning_messages = [msg for msg in self.warning_messages 
                               if current_time_ms - msg['time'] < 5000]
    
    def start_fire_simulation(self):
        self.fire_particles = []
        self.fire_start_time = time.time()
        self.fire_intensity = 1.0
        for _ in range(20):
            particle = {
                'x': random.randint(0, 150),
                'y': 365,
                'vx': random.uniform(0.5, 2.0),
                'vy': random.uniform(-5, -2),
                'size': random.randint(3, 8),
                'color': random.choice([(255, 50, 0), (255, 150, 0), (200, 200, 0)]),
                'life': random.randint(30, 90)
            }
            self.fire_particles.append(particle)
    
    def update_fire_particles(self):
        elapsed_time = time.time() - self.fire_start_time
        fire_stages = int(elapsed_time / 3)
        
        if fire_stages > 0 and self.fire_intensity < 5.0:
            self.fire_intensity = min(1.0 + (fire_stages * 0.8), 5.0)

        if self.fire_intensity >= 5.0:
            self.trigger_explosion()
            return
        
        if random.random() < 0.2 * self.fire_intensity:
            particles_to_add = int(5 * self.fire_intensity)
            spread_x = 150 + int(100 * self.fire_intensity)
            
            for _ in range(particles_to_add):
                particle = {
                    'x': random.randint(0, spread_x),
                    'y': 365,
                    'vx': random.uniform(0, 1.5),
                    'vy': random.uniform(-5, -1),
                    'size': random.randint(3, int(8 * self.fire_intensity)),
                    'color': random.choice([(255, 50, 0), (255, 150, 0), (200, 200, 0)]),
                    'life': random.randint(30, 90)
                }
                self.fire_particles.append(particle)
        
        updated_particles = []
        for p in self.fire_particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.05
            p['life'] -= 1
            
            if p['life'] > 0:
                updated_particles.append(p)
        
        self.fire_particles = updated_particles

    def add_warning(self, message):
        self.warning_messages.append({
            'message': message,
            'time': pygame.time.get_ticks()
        })

    def trigger_explosion(self):
        self.fire_particles = []
        for _ in range(500):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(5, 15)
            particle = {
                'x': SCREEN_WIDTH // 2,
                'y': 350,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'size': random.randint(5, 15),
                'color': random.choice([(255, 50, 0), (255, 150, 0), (255, 255, 0)]),
                'life': random.randint(30, 90)
            }
            self.fire_particles.append(particle)
        
        self.machine_health = 0
        self.explosion_time = time.time()
        self.exploded = True
    
    def select_screw(self, mouse_pos):
        mouse_x, mouse_y = mouse_pos
        
        for screw in self.screws:
            if screw.marked_for_removal:
                continue
                
            dx = mouse_x - screw.x
            dy = mouse_y - screw.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            in_body = (abs(dx) < screw.size // 3 and 
                    0 < mouse_y - screw.y < screw.size * 3)
            
            if distance < screw.size or in_body:
                if screw.defective:
                    screw.marked_for_removal = True
                    self.defective_count += 1
                    self.machine_health = min(100, self.machine_health + 0.5)
                    return True
                else:
                    screw.marked_for_removal = True
                    self.false_positives += 1
                    self.add_warning("False alarm! Product was good!")
                    self.machine_health = max(0, self.machine_health - 0.5)
                    return False
        
        return None
    
    def mark_defective(self):
        if self.selected_screw_index >= 0 and self.selected_screw_index < len(self.screws):
            screw = self.screws[self.selected_screw_index]
            if not screw.inspected:
                screw.inspected = True
                if screw.defective:
                    self.defective_count += 1
                    self.machine_health = min(100, self.machine_health + 0.2)
                else:
                    self.false_positives += 1
                    self.add_warning("False alarm! Product was good!")
    
    def mark_good(self):
        if self.selected_screw_index >= 0 and self.selected_screw_index < len(self.screws):
            screw = self.screws[self.selected_screw_index]
            if not screw.inspected:
                screw.inspected = True
                if not screw.defective:
                    self.good_count += 1
                else:
                    self.missed_defects += 1
                    self.add_warning("Defective product marked as good!")
                    self.machine_health = max(0, self.machine_health - 1.0)
    
    def draw(self, screen):
        belt_y = 365
        belt_height = 15
        pygame.draw.rect(screen, DARK_GRAY, (0, belt_y, SCREEN_WIDTH, belt_height))
        
        for x in range(0, SCREEN_WIDTH, 30):
            pygame.draw.line(screen, BLACK, (x, belt_y), (x, belt_y + belt_height), 1)
        
        for screw in self.screws:
            screw.draw(screen)
        
        machine_color = (80, 80, 100)
        pygame.draw.rect(screen, machine_color, (SCREEN_WIDTH - 100, 300, 100, 150))
        pygame.draw.rect(screen, machine_color, (0, 300, 80, 150))
        
        panel_rect = pygame.Rect(50, 500, SCREEN_WIDTH - 100, 250)
        pygame.draw.rect(screen, (40, 40, 60), panel_rect)
        pygame.draw.rect(screen, (100, 100, 120), panel_rect, 3)
        
        pygame.draw.rect(screen, (60, 60, 70), (0, 0, SCREEN_WIDTH, 100))
        
        for x in range(100, SCREEN_WIDTH - 100, 150):
            pygame.draw.rect(screen, (80, 80, 90), (x, 0, 30, 150))
            pygame.draw.rect(screen, (90, 90, 100), (x-5, 130, 40, 20))
        
        for x in range(200, SCREEN_WIDTH - 200, 300):
            window_rect = pygame.Rect(x, 150, 100, 80)
            pygame.draw.rect(screen, (150, 200, 255), window_rect)
            pygame.draw.rect(screen, (100, 100, 110), window_rect, 3)
            pygame.draw.line(screen, (100, 100, 110), (x + 50, 150), (x + 50, 230), 2)
            pygame.draw.line(screen, (100, 100, 110), (x, 190), (x + 100, 190), 2)

        if self.critical_failure:
            for p in self.fire_particles:
                pygame.draw.circle(screen, p['color'], (int(p['x']), int(p['y'])), p['size'])
                
                if random.random() < 0.1:
                    smoke_y = p['y'] - random.randint(10, 30)
                    smoke_size = random.randint(2, 6)
                    smoke_alpha = random.randint(50, 150)
                    smoke_surface = pygame.Surface((smoke_size*2, smoke_size*2), pygame.SRCALPHA)
                    pygame.draw.circle(smoke_surface, (100, 100, 100, smoke_alpha), 
                                     (smoke_size, smoke_size), smoke_size)
                    screen.blit(smoke_surface, (int(p['x'] - smoke_size), int(smoke_y - smoke_size)))


class BackgroundProductionLine:
    def __init__(self):
        self.to_show = False
        self.system_monitor = SystemMonitor(to_show=self.to_show)  
        self.production_lines = [
            ProductionLine(self.system_monitor, speed_multiplier=3.0, background_mode=True),
            ProductionLine(self.system_monitor, speed_multiplier=2.0, background_mode=True),
            ProductionLine(self.system_monitor, speed_multiplier=4.0, background_mode=True)
        ]
        
    def update(self, current_time):
        for line in self.production_lines:
            line.update(current_time)
    
    def draw(self, screen):
        screen.fill((20, 20, 35))
        
        belt_positions = [250, 350, 450, 550]
        for i, line in enumerate(self.production_lines):
            original_y = line.screws[0].y if line.screws else 350
            for screw in line.screws:
                screw.y = belt_positions[i]
            
            belt_y = belt_positions[i] + 15
            pygame.draw.rect(screen, DARK_GRAY, (0, belt_y, SCREEN_WIDTH, 15))
            
            for x in range(0, SCREEN_WIDTH, 30):
                pygame.draw.line(screen, BLACK, (x, belt_y), (x, belt_y + 15), 1)
            
            line.draw(screen)
            
            for screw in line.screws:
                screw.y = original_y
