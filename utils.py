import pygame
from OpenGL.GL import *
import math

def draw_text(x, y, text, font_size=24):
    font = pygame.font.Font(None, font_size)
    text_surface = font.render(text, True, (255, 255, 255, 255), (0, 0, 0, 0))
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    glWindowPos2d(x, y)
    glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)

def draw_throttle(x, y, width, height, thrust_level):
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Draw tick marks for reference
    glColor4f(1.0, 1.0, 1.0, 0.4)
    glLineWidth(1.0)
    for i in range(11):
        tick_y = y + i * (height / 10.0)
        glBegin(GL_LINES)
        glVertex2f(x - 5, tick_y)
        glVertex2f(x, tick_y)
        glEnd()

    # Draw the colored throttle level bar using a gradient
    fill_height = height * thrust_level
    glBegin(GL_QUADS)
    
    # Bottom color (Blue)
    glColor3f(0.2, 0.4, 1.0) 
    glVertex2f(x, y)
    glVertex2f(x + width, y)

    # Top color (interpolated: Blue -> Yellow -> Red)
    if thrust_level <= 0.6:
        interp = thrust_level / 0.6
        r = 0.2 * (1 - interp) + 1.0 * interp
        g = 0.4 * (1 - interp) + 1.0 * interp
        b = 1.0 * (1 - interp) + 0.2 * interp
    else:
        interp = (thrust_level - 0.6) / 0.4
        r = 1.0 * (1 - interp) + 1.0 * interp
        g = 1.0 * (1 - interp) + 0.3 * interp
        b = 0.2 * (1 - interp) + 0.2 * interp
    
    glColor3f(r, g, b)
    glVertex2f(x + width, y + fill_height)
    glVertex2f(x, y + fill_height)
    glEnd()

    # Draw a clean border around the slider's full range
    glColor4f(0.8, 0.8, 0.8, 0.7)
    glLineWidth(1.5)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()

    # Draw a sleek indicator handle next to the bar
    handle_y = y + fill_height
    handle_size = width * 0.8
    glColor4f(1.0, 1.0, 1.0, 0.9)
    glBegin(GL_TRIANGLES)
    glVertex2f(x - 8, handle_y - handle_size / 2)
    glVertex2f(x - 2, handle_y)
    glVertex2f(x - 8, handle_y + handle_size / 2)
    glEnd()
    glDisable(GL_BLEND)

def draw_compass(x, y, radius, yaw):
    # Draw compass background
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_POLYGON)
    for i in range(100):
        angle = 2 * math.pi * i / 100
        glVertex2f(x + radius * math.cos(angle), y + radius * math.sin(angle))
    glEnd()
    
    # Draw North indicator needle
    glColor3f(1.0, 0.0, 0.0) # Red for North
    glLineWidth(3.0)
    glBegin(GL_LINES)
    angle = math.radians(-yaw)
    glVertex2f(x, y)
    glVertex2f(x + radius * math.sin(angle), y + radius * math.cos(angle))
    glEnd()

def draw_cylinder(radius=0.5, length=0.2, slices=24):
    # Draw a simple cylinder along the X axis
    glBegin(GL_QUAD_STRIP)
    for i in range(slices + 1):
        theta = 2.0 * math.pi * i / slices
        x = radius * math.cos(theta)
        y = radius * math.sin(theta)
        glVertex3f(x, y, -length/2)
        glVertex3f(x, y, length/2)
    glEnd()
    # Draw end caps
    for z in [-length/2, length/2]:
        glBegin(GL_POLYGON)
        for i in range(slices):
            theta = 2.0 * math.pi * i / slices
            x = radius * math.cos(theta)
            y = radius * math.sin(theta)
            glVertex3f(x, y, z)
        glEnd()

