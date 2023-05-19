import board
from kmk.hid import HIDModes

from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC
from kmk.modules.mouse_keys import MouseKeys
from kmk.modules.split import Split, SplitType, SplitSide
from kmk.modules.layers import Layers
from storage import getmount
from kmk.utils import Debug
import traceback
from kmk.modules.combos import Combos, Chord, Sequence
from kmk.extensions.media_keys import MediaKeys

# identify which side the keyboard is on
side = SplitSide.RIGHT if str(getmount('/').label)[-1] == 'R' else SplitSide.LEFT

keyboard = KMKKeyboard()
keyboard.debug_enabled = True

# keyboard.diode_orientation = DiodeOrientation.COL2ROW
# \keyboard.col_pins = (board.GP6, board.GP5, board.GP4, board.GP3, board.GP2)
# keyboard.row_pins = (board.GP13, board.GP12, board.GP11, board.GP10, board.GP9)

keyboard.SCL=board.GP17
keyboard.SDA=board.GP16

keyboard.coord_mapping = [
     24, 23, 22, 21, 20,                   49, 48, 47, 46, 45,
     19, 18, 17, 16, 15,                   44, 43, 42, 41, 40,
     14, 13, 12, 11, 10,                   39, 38, 37, 36, 35,
                7, 6, 5,                   32, 33, 34,
]

pmw3360 = PMW3360(cs=board.GP21, miso=board.GP20, mosi=board.GP19, sclk=board.GP18, invert_x=True, invert_y=True, flip_xy=True)
keyboard.modules.append(pmw3360)

layers = Layers()
keyboard.modules.append(layers)

keyboard.extensions.append(MediaKeys())
# identify data pin values based on side
if side == SplitSide.RIGHT:
  split = Split(split_type=SplitType.UART, split_side=side, split_target_left=False, data_pin=board.GP1, data_pin2=board.GP0, use_pio=True, uart_flip = True)
elif side == SplitSide.LEFT:
  split = Split(split_type=SplitType.UART, split_side=side, split_target_left=False, data_pin=board.GP0, data_pin2=board.GP1, use_pio=True, uart_flip = True)
keyboard.modules.append(split)

# different OLED display on each side
if side == SplitSide.LEFT:
  oled_ext = Oled(
    OledData(
        corner_one={0:OledReactionType.STATIC,1:["layer"]},
        corner_two={0:OledReactionType.LAYER,1:["0","1","2"]},
        corner_three={0:OledReactionType.LAYER,1:["base","raise","lower"]},
        corner_four={0:OledReactionType.LAYER,1:["qwerty","nums","symbols"]}
        ),
        toDisplay=OledDisplayMode.TXT,flip=False)
elif side == SplitSide.RIGHT:
  oled_ext = Oled(
    OledData(
        image={0:OledReactionType.LAYER,1:["narwhal.bmp","penguin.bmp"]}
        ),
        toDisplay=OledDisplayMode.IMG,flip=False)
keyboard.extensions.append(oled_ext)

keyboard.modules.append(MouseKeys())
# auto mouse layer
class MouseLayer():
  def __init__(self, keyboard, keys):
    self.timeout = None
    self.keyboard = keyboard
    for key in keys:
      key.after_press_handler(self.on_mouse_key)
    self.pmw3360 = next(x for x in keyboard.modules if type(x) is PMW3360)
    if self.pmw3360 is not None:
      self.pmw3360.on_move = self.on_mouse_move
  def on_mouse_key(self, key, keyboard, *args):
    self.on_mouse_move(keyboard)
    return key
  def on_mouse_move(self, keyboard):
    if self.timeout is None:
      self.keyboard.keymap[0][16] = KC.MB_LMB
      self.keyboard.keymap[0][18] = KC.MB_RMB
    if self.timeout is not None:
      self.keyboard.cancel_timeout(self.timeout)
    self.timeout = self.keyboard.set_timeout(300, self.release)
  def release(self):
      self.keyboard.keymap[0][16] = KC.J
      self.keyboard.keymap[0][18] = KC.L
      self.timeout = None
  
if side == SplitSide.RIGHT:
  ml = MouseLayer(keyboard, [KC.MB_LMB, KC.MB_RMB])

# vertical drag scroll
def ball_scroll_enable(key, keyboard, *args):
    pmw3360.start_v_scroll()
    return True

def ball_scroll_disable(key, keyboard, *args):
    pmw3360.start_v_scroll(False)
    return True

l1 = KC.MO(1)

l1.before_press_handler(ball_scroll_enable)
l1.before_release_handler(ball_scroll_disable)

combos = Combos()
keyboard.modules.append(combos)

combos.combos = [
    Chord((KC.S, KC.D), KC.TAB),
    Chord((KC.J, KC.K), KC.ENT),
]

keyboard.keymap = [[
  KC.Q, KC.W, KC.E,    KC.R, KC.T,        KC.Y,    KC.U,     KC.I,    KC.O,   KC.P,
  KC.A, KC.S, KC.D,    KC.F, KC.G,        KC.H,    KC.J,     KC.K,    KC.L,   KC.QUOT,
  KC.Z, KC.X, KC.C,    KC.V, KC.B,        KC.N,    KC.M,     KC.COMM, KC.DOT, KC.SLSH,
              KC.LCTL, l1,   KC.SPACE,    KC.BSPC, KC.MO(2), KC.RSFT, 
],
[
  KC.NO,   KC.NO, KC.ESC,  KC.NO,   KC.NO,      KC.N6,   KC.N7,     KC.N8,    KC.N9,     KC.N0,
  KC.CAPS, KC.NO, KC.RPRN, KC.LPRN, KC.NO,      KC.VOLU, KC.MB_LMB, KC.MS_UP, KC.MB_RMB, KC.MINS,
  KC.NO,   KC.NO, KC.RBRC, KC.LBRC, KC.NO,      KC.VOLD, KC.MS_LT,  KC.MS_DN, KC.MS_RT,  KC.EQL,
                  KC.LSFT, KC.NO,   KC.NO,      KC.MUTE, KC.RSFT,   KC.RWIN, 
],
[
  KC.N1, KC.N2,   KC.N3,   KC.N4, 	KC.N5,      KC.NO, KC.NO,   KC.NO,   KC.NO,   KC.NO,
  KC.NO, KC.SCLN, KC.NO,   KC.NO,   KC.NO,      KC.NO, KC.HOME, KC.UP,   KC.END,  KC.NO,
  KC.NO, KC.NO,   KC.COLN, KC.NO,   KC.BSLS,    KC.NO, KC.LEFT, KC.DOWN, KC.RGHT, KC.NO,
                  KC.NO,   KC.LSFT, KC.NO,      KC.NO, KC.NO,   KC.NO, 
]
]

if __name__ == '__main__':
  print('starting kmk...')
  keyboard.go(hid_type=HIDModes.BLE)
  print('returned from kmk...')
