"""Six-lamp LVGL panel using the new pool-based ``twai`` API.

Copy this file to the device and run it after flashing the firmware that
contains ``ext_mod/twai``.  It retains the CAN message layout used by the old
application:

* TX ID 0x001, payload ``[value, register]``
* RX ID 0x101, first payload byte is the six-lamp state bitmap

It is safe to execute this file again in the same REPL: the previous node is
drained and deinitialised first.  Before an actual MicroPython soft reboot
(Ctrl-D), run ``shutdown_can()``.  The current node API has no automatic
soft-reboot cleanup hook.
"""

import gc
gc.collect()

import time
import twai
from micropython import const
import lvgl as lv
import lcd_bus
import rgb_display
import task_handler


# ---------------------------------------------------------
# 1. TWAI setup (new node/Frame API)
# ---------------------------------------------------------

PHYSICAL_ADDR = const(0x01)
CAN_STATE_ID = const(0x0101)
CAN_TX_PIN = const(15)
CAN_RX_PIN = const(16)
CAN_BITRATE = const(50000)

# RX frames stay owned by the application until release() is called.  Eight
# entries absorb short bursts while LVGL's 50-ms timer is between callbacks.
CAN_RX_POOL_SIZE = const(8)
CAN_TX_POOL_SIZE = const(4)


def _deinit_idle_can_node(node, rx_pool, tx_pool):
    # Ready RX frames are still inside the node queue.  Release every one so
    # Node.deinit() can perform its strict idle check.
    while True:
        old_frame = node.recv()
        if old_frame is None:
            break
        old_frame.release()

    for _ in range(25):
        busy = False
        for old_frame in rx_pool + tx_pool:
            if old_frame.in_use:
                busy = True
                break
        if not busy:
            break
        time.sleep_ms(10)

    if busy:
        raise RuntimeError("TWAI Frame is still in use; release it and retry")
    node.deinit()


def _stop_previous_can_node():
    """Allow re-running this script in one REPL without leaking the node."""
    old_node = globals().get("can_node")
    if old_node is not None:
        _deinit_idle_can_node(
            old_node,
            globals().get("can_rx_pool", ()),
            globals().get("can_tx_pool", ()),
        )


_stop_previous_can_node()

# The Frame objects are allocated once.  Node keeps strong references to both
# pools; the TX picker below uses only a Frame whose driver ownership ended.
can_rx_pool = tuple([twai.Frame() for _ in range(CAN_RX_POOL_SIZE)])
can_tx_pool = tuple([twai.Frame() for _ in range(CAN_TX_POOL_SIZE)])
can_node = twai.Node(
    CAN_TX_PIN,
    CAN_RX_PIN,
    CAN_BITRATE,
    rx_pool=can_rx_pool,
    tx_pool=can_tx_pool,
)
can_node.start()
print("TWAI Ready.")


def shutdown_can():
    """Drain/release RX Frames and deinitialise TWAI before Ctrl-D."""
    global can_node
    _deinit_idle_can_node(can_node, can_rx_pool, can_tx_pool)
    # A deinitialised Node no longer owns valid FreeRTOS queues.  Do not let a
    # later script re-run try to drain that object again.
    can_node = None


def _idle_tx_frame():
    for frame in can_tx_pool:
        if not frame.in_use:
            return frame
    return None


def send_reg_write(addr, reg_addr, value):
    """Submit a non-blocking write with the original wire format."""
    frame = _idle_tx_frame()
    if frame is None:
        print("TWAI send skipped: all TX Frames are busy")
        return False

    try:
        frame.flags = 0
        frame.id = addr
        frame.dlc = 2
        frame.data[0] = value
        frame.data[1] = reg_addr
        can_node.send(frame)
        return True
    except OSError as exc:
        # EAGAIN means the non-blocking software TX queue is full.
        print("TWAI send failed:", exc)
    except (RuntimeError, ValueError) as exc:
        print("TWAI frame setup failed:", exc)
    return False


# ---------------------------------------------------------
# 2. LCD hardware configuration
# ---------------------------------------------------------

WIDTH = const(1024)
HEIGHT = const(600)

try:
    if lv.is_initialized():
        lv.deinit()
        time.sleep_ms(50)
except Exception as exc:
    print("LVGL deinit warning:", exc)

lv.init()

bus = lcd_bus.RGBBus(
    hsync=46, vsync=3, de=5, pclk=7,
    data0=14, data1=38, data2=18, data3=17, data4=10,
    data5=39, data6=0, data7=45, data8=48, data9=47, data10=21,
    data11=1, data12=2, data13=42, data14=41, data15=40,
    freq=12000000,
    hsync_front_porch=40, hsync_back_porch=140, hsync_pulse_width=20,
    vsync_front_porch=12, vsync_back_porch=20, vsync_pulse_width=3,
    hsync_idle_low=False, vsync_idle_low=False, de_idle_high=False,
    pclk_idle_high=False, pclk_active_low=False,
)

BUFFER_SIZE = 1024 * 60 * 2
buf1 = bus.allocate_framebuffer(BUFFER_SIZE, lcd_bus.MEMORY_SPIRAM)

