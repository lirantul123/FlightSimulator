import pygame
from OpenGL.GL import *

class Skybox:
    def __init__(self):
        self.textures = self.load_skybox_textures()

    def load_skybox_textures(self):
        texture_paths = [
            'assets/skybox/Daylight Box_Right.bmp', 'assets/skybox/Daylight Box_Left.bmp',
            'assets/skybox/Daylight Box_Top.bmp', 'assets/skybox/Daylight Box_Bottom.bmp',
            'assets/skybox/Daylight Box_Front.bmp', 'assets/skybox/Daylight Box_Back.bmp'
        ]
        textures = []
        for path in texture_paths:
            texture_surface = pygame.image.load(path)
            texture_data = pygame.image.tostring(texture_surface, "RGB", True)
            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, texture_surface.get_width(), texture_surface.get_height(), 0, GL_RGB, GL_UNSIGNED_BYTE, texture_data)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            textures.append(tex_id)
        return textures

    def draw(self, player_pos):
        glPushMatrix()
        # Move the skybox to the player's position so it's always surrounding the camera
        glTranslatef(player_pos[0], player_pos[1], player_pos[2])

        size = 100 # Increased size to avoid clipping
        glDisable(GL_LIGHTING)
        glDepthMask(GL_FALSE)
        glColor3f(1.0, 1.0, 1.0) # Reset color to white
        
        quads = [
            # Right
            [self.textures[0], [size, -size, -size], [size, size, -size], [size, size, size], [size, -size, size]],
            # Left
            [self.textures[1], [-size, -size, size], [-size, size, size], [-size, size, -size], [-size, -size, -size]],
            # Top
            [self.textures[2], [-size, size, size], [size, size, size], [size, size, -size], [-size, size, -size]],
            # Bottom
            [self.textures[3], [-size, -size, -size], [size, -size, -size], [size, -size, size], [-size, -size, size]],
            # Front
            [self.textures[4], [-size, -size, size], [size, -size, size], [size, size, size], [-size, size, size]],
            # Back
            [self.textures[5], [size, -size, -size], [-size, -size, -size], [-size, size, -size], [size, size, -size]]
        ]

        glEnable(GL_TEXTURE_2D)
        for tex_id, v1, v2, v3, v4 in quads:
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0); glVertex3fv(v1)
            glTexCoord2f(1, 0); glVertex3fv(v2)
            glTexCoord2f(1, 1); glVertex3fv(v3)
            glTexCoord2f(0, 1); glVertex3fv(v4)
            glEnd()
        glDisable(GL_TEXTURE_2D)
        
        glDepthMask(GL_TRUE)
        glEnable(GL_LIGHTING)
        glPopMatrix() 