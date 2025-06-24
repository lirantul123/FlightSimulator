import pygame
import sys
import math
import time

class SimpleFlightSimulator:
    def __init__(self):
        pygame.init()
        
        self.display = (800, 600)
        self.screen = pygame.display.set_mode(self.display)
        pygame.display.set_caption("Simple Flight Simulator")
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.BLUE = (0, 100, 255)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        self.YELLOW = (255, 255, 0)
        
        # Game state
        self.state = "menu"  # menu, flying, crashed
        self.menu_selection = 0
        
        # Plane data
        self.plane_x = 400
        self.plane_y = 300
        self.plane_angle = 0
        self.velocity = 0
        self.thrust = 0
        self.altitude = 0
        self.is_airborne = False
        
        # Game features
        self.score = 0
        self.flight_time = 0
        self.start_time = time.time()
        
        # Fonts
        self.font_large = pygame.font.Font(None, 60)
        self.font_medium = pygame.font.Font(None, 40)
        self.font_small = pygame.font.Font(None, 30)
        
        self.clock = pygame.time.Clock()
        
    def draw_menu(self):
        self.screen.fill(self.BLUE)
        
        # Title
        title = self.font_large.render("FLIGHT SIMULATOR", True, self.WHITE)
        title_rect = title.get_rect(center=(self.display[0]//2, 100))
        self.screen.blit(title, title_rect)
        
        # Menu options
        options = ["Start Flight", "Settings", "Exit"]
        for i, option in enumerate(options):
            color = self.YELLOW if i == self.menu_selection else self.WHITE
            text = self.font_medium.render(option, True, color)
            text_rect = text.get_rect(center=(self.display[0]//2, 250 + i * 60))
            self.screen.blit(text, text_rect)
        
        # Instructions
        instructions = [
            "Use UP/DOWN arrows to navigate",
            "Press ENTER to select"
        ]
        for i, instruction in enumerate(instructions):
            text = self.font_small.render(instruction, True, self.WHITE)
            self.screen.blit(text, (50, 500 + i * 30))
    
    def draw_game(self):
        self.screen.fill(self.BLUE)
        
        # Draw ground
        pygame.draw.rect(self.screen, self.GREEN, (0, 500, self.display[0], 100))
        
        # Draw plane (simple triangle)
        plane_points = [
            (self.plane_x, self.plane_y),
            (self.plane_x - 20, self.plane_y + 10),
            (self.plane_x - 20, self.plane_y - 10)
        ]
        
        # Rotate plane points
        rotated_points = []
        for point in plane_points:
            x, y = point
            # Simple rotation
            cos_a = math.cos(math.radians(self.plane_angle))
            sin_a = math.sin(math.radians(self.plane_angle))
            new_x = (x - self.plane_x) * cos_a - (y - self.plane_y) * sin_a + self.plane_x
            new_y = (x - self.plane_x) * sin_a + (y - self.plane_y) * cos_a + self.plane_y
            rotated_points.append((new_x, new_y))
        
        pygame.draw.polygon(self.screen, self.WHITE, rotated_points)
        
        # Draw HUD
        self.draw_hud()
    
    def draw_hud(self):
        # Altitude
        alt_text = self.font_small.render(f"Altitude: {self.altitude:.0f} ft", True, self.WHITE)
        self.screen.blit(alt_text, (10, 10))
        
        # Speed
        speed_text = self.font_small.render(f"Speed: {self.velocity:.1f} kts", True, self.WHITE)
        self.screen.blit(speed_text, (10, 30))
        
        # Thrust
        thrust_text = self.font_small.render(f"Thrust: {self.thrust:.1f}", True, self.WHITE)
        self.screen.blit(thrust_text, (10, 50))
        
        # Flight time
        time_text = self.font_small.render(f"Time: {self.flight_time:.0f}s", True, self.WHITE)
        self.screen.blit(time_text, (10, 70))
        
        # Status
        status = "AIRBORNE" if self.is_airborne else "ON GROUND"
        status_text = self.font_small.render(status, True, self.WHITE)
        self.screen.blit(status_text, (10, 90))
        
        # Controls
        controls = [
            "W/S: Throttle",
            "A/D: Turn",
            "ESC: Menu"
        ]
        for i, control in enumerate(controls):
            text = self.font_small.render(control, True, self.WHITE)
            self.screen.blit(text, (self.display[0] - 150, 10 + i * 20))
    
    def draw_crash_screen(self):
        self.screen.fill(self.RED)
        
        crash_text = self.font_large.render("CRASH!", True, self.WHITE)
        crash_rect = crash_text.get_rect(center=(self.display[0]//2, self.display[1]//2))
        self.screen.blit(crash_text, crash_rect)
        
        restart_text = self.font_medium.render("Press R to restart", True, self.WHITE)
        restart_rect = restart_text.get_rect(center=(self.display[0]//2, self.display[1]//2 + 50))
        self.screen.blit(restart_text, restart_rect)
    
    def handle_menu_input(self, keys):
        if keys[pygame.K_UP]:
            self.menu_selection = (self.menu_selection - 1) % 3
        if keys[pygame.K_DOWN]:
            self.menu_selection = (self.menu_selection + 1) % 3
        if keys[pygame.K_RETURN]:
            if self.menu_selection == 0:  # Start Flight
                self.start_new_game()
            elif self.menu_selection == 1:  # Settings
                pass  # Could add settings later
            elif self.menu_selection == 2:  # Exit
                return False
        return True
    
    def handle_game_input(self, keys):
        if keys[pygame.K_w]:
            self.thrust = min(1.0, self.thrust + 0.01)
        if keys[pygame.K_s]:
            self.thrust = max(0.0, self.thrust - 0.01)
        
        if keys[pygame.K_a]:
            self.plane_angle += 2
        if keys[pygame.K_d]:
            self.plane_angle -= 2
        
        if keys[pygame.K_ESCAPE]:
            self.state = "menu"
    
    def start_new_game(self):
        self.plane_x = 400
        self.plane_y = 500  # Start on ground
        self.plane_angle = 0
        self.velocity = 0
        self.thrust = 0
        self.altitude = 0
        self.is_airborne = False
        self.state = "flying"
        self.flight_time = 0
        self.start_time = time.time()
        self.score = 0
    
    def update_game(self):
        # Update flight time
        self.flight_time = time.time() - self.start_time
        
        # Simple physics
        self.velocity += self.thrust * 0.1
        self.velocity *= 0.98  # Drag
        
        # Move plane
        angle_rad = math.radians(self.plane_angle)
        self.plane_x += math.sin(angle_rad) * self.velocity
        self.plane_y -= math.cos(angle_rad) * self.velocity
        
        # Ground collision
        if self.plane_y >= 500:
            self.plane_y = 500
            self.velocity = 0
            self.is_airborne = False
            self.altitude = 0
        else:
            self.is_airborne = True
            self.altitude = (500 - self.plane_y) * 3.28084  # Convert to feet
        
        # Crash detection
        if self.velocity > 5 and self.plane_y >= 500:
            self.state = "crashed"
        
        # Keep plane on screen
        self.plane_x = max(0, min(self.display[0], self.plane_x))
    
    def run(self):
        running = True
        
        while running:
            keys = pygame.key.get_pressed()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            if self.state == "menu":
                running = self.handle_menu_input(keys)
                self.draw_menu()
            elif self.state == "flying":
                self.handle_game_input(keys)
                self.update_game()
                self.draw_game()
            elif self.state == "crashed":
                if keys[pygame.K_r]:
                    self.start_new_game()
                self.draw_crash_screen()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    simulator = SimpleFlightSimulator()
    simulator.run() 