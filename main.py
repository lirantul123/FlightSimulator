import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import sys
import math
import random
import socket
import threading
import json
import time
import queue

# My modules
from plane import Plane
from environment import Environment
from skybox import Skybox
from camera import Camera
from instruments import Instruments
from utils import draw_text, draw_throttle, draw_compass, draw_health_bar, draw_hud_box, draw_rounded_box, draw_icon, draw_cube
import sound

PLANE_OPTIONS = [
    {
        'name': 'Cessna 172',
        'max_speed': 140, 'max_altitude': 14000, 'firepower': 1,
        'color': (0.8, 0.8, 0.8)
    },
    {
        'name': 'F-16',
        'max_speed': 1500, 'max_altitude': 50000, 'firepower': 5,
        'color': (0.7, 0.7, 0.9)
    },
    {
        'name': 'Cyberpink',
        'max_speed': 800, 'max_altitude': 30000, 'firepower': 3,
        'color': (1.0, 0.4, 0.7)
    }
]

selected_plane_idx = 0
plane_selected = False
player_name = ""
player_id = 0
lobby_entered = False
other_players = {}
network_thread = None
network_running = False
chat_messages = []
chat_input = ""
chat_active = False
remote_bullets = []
network_status = "Disconnected" # Can be: Disconnected, Connecting, Connected, Error
scoreboard_active = False
game_events = [] # A list of event messages
event_feed_timers = {} # Tracks fade-out time for each message
outgoing_messages = queue.Queue() # Thread-safe queue for sending messages

settings = {
    'callsign': '',
    'server_ip': '127.0.0.1',
    'plane_idx': 0,
}
settings_focus = 0  # 0: callsign, 1: server_ip, 2: plane, 3: start
settings_active = True
settings_error = ''
pause_focus = 0 # 0: Resume, 1: Restart, 2: Main Menu
server_ip = ''

# Game States
GAME_STATE_SETTINGS = 0
GAME_STATE_PLAYING = 1
GAME_STATE_PAUSED = 2
game_state = GAME_STATE_SETTINGS

