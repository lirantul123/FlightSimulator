import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import sys
import math
import time

# My modules
from plane import Plane
from environment import Environment
from skybox import Skybox
from camera import Camera
from instruments import Instruments
from utils import draw_text, draw_throttle, draw_compass
import sound

class GameState:
    MENU = "menu"
    FLYING = "flying"
    PAUSED = "paused"
    CRASHED = "crashed"
    SETTINGS = "settings"

class MacFlightSimulator:
    def __init__(self):
        pygame.init()
        sound.init_sound()
        sound.load_sounds()

        # Use a smaller, more compatible resolution
        self.display = (1024, 768)
        
        # Set OpenGL attributes for macOS compatibility
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 2)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 1)
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 16)
        pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
        
        # Create the window
        try:
            self.screen = pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL)
            pygame.display.set_caption("Flight Simulator - macOS")
            print(f"Display initialized: {self.display[0]}x{self.display[1]}")
            
            # Initialize OpenGL
            self.setup_opengl()
            
            # Test window visibility
            self.draw_test_screen()
            pygame.display.flip()
            pygame.time.wait(2000)  # Wait 2 seconds
            
        except Exception as e:
            print(f"Failed to initialize display: {e}")
            sys.exit(1)

        # Game state
        self.state = GameState.MENU
        self.clock = pygame.time.Clock()
        
        # Game objects
        self.player = None
        self.game_environment = None
        self.skybox = None
        self.camera = None
        self.instruments = None
        
        # Game features
        self.weather = "clear"
        self.time_of_day = "day"
        self.difficulty = "normal"
        self.mission_mode = False
        self.mission_target = None
        self.score = 0
        self.flight_time = 0
        self.start_time = time.time()
        
        # UI elements
        self.menu_selection = 0
        self.settings_selection = 0
        
    def setup_opengl(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glLightfv(GL_LIGHT0, GL_POSITION, [0, 5, 5, 1])
        
    def draw_test_screen(self):
        """Draw a test screen to ensure OpenGL is working"""
        glClearColor(0.2, 0.3, 0.8, 1.0)  # Blue background
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Set up 2D projection for test
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, self.display[0], 0, self.display[1])
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        
        # Draw a test rectangle
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glVertex2f(100, 100)
        glVertex2f(300, 100)
        glVertex2f(300, 200)
        glVertex2f(100, 200)
        glEnd()
        
        print("Test screen drawn - you should see a blue background with white rectangle")

    def start_new_game(self):
        self.player = Plane(0, 5, 0)
        self.game_environment = Environment()
        self.skybox = Skybox()
        self.camera = Camera(self.player)
        self.instruments = Instruments(self.display[0]/2 - (75 * 1.5 + 5), 10, 75)

        self.game_environment.runways.append(([0, 0.1, 0], [10, 200], 0))
        self.game_environment.generate_scenery([0,0,0], mountain_count=20, tree_count=100)
        
        sound.play_engine(volume=0.3)
        sound.play_wind(volume=0.0)
        sound.play_ground(volume=0.0)

        self.state = GameState.FLYING
        self.flight_time = 0
        self.start_time = time.time()
        self.score = 0

    def handle_menu_input(self, keys):
        if keys[pygame.K_UP]:
            self.menu_selection = (self.menu_selection - 1) % 4
        if keys[pygame.K_DOWN]:
            self.menu_selection = (self.menu_selection + 1) % 4
        if keys[pygame.K_RETURN]:
            if self.menu_selection == 0:  # Start Flight
                self.start_new_game()
            elif self.menu_selection == 1:  # Mission Mode
                self.mission_mode = True
                self.start_new_game()
            elif self.menu_selection == 2:  # Settings
                self.state = GameState.SETTINGS
            elif self.menu_selection == 3:  # Exit
                return False
        return True

    def handle_settings_input(self, keys):
        if keys[pygame.K_UP]:
            self.settings_selection = (self.settings_selection - 1) % 6
        if keys[pygame.K_DOWN]:
            self.settings_selection = (self.settings_selection + 1) % 6
        if keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]:
            if self.settings_selection == 0:  # Weather
                weather_options = ["clear", "cloudy", "storm"]
                current_index = weather_options.index(self.weather)
                if keys[pygame.K_RIGHT]:
                    self.weather = weather_options[(current_index + 1) % len(weather_options)]
                else:
                    self.weather = weather_options[(current_index - 1) % len(weather_options)]
            elif self.settings_selection == 1:  # Time of Day
                time_options = ["day", "night", "sunset"]
                current_index = time_options.index(self.time_of_day)
                if keys[pygame.K_RIGHT]:
                    self.time_of_day = time_options[(current_index + 1) % len(time_options)]
                else:
                    self.time_of_day = time_options[(current_index - 1) % len(time_options)]
            elif self.settings_selection == 2:  # Difficulty
                diff_options = ["easy", "normal", "hard"]
                current_index = diff_options.index(self.difficulty)
                if keys[pygame.K_RIGHT]:
                    self.difficulty = diff_options[(current_index + 1) % len(diff_options)]
                else:
                    self.difficulty = diff_options[(current_index - 1) % len(diff_options)]
        if keys[pygame.K_ESCAPE]:
            self.state = GameState.MENU
        return True

    def handle_game_input(self, keys):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    self.camera.cycle_mode()
                if event.key == pygame.K_p:
                    self.player.reset()
                    self.game_environment.reset()
                    sound.play_engine(volume=0.3)
                if event.key == pygame.K_r and self.player.crashed:
                    sound.stop_all_sounds()
                    return True
                if event.key == pygame.K_ESCAPE:
                    self.state = GameState.PAUSED
                if event.key == pygame.K_m:
                    self.state = GameState.MENU

        if not self.player.crashed:
            self.player.handle_input(keys)
            self.player.update()
            
            # Sound updates
            base_volume = 0.2
            thrust_volume = (1.0 - base_volume) * self.player.thrust_level
            sound.set_engine_volume(base_volume + thrust_volume)

            if self.player.is_airborne:
                sound.stop_ground()
                wind_volume = min(1.0, self.player.velocity / 2.0)
                sound.set_wind_volume(wind_volume)
            else:
                sound.stop_wind()
                if self.player.velocity > 0.1:
                    if not sound.channels['ground'].get_busy():
                         sound.play_ground()
                    ground_volume = min(1.0, self.player.velocity / 1.0)
                    sound.set_ground_volume(ground_volume)
                else:
                    sound.stop_ground()

        return True

    def draw_menu(self):
        glClearColor(0.1, 0.2, 0.4, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Set up 2D orthographic projection for menu
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, self.display[0], 0, self.display[1])
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        
        # Draw background
        glColor3f(0.1, 0.2, 0.4)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(self.display[0], 0)
        glVertex2f(self.display[0], self.display[1])
        glVertex2f(0, self.display[1])
        glEnd()
        
        # Title
        font = pygame.font.Font(None, 80)
        text_surface = font.render("FLIGHT SIMULATOR", True, (255, 255, 255, 255))
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        glWindowPos2d(self.display[0]/2 - 300, self.display[1] - 150)
        glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        
        # Menu options
        menu_options = ["Start Flight", "Mission Mode", "Settings", "Exit"]
        font = pygame.font.Font(None, 50)
        
        for i, option in enumerate(menu_options):
            color = (255, 255, 0, 255) if i == self.menu_selection else (255, 255, 255, 255)
            text_surface = font.render(option, True, color)
            text_data = pygame.image.tostring(text_surface, "RGBA", True)
            glWindowPos2d(self.display[0]/2 - 100, self.display[1]/2 - 100 + i * 60)
            glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        
        # Instructions
        font = pygame.font.Font(None, 30)
        instructions = [
            "Use UP/DOWN arrows to navigate",
            "Press ENTER to select",
            "Press ESC to go back"
        ]
        for i, instruction in enumerate(instructions):
            text_surface = font.render(instruction, True, (200, 200, 200, 255))
            text_data = pygame.image.tostring(text_surface, "RGBA", True)
            glWindowPos2d(50, 50 + i * 30)
            glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)

    def draw_settings(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, self.display[0], 0, self.display[1])
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        
        # Title
        font = pygame.font.Font(None, 60)
        text_surface = font.render("SETTINGS", True, (255, 255, 255, 255))
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        glWindowPos2d(self.display[0]/2 - 100, self.display[1] - 100)
        glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        
        # Settings options
        settings_data = [
            ("Weather", self.weather),
            ("Time of Day", self.time_of_day),
            ("Difficulty", self.difficulty),
            ("Sound Volume", "80%"),
            ("Graphics Quality", "High"),
            ("Back", "")
        ]
        
        font = pygame.font.Font(None, 40)
        for i, (setting, value) in enumerate(settings_data):
            color = (255, 255, 0, 255) if i == self.settings_selection else (255, 255, 255, 255)
            text = f"{setting}: {value}" if value else setting
            text_surface = font.render(text, True, color)
            text_data = pygame.image.tostring(text_surface, "RGBA", True)
            glWindowPos2d(self.display[0]/2 - 150, self.display[1]/2 - 100 + i * 50)
            glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)

    def draw_pause_menu(self):
        # Semi-transparent overlay
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glBegin(GL_QUADS)
        glColor4f(0, 0, 0, 0.7)
        glVertex2f(0, 0)
        glVertex2f(self.display[0], 0)
        glVertex2f(self.display[0], self.display[1])
        glVertex2f(0, self.display[1])
        glEnd()
        
        glDisable(GL_BLEND)
        
        # Pause text
        font = pygame.font.Font(None, 80)
        text_surface = font.render("PAUSED", True, (255, 255, 255, 255))
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        glWindowPos2d(self.display[0]/2 - 100, self.display[1]/2)
        glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        
        font = pygame.font.Font(None, 30)
        text_surface = font.render("Press ESC to resume, M for main menu", True, (255, 255, 255, 255))
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        glWindowPos2d(self.display[0]/2 - 150, self.display[1]/2 - 50)
        glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)

    def draw_game(self):
        # Update flight time
        if self.state == GameState.FLYING and not self.player.crashed:
            self.flight_time = time.time() - self.start_time
        
        self.camera.update()
        self.game_environment.update([self.player.x, self.player.y, self.player.z])

        # 3D Drawing
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (self.display[0] / self.display[1]), 0.1, 500.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        self.camera.apply()

        glEnable(GL_DEPTH_TEST)
        self.skybox.draw([self.player.x, self.player.y, self.player.z])
        self.game_environment.draw([self.player.x, self.player.y, self.player.z])

        if self.camera.get_mode() != 'cockpit':
            self.player.draw()

        # 2D Drawing (HUD)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, self.display[0], 0, self.display[1])
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        
        # Enhanced HUD
        self.draw_enhanced_hud()
        
        if self.player.crashed:
            self.draw_crash_screen()

    def draw_enhanced_hud(self):
        # Throttle indicator
        draw_throttle(self.display[0] - 40, 50, 20, 200, self.player.thrust_level)
        
        # Flight data
        altitude = self.player.y * 3.28084
        airspeed = self.player.velocity * 120
        draw_text(10, 50, f"Altitude: {altitude:.0f} ft")
        draw_text(10, 30, f"Airspeed: {airspeed:.0f} kts")
        draw_text(10, 70, f"Flight Time: {self.flight_time:.0f}s")
        draw_text(10, 90, f"Score: {self.score}")
        
        # Weather and time info
        draw_text(self.display[0] - 200, 30, f"Weather: {self.weather.title()}")
        draw_text(self.display[0] - 200, 50, f"Time: {self.time_of_day.title()}")
        
        # Compass
        draw_compass(80, 120, 50, self.player.yaw)
        
        # Camera mode
        camera_mode_text = f"View: {self.camera.get_mode().title()}"
        draw_text(10, self.display[1] - 30, camera_mode_text)
        
        # FPS
        fps = self.clock.get_fps()
        fps_text = f"FPS: {int(fps)}"
        draw_text(10, self.display[1] - 50, fps_text)
        
        # Stall warning
        if self.player.is_stalling:
            font = pygame.font.Font(None, 50)
            text_surface = font.render("STALL", True, (255, 0, 0, 255))
            text_data = pygame.image.tostring(text_surface, "RGBA", True)
            glWindowPos2d(self.display[0]/2 - 50, self.display[1] - 100)
            glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        
        # Ground movement instructions
        if not self.player.is_airborne and not self.player.crashed:
            draw_text(10, self.display[1] - 80, "Ground: A/D to turn, W/S for throttle")
        
        # Mission info
        if self.mission_mode:
            draw_text(self.display[0] - 200, 70, "MISSION MODE")
            draw_text(self.display[0] - 200, 90, "Find the target!")

        # Instruments (cockpit view)
        if self.camera.get_mode() == 'cockpit':
            self.instruments.draw(self.player)

    def draw_crash_screen(self):
        # Enhanced crash screen
        font = pygame.font.Font(None, 80)
        text_surface = font.render("CRASH!", True, (255, 0, 0, 255))
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        glWindowPos2d(self.display[0]/2 - 150, self.display[1]/2 + 50)
        glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        
        # Pulsing restart message
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.01)) * 0.5 + 0.5
        font = pygame.font.Font(None, 40)
        text_surface = font.render("Press 'R' to Restart", True, (255, 255, 255, int(255 * pulse)))
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        glWindowPos2d(self.display[0]/2 - 120, self.display[1]/2 - 20)
        glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        
        # Crash details
        font = pygame.font.Font(None, 30)
        crash_speed = self.player.velocity * 120
        text_surface = font.render(f"Impact Speed: {crash_speed:.1f} kts", True, (255, 200, 200, 255))
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        glWindowPos2d(self.display[0]/2 - 100, self.display[1]/2 - 60)
        glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        
        # Flight statistics
        text_surface = font.render(f"Flight Time: {self.flight_time:.1f}s", True, (255, 200, 200, 255))
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        glWindowPos2d(self.display[0]/2 - 100, self.display[1]/2 - 80)
        glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)

    def run(self):
        running = True
        
        while running:
            keys = pygame.key.get_pressed()
            
            if self.state == GameState.MENU:
                running = self.handle_menu_input(keys)
                self.draw_menu()
            elif self.state == GameState.SETTINGS:
                running = self.handle_settings_input(keys)
                self.draw_settings()
            elif self.state == GameState.FLYING:
                running = self.handle_game_input(keys)
                self.draw_game()
            elif self.state == GameState.PAUSED:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.state = GameState.FLYING
                        if event.key == pygame.K_m:
                            self.state = GameState.MENU
                
                self.draw_game()
                self.draw_pause_menu()
            
            pygame.display.flip()
            self.clock.tick(60)

        sound.stop_all_sounds()
        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    simulator = MacFlightSimulator()
    simulator.run() 