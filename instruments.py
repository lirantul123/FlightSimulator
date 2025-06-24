from OpenGL.GL import *
from OpenGL.GLU import *
import pygame
import math

def draw_text(x, y, text, font):
    text_surface = font.render(text, True, (255, 255, 255, 255))
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    glWindowPos2d(x, y)
    glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)

class Instruments:
    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.instrument_size = size
        self.padding = 5 # Reduced padding
        self.font = pygame.font.Font(None, 18) # Smaller font

    def draw(self, plane):
        # Top Row
        glPushMatrix()
        glTranslatef(self.x, self.y + self.instrument_size + self.padding, 0)
        self.draw_airspeed_indicator(plane.velocity * 120)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(self.x + self.instrument_size + self.padding, self.y + self.instrument_size + self.padding, 0)
        self.draw_attitude_indicator(plane.pitch, plane.roll)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(self.x + 2 * (self.instrument_size + self.padding), self.y + self.instrument_size + self.padding, 0)
        self.draw_altimeter(plane.y * 3.28084)
        glPopMatrix()

        # Bottom Row
        glPushMatrix()
        glTranslatef(self.x, self.y, 0)
        self.draw_turn_coordinator(plane.roll, (math.sin(math.radians(plane.roll)) * plane.velocity * 0.3))
        glPopMatrix()

        glPushMatrix()
        glTranslatef(self.x + self.instrument_size + self.padding, self.y, 0)
        self.draw_heading_indicator(plane.yaw)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(self.x + 2 * (self.instrument_size + self.padding), self.y, 0)
        self.draw_vertical_speed_indicator(plane.vertical_speed)
        glPopMatrix()

    def draw_background(self, label):
        radius = self.instrument_size / 2
        
        # Draw background circle
        glColor3f(0.2, 0.2, 0.2)
        glBegin(GL_POLYGON)
        for i in range(100):
            angle = 2 * math.pi * i / 100
            glVertex2f(radius + radius * math.cos(angle), 
                       radius + radius * math.sin(angle))
        glEnd()
        
        # Draw label
        draw_text(radius - 10, self.instrument_size - 20, label, self.font)
        
        return radius
    
    def draw_needle(self, radius, angle, length, width):
        glPushMatrix()
        glTranslatef(radius, radius, 0)
        glRotatef(-angle, 0, 0, 1)
        glColor3f(1.0, 1.0, 1.0)
        glLineWidth(width)
        glBegin(GL_LINES)
        glVertex2f(0, 0)
        glVertex2f(0, length)
        glEnd()
        glPopMatrix()

    def draw_attitude_indicator(self, pitch, roll):
        instrument_radius = self.instrument_size / 2
        
        glPushMatrix()
        
        # Draw background circle
        glColor3f(0.2, 0.2, 0.2)
        glBegin(GL_POLYGON)
        for i in range(100):
            angle = 2 * math.pi * i / 100
            glVertex2f(instrument_radius + instrument_radius * math.cos(angle), 
                       instrument_radius + instrument_radius * math.sin(angle))
        glEnd()

        # Artificial Horizon
        glEnable(GL_SCISSOR_TEST)
        glScissor(int(self.x), int(self.y), self.instrument_size, self.instrument_size)
        
        glPushMatrix()
        glTranslatef(instrument_radius, instrument_radius, 0)
        glRotatef(-roll, 0, 0, 1)
        
        # Sky
        glColor3f(0.3, 0.5, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(-self.instrument_size, pitch * 2)
        glVertex2f(self.instrument_size, pitch * 2)
        glVertex2f(self.instrument_size, self.instrument_size)
        glVertex2f(-self.instrument_size, self.instrument_size)
        glEnd()
        
        # Ground
        glColor3f(0.6, 0.4, 0.2)
        glBegin(GL_QUADS)
        glVertex2f(-self.instrument_size, -self.instrument_size)
        glVertex2f(self.instrument_size, -self.instrument_size)
        glVertex2f(self.instrument_size, pitch * 2)
        glVertex2f(-self.instrument_size, pitch * 2)
        glEnd()
        
        glPopMatrix()
        glDisable(GL_SCISSOR_TEST)

        # Draw fixed plane symbol
        glColor3f(1.0, 1.0, 0.0)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        # Wings
        glVertex2f(instrument_radius - 30, instrument_radius)
        glVertex2f(instrument_radius + 30, instrument_radius)
        # Fuselage dot
        glEnd()
        glBegin(GL_POINTS)
        glVertex2f(instrument_radius, instrument_radius)
        glEnd()

        glPopMatrix() 

    def draw_airspeed_indicator(self, airspeed):
        radius = self.draw_background("ASI")
        # Draw airspeed markings and needle
        # (Simplified for now)
        angle = airspeed * 1.5 # Scale factor
        self.draw_needle(radius, angle, radius * 0.9, 2.0)

    def draw_altimeter(self, altitude):
        radius = self.draw_background("ALT")
        # Simplified: one needle for hundreds of feet
        angle = (altitude % 1000) / 1000 * 360
        self.draw_needle(radius, angle, radius * 0.9, 2.0)
        # Thousands needle
        angle_1000 = (altitude / 10000) * 360
        self.draw_needle(radius, angle_1000, radius * 0.6, 3.0)

    def draw_turn_coordinator(self, roll, turn_rate):
        radius = self.draw_background("TC")
        glPushMatrix()
        glTranslatef(radius, radius, 0)
        glRotatef(-roll, 0, 0, 1)
        # Draw small plane symbol
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_TRIANGLES)
        glVertex2f(0, 10)
        glVertex2f(-10, -5)
        glVertex2f(10, -5)
        glEnd()
        glPopMatrix()

    def draw_heading_indicator(self, yaw):
        radius = self.draw_background("HDG")
        glPushMatrix()
        glTranslatef(radius, radius, 0)
        glRotatef(yaw, 0, 0, 1)
        
        # Draw compass markings
        cardinals = {'N': 0, 'E': 90, 'S': 180, 'W': 270}
        for_each = ['N', 'E', 'S', 'W']
        for p in for_each:
            angle = math.radians(cardinals[p])
            x = radius * 0.8 * math.sin(angle)
            y = radius * 0.8 * math.cos(angle)
            draw_text(radius + x - 5, radius + y - 5, p, self.font)
        
        glPopMatrix()
        # Draw fixed needle
        self.draw_needle(radius, 0, radius * 0.9, 2.0)

    def draw_vertical_speed_indicator(self, vsi):
        radius = self.draw_background("VSI")
        # vsi is in ft/sec, scale it for the gauge
        angle = -vsi * 0.5
        self.draw_needle(radius, angle, radius * 0.9, 2.0) 