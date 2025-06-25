from OpenGL.GL import *
import random
from utils import draw_cube
import math

class Environment:
    def __init__(self):
        self.mountains = []
        self.trees = []
        self.runways = []
        self.clouds = []  # New: clouds for weather effects
        self.generation_radius = 200
        self.culling_radius = 250
        self.last_player_pos = [0, 0, 0]
        self.weather = "clear"  # clear, cloudy, storm
        self.time_of_day = "day"  # day, night, sunset
        self.rain_particles = []  # For rain effects

    def update(self, player_pos):
        if math.dist(player_pos, self.last_player_pos) > 100:
            self.last_player_pos = list(player_pos)
            self.generate_scenery(player_pos)
            self.cull_scenery(player_pos)

    def generate_scenery(self, center_pos, mountain_count=5, tree_count=20, runway_chance=0.1):
        # Generate mountains
        for _ in range(mountain_count):
            x = random.uniform(-self.generation_radius, self.generation_radius) + center_pos[0]
            z = random.uniform(-self.generation_radius, self.generation_radius) + center_pos[2]
            y = 0
            if any(math.dist([x,y,z], m['pos']) < 30 for m in self.mountains): continue # Avoid clumping
            height = random.uniform(5, 30)
            base = random.uniform(5, 20)
            self.mountains.append({'pos': [x, y, z], 'height': height, 'base': base})
        
        # Generate trees
        for _ in range(tree_count):
            x = random.uniform(-self.generation_radius, self.generation_radius) + center_pos[0]
            z = random.uniform(-self.generation_radius, self.generation_radius) + center_pos[2]
            
            on_runway = False
            for r_pos, r_size, _ in self.runways:
                if (r_pos[0] - r_size[0]/2 < x < r_pos[0] + r_size[0]/2) and \
                   (r_pos[2] - r_size[1]/2 < z < r_pos[2] + r_size[1]/2):
                    on_runway = True
                    break
            if on_runway: continue

            y = 0
            if any(math.dist([x,y,z], t) < 3 for t in self.trees): continue
            self.trees.append([x, y, z])

        # Generate runways
        if random.random() < runway_chance:
            x = center_pos[0]
            z = center_pos[2]
            y = 0.1
            angle = random.choice([0, 90, 180, 270])
            self.runways.append(([x, y, z], [10, 200], angle))
            
        # Generate clouds
        if self.weather in ["cloudy", "storm"]:
            for _ in range(10):
                x = random.uniform(-self.generation_radius, self.generation_radius) + center_pos[0]
                z = random.uniform(-self.generation_radius, self.generation_radius) + center_pos[2]
                y = random.uniform(20, 50)  # High altitude
                size = random.uniform(5, 15)
                self.clouds.append({'pos': [x, y, z], 'size': size})

    def cull_scenery(self, center_pos):
        self.mountains = [m for m in self.mountains if math.dist(m['pos'], center_pos) < self.culling_radius]
        self.trees = [t for t in self.trees if math.dist(t, center_pos) < self.culling_radius]
        self.runways = [r for r in self.runways if math.dist(r[0], center_pos) < self.culling_radius]

    def draw_ground(self, center_pos):
        size = self.generation_radius * 2
        x, _, z = center_pos
        glColor3f(0.2, 0.6, 0.2)
        glBegin(GL_QUADS)
        glNormal3f(0, 1, 0)
        glVertex3f(x - size, 0, z - size)
        glVertex3f(x + size, 0, z - size)
        glVertex3f(x + size, 0, z + size)
        glVertex3f(x - size, 0, z + size)
        glEnd()

    def draw_runway(self, position, size, angle):
        x, y, z = position
        width, length = size
        
        glPushMatrix()
        glTranslatef(x, y, z)
        glRotatef(angle, 0, 1, 0)
        
        # Main runway
        glColor3f(0.4, 0.4, 0.4)
        glBegin(GL_QUADS)
        glNormal3f(0, 1, 0)
        glVertex3f(-width/2, 0, -length/2)
        glVertex3f(width/2, 0, -length/2)
        glVertex3f(width/2, 0, length/2)
        glVertex3f(-width/2, 0, length/2)
        glEnd()

        # Markings
        glColor3f(1.0, 1.0, 1.0)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        
        # Centerline
        for i in range(int(length / 20)):
            glVertex3f(0, 0.01, -length/2 + i*20)
            glVertex3f(0, 0.01, -length/2 + i*20 + 10)

        glEnd()
        glPopMatrix()

    def draw_mountain(self, position, height, base):
        x, y, z = position
        glColor3f(0.5, 0.35, 0.25) # Brownish color for mountains
        
        glBegin(GL_TRIANGLES)
        # Base
        glVertex3f(x - base, y, z - base)
        glVertex3f(x + base, y, z - base)
        glVertex3f(x - base, y, z + base)

        glVertex3f(x + base, y, z - base)
        glVertex3f(x + base, y, z + base)
        glVertex3f(x - base, y, z + base)
        
        # Sides
        glVertex3f(x, y + height, z)
        glVertex3f(x - base, y, z - base)
        glVertex3f(x + base, y, z - base)

        glVertex3f(x, y + height, z)
        glVertex3f(x + base, y, z - base)
        glVertex3f(x + base, y, z + base)

        glVertex3f(x, y + height, z)
        glVertex3f(x + base, y, z + base)
        glVertex3f(x - base, y, z + base)

        glVertex3f(x, y + height, z)
        glVertex3f(x - base, y, z + base)
        glVertex3f(x - base, y, z - base)
        glEnd()

    def draw_tree(self, position):
        x, y, z = position
        
        glPushMatrix()
        glTranslatef(x, y, z)

        # Trunk
        glColor3f(0.5, 0.35, 0.25) # Brown
        glPushMatrix()
        glTranslatef(0, 1.5, 0)
        glScalef(0.2, 3.0, 0.2)
        draw_cube()
        glPopMatrix()

        # Canopy
        glColor3f(0.1, 0.5, 0.1) # Dark green
        glPushMatrix()
        glTranslatef(0, 3.5, 0)
        glScalef(1.5, 2.0, 1.5)
        draw_cube()
        glPopMatrix()

        glPopMatrix()

    def draw(self, player_pos):
        # Set lighting based on time of day
        if self.time_of_day == "night":
            glLightfv(GL_LIGHT0, GL_AMBIENT, [0.1, 0.1, 0.2, 1.0])  # Blue ambient light
            glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.3, 0.3, 0.5, 1.0])  # Dim blue light
        elif self.time_of_day == "sunset":
            glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.2, 0.1, 1.0])  # Orange ambient
            glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.5, 0.3, 1.0])  # Orange light
        else:  # day
            glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])  # Normal ambient
            glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])  # Normal light
            
        self.draw_ground(player_pos)
        for r_pos, r_size, r_angle in self.runways:
            self.draw_runway(r_pos, r_size, r_angle)
        for mountain in self.mountains:
            self.draw_mountain(mountain['pos'], mountain['height'], mountain['base'])
        for tree in self.trees:
            glPushMatrix()
            self.draw_tree(tree)
            glPopMatrix()
        for cloud in self.clouds:
            self.draw_cloud(cloud['pos'], cloud['size'])
            
        # Draw rain if stormy weather
        if self.weather == "storm":
            self.draw_rain()

    def draw_cloud(self, position, size):
        x, y, z = position
        glColor3f(0.9, 0.9, 0.9)  # White clouds
        
        # Draw multiple spheres to create cloud shape
        for i in range(5):
            offset_x = (i - 2) * size * 0.3
            offset_y = (i % 2) * size * 0.2
            offset_z = (i - 2) * size * 0.3
            
            glPushMatrix()
            glTranslatef(x + offset_x, y + offset_y, z + offset_z)
            glScalef(size * 0.4, size * 0.3, size * 0.4)
            self.draw_sphere()
            glPopMatrix()

    def draw_sphere(self):
        # Simple sphere approximation
        glBegin(GL_QUADS)
        for i in range(8):
            for j in range(4):
                angle1 = i * 45
                angle2 = (i + 1) * 45
                angle3 = j * 45
                angle4 = (j + 1) * 45
                
                x1 = math.cos(math.radians(angle1)) * math.cos(math.radians(angle3))
                y1 = math.sin(math.radians(angle3))
                z1 = math.sin(math.radians(angle1)) * math.cos(math.radians(angle3))
                
                x2 = math.cos(math.radians(angle2)) * math.cos(math.radians(angle3))
                y2 = math.sin(math.radians(angle3))
                z2 = math.sin(math.radians(angle2)) * math.cos(math.radians(angle3))
                
                x3 = math.cos(math.radians(angle2)) * math.cos(math.radians(angle4))
                y3 = math.sin(math.radians(angle4))
                z3 = math.sin(math.radians(angle2)) * math.cos(math.radians(angle4))
                
                x4 = math.cos(math.radians(angle1)) * math.cos(math.radians(angle4))
                y4 = math.sin(math.radians(angle4))
                z4 = math.sin(math.radians(angle1)) * math.cos(math.radians(angle4))
                
                glVertex3f(x1, y1, z1)
                glVertex3f(x2, y2, z2)
                glVertex3f(x3, y3, z3)
                glVertex3f(x4, y4, z4)
        glEnd()

    def draw_rain(self):
        # Draw rain particles
        glColor3f(0.5, 0.7, 1.0)  # Blue rain
        glBegin(GL_LINES)
        for i in range(100):
            x = random.uniform(-50, 50)
            y = random.uniform(0, 30)
            z = random.uniform(-50, 50)
            
            glVertex3f(x, y, z)
            glVertex3f(x, y - 2, z)
        glEnd()

    def reset(self):
        """Reset the environment to initial state"""
        self.mountains = []
        self.trees = []
        self.runways = []
        self.last_player_pos = [0, 0, 0]
        # Generate initial scenery
        self.generate_scenery([0, 0, 0], mountain_count=20, tree_count=100) 