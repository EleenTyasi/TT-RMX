from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject
from panda3d.core import *

# Street sign download is disabled for local server use.
# The remote URL (ttoffline.com) is irrelevant here and was crashing the game
# by saving 404 HTML pages as texture.jpg, which Panda3D can't load.

class StreetSign(DistributedObject.DistributedObject):
    RedownloadTaskName = 'RedownloadStreetSign'
    StreetSignFileName = config.GetString('street-sign-filename', 'texture.jpg')
    StreetSignBaseDir = config.GetString('street-sign-base-dir', 'sign')
    StreetSignUrl = ''
    notify = DirectNotifyGlobal.directNotify.newCategory('StreetSign')

    def __init__(self):
        self.downloadingStreetSign = False
        self.percentDownloaded = 0.0

    def replaceTexture(self):
        pass

    def redownloadStreetSign(self):
        pass

    def downloadStreetSignTask(self, task):
        return task.done