disp = rgb_display.RGBDisplay(
    data_bus=bus, display_width=WIDTH, display_height=HEIGHT,
    frame_buffer1=buf1, frame_buffer2=None,
    color_space=lv.COLOR_FORMAT.RGB565, rgb565_byte_swap=False,
)
disp.init()
try:
    disp.set_power(True)
    disp.set_backlight(6)
except Exception:
    pass


# ---------------------------------------------------------
# 2.5. Release TP_RST via CH422G before starting the touch IC
# ---------------------------------------------------------

try:
    from machine import I2C as _MachineI2C, Pin as _Pin

    _ch422g_i2c = _MachineI2C(0, sda=_Pin(8), scl=_Pin(9), freq=100000)
    _ch422g_i2c.writeto(0x24, bytes([0x01]))
    _ch422g_i2c.writeto(0x38, bytes([0xFF]))
    time.sleep_ms(100)
    try:
        _ch422g_i2c.deinit()
    except Exception:
        pass
    del _ch422g_i2c
    print("CH422G touch reset released.")
except Exception as exc:
    print("CH422G reset warning:", exc)


# ---------------------------------------------------------
# 3. GT911 touch, SDA=8/SCL=9
# ---------------------------------------------------------

touch_indev = None
try:
    from i2c import I2C
    import gt911

    I2C_BUS = I2C.Bus(
        host=1,
        scl=const(9),
        sda=const(8),
        freq=400000,
        use_locks=False,
    )
    TOUCH_DEVICE = I2C.Device(I2C_BUS, dev_id=gt911.I2C_ADDR, reg_bits=gt911.BITS)
    touch_indev = gt911.GT911(TOUCH_DEVICE)
    print("Touch (GT911) initialized OK.")
except Exception as exc:
    print("Touch init failed:", exc)


# ---------------------------------------------------------
# 4. GUI
# ---------------------------------------------------------

scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x050814), 0)

lamps = []
labels = []
lamp_states = [False] * 6
positions = [
    (150, 150), (512, 150), (874, 150),
    (150, 450), (512, 450), (874, 450),
]

for i in range(6):
    x, y = positions[i]
    obj = lv.obj(scr)
    obj.set_size(180, 180)
    obj.set_pos(x - 90, y - 90)
    obj.set_style_radius(9999, 0)
    obj.set_style_bg_color(lv.color_hex(0x333333), 0)
    obj.add_flag(lv.obj.FLAG.CLICKABLE)
    obj.set_style_bg_color(lv.color_hex(0x555555), lv.PART.MAIN | lv.STATE.PRESSED)

    lbl = lv.label(obj)
    lbl.set_text("LAMP {}\nOFF".format(i + 1))
    lbl.center()
    lamps.append(obj)
    labels.append(lbl)


def update_gui_from_state(state_byte):
    for i in range(6):
        is_on = bool((state_byte >> i) & 1)
        if lamp_states[i] != is_on:
            lamp_states[i] = is_on
            if is_on:
                lamps[i].set_style_bg_color(lv.color_hex(0x00FF66), 0)
                labels[i].set_text("LAMP {}\nON".format(i + 1))
            else:
                lamps[i].set_style_bg_color(lv.color_hex(0x333333), 0)
                labels[i].set_text("LAMP {}\nOFF".format(i + 1))


# ---------------------------------------------------------
# 5. Drain all queued CAN frames from LVGL's timer context
# ---------------------------------------------------------

def check_can_bus_cb(_timer):
    try:
        while True:
            frame = can_node.recv()
            if frame is None:
                break
            try:
                if (frame.id == CAN_STATE_ID
                        and not (frame.flags & twai.RTR)
                        and frame.dlc >= 1):
                    update_gui_from_state(frame.data[0])
            finally:
                # RX pool capacity is restored only by release().
                frame.release()
    except Exception as exc:
        print("TWAI receive warning:", exc)


lv.timer_create(check_can_bus_cb, 50, None)


# ---------------------------------------------------------
# 6. REPL and touch controls
# ---------------------------------------------------------

current_local_state = 0x00


def lamp_on(lamp_id):
    global current_local_state
    if 1 <= lamp_id <= 6:
        lamp_mask = 1 << (lamp_id - 1)
        send_reg_write(PHYSICAL_ADDR, 0x01, lamp_mask)
        current_local_state |= lamp_mask
        update_gui_from_state(current_local_state)


def lamp_off(lamp_id):
    global current_local_state
    if 1 <= lamp_id <= 6:
        lamp_mask = 1 << (lamp_id - 1)
        send_reg_write(PHYSICAL_ADDR, 0x02, lamp_mask)
        current_local_state &= ~lamp_mask
        update_gui_from_state(current_local_state)


def on_lamp_touched(event):
    obj = event.get_target_obj()
    try:
        lamp_id = lamps.index(obj) + 1
    except ValueError:
        return
    if lamp_states[lamp_id - 1]:
        lamp_off(lamp_id)
    else:
        lamp_on(lamp_id)


for lamp_obj in lamps:
    lamp_obj.add_event_cb(on_lamp_touched, lv.EVENT.CLICKED, None)


print("System Ready! You can type lamp_on(1) or tap the screen.")
th = task_handler.TaskHandler()
