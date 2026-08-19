from direct.directnotify import DirectNotifyGlobal
from direct.showbase.InputStateGlobal import inputState

# Action IDs -> Default Key mapping
DEFAULT_KEYBINDS = {
    'forward': 'arrow_up',
    'reverse': 'arrow_down',
    'turnLeft': 'arrow_left',
    'turnRight': 'arrow_right',
    'jump': 'control',
    'sprint': 'shift',
    'book': 'f8',
    'chat': '/',
}

KEY_DISPLAY_NAMES = {
    'arrow_up': 'Up Arrow',
    'arrow_down': 'Down Arrow',
    'arrow_left': 'Left Arrow',
    'arrow_right': 'Right Arrow',
    'control': 'Ctrl',
    'lcontrol': 'Left Ctrl',
    'rcontrol': 'Right Ctrl',
    'shift': 'Shift',
    'lshift': 'Left Shift',
    'rshift': 'Right Shift',
    'space': 'Space',
    'enter': 'Enter',
    'escape': 'Escape',
    '/': '/',
    'f1': 'F1',
    'f2': 'F2',
    'f3': 'F3',
    'f4': 'F4',
    'f5': 'F5',
    'f6': 'F6',
    'f7': 'F7',
    'f8': 'F8',
    'f9': 'F9',
    'f10': 'F10',
    'f11': 'F11',
    'f12': 'F12',
    'tab': 'Tab',
    'home': 'Home',
    'end': 'End',
    'page_up': 'Page Up',
    'page_down': 'Page Down',
    'delete': 'Delete',
    'insert': 'Insert',
}

_active_custom_tokens = []


def getKeyName(key):
    key = str(key).lower()
    if key in KEY_DISPLAY_NAMES:
        return KEY_DISPLAY_NAMES[key]
    return key.upper()


def getKey(action):
    base_obj = __builtins__.get('base') if isinstance(__builtins__, dict) else getattr(__builtins__, 'base', None)
    if base_obj and hasattr(base_obj, 'settings') and base_obj.settings:
        val = base_obj.settings.getOption('controls', action, DEFAULT_KEYBINDS.get(action, ''))
        if val:
            return str(val).lower()
    return DEFAULT_KEYBINDS.get(action, '')


def setKey(action, key):
    key = str(key).lower()
    base_obj = __builtins__.get('base') if isinstance(__builtins__, dict) else getattr(__builtins__, 'base', None)
    if base_obj and hasattr(base_obj, 'settings') and base_obj.settings:
        base_obj.settings.updateSetting('controls', action, key)
    applyKeybinds()
    if 'messenger' in __builtins__ if isinstance(__builtins__, dict) else hasattr(__builtins__, 'messenger'):
        messenger.send('keybinds-changed')


def applyKeybinds():
    global _active_custom_tokens
    for token in _active_custom_tokens:
        token.release()
    _active_custom_tokens = []

    fwd = getKey('forward')
    rev = getKey('reverse')
    left = getKey('turnLeft')
    right = getKey('turnRight')
    jmp = getKey('jump')

    # Register customized movement bindings on inputState
    if fwd:
        _active_custom_tokens.append(inputState.watchWithModifiers('forward', fwd, inputSource=inputState.ArrowKeys))
    if rev:
        _active_custom_tokens.append(inputState.watchWithModifiers('reverse', rev, inputSource=inputState.ArrowKeys))
    if left:
        _active_custom_tokens.append(inputState.watchWithModifiers('turnLeft', left, inputSource=inputState.ArrowKeys))
    if right:
        _active_custom_tokens.append(inputState.watchWithModifiers('turnRight', right, inputSource=inputState.ArrowKeys))
    if jmp:
        if jmp in ('control', 'lcontrol', 'rcontrol'):
            _active_custom_tokens.append(inputState.watch('jump', 'control', 'control-up'))
        else:
            _active_custom_tokens.append(inputState.watchWithModifiers('jump', jmp))
