"""
LawbotOfficeRoomSpecs.py

Room spec registry for the Lawbot DA Office, used by the Cog Building mini-dungeon system.
Mirrors the structure of MintRoomSpecs.py / CountryClubRoomSpecs.py.
"""
from direct.showbase.PythonUtil import invertDict
from toontown.coghq import NullCogs

# Individual room spec modules
from toontown.coghq import LawbotOfficeBoilerRoom_Action01
from toontown.coghq import LawbotOfficeBoilerRoom_Battle00
from toontown.coghq import LawbotOfficeBoilerRoom_Battle00_Cogs
from toontown.coghq import LawbotOfficeDiamondRoom_Action00
from toontown.coghq import LawbotOfficeDiamondRoom_Action01
from toontown.coghq import LawbotOfficeDiamondRoom_Battle00
from toontown.coghq import LawbotOfficeDiamondRoom_Battle00_Cogs
from toontown.coghq import LawbotOfficeGearRoom_Action00
from toontown.coghq import LawbotOfficeGearRoom_Battle00
from toontown.coghq import LawbotOfficeGearRoom_Battle00_Cogs
from toontown.coghq import LawbotOfficeLobby_Action00
from toontown.coghq import LawbotOfficeLobby_Action01
from toontown.coghq import LawbotOfficeLobby_Trap00
from toontown.coghq import LawbotOfficeLobby_Trap00_Cogs
from toontown.coghq import LawbotOfficeOilRoom_Battle00
from toontown.coghq import LawbotOfficeOilRoom_Battle00_Cogs
from toontown.coghq import LawbotOfficeOilRoom_Battle01
from toontown.coghq import LawbotOfficeOilRoom_Battle01_Cogs

# Room ID → room spec name
LawbotOfficeRoomId2RoomName = {
    0:  'LawbotOfficeLobby_Action00',
    1:  'LawbotOfficeLobby_Action01',
    2:  'LawbotOfficeLobby_Trap00',
    3:  'LawbotOfficeGearRoom_Action00',
    4:  'LawbotOfficeGearRoom_Battle00',
    5:  'LawbotOfficeBoilerRoom_Action01',
    6:  'LawbotOfficeBoilerRoom_Battle00',
    7:  'LawbotOfficeDiamondRoom_Action00',
    8:  'LawbotOfficeDiamondRoom_Action01',
    9:  'LawbotOfficeDiamondRoom_Battle00',
    10: 'LawbotOfficeOilRoom_Battle00',
    11: 'LawbotOfficeOilRoom_Battle01',
}
LawbotOfficeRoomName2RoomId = invertDict(LawbotOfficeRoomId2RoomName)

# Entrance, traversal (puzzle/action), and battle room ID groups
LawbotOfficeEntranceIDs  = (0,)
LawbotOfficeActionIDs    = (1, 2, 3, 5, 7, 8)   # goon-patrol / trap / action rooms
LawbotOfficeBattleIDs    = (4, 6, 9, 10, 11)     # rooms with Cog battles
LawbotOfficeMiddleRoomIDs = LawbotOfficeActionIDs + LawbotOfficeBattleIDs

# Spec module map keyed by room ID
LawbotOfficeSpecModules = {
    0:  LawbotOfficeLobby_Action00,
    1:  LawbotOfficeLobby_Action01,
    2:  LawbotOfficeLobby_Trap00,
    3:  LawbotOfficeGearRoom_Action00,
    4:  LawbotOfficeGearRoom_Battle00,
    5:  LawbotOfficeBoilerRoom_Action01,
    6:  LawbotOfficeBoilerRoom_Battle00,
    7:  LawbotOfficeDiamondRoom_Action00,
    8:  LawbotOfficeDiamondRoom_Action01,
    9:  LawbotOfficeDiamondRoom_Battle00,
    10: LawbotOfficeOilRoom_Battle00,
    11: LawbotOfficeOilRoom_Battle01,
}

# Cog spec module map keyed by room name
CogSpecModules = {
    'LawbotOfficeBoilerRoom_Battle00':   LawbotOfficeBoilerRoom_Battle00_Cogs,
    'LawbotOfficeDiamondRoom_Battle00':  LawbotOfficeDiamondRoom_Battle00_Cogs,
    'LawbotOfficeGearRoom_Battle00':     LawbotOfficeGearRoom_Battle00_Cogs,
    'LawbotOfficeLobby_Trap00':          LawbotOfficeLobby_Trap00_Cogs,
    'LawbotOfficeOilRoom_Battle00':      LawbotOfficeOilRoom_Battle00_Cogs,
    'LawbotOfficeOilRoom_Battle01':      LawbotOfficeOilRoom_Battle01_Cogs,
}


def getLawbotOfficeRoomSpecModule(roomId):
    return LawbotOfficeSpecModules[roomId]


def getCogSpecModule(roomId):
    roomName = LawbotOfficeRoomId2RoomName[roomId]
    return CogSpecModules.get(roomName, NullCogs)


def hasBattle(roomId):
    roomName = LawbotOfficeRoomId2RoomName.get(roomId, '')
    return roomName in CogSpecModules
