from OpenGL.GL import *
import math
from utils import draw_cube, draw_cylinder
import pygame
import sound
import time

class Plane:
    def __init__(self, x, y, z, plane_id=0):
        self.initial_pos = (0, 1.7, 0)  # Start above the ground, y=1.7
        self.x, self.y, self.z = self.initial_pos
        self.pitch = 0.0
        self.roll = 0.0
        self.yaw = 0.0
        self.velocity = 0.0
        self.thrust_level = 0.0
        
        self.pitch_rate = 0.0
        self.roll_rate = 0.0
        self.target_roll_angle = 0.0
        
        self.is_airborne = False  # Start on the ground
        self.is_stalling = False
        self.crash_sound_played = False
        self.crash_timer = 0  # For crash animation

        # Animation
        self.propeller_angle = 0
        
        self.max_thrust = 0.013
        self.drag = 0.00003
        self.gravity = 0.005
        self.ground_roll_resist_low = 0.999
        self.ground_roll_resist_high = 0.9999
        self.ground_turn_sensitivity = 0.2
        self.ground_turn_sensitivity_high = 0.05
        
        self.size = 1.0
        
        # Animation
        self.aileron_angle = 0
        self.elevator_angle = 0

        self.vertical_speed = 0
        self.last_y = self.y
        
        # New features
        self.fuel = 100.0  # Fuel percentage
        self.fuel_consumption = 0.1  # Reduced fuel consumption per frame
        self.damage = 0.0  # Damage percentage
        self.max_damage = 100.0
        self.engine_health = 100.0
        self.wing_health = 100.0
        self.landing_gear_health = 100.0

        self.flaps_deployed = False
        self.flap_lift_bonus = 0.002
        self.flap_drag_penalty = 0.0005
        self.autopilot = False

        self.brakes_applied = False
        self.ground_turn_rate = 0

        self.takeoff_speed = 0.28
        self.ground_effect = False

        self.lift_takeoff_boost = 0.006
        self.taxi_blend_factor = 0.22
        self.ground_velocity_x = 0.0
        self.ground_velocity_z = 0.0

        self.airborne_timer = 0  # Time spent airborne (frames)

        self.bullets = []  # List of active bullets
        self.last_shot_time = 0
        self.shot_cooldown = 0.15  # seconds between shots
        self.player_id = plane_id  # For multiplayer
        self.health = 100
        self.explosion_timer = 0
        self.smoke_timer = 0
        self.respawn_timer = 0
        self.color = (0.8, 0.8, 0.8)  # Default color, can be set externally

        self.max_speed_knots = 140
        self.max_altitude_ft = 14000
        self.firepower = 1

        self.deaths = 0

    def set_properties_from_selection(self, plane_stats):
        self.max_speed_knots = plane_stats['max_speed']
        self.max_altitude_ft = plane_stats['max_altitude']
        self.firepower = plane_stats['firepower']
        self.color = plane_stats['color']

    def update(self, other_planes=None):
        if self.health <= 0:
            self.update_destroyed()
            return
        
        ground_level = 1.7
        # Always update orientation (pitch, roll)
        self.pitch += self.pitch_rate
        self.roll += (self.target_roll_angle - self.roll) * 0.05
        # Yaw update
        if self.is_airborne:
            effective_velocity = max(self.velocity, 0.3)
            self.yaw += math.sin(math.radians(self.roll)) * effective_velocity * 1.0
        else:
            self.yaw += self.ground_turn_rate * 1.5 * self.velocity
        
        # Clamp pitch and roll
        self.roll = max(-65.0, min(65.0, self.roll))
        self.pitch = max(-55.0, min(55.0, self.pitch))

        # 2. Update Velocity
        thrust_force = self.thrust_level * self.max_thrust
        drag_force = self.drag * self.velocity * self.velocity
        if not self.is_airborne:
            drag_force += 0.01 * self.velocity 
        self.velocity += thrust_force - drag_force
        if self.velocity < 0: self.velocity = 0

        # 3. Calculate new position based on orientation and velocity
        yaw_rad = math.radians(self.yaw)
        pitch_rad = math.radians(self.pitch)
        fwd_x = math.sin(yaw_rad) * math.cos(pitch_rad)
        fwd_y = math.sin(pitch_rad)
        fwd_z = -math.cos(yaw_rad) * math.cos(pitch_rad)
        self.x += self.velocity * fwd_x
        self.y += self.velocity * fwd_y
        self.z += self.velocity * fwd_z
        
        # 4. Handle Gravity and Ground Interaction
        taking_off = (not self.is_airborne and self.thrust_level > 0.3 and self.velocity > 2.0 and self.pitch > 2)
        if taking_off:
            self.is_airborne = True
            self.y += 0.1 # Pop off the ground
            sound.play_wind()
        if self.is_airborne:
            self.y -= self.gravity

        self.vertical_speed = (self.y - self.last_y) * 60.0
        self.last_y = self.y
        
        # Ground collision logic (for landing or if below ground)
        if self.y < ground_level:
            self.y = ground_level
            self.is_airborne = False
            self.roll = 0 # Level out on landing
            if self.vertical_speed < -0.8: # Hard landing
                self.health -= 60
                sound.play_crash()
            else:
                sound.play_ground()
        
        # Fuel consumption
        if self.thrust_level > 0:
            self.fuel -= self.fuel_consumption * self.thrust_level
            if self.fuel <= 0:
                self.fuel = 0
                self.thrust_level = 0  # Engine stops when out of fuel
                
        # Damage effects
        if self.damage > 50:
            # Reduced performance when damaged
            self.max_thrust *= 0.8
        if self.damage > 80:
            # Critical damage - engine problems
            self.engine_health -= 0.1
            if self.engine_health < 20:
                self.thrust_level *= 0.5  # Reduced thrust
        
        # Animate propeller (spin faster with more thrust)
        self.propeller_angle += self.thrust_level * 100
        if self.propeller_angle > 360.0:
            self.propeller_angle -= 360.0

        # Animate wheels (spin when on ground, stop in air)
        if self.y <= 0.6 and self.velocity > 0:
            if not hasattr(self, 'wheel_angle'):
                self.wheel_angle = 0.0
            self.wheel_angle += self.velocity * 60  # Spin rate proportional to speed
            if self.wheel_angle > 360.0:
                self.wheel_angle -= 360.0
        else:
            if not hasattr(self, 'wheel_angle'):
                self.wheel_angle = 0.0

        # Update bullets
        new_bullets = []
        for bullet in self.bullets:
            # Move bullet forward
            bullet_yaw_rad = math.radians(bullet['yaw'])
            bullet_pitch_rad = math.radians(bullet['pitch'])
            
            b_fwd_x = math.sin(bullet_yaw_rad) * math.cos(bullet_pitch_rad)
            b_fwd_y = math.sin(bullet_pitch_rad)
            b_fwd_z = -math.cos(bullet_yaw_rad) * math.cos(bullet_pitch_rad)

            bullet['x'] += bullet['speed'] * b_fwd_x
            bullet['y'] += bullet['speed'] * b_fwd_y
            bullet['z'] += bullet['speed'] * b_fwd_z
            bullet['life'] -= 1
            # Hit detection (for multiplayer)
            if other_planes:
                for plane in other_planes:
                    if plane.player_id != bullet['player_id'] and plane.health > 0:
                        dx = bullet['x'] - plane.x
                        dy = bullet['y'] - plane.y
                        dz = bullet['z'] - plane.z
                        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
                        if dist < 0.7:  # hitbox radius
                            plane.health -= bullet.get('damage', 20)
                            print(f"Plane {plane.player_id} was hit! Health: {plane.health}")
                            bullet['life'] = 0
            if bullet['life'] > 0:
                new_bullets.append(bullet)
        self.bullets = new_bullets

    def update_destroyed(self):
        if self.explosion_timer == 0 and self.smoke_timer == 0: # First time
            self.explosion_timer = 40
            self.smoke_timer = 120
            self.respawn_timer = 120
        
        if self.explosion_timer > 0:
            self.explosion_timer -= 1
        elif self.smoke_timer > 0: # After explosion, smoke
            self.smoke_timer -= 1

        if self.respawn_timer > 0:
            self.respawn_timer -= 1
        else:
            self.respawn()

    def calculate_wing_slope(self):
        # Smoothly interpolate the roll angle to the target angle
        self.roll += (self.target_roll_angle - self.roll) * 0.05

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.yaw, 0, 1, 0)
        glRotatef(self.roll, 0, 0, 1)
        glRotatef(self.pitch, 1, 0, 0)
        
        # Fuselage
        glPushMatrix()
        glColor3f(*self.color)
        glScalef(1.0, 0.2, 5.0)
        draw_cube()
        glPopMatrix()

        # Wings (now with animated ailerons)
        # Main wing section
        glPushMatrix()
        glColor3f(*(c * 0.8 for c in self.color))
        glTranslatef(0, 0, -1)
        glScalef(3.0, 0.1, 1.0)
        draw_cube()
        glPopMatrix()
        
        # Left Aileron
        glPushMatrix()
        glColor3f(0.5, 0.5, 0.5)
        glTranslatef(-2.0, 0, -1)
        glRotatef(self.aileron_angle, 1, 0, 0)
        glScalef(1.0, 0.1, 1.0)
        draw_cube()
        glPopMatrix()
        
        # Right Aileron
        glPushMatrix()
        glColor3f(0.5, 0.5, 0.5)
        glTranslatef(2.0, 0, -1)
        glRotatef(-self.aileron_angle, 1, 0, 0)
        glScalef(1.0, 0.1, 1.0)
        draw_cube()
        glPopMatrix()

        # Tail (now with animated elevator)
        # Vertical Stabilizer
        glPushMatrix()
        glColor3f(0.6, 0.6, 0.6)
        glTranslatef(0, 0.5, 2.0)
        glScalef(0.2, 1.0, 1.0)
        draw_cube()
        glPopMatrix()
        
        # Horizontal Stabilizer (Elevator)
        glPushMatrix()
        glColor3f(0.5, 0.5, 0.5)
        glTranslatef(0, 0.5, 2.2)
        glRotatef(self.elevator_angle, 1, 0, 0)
        glScalef(2.0, 0.1, 0.5)
        draw_cube()
        glPopMatrix()

        # Cockpit
        glPushMatrix()
        glColor3f(0.2, 0.2, 0.8)  # Blue
        glTranslatef(0, 0.25, -1.5)
        glScalef(0.5, 0.2, 0.5)
        draw_cube()
        glPopMatrix()

        # Propeller
        glPushMatrix()
        glColor3f(0.1, 0.1, 0.1)
        glTranslatef(0, 0, -2.6)
        glRotatef(self.propeller_angle, 0, 0, 1)
        glScalef(0.1, 1.5, 0.1)
        draw_cube()
        glPopMatrix()

        # Draw permanent wheels (always show)
        self.draw_wheels()
        # Draw bullets
        self.draw_bullets()
        # Draw explosion/smoke if destroyed
        if self.health <= 0:
            self.draw_explosion_and_smoke()

        glPopMatrix()

    def draw_wheels(self):
        # Draw permanent wheels on the plane (realistic, round wheels, default struts, no smoke)
        # Struts (vertical, default)
        glColor3f(0.1, 0.1, 0.1) # Dark for struts
        # Left Strut
        glPushMatrix()
        glTranslatef(-1.1, 0.0, -1.2)
        glScalef(0.12, 0.7, 0.12)
        draw_cube()
        glPopMatrix()
        # Right Strut
        glPushMatrix()
        glTranslatef(1.1, 0.0, -1.2)
        glScalef(0.12, 0.7, 0.12)
        draw_cube()
        glPopMatrix()

        # Wheels (realistic cylinders, animated vertically, fixed positions)
        glColor3f(0.1, 0.1, 0.1) # Very dark grey/black for rubber
        # Left Wheel
        glPushMatrix()
        glTranslatef(-1.1, -0.7, -1.2)
        glRotatef(getattr(self, 'wheel_angle', 0.0), 1, 0, 0)  # Rotate around X axis
        glRotatef(90, 0, 1, 0)  # Orient cylinder to roll forward
        draw_cylinder(radius=0.22, length=0.12, slices=24)
        glPopMatrix()
        # Right Wheel
        glPushMatrix()
        glTranslatef(1.1, -0.7, -1.2)
        glRotatef(getattr(self, 'wheel_angle', 0.0), 1, 0, 0)
        glRotatef(90, 0, 1, 0)
        draw_cylinder(radius=0.22, length=0.12, slices=24)
        glPopMatrix()
        # Tail Wheel
        glPushMatrix()
        glTranslatef(0, -0.8, 2.5)
        glRotatef(getattr(self, 'wheel_angle', 0.0), 1, 0, 0)
        glRotatef(90, 0, 1, 0)
        draw_cylinder(radius=0.11, length=0.07, slices=20)
        glPopMatrix()

    def draw_bullets(self):
        for bullet in self.bullets:
            # Tracer: bright yellow with a glowing tail
            glColor3f(1.0, 1.0, 0.2)
            glPushMatrix()
            glTranslatef(bullet['x'] - self.x, bullet['y'] - self.y, bullet['z'] - self.z)
            glScalef(0.12, 0.12, 1.0)
            draw_cube()
            glPopMatrix()
            # Tail (fainter)
            glColor3f(1.0, 0.8, 0.2)
            for i in range(1, 4):
                glPushMatrix()
                glTranslatef(bullet['x'] - self.x, bullet['y'] - self.y, bullet['z'] - self.z + 0.3 * i)
                glScalef(0.08, 0.08, 0.5)
                draw_cube()
                glPopMatrix()

    def draw_explosion_and_smoke(self):
        # Explosion (first frames)
        if self.explosion_timer > 0:
            for i in range(20):
                glPushMatrix()
                glColor3f(1.0, 0.5 + 0.5 * (i % 2), 0.0)
                angle = i * (360 / 20)
                dist = 0.5 + 0.5 * (self.explosion_timer / 40)
                x = math.cos(math.radians(angle)) * dist
                y = math.sin(math.radians(angle)) * dist
                glTranslatef(x, y, 0)
                glScalef(0.3, 0.3, 0.3)
                draw_cube()
                glPopMatrix()
        # Smoke (after explosion)
        if self.smoke_timer > 0:
            for i in range(8):
                glPushMatrix()
                glColor3f(0.3, 0.3, 0.3)
                angle = i * (360 / 8)
                dist = 0.7 + 0.2 * (self.smoke_timer / 120)
                x = math.cos(math.radians(angle)) * dist
                y = math.sin(math.radians(angle)) * dist
                glTranslatef(x, y + 0.2 * (120 - self.smoke_timer), 0)
                glScalef(0.25, 0.25, 0.25)
                draw_cube()
                glPopMatrix()

    def handle_input(self, keys):
        if self.health <= 0 and self.respawn_timer > 0:
            return  # Ignore input while destroyed
        # Throttle controls
        if keys[pygame.K_w]:
            self.thrust_level += 0.01
        if keys[pygame.K_s]:
            self.thrust_level -= 0.01
        
        # Clamp throttle after input
        self.thrust_level = max(0.0, min(1.0, self.thrust_level))

        # Ground movement controls
        if not self.is_airborne:
            self.ground_turn_rate = 0
            if keys[pygame.K_LEFT]:
                self.ground_turn_rate = 1.0  # A or Left = left
            if keys[pygame.K_RIGHT]:
                self.ground_turn_rate = -1.0 # D or Right = right

        # Always allow pitch control (for takeoff rotation)
        if keys[pygame.K_UP]:
            self.pitch_rate = -0.5
            self.elevator_angle = -20.0
        elif keys[pygame.K_DOWN]:
            self.pitch_rate = 0.5
            self.elevator_angle = 20.0
        else:
            self.pitch_rate = 0.0
            self.elevator_angle = 0.0

        # Roll/aileron animation (always animate wings for feedback)
        if keys[pygame.K_LEFT]:
            self.target_roll_angle = 30.0
            self.aileron_angle = 20.0
        elif keys[pygame.K_RIGHT]:
            self.target_roll_angle = -30.0
            self.aileron_angle = -20.0
        else:
            self.target_roll_angle = 0.0
            self.aileron_angle = 0.0

        if keys[pygame.K_f]:
            self.flaps_deployed = True
        else:
            self.flaps_deployed = False

        if keys[pygame.K_b]:
            self.brakes_applied = True
        else:
            self.brakes_applied = False

        # Shooting (SPACE)
        if keys[pygame.K_SPACE]:
            now = time.time()
            if now - self.last_shot_time > self.shot_cooldown:
                # Fire a bullet from the nose (propeller position)
                # Nose offset in local plane coordinates: (0, 0, -2.6)
                nose_offset = -2.6
                yaw_rad = math.radians(self.yaw)
                pitch_rad = math.radians(self.pitch)
                
                # Calculate the forward vector
                fwd_x = math.sin(yaw_rad) * math.cos(pitch_rad)
                fwd_y = math.sin(pitch_rad)
                fwd_z = -math.cos(yaw_rad) * math.cos(pitch_rad)

                # Calculate world position of the nose
                nose_x = self.x + fwd_x * nose_offset
                nose_y = self.y + fwd_y * nose_offset
                nose_z = self.z + fwd_z * nose_offset
                
                bullet = {
                    'x': nose_x,
                    'y': nose_y,
                    'z': nose_z,
                    'yaw': self.yaw,
                    'pitch': self.pitch,
                    'speed': 2.5,
                    'life': 60,  # frames
                    'player_id': self.player_id,
                    'damage': self.firepower * 10
                }
                self.bullets.append(bullet)
                self.last_shot_time = now
                sound.play_shoot()

    def reset(self):
        self.x, self.y, self.z = self.initial_pos
        self.pitch = 0.0
        self.roll = 0.0
        self.yaw = 0.0
        self.velocity = 0.0
        self.thrust_level = 0.0

        self.pitch_rate = 0.0
        self.roll_rate = 0.0
        self.target_roll_angle = 0.0
        
        self.is_airborne = False  # Reset to ground
        self.is_stalling = False
        self.crash_sound_played = False
        self.crash_timer = 0

        # Animation
        self.propeller_angle = 0
        self.aileron_angle = 0
        self.elevator_angle = 0
        self.ground_turn_rate = 0
        
        self.vertical_speed = 0
        self.last_y = self.y

        # New features
        self.fuel = 100.0  # Fuel percentage
        self.fuel_consumption = 0.005  # Fuel consumption per frame
        self.damage = 0.0  # Damage percentage
        self.max_damage = 100.0
        self.engine_health = 100.0
        self.wing_health = 100.0
        self.landing_gear_health = 100.0

        self.brakes_applied = False

        self.ground_velocity_x = 0.0
        self.ground_velocity_z = 0.0

        self.bullets = []  # List of active bullets
        self.last_shot_time = 0
        self.shot_cooldown = 0.15  # seconds between shots
        self.respawn_timer = 0

    def respawn(self):
        self.deaths += 1
        self.x, self.y, self.z = self.initial_pos
        self.pitch = 0.0
        self.roll = 0.0
        self.yaw = 0.0
        self.velocity = 0.0
        self.thrust_level = 0.0
        self.health = 100
        self.explosion_timer = 0
        self.smoke_timer = 0
        self.respawn_timer = 0
        self.bullets = []
        self.pitch_rate = 0.0
        self.roll_rate = 0.0
        self.target_roll_angle = 0.0
        self.is_airborne = False
        self.is_stalling = False
        self.crash_sound_played = False
        self.crash_timer = 0
        self.propeller_angle = 0
        self.aileron_angle = 0
        self.elevator_angle = 0
        self.ground_turn_rate = 0
        self.vertical_speed = 0
        self.last_y = self.y
        self.fuel = 100.0
        self.fuel_consumption = 0.005
        self.damage = 0.0
        self.max_damage = 100.0
        self.engine_health = 100.0
        self.wing_health = 100.0
        self.landing_gear_health = 100.0
        self.flaps_deployed = False
        self.flap_lift_bonus = 0.002
        self.flap_drag_penalty = 0.0005
        self.autopilot = False
        self.brakes_applied = False
        self.ground_velocity_x = 0.0
        self.ground_velocity_z = 0.0
        self.airborne_timer = 0
        self.last_shot_time = 0
        self.shot_cooldown = 0.15

    def network_update(self, data):
        # Stub for future multiplayer sync
        pass