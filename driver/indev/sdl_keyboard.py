from micropython import const
import lvgl as lv

import keypad_framework

KEY_UNKNOWN = 0
KEY_BACKSPACE = 8  #            LV_KEY_BACKSPACE
KEY_TAB = 9  #                  LV_KEY_NEXT
KEY_CLEAR = 12
KEY_RETURN = 13  #              LV_KEY_ENTER
KEY_PAUSE = 19  #
KEY_ESCAPE = 27  #              LV_KEY_ESC
KEY_SPACE = 32  # " "
KEY_EXCLAIM = 33  # !
KEY_QUOTEDBL = 34  # "
KEY_HASH = 35  # #
KEY_DOLLAR = 36 # $
KEY_AMPERSAND = 38 # &
KEY_QUOTE = 39 # '
KEY_LEFTPAREN = 40 # (
KEY_RIGHTPAREN = 41 # )
KEY_ASTERISK = 42 # *
KEY_PLUS = 43 # +
KEY_COMMA = 44 # ,
KEY_MINUS = 45 # -
KEY_PERIOD = 46 # .
KEY_SLASH = 47 # /

KEY_0 = 48  # 0
KEY_1 = 49  # 1
KEY_2 = 50  # 2
KEY_3 = 51  # 3
KEY_4 = 52  # 4
KEY_5 = 53  # 5
KEY_6 = 54  # 6
KEY_7 = 55  # 7
KEY_8 = 56  # 8
KEY_9 = 57  # 9

KEY_COLON = 58  # :
KEY_SEMICOLON = 59  # ;
KEY_LESS = 60  # <
KEY_EQUALS = 61  # =
KEY_GREATER = 62  # >
KEY_QUESTION = 63  # ?
KEY_AT = 64  # @
KEY_LEFTBRACKET = 91  # [
KEY_BACKSLASH = 92  # \
KEY_RIGHTBRACKET = 93  # ]
KEY_CARET = 94  # |
KEY_UNDERSCORE = 95  # _
KEY_BACKQUOTE = 96  # `
KEY_DELETE = 127  #             LV_KEY_DEL

# Numeric keypad
# if MOD_KEY_NUM then it's numbers.

KEYPAD_0 = 256  # 0/INS
KEYPAD_1 = 257  # 1/END         LV_KEY_END
KEYPAD_2 = 258  # 2/DOWN        LV_KEY_DOWN
KEYPAD_3 = 259  # 3/PAGEDOWN
KEYPAD_4 = 260  # 4/LEFT        LV_KEY_LEFT
KEYPAD_5 = 261  # 5
KEYPAD_6 = 262  # 6/RIGHT       LV_KEY_RIGHT
KEYPAD_7 = 263  # 7/HOME        LV_KEY_HOME
KEYPAD_8 = 264  # 8/UP          LV_KEY_UP
KEYPAD_9 = 265  # 9/PAGEUP
KEYPAD_PERIOD = 266  # ./DEL    LV_KEY_DEL
KEYPAD_DIVIDE = 267  # /
KEYPAD_MULTIPLY = 268   # *
KEYPAD_MINUS = 269  # -
KEYPAD_PLUS = 270  # +
KEYPAD_ENTER = 271  #           LV_KEY_ENTER
KEYPAD_EQUALS = 272  # =

# Arrows + Home/End pad

KEY_UP = 273  #                 LV_KEY_UP
KEY_DOWN = 274  #               LV_KEY_DOWN
KEY_RIGHT = 275  #              LV_KEY_RIGHT
KEY_LEFT = 276  #               LV_KEY_LEFT
KEY_INSERT = 277
KEY_HOME = 278  #               LV_KEY_HOME
KEY_END = 279  #                LV_KEY_END
KEY_PAGEUP = 280
KEY_PAGEDOWN = 281

KEY_F1 = 282 
KEY_F2 = 283 
KEY_F3 = 284 
KEY_F4 = 285 
KEY_F5 = 286 
KEY_F6 = 287 
KEY_F7 = 288 
KEY_F8 = 289 
KEY_F9 = 290 
KEY_F10 = 291
KEY_F11 = 292
KEY_F12 = 293
KEY_F13 = 294
KEY_F14 = 295
KEY_F15 = 296

KEY_NUMLOCK = 300
KEY_CAPSLOCK = 301
KEY_SCROLLOCK = 302
KEY_RSHIFT = 303
KEY_LSHIFT = 304
KEY_RCTRL = 305
KEY_LCTRL = 306
KEY_RALT = 307
KEY_LALT = 308
KEY_RMETA = 309
KEY_LMETA = 310

# Left "Windows" key
KEY_LSUPER = 311

# Right "Windows" key
KEY_RSUPER = 312

# Alt Gr" key 
KEY_MODE = 313
# Multi-key compose key
KEY_COMPOSE = 314

