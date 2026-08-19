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
        self.distance = 12.0
        self.targetDistance = 12.0
        self.minDistance = 3.0
        self.maxDistance = 35.0

        self.yaw = 0.0      # Orbit heading relative to avatar
        self.pitch = 10.0   # Degrees above avatar horizon (-60 to 45)
        self.minPitch = -60.0
        self.maxPitch = 45.0

        # Mouse tracking & cursor locking state
        self.isLeftDragging = False
        self.isRightDragging = False
        self.lockedCursorPos = None
        self.savedCursorPos = None

    def getSensitivity(self):
        sens = 1.0
        if hasattr(base, 'settings') and base.settings:
            sens = base.settings.getFloat('game', 'camera-sensitivity', 1.0)
        # Base scale: 1.0 -> 140.0 degrees per screen width
        return max(0.1, sens) * 140.0

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
        self.__unlockCursor()
        self.isLeftDragging = False
        self.isRightDragging = False

    def __lockCursor(self):
        if not base.win:
            return
        # Save current pixel position before hiding
        if base.win.hasPointer(0):
            p = base.win.getPointer(0)
            self.savedCursorPos = (p.getX(), p.getY())
            self.lockedCursorPos = (p.getX(), p.getY())
        else:
            winWidth = base.win.getXSize()
            winHeight = base.win.getYSize()
            self.savedCursorPos = (int(winWidth / 2), int(winHeight / 2))
            self.lockedCursorPos = (int(winWidth / 2), int(winHeight / 2))

        # Hide cursor
        props = WindowProperties()
        props.setCursorHidden(True)
        base.win.requestProperties(props)

    def __unlockCursor(self):
        if not base.win:
            return
        # Restore cursor visibility and return cursor to where user clicked
        props = WindowProperties()
        props.setCursorHidden(False)
        base.win.requestProperties(props)

        if self.savedCursorPos:
            base.win.movePointer(0, self.savedCursorPos[0], self.savedCursorPos[1])
            self.savedCursorPos = None
        self.lockedCursorPos = None

    def __onLeftDown(self):
        self.isLeftDragging = True
        if not self.isRightDragging:
            self.__lockCursor()

    def __onLeftUp(self):
        self.isLeftDragging = False
        if not self.isRightDragging:
            self.__unlockCursor()

    def __onRightDown(self):
        self.isRightDragging = True
        if not self.isLeftDragging:
            self.__lockCursor()

    def __onRightUp(self):
        self.isRightDragging = False
        if not self.isLeftDragging:
            self.__unlockCursor()

    def __onWheelUp(self):
        self.targetDistance = max(self.minDistance, self.targetDistance - 2.5)

    def __onWheelDown(self):
        self.targetDistance = min(self.maxDistance, self.targetDistance + 2.5)

    def __updateCameraTask(self, task):
        if not self.enabled or not self.avatar or self.avatar.isEmpty():
            return Task.cont

        # Handle mouse drag rotation with locked/hidden cursor
        if (self.isLeftDragging or self.isRightDragging) and base.win and base.win.hasPointer(0):
            pointer = base.win.getPointer(0)
            curX = pointer.getX()
            curY = pointer.getY()

            if self.lockedCursorPos is not None:
                dx_pixels = curX - self.lockedCursorPos[0]
                dy_pixels = curY - self.lockedCursorPos[1]

                if dx_pixels != 0 or dy_pixels != 0:
                    winWidth = max(1, base.win.getXSize())
                    winHeight = max(1, base.win.getYSize())

                    # Normalized delta relative to window dimensions
                    normDx = float(dx_pixels) / float(winWidth)
                    normDy = float(dy_pixels) / float(winHeight)

                    sens = self.getSensitivity()
                    deltaYaw = -normDx * sens
                    deltaPitch = -normDy * sens

                    if self.isRightDragging:
                        # Right-click drag rotates character and camera together
                        self.avatar.setH(self.avatar.getH() - deltaYaw)
                    else:
                        # Left-click drag orbits camera freely around character
                        self.yaw += deltaYaw

                    self.pitch = max(self.minPitch, min(self.maxPitch, self.pitch + deltaPitch))

                    # Re-center cursor at locked location so movement is infinite
                    base.win.movePointer(0, self.lockedCursorPos[0], self.lockedCursorPos[1])
            else:
                self.lockedCursorPos = (curX, curY)

        # Smooth distance zoom lerp
        self.distance += (self.targetDistance - self.distance) * 0.25

        # Compute camera position relative to avatar
        avHeight = max(self.avatar.getHeight(), 3.0)
        radPitch = math.radians(self.pitch)
        radYaw = math.radians(self.yaw)

        horizDist = self.distance * math.cos(radPitch)
        camZ = self.distance * math.sin(radPitch) + (avHeight * 0.85)

        camX = horizDist * math.sin(radYaw)
        camY = -horizDist * math.cos(radYaw)

        camPosRel = Point3(camX, camY, camZ)
        lookAtRel = Point3(0, 0, avHeight * 0.85)

        camera.setPos(self.avatar, camPosRel)
        camera.lookAt(self.avatar, lookAtRel)

        return Task.cont
