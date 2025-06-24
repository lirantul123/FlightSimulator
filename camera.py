import math
from OpenGL.GL import *
from OpenGL.GLU import *

class Camera:
    def __init__(self, plane):
        self.plane = plane
        self.modes = ['chase', 'cockpit', 'tail']
        self.mode_index = 0

    def cycle_mode(self):
        self.mode_index = (self.mode_index + 1) % len(self.modes)

    def get_mode(self):
        return self.modes[self.mode_index]

    def apply(self):
        mode = self.get_mode()
        player = self.plane

        if mode == 'chase':
            offset_z = 12
            offset_y = 4
            camera_x = player.x - offset_z * math.sin(math.radians(player.yaw))
            camera_y = player.y + offset_y
            camera_z = player.z - offset_z * math.cos(math.radians(player.yaw))
            gluLookAt(camera_x, camera_y, camera_z, player.x, player.y, player.z, 0, 1, 0)
        elif mode == 'cockpit':
            glRotatef(-player.pitch, 1, 0, 0)
            glRotatef(-player.roll, 0, 0, 1)
            glRotatef(-player.yaw, 0, 1, 0)
            glTranslatef(-player.x, -player.y - 0.5, -player.z)
        elif mode == 'tail':
            glTranslatef(0, -2, -8)
            glRotatef(-player.pitch, 1, 0, 0)
            glRotatef(-player.roll, 0, 0, 1)
            glRotatef(-player.yaw, 0, 1, 0)
            glTranslatef(-player.x, -player.y, -player.z)

    def update(self):
        # This method is not strictly needed with the current "apply" logic
        # but it's kept for consistency with the call in main.py
        pass 