def draw_cube():
    # ... (code from Plane.draw_cube)
    glBegin(GL_QUADS)
    # Front face
    glNormal3f(0, 0, 1)
    glVertex3f(-0.5, -0.5, 0.5)
    glVertex3f(0.5, -0.5, 0.5)
    glVertex3f(0.5, 0.5, 0.5)
    glVertex3f(-0.5, 0.5, 0.5)
    # Back face
    glNormal3f(0, 0, -1)
    glVertex3f(-0.5, -0.5, -0.5)
    glVertex3f(-0.5, 0.5, -0.5)
    glVertex3f(0.5, 0.5, -0.5)
    glVertex3f(0.5, -0.5, -0.5)
    # Top face
    glNormal3f(0, 1, 0)
    glVertex3f(-0.5, 0.5, -0.5)
    glVertex3f(-0.5, 0.5, 0.5)
    glVertex3f(0.5, 0.5, 0.5)
    glVertex3f(0.5, 0.5, -0.5)
    # Bottom face
    glNormal3f(0, -1, 0)
    glVertex3f(-0.5, -0.5, -0.5)
    glVertex3f(0.5, -0.5, -0.5)
    glVertex3f(0.5, -0.5, 0.5)
    glVertex3f(-0.5, -0.5, 0.5)
    # Right face
    glNormal3f(1, 0, 0)
    glVertex3f(0.5, -0.5, -0.5)
    glVertex3f(0.5, 0.5, -0.5)
    glVertex3f(0.5, 0.5, 0.5)
    glVertex3f(0.5, -0.5, 0.5)
    # Left face
    glNormal3f(-1, 0, 0)
    glVertex3f(-0.5, -0.5, -0.5)
    glVertex3f(-0.5, -0.5, 0.5)
    glVertex3f(-0.5, 0.5, 0.5)
    glVertex3f(-0.5, 0.5, -0.5)
    glEnd()

def draw_health_bar(x, y, width, height, health, max_health=100):
    # Background
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()

    # Health color (green to red)
    health_ratio = max(0.0, min(1.0, health / max_health))
    r = 1.0 - health_ratio
    g = health_ratio
    glColor3f(r, g, 0.0)
    fill_width = width * health_ratio
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + fill_width, y)
    glVertex2f(x + fill_width, y + height)
    glVertex2f(x, y + height)
    glEnd() 

def draw_hud_box(x, y, width, height, alpha=0.5):
    glColor4f(0.1, 0.1, 0.1, alpha)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()
    glDisable(GL_BLEND) 

def draw_rounded_box(x, y, width, height, radius=12, color=(0.1,0.1,0.1,0.7)):
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(*color)
    # Center rectangle
    glBegin(GL_QUADS)
    glVertex2f(x+radius, y)
    glVertex2f(x+width-radius, y)
    glVertex2f(x+width-radius, y+height)
    glVertex2f(x+radius, y+height)
    glEnd()
    # Side rectangles
    glBegin(GL_QUADS)
    glVertex2f(x, y+radius)
    glVertex2f(x+radius, y+radius)
    glVertex2f(x+radius, y+height-radius)
    glVertex2f(x, y+height-radius)
    glVertex2f(x+width-radius, y+radius)
    glVertex2f(x+width, y+radius)
    glVertex2f(x+width, y+height-radius)
    glVertex2f(x+width-radius, y+height-radius)
    glEnd()
    # Corners (draw as triangle fans)
    for cx, cy, start in [(x+radius, y+radius, 180), (x+width-radius, y+radius, 270), (x+width-radius, y+height-radius, 0), (x+radius, y+height-radius, 90)]:
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(cx, cy)
        for a in range(start, start+91, 15):
            angle = math.radians(a)
            glVertex2f(cx + math.cos(angle)*radius, cy + math.sin(angle)*radius)
        glEnd()
    glDisable(GL_BLEND)

def draw_icon(x, y, icon_type, size=18):
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    if icon_type == 'health':
        glColor3f(1,0,0)
        glBegin(GL_TRIANGLES)
        glVertex2f(x, y)
        glVertex2f(x+size, y)
        glVertex2f(x+size/2, y+size)
        glEnd()
    elif icon_type == 'throttle':
        glColor3f(0.8,0.8,0.2)
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x+size, y)
        glVertex2f(x+size, y+size)
        glVertex2f(x, y+size)
        glEnd()
    elif icon_type == 'radar':
        glColor3f(0.2,0.8,1.0)
        glBegin(GL_LINE_LOOP)
        for i in range(32):
            angle = 2*math.pi*i/32
            glVertex2f(x+size/2+math.cos(angle)*size/2, y+size/2+math.sin(angle)*size/2)
        glEnd()
    glDisable(GL_BLEND) 