def draw_pause_menu(display, focus):
    # Semi-transparent overlay
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.1, 0.1, 0.2, 0.75)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(display[0], 0)
    glVertex2f(display[0], display[1])
    glVertex2f(0, display[1])
    glEnd()
    glDisable(GL_BLEND)

    # Menu box
    box_w, box_h = 400, 280
    box_x, box_y = display[0]//2 - box_w//2, display[1]//2 - box_h//2
    draw_rounded_box(box_x, box_y, box_w, box_h, color=(0.12, 0.12, 0.12, 0.95))
    draw_text(box_x + box_w//2 - 60, box_y + box_h - 60, 'PAUSED', font_size=42)
    
    options = ["Resume", "Restart Mission", "Return to Hangar"]
    for i, option in enumerate(options):
        y = box_y + box_h - 140 - i * 55
        btn_w, btn_h = 280, 45
        btn_x = box_x + box_w//2 - btn_w//2
        
        is_focused = i == focus
        btn_color = (0.4, 0.8, 0.4, 0.9) if is_focused else (0.25, 0.25, 0.25, 0.8)
        
        draw_rounded_box(btn_x, y, btn_w, btn_h, color=btn_color)
        
        text_color = (255, 255, 0) if is_focused else (220, 220, 220)
        draw_text(btn_x + btn_w//2 - len(option)*6, y + 15, option, font_size=24) #, color=text_color)

def draw_minimap(player, other_players, display):
    # Player-up Circular Radar
    map_size = 80 
    map_x = display[0] - map_size - 25
    map_y = display[1] - map_size - 25
    
    # Draw background circle
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.1, 0.1, 0.15, 0.75)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(map_x, map_y)
    for i in range(121):
        angle = i * (2 * math.pi / 120)
        glVertex2f(map_x + math.cos(angle) * map_size, map_y + math.sin(angle) * map_size)
    glEnd()

    # Draw player's heading line and range rings
    player_heading_rad = -math.radians(player.yaw) # Invert for screen coords
    
    glPushMatrix()
    glTranslatef(map_x, map_y, 0)
    glRotatef(player.yaw, 0, 0, 1) # Rotate the whole radar view
    
    # Draw range rings
    glColor4f(0.3, 0.7, 0.3, 0.3)
    for r in [0.25, 0.5, 0.75, 1.0]:
        glBegin(GL_LINE_LOOP)
        for i in range(60):
            angle = i * (2 * math.pi / 59)
            glVertex2f(math.cos(angle) * map_size * r, math.sin(angle) * map_size * r)
        glEnd()

    # Draw crosshairs
    glBegin(GL_LINES)
    glVertex2f(-map_size, 0)
    glVertex2f(map_size, 0)
    glVertex2f(0, -map_size)
    glVertex2f(0, map_size)
    glEnd()
    glPopMatrix()
    
    # Draw player icon (static, points up)
    glColor3f(1.0, 1.0, 0.2)
    glBegin(GL_TRIANGLES)
    glVertex2f(map_x, map_y + 8)
    glVertex2f(map_x - 5, map_y - 5)
    glVertex2f(map_x + 5, map_y - 5)
    glEnd()

    scale = 0.05
    
    # Function to draw a rotated target
    def draw_target(px, py, pz, pyaw, tx, ty, tz, tyaw, color, is_arrow=False):
        # Calculate vector from player to target
        dx_world = tx - px
        dz_world = tz - pz

        # Rotate vector by player's yaw to get map coordinates
        yaw_rad = math.radians(-pyaw) # Invert yaw to fix direction
        dx_map = (dx_world * math.cos(yaw_rad) + dz_world * math.sin(yaw_rad)) * scale
        dz_map = (-dx_world * math.sin(yaw_rad) + dz_world * math.cos(yaw_rad)) * scale

        dist = math.sqrt(dx_map**2 + dz_map**2)

        if dist < map_size:
            glPushMatrix()
            glTranslatef(map_x + dx_map, map_y + dz_map, 0)
            relative_yaw = tyaw - pyaw
            glRotatef(-relative_yaw, 0, 0, 1)
            
            glColor3f(*color)
            if is_arrow:
                glBegin(GL_TRIANGLES)
                glVertex2f(0, 6) # Make arrow larger
                glVertex2f(-4, -4)
                glVertex2f(4, -4)
                glEnd()
            else:
                glPointSize(5)
                glBegin(GL_POINTS)
                glVertex2f(0, 0)
                glEnd()
            glPopMatrix()

    # Draw entities
    for p_obj in other_players.values():
        if p_obj.health > 0:
            color = (1.0, 0.2, 0.2) # Bright Red
            draw_target(player.x, player.y, player.z, player.yaw, p_obj.x, p_obj.y, p_obj.z, p_obj.yaw, color, is_arrow=True)
    
    glDisable(GL_BLEND)

def network_loop(player, player_name, player_id, server_ip):
    global other_players, network_running, remote_bullets, chat_messages, network_status, outgoing_messages, score
    network_status = "Connecting..."
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((server_ip, 50007))
        s.setblocking(False) # Make the socket non-blocking
        network_status = "Connected"
    except Exception as e:
        print(f"Could not connect to server: {e}")
        network_status = f"Error: {e}"
        return
    
    network_running = True
    
    # Add a welcome message
    outgoing_messages.put(json.dumps({'type': 'chat', 'name': 'System', 'text': f'{player_name} has joined the lobby.'}))

    buffer = ""
    while network_running:
        try:
            # Send our state and any queued messages first
            state_msg = {
                'type': 'state', 'player_id': player_id, 'name': player_name,
                'x': player.x, 'y': player.y, 'z': player.z,
                'yaw': player.yaw, 'pitch': player.pitch, 'roll': player.roll,
                'health': player.health,
                'color': player.color,
                'score': score,
                'deaths': player.deaths
            }
            s.sendall(json.dumps(state_msg).encode())
            while not outgoing_messages.empty():
                msg_to_send = outgoing_messages.get_nowait()
                s.sendall(msg_to_send.encode())
            
            # Now, try to receive data
            data = s.recv(4096).decode()
            if not data:
                network_running = False
                break
            buffer += data
            
        except BlockingIOError:
            # This is expected when no data is available.
            pass
        except Exception as e:
            print(f"Network error: {e}")
            network_running = False
            break

        # Process everything in the buffer
        while True: 
            if not buffer:
                break
            try:
                msg, end_index = json.JSONDecoder().raw_decode(buffer)
                
                if msg['type'] == 'state' and msg['player_id'] != player_id:
                    p_id = msg['player_id']
                    if p_id not in other_players:
                        other_players[p_id] = Plane(0,0,0, plane_id=p_id)

                    # Update the remote player's state
                    p = other_players[p_id]
                    p.x = msg.get('x', p.x)
                    p.y = msg.get('y', p.y)
                    p.z = msg.get('z', p.z)
                    p.pitch = msg.get('pitch', p.pitch)
                    p.roll = msg.get('roll', p.roll)
                    p.yaw = msg.get('yaw', p.yaw)
                    p.health = msg.get('health', p.health)
                    p.color = msg.get('color', p.color)
                    p.name = msg.get('name', p.name)
                elif msg['type'] == 'bullet' and msg['player_id'] != player_id:
                    remote_bullets.append(msg)
                elif msg['type'] == 'chat':
                    chat_messages.append((msg['name'], msg['text']))
                    if len(chat_messages) > 8: chat_messages.pop(0)
                elif msg['type'] == 'hit':
                    target_id = msg['target_id']
                    if target_id == player_id:
                        player.health -= msg['damage']
                        add_game_event(f"You were hit by {msg['attacker_name']}")
                    elif target_id in other_players:
                        other_players[target_id]['health'] -= msg['damage']
                    
                    if msg.get('is_kill'):
                        # The shooter's client will have already incremented their score.
                        # We just need to update the death count of the victim.
                        if target_id == player_id:
                            player.deaths += 1
                        elif target_id in other_players:
                            # This part is tricky; we don't have a 'deaths' field
                            # in other_players yet. We'll add it.
                            if 'deaths' not in other_players[target_id]:
                                other_players[target_id]['deaths'] = 0
                            other_players[target_id]['deaths'] += 1

                buffer = buffer[end_index:].lstrip()
            except json.JSONDecodeError:
                break # Incomplete message in buffer
        
        time.sleep(1/60) # Limit loop to ~60Hz

    network_status = "Disconnected"
    s.close()
    network_running = False

def draw_scoreboard(players, display, score, player):
    box_w, box_h = 500, 300
    box_x, box_y = display[0]//2 - box_w//2, display[1]//2 - box_h//2
    draw_rounded_box(box_x, box_y, box_w, box_h, color=(0.1, 0.1, 0.1, 0.9))
    draw_text(box_x + 20, box_y + box_h - 40, "Scoreboard", font_size=32)
    
    # Headers
    draw_text(box_x + 30, box_y + box_h - 80, "Player", font_size=22)
    draw_text(box_x + 250, box_y + box_h - 80, "Score", font_size=22)
    draw_text(box_x + 380, box_y + box_h - 80, "Deaths", font_size=22)

    # Player data (add local player to list for display)
    all_players = list(players.values())
    all_players.append(player) # Add self
    
    for i, p in enumerate(all_players):
        y = box_y + box_h - 120 - i * 30
        # Use attribute access for Plane objects, fallback to dict for local player
        name = getattr(p, 'name', getattr(p, 'player_name', None)) or getattr(p, 'player_name', None) or getattr(p, 'callsign', None) or 'You'
        score_val = getattr(p, 'score', None)
        if score_val is None:
            score_val = getattr(p, 'score', 0) if hasattr(p, 'score') else score
        deaths_val = getattr(p, 'deaths', 0)
        draw_text(box_x + 30, y, str(name), font_size=20)
        draw_text(box_x + 250, y, str(score_val), font_size=20)
        draw_text(box_x + 380, y, str(deaths_val), font_size=20)

def add_game_event(text):
    event_id = time.time()
    game_events.append({'id': event_id, 'text': text})
    event_feed_timers[event_id] = 5 # seconds to display

def draw_event_feed(display):
    y = display[1] - 200
    for event in reversed(game_events[-5:]): # Show last 5 events
        event_id = event['id']
        if event_id in event_feed_timers:
            remaining = event_feed_timers[event_id]
            alpha = max(0, min(1, remaining / 2.0)) # Fade out over last 2 seconds
            if alpha > 0:
                draw_text(display[0] - 350, y, event['text'], font_size=18)
                y -= 25

def draw_chat_ui(display, history, current_input, is_active):
    box_x, box_y = 20, 200
    box_w, box_h = 400, 200
    
    # Draw chat history box
    draw_rounded_box(box_x, box_y, box_w, box_h, color=(0.1, 0.1, 0.1, 0.5 if not is_active else 0.8))
    
    y = box_y + box_h - 30
    for name, text in reversed(history[-8:]):
        full_text = f"<{name}> {text}"
        color = (255, 255, 0) if name == "System" else (255, 255, 255)
        draw_text(box_x + 10, y, full_text, font_size=18)
        y -= 22

    # Draw input box when active
    if is_active:
        draw_rounded_box(box_x, box_y - 40, box_w, 35, color=(0.2, 0.2, 0.2, 0.9))
        input_display = "> " + current_input + "_"
        draw_text(box_x + 10, box_y - 30, input_display, font_size=20)

def draw_fuel_gauge(x, y, w, h, fuel_level):
    # Draw background
    draw_rounded_box(x, y, w, h, color=(0.1, 0.1, 0.1, 0.8))
    
    # Draw fuel bar
    bar_w = w - 10
    bar_h = h - 20
    bar_x = x + 5
    bar_y = y + 10
    
    fuel_width = bar_w * (fuel_level / 100.0)
    
    # Fuel color (green to red)
    fuel_color = (1.0 - (fuel_level/100.0), fuel_level/100.0, 0.1, 0.9)
    
    # Draw the current fuel level
    glEnable(GL_BLEND)
    glColor4f(*fuel_color)
    glBegin(GL_QUADS)
    glVertex2f(bar_x, bar_y)
    glVertex2f(bar_x + fuel_width, bar_y)
    glVertex2f(bar_x + fuel_width, bar_y + bar_h)
    glVertex2f(bar_x, bar_y + bar_h)
    glEnd()
    
    # Draw text "FUEL"
    draw_text(x + w / 2 - 20, y + h - 15, "FUEL", font_size=18)
    glDisable(GL_BLEND)

def main():
    global selected_plane_idx, plane_selected, player_name, player_id, lobby_entered, other_players, network_thread, network_running, chat_messages, chat_input, chat_active, remote_bullets, settings, settings_focus, settings_active, settings_error, server_ip, pause_focus, network_status, scoreboard_active, game_state, outgoing_messages, score
    pygame.init()
    sound.load_sounds()

    display = (1200, 800)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Flight Simulator")

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glLightfv(GL_LIGHT0, GL_POSITION, [0, 5, 5, 1])

    player = Plane(0, 0.6, 0, plane_id=0)
    score = 0
    
    game_state = GAME_STATE_SETTINGS # Start in settings
    
    game_environment = Environment()
    skybox = Skybox()
    camera = Camera(player)
    instruments = Instruments(display[0]/2 - (75 * 1.5 + 5), 10, 75)

    game_environment.runways.append(([0, 0.1, 0], [10, 200], 0))
    game_environment.generate_scenery([0,0,0], mountain_count=20, tree_count=100)
    
    sound.play_engine(volume=0.3)
    sound.play_wind(volume=0.0)

    clock = pygame.time.Clock()
    running = True

    while running:
        # --- Event Loop ---
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                network_running = False
                running = False

        # --- State-based Logic ---
        if game_state == GAME_STATE_SETTINGS:
            # Settings Screen Logic
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_TAB:
                        settings_focus = (settings_focus + 1) % 4
                    elif event.key == pygame.K_UP:
                        if settings_focus == 2:
                            settings['plane_idx'] = (settings['plane_idx'] - 1) % len(PLANE_OPTIONS)
                    elif event.key == pygame.K_DOWN:
                        if settings_focus == 2:
                            settings['plane_idx'] = (settings['plane_idx'] + 1) % len(PLANE_OPTIONS)
                    elif event.key == pygame.K_RETURN:
                        if settings_focus == 3: # Start button
                            if not settings['callsign']:
                                settings_error = 'Enter a callsign.'
                            elif not settings['server_ip']:
                                settings_error = 'Enter server IP.'
                            else:
                                player_name = settings['callsign']
                                selected_plane_idx = settings['plane_idx']
                                server_ip = settings['server_ip']
                                
                                # Reset the existing player and apply new properties
                                player.reset()
                                player.set_properties_from_selection(PLANE_OPTIONS[selected_plane_idx])

                                game_state = GAME_STATE_PLAYING
                                lobby_entered = True
                                settings_error = ''

                                # Start network thread if not already running
                                if not network_running:
                                    player_id = random.randint(1000, 9999)
                                    player.player_id = player_id
                                    network_thread = threading.Thread(target=network_loop, args=(player, player_name, player_id, server_ip), daemon=True)
                                    network_thread.start()
                        else:
                            settings_focus = (settings_focus + 1) % 4
                    elif event.key == pygame.K_BACKSPACE:
                        if settings_focus == 0:
                            settings['callsign'] = settings['callsign'][:-1]
                        elif settings_focus == 1:
                            settings['server_ip'] = settings['server_ip'][:-1]
                    elif event.unicode.isprintable():
                        if settings_focus == 0 and len(settings['callsign']) < 16:
                            settings['callsign'] += event.unicode
                        elif settings_focus == 1 and len(settings['server_ip']) < 32:
                            settings['server_ip'] += event.unicode
        
        elif game_state == GAME_STATE_PAUSED:
            # Pause Menu Logic
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        game_state = GAME_STATE_PLAYING
                    elif event.key == pygame.K_DOWN:
                        pause_focus = (pause_focus + 1) % 3
                    elif event.key == pygame.K_UP:
                        pause_focus = (pause_focus - 1 + 3) % 3 # Correct modulo for negative numbers
                    elif event.key == pygame.K_RETURN:
                        if pause_focus == 0: # Resume
                            game_state = GAME_STATE_PLAYING
                        elif pause_focus == 1: # Restart
                            player.respawn()
                            score = 0
                            game_state = GAME_STATE_PLAYING
                        elif pause_focus == 2: # Main Menu
                            network_running = False
                            if network_thread:
                                network_thread.join()
                            network_thread = None
                            other_players = {}
                            game_state = GAME_STATE_SETTINGS
                            lobby_entered = False
                            player.reset()
                            score = 0
        
        elif game_state == GAME_STATE_PLAYING:
            # --- Chat Input Logic ---
            if chat_active:
                for event in events:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            if chat_input:
                                # Add to local history immediately for responsiveness
                                chat_messages.append((player_name, chat_input))
                                if len(chat_messages) > 8:
                                    chat_messages.pop(0)

                                # Queue chat message to be sent by network thread
                                msg = json.dumps({'type': 'chat', 'name': player_name, 'text': chat_input})
                                outgoing_messages.put(msg)
                                chat_input = ""
                            chat_active = False # Deactivate chat on send or empty send
                        elif event.key == pygame.K_ESCAPE:
                            chat_active = False
                            chat_input = ""
                        elif event.key == pygame.K_BACKSPACE:
                            chat_input = chat_input[:-1]
                        elif event.unicode.isprintable() and len(chat_input) < 60:
                            chat_input += event.unicode
            else: # Regular Gameplay Key Presses
                for event in events:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            game_state = GAME_STATE_PAUSED
                            pause_focus = 0
                        elif event.key == pygame.K_t:
                            chat_active = True
                            chat_input = ""
                        elif event.key == pygame.K_c:
                            camera.cycle_mode()
                        elif event.key == pygame.K_TAB:
                            scoreboard_active = not scoreboard_active

        # --- Continuous Key Presses (outside event loop) ---
        if game_state == GAME_STATE_PLAYING and not chat_active:
            keys = pygame.key.get_pressed()
            player.handle_input(keys)
        
        # --- Game Logic Update ---
        game_environment.update([player.x, player.y, player.z])
        if game_state == GAME_STATE_PLAYING:
            if player.health <= 0:
                player.update_destroyed() # This will handle the explosion and timers
                if player.respawn_timer <= 0:
                    player.respawn()
                    add_game_event("You have respawned.")
            else:
                hit_events = player.update(list(other_players.values()))
                for event in hit_events:
                    event['attacker_name'] = player_name
                    outgoing_messages.put(json.dumps(event))

                    # Process locally for immediate feedback
                    target_id = event['target_id']
                    if target_id in other_players:
                        # Don't modify the health directly, wait for server confirmation
                        pass

                    if event.get('is_kill'):
                        score += 1
                        add_game_event(f"You shot down {event['victim_name']}")
            
            # --- Sound Updates ---
            # Engine Volume
            base_volume = 0.2
            thrust_volume = (1.0 - base_volume) * player.thrust_level
            sound.set_engine_volume(base_volume + thrust_volume)

            # Wind and Ground Sounds
            if player.is_airborne:
                sound.stop_wind()
                # Make wind volume proportional to airspeed
                wind_volume = min(1.0, player.velocity / 2.0) # Normalize
                sound.set_wind_volume(wind_volume)
            else: # On the ground
                sound.stop_wind()
                # Make ground rolling volume proportional to speed
                if player.velocity > 0.1:
                    if sound.channels.get('ground') and not sound.channels['ground'].get_busy():
                         sound.play_ground()
                    ground_volume = min(1.0, player.velocity / 1.0) # Normalize

        # --- Drawing ---
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (display[0] / display[1]), 0.1, 500.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        camera.apply()

        glEnable(GL_DEPTH_TEST)
        skybox.draw([player.x, player.y, player.z])
        game_environment.draw([player.x, player.y, player.z])

        if camera.get_mode() != 'cockpit':
            player.draw()

        # Draw other players
        for p_obj in other_players.values():
            if p_obj.health > 0:
                p_obj.draw()

                # Health bar above other players
                glPushMatrix()
                glTranslatef(p_obj.x, p_obj.y + 2.0, p_obj.z)
                draw_health_bar(-0.8, 0, 1.6, 0.2, p_obj.health)
                glPopMatrix()

        # Multiplayer bullet firing
        if player.bullets:
            for bullet in player.bullets:
                if bullet.get('just_fired', True):
                    bullet['just_fired'] = False
                    msg = json.dumps({'type': 'bullet', 'player_id': player_id, 'x': bullet['x'], 'y': bullet['y'], 'z': bullet['z'], 'yaw': bullet['yaw'], 'pitch': bullet['pitch']})
                    outgoing_messages.put(msg)
        
        # Render remote bullets
        for b in remote_bullets:
            glPushMatrix()
            glColor3f(1.0, 0.8, 0.2)
            glTranslatef(b['x'] - player.x, b['y'] - player.y, b['z'] - player.z)
            glScalef(0.12, 0.12, 1.0)
            draw_cube()
            glPopMatrix()

        # --- 2D Drawing (HUD) ---
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, display[0], 0, display[1])
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        
        # Health bar (top left)
        draw_rounded_box(20, display[1] - 90, 200, 85)
        draw_health_bar(30, display[1] - 75, 180, 20, player.health)
        draw_text(30, display[1] - 30, f"Health: {player.health}", font_size=22)
        shown_name = player_name[:14] + ("..." if len(player_name) > 14 else "")
        draw_text(30, display[1] - 45, f"Pilot: {shown_name}", font_size=16)
        # Score (top center)
        draw_text(display[0]//2 - 30, display[1] - 55, f"Score: {score}", font_size=28)
        
        # Minimap (bottom right) and Chat (bottom left)
        draw_minimap(player, other_players, display)
        draw_chat_ui(display, chat_messages, chat_input, chat_active)

        # Throttle (bottom right)
        draw_rounded_box(display[0] - 110, 40, 80, 240)
        draw_throttle(display[0] - 95, 55, 30, 200, player.thrust_level)
        # Plane stats (bottom left)
        draw_rounded_box(20, 20, 270, 120)
        draw_text(30, 120, f"Plane: {PLANE_OPTIONS[selected_plane_idx]['name']}", font_size=20)
        draw_text(30, 100, f"Speed: {player.max_speed_knots} kts  Alt: {player.max_altitude_ft} ft  Firepower: {player.firepower}", font_size=16)
        altitude = player.y * 3.28084
        airspeed = player.velocity * 120
        draw_text(30, 80, f"Altitude: {altitude:.2f} ft", font_size=16)
        draw_text(30, 60, f"Airspeed: {airspeed:.2f} kts", font_size=16)
        # Distance indicator (from origin)
        distance = ((player.x ** 2 + player.y ** 2 + player.z ** 2) ** 0.5)
        draw_text(30, 40, f"Distance from origin: {distance:.1f} m", font_size=16)
        # Vibe message (bottom center)
        
        # Fuel Gauge (next to plane stats)
        draw_fuel_gauge(300, 20, 150, 40, player.fuel)

        # Low Fuel Warning
        if player.fuel < 20:
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.005))
            warn_color = (1.0, 0.2, 0.2, pulse * 0.8)
            draw_rounded_box(display[0]//2 - 100, 150, 200, 40, color=warn_color)
            draw_text(display[0]//2 - 50, 162, "LOW FUEL", font_size=24)

        # Camera mode and FPS (bottom right, above throttle)
        draw_rounded_box(display[0] - 220, 300, 200, 54)
        camera_mode_text = f"View: {camera.get_mode().title()}"
        draw_text(display[0] - 210, 340, camera_mode_text, font_size=16)
        fps = clock.get_fps()
        fps_text = f"FPS: {int(fps)}"
        draw_text(display[0] - 210, 320, fps_text, font_size=16)
        # Show ground movement instructions when on ground (center bottom)
        
        if game_state == GAME_STATE_PAUSED:
            draw_pause_menu(display, pause_focus)

        if game_state == GAME_STATE_SETTINGS:
            # Settings screen must be drawn last to be on top
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT) # Clear screen for settings
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluOrtho2D(0, display[0], 0, display[1])
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            glDisable(GL_DEPTH_TEST)
            # Settings box
            box_w, box_h = 500, 420
            box_x, box_y = display[0]//2 - box_w//2, display[1]//2 - box_h//2
            draw_rounded_box(box_x, box_y, box_w, box_h, color=(0.12,0.12,0.12,0.95))
            draw_text(box_x+30, box_y+box_h-60, 'Multiplayer Flight Simulator', font_size=36)
            # Callsign
            draw_text(box_x+30, box_y+box_h-110, 'Callsign:', font_size=22)
            draw_rounded_box(box_x+160, box_y+box_h-120, 220, 36, color=(0.2,0.2,0.2,0.8))
            draw_text(box_x+170, box_y+box_h-110, settings['callsign'] + ('_' if settings_focus==0 else ''), font_size=22)
            # Server IP
            draw_text(box_x+30, box_y+box_h-170, 'Server IP:', font_size=22)
            draw_rounded_box(box_x+160, box_y+box_h-180, 220, 36, color=(0.2,0.2,0.2,0.8))
            draw_text(box_x+170, box_y+box_h-170, settings['server_ip'] + ('_' if settings_focus==1 else ''), font_size=22)
            # Plane selection
            draw_text(box_x+30, box_y+box_h-230, 'Plane:', font_size=22)
            for i, plane in enumerate(PLANE_OPTIONS):
                y = box_y+box_h-250 - i*40
                color = (255,255,0,255) if i == settings['plane_idx'] and settings_focus==2 else (200,200,200,255)
                draw_text(box_x+170, y, plane['name'], font_size=22)
                stats = f"Speed: {plane['max_speed']}kts Alt: {plane['max_altitude']}ft Firepower: {plane['firepower']}"
                draw_text(box_x+320, y, stats, font_size=16)
            # Start button
            btn_color = (0.3,0.7,0.3,0.9) if settings_focus==3 else (0.2,0.2,0.2,0.8)
            draw_rounded_box(box_x+box_w//2-70, box_y+40, 140, 44, color=btn_color)
            draw_text(box_x+box_w//2-30, box_y+55, 'Start', font_size=26)
            # Error
            if settings_error:
                draw_text(box_x+30, box_y+20, settings_error, font_size=18)
            # Network status / error message
            if network_status and network_status != "Connected":
                draw_text(box_x+30, box_y+10, f"Status: {network_status}", font_size=18)
            pygame.display.flip()
            clock.tick(60)
            continue

        if scoreboard_active:
            draw_scoreboard(other_players, display, score, player)

        # Update event feed timers
        for event_id, timer in list(event_feed_timers.items()):
            new_timer = timer - (1/60.0)
            if new_timer <= 0:
                del event_feed_timers[event_id]
            else:
                event_feed_timers[event_id] = new_timer

        # Draw event feed
        draw_event_feed(display)

        pygame.display.flip()
        clock.tick(60)

    # --- Shutdown ---
    if network_thread:
        network_thread.join()
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    while True:
        main()