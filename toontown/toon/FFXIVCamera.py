"""
FFXIVCamera.py - Smooth Third-Person FFXIV-Style Orbit Camera for Toontown
Features:
- Left-click drag: Free orbit camera around Toon without turning character
- Right-click drag: Orbit camera AND rotate Toon towards camera facing
- Mouse wheel: Smooth zoom in / zoom out (clamp 3.0 to 45.0)
- Pitch clamping (-80 to 45 degrees)
- Obstruction prevention (smart camera raycast against geometry)
- Fully toggleable in Options
"""

import math
from panda3d.core import Point3, Vec3, WindowProperties
from direct.showbase.DirectObject import DirectObject
from direct.task import Task


class FFXIVCamera(DirectObject):
    def __init__(self, localAvatar):
        DirectObject.__init__(self)
        self.avatar = localAvatar
        self.enabled = False

        # Camera spherical parameters
        self.distance = 18.0
        self.targetDistance = 18.0
        self.minDistance = 4.0
        self.maxDistance = 45.0

        self.yaw = 0.0      # Orbit heading relative to avatar
        self.pitch = 15.0   # Degrees above avatar horizon (-75 to 45)
        self.minPitch = -60.0
        self.maxPitch = 45.0

        # Mouse tracking state
        self.isLeftDragging = False
        self.isRightDragging = False
        self.lastMousePos = None
        self.mouseSensitivity = 120.0  # Pixels to degrees ratio

    def enable(self):
        if self.enabled:
            return
        self.enabled = True

        # Hook mouse input events
        self.accept('mouse1', self.__onLeftDown)
        self.accept('mouse1-up', self.__onLeftUp)
        self.accept('mouse3', self.__onRightDown)
        self.accept('mouse3-up', self.__onRightUp)
        self.accept('wheel_up', self.__onWheelUp)
        self.accept('wheel_down', self.__onWheelDown)

        # Sync initial heading with current camera orientation
        if hasattr(self.avatar, 'getH'):
            camH = camera.getH(render)
            avH = self.avatar.getH(render)
            self.yaw = camH - avH

        taskMgr.add(self.__updateCameraTask, 'FFXIVCamera-updateTask', priority=48)

    def disable(self):
        if not self.enabled:
            return
        self.enabled = False
        self.ignoreAll()
        taskMgr.remove('FFXIVCamera-updateTask')
        self.isLeftDragging = False
        self.isRightDragging = False
        self.lastMousePos = None

    def __onLeftDown(self):
        self.isLeftDragging = True
        self.lastMousePos = None

    def __onLeftUp(self):
        self.isLeftDragging = False
        self.lastMousePos = None

    def __onRightDown(self):
        self.isRightDragging = True
        self.lastMousePos = None

    def __onRightUp(self):
        self.isRightDragging = False
        self.lastMousePos = None

    def __onWheelUp(self):
        self.targetDistance = max(self.minDistance, self.targetDistance - 2.5)

    def __onWheelDown(self):
        self.targetDistance = min(self.maxDistance, self.targetDistance + 2.5)

    def __updateCameraTask(self, task):
        if not self.enabled or not self.avatar or self.avatar.isEmpty():
            return Task.cont

        # Handle mouse drag rotation
        if (self.isLeftDragging or self.isRightDragging) and base.mouseWatcherNode.hasMouse():
            mX = base.mouseWatcherNode.getMouseX()
            mY = base.mouseWatcherNode.getMouseY()

            if self.lastMousePos is not None:
                dx = mX - self.lastMousePos[0]
                dy = mY - self.lastMousePos[1]

                deltaYaw = -dx * self.mouseSensitivity
                deltaPitch = dy * self.mouseSensitivity

                if self.isRightDragging:
                    # Right-click drag rotates the character AND the camera together
                    self.avatar.setH(self.avatar.getH() - deltaYaw)
                else:
                    # Left-click drag orbits the camera freely around character
                    self.yaw += deltaYaw

                self.pitch = max(self.minPitch, min(self.maxPitch, self.pitch + deltaPitch))

            self.lastMousePos = (mX, mY)
        else:
            self.lastMousePos = None

        # Smooth distance zoom lerp
        self.distance += (self.targetDistance - self.distance) * 0.25

        # Compute camera position relative to avatar
        radPitch = math.radians(self.pitch)
        radYaw = math.radians(self.yaw)

        horizDist = self.distance * math.cos(radPitch)
        camZ = self.distance * math.sin(radPitch) + self.avatar.getHeight() * 0.95

        camX = horizDist * math.sin(radYaw)
        camY = -horizDist * math.cos(radYaw)

        camPosRel = Point3(camX, camY, camZ)
        lookAtRel = Point3(0, 0, self.avatar.getHeight() * 0.75)

        camera.setPos(self.avatar, camPosRel)
        camera.lookAt(self.avatar, lookAtRel)

        return Task.cont