KEY_HELP = 315 
KEY_PRINT = 316 
KEY_SYSREQ = 317 
KEY_BREAK = 318 
KEY_MENU = 319 
# Power Macintosh power key
KEY_POWER  = 320
# Some european keyboards
KEY_EURO = 321
#  Atari keyboard has Undo
KEY_UNDO = 322

MOD_KEY_NONE = 0x0000
MOD_KEY_LSHIFT = 0x0001
MOD_KEY_RSHIFT = 0x0002
MOD_KEY_LCTRL = 0x0040
MOD_KEY_RCTRL = 0x0080
MOD_KEY_LALT = 0x0100
MOD_KEY_RALT = 0x0200
MOD_KEY_LMETA = 0x0400
MOD_KEY_RMETA = 0x0800
MOD_KEY_NUM = 0x1000
MOD_KEY_CAPS = 0x2000
MOD_KEY_MODE = 0x4000
MOD_KEY_CTRL = MOD_KEY_LCTRL | MOD_KEY_RCTRL
MOD_KEY_SHIFT = MOD_KEY_LSHIFT | MOD_KEY_RSHIFT
MOD_KEY_ALT = MOD_KEY_LALT | MOD_KEY_RALT
MOD_KEY_META = MOD_KEY_LMETA | MOD_KEY_RMETA


class KEYeyboard(keypad_framework.KeypadDriver):

    def __init__(self):
        super().__init__()
        self._disp_drv._data_bus.register_keypad_callback(self._keypad_cb)
        self.__last_key = -1
        self.__current_state = lv.INDEV_STATE.RELEASED

        self.group = lv.group_create()
        self.group.set_default()
        self.set_group(self.group)

    def _get_key(self):
        return self.__current_state, self.__last_key

    def _keypad_cb(self, kwargs):
        key = kwargs['key']
        mod = kwargs['mod']

        if KEYPAD_0 <= key <= KEYPAD_EQUALS:
            if mod == MOD_KEY_NUM:
                mapping = {
                    KEYPAD_0: KEY_0,
                    KEYPAD_1: KEY_1,
                    KEYPAD_2: KEY_2,
                    KEYPAD_3: KEY_3,
                    KEYPAD_4: KEY_4,
                    KEYPAD_5: KEY_5,
                    KEYPAD_6: KEY_6,
                    KEYPAD_7: KEY_7,
                    KEYPAD_8: KEY_8,
                    KEYPAD_9: KEY_9,
                    KEYPAD_PERIOD: KEY_PERIOD,
                    KEYPAD_DIVIDE: KEY_SLASH,
                    KEYPAD_MULTIPLY: KEY_ASTERISK,
                    KEYPAD_MINUS: KEY_MINUS,
                    KEYPAD_PLUS: KEY_PLUS,
                    KEYPAD_ENTER: KEY_EQUALS,
                    KEYPAD_EQUALS: KEY_EQUALS
                }
            else:
                mapping = {
                    KEYPAD_0: KEY_INSERT,
                    KEYPAD_1: lv.KEY.END,
                    KEYPAD_2: lv.KEY.DOWN,
                    KEYPAD_3: lv.KEY.PREV,
                    KEYPAD_4: lv.KEY.LEFT,
                    KEYPAD_5: KEY_5,
                    KEYPAD_6: lv.KEY.RIGHT,
                    KEYPAD_7: lv.KEY.HOME,
                    KEYPAD_8: lv.KEY.UP,
                    KEYPAD_9: lv.KEY.NEXT,
                    KEYPAD_PERIOD: lv.KEY.DEL,
                    KEYPAD_DIVIDE: KEY_SLASH,
                    KEYPAD_MULTIPLY: KEY_ASTERISK,
                    KEYPAD_MINUS: KEY_MINUS,
                    KEYPAD_PLUS: KEY_PLUS,
                    KEYPAD_ENTER: lv.KEY.ENTER,
                    KEYPAD_EQUALS: KEY_EQUALS
                }

            self.__last_key = mapping[key]
        elif key == KEY_PAUSE:
            return
        else:
            mapping = {
                KEY_BACKSPACE: lv.KEY.BACKSPACE,
                KEY_TAB: lv.KEY.NEXT,
                KEY_RETURN: lv.KEY.ENTER,
                KEY_ESCAPE: lv.KEY.ESC,
                KEY_DELETE: lv.KEY.DEL,
                KEY_UP: lv.KEY.UP,
                KEY_DOWN: lv.KEY.DOWN,
                KEY_RIGHT: lv.KEY.RIGHT,
                KEY_LEFT: lv.KEY.LEFT,
                KEY_HOME: lv.KEY.HOME,
                KEY_END: lv.KEY.END,
                KEY_PAGEDOWN: lv.KEY.PREV,
                KEY_PAGEUP: lv.KEY.NEXT
            }
            self.__last_key = mapping.get(key, key)

        if kwargs['state']:
            self.__current_state = lv.INDEV_STATE.PRESSED
        else:
            self.__current_state = lv.INDEV_STATE.RELEASED
