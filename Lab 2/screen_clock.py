# vague_clock_rot90.py
# Mini PiTFT ST7789 (240x135, x/y offsets as below), rotated 90° to landscape.
# A => Mode 1 (color fill by day part)
# B => Mode 2 (word clock between events)
# A+B => toggles backlight

import time
import digitalio
import board
from datetime import datetime, timedelta

from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
from adafruit_rgb_display.rgb import color565

# ---------------------------
# SPI + Display configuration
# ---------------------------
cs_pin = digitalio.DigitalInOut(board.D5)   # GPIO5  (PIN 29)
dc_pin = digitalio.DigitalInOut(board.D25)  # GPIO25 (PIN 22)
reset_pin = None
BAUDRATE = 64_000_000
spi = board.SPI()

# Create ST7789 display (no rotation arg here; we rotate when pushing the image)
disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

# ---------------------------
# Logical canvas size (landscape)
# ---------------------------
# Follow the reference pattern: swap width/height & set rotation=90 for display.image().
rotation = 90
LOGICAL_WIDTH  = disp.height  # 240
LOGICAL_HEIGHT = disp.width   # 135

# Pillow drawing surface
image = Image.new("RGB", (LOGICAL_WIDTH, LOGICAL_HEIGHT))
draw = ImageDraw.Draw(image)

# ---------------------------
# Backlight + Buttons
# ---------------------------
backlight = digitalio.DigitalInOut(board.D22)  # GPIO22
backlight.switch_to_output(value=True)

buttonA = digitalio.DigitalInOut(board.D23)    # GPIO23
buttonB = digitalio.DigitalInOut(board.D24)    # GPIO24
buttonA.switch_to_input(pull=digitalio.Pull.UP)  # active LOW
buttonB.switch_to_input(pull=digitalio.Pull.UP)

# ---------------------------
# Fonts
# ---------------------------
def load_fonts():
    try:
        font_big   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
        font_med   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except Exception:
        font_big = font_med = font_small = ImageFont.load_default()
    return font_big, font_med, font_small

FONT_BIG, FONT_MED, FONT_SMALL = load_fonts()

# ---------------------------
# Configurable event times (24h)
# ---------------------------
EVENT_DEFAULTS = {
    "get_up":   (9, 0),    # 09:00
    "lunch":    (13, 0),   # 13:00
    "end_day":  (18, 0),   # 18:00
    "dinner":   (19, 30),  # 19:30
    "bed":      (0, 0),    # 00:00 (midnight)
}

def build_today_schedule(now=None):
    if now is None:
        now = datetime.now()
    today = now.date()
    def dt(h, m, day_offset=0):
        return datetime(today.year, today.month, today.day, h, m) + timedelta(days=day_offset)

    get_up  = dt(*EVENT_DEFAULTS["get_up"])
    lunch   = dt(*EVENT_DEFAULTS["lunch"])
    end_day = dt(*EVENT_DEFAULTS["end_day"])
    dinner  = dt(*EVENT_DEFAULTS["dinner"])
    bed0    = dt(*EVENT_DEFAULTS["bed"])
    bed1    = dt(*EVENT_DEFAULTS["bed"], 1)

    schedule = [
        ("Go to bed", bed0),
        ("Get up", get_up),
        ("Lunch", lunch),
        ("End of work", end_day),
        ("Dinner", dinner),
        ("Go to bed", bed1),
    ]
    schedule.sort(key=lambda x: x[1])
    return schedule

def find_prev_next(schedule, now=None):
    if now is None:
        now = datetime.now()
    prev_evt = schedule[0]
    next_evt = schedule[-1]
    for i in range(len(schedule) - 1):
        a_name, a_time = schedule[i]
        b_name, b_time = schedule[i+1]
        if a_time <= now < b_time:
            prev_evt = (a_name, a_time)
            next_evt = (b_name, b_time)
            break
        if now >= schedule[-2][1]:
            prev_evt = schedule[-2]
            next_evt = schedule[-1]
    return prev_evt, next_evt

def fmt_duration(td):
    total_seconds = int(td.total_seconds())
    if total_seconds < 0:
        total_seconds = 0
    h, rem = divmod(total_seconds, 3600)
    m, _ = divmod(rem, 60)
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"

def daypart_color(now=None):
    if now is None:
        now = datetime.now()
    hr = now.hour
    if 6 <= hr < 12:
        return (255, 236, 179)  # light yellow / soft orange
    elif 12 <= hr < 18:
        return (135, 206, 235)  # bright/sky blue
    else:
        return (75, 0, 130)     # deep purple

def draw_centered(draw, text, font, xy_center, fill=(255,255,255)):
    # textbbox returns (x0,y0,x1,y1)
    x1, y1 = draw.textbbox((0,0), text, font=font)[2:]
    draw.text((xy_center[0] - x1/2, xy_center[1] - y1/2), text, font=font, fill=fill)

def clear(color=(0,0,0)):
    draw.rectangle((0, 0, LOGICAL_WIDTH, LOGICAL_HEIGHT), outline=0, fill=color)

# ---------------------------
# Modes
# ---------------------------
MODE_COLOR = 1
MODE_WORDS = 2
mode = MODE_COLOR
backlight_on = True

def render_mode_color():
    # Fill by daypart color, using the rotated image pipeline
    bg = daypart_color()
    clear(bg)
    disp.image(image, rotation)  # push with rotation

def render_mode_words():
    # Background
    base = tuple(int(c * 0.6) for c in daypart_color())
    clear(base)

    now = datetime.now()
    schedule = build_today_schedule(now)
    (prev_name, prev_time), (next_name, next_time) = find_prev_next(schedule, now)
    since_td = now - prev_time
    until_td = next_time - now

    # Determine a friendly phase label
    timeline = ["Go to bed", "Get up", "Lunch", "End of work", "Dinner", "Go to bed"]
    pair_to_label = {
        ("Go to bed", "Get up"):           "Since get up" if now >= schedule[1][1] else "Towards the time for go to bed",
        ("Get up", "Lunch"):               "Towards lunch",
        ("Lunch", "End of work"):          "Past lunch",
        ("End of work", "Dinner"):         "Till the end of work",
        ("Dinner", "Go to bed"):           "Past the dinner",
    }
    phase_line = pair_to_label.get((prev_name, next_name), "Vague time")

    # Title & phase
    draw_centered(draw, "Vague Clock", FONT_BIG, (LOGICAL_WIDTH//2, 20))
    draw_centered(draw, phase_line,  FONT_BIG, (LOGICAL_WIDTH//2, 45))

    # Time now
    now_str = datetime.now().strftime("%-I:%M %p") if hasattr(datetime.now(), "strftime") else datetime.now().strftime("%I:%M %p")
    draw_centered(draw, f"Now: {now_str}", FONT_MED, (LOGICAL_WIDTH//2, 68))

    # Two lines as requested
    line1 = f"It has been {fmt_duration(since_td)} since {prev_name.lower()}."
    line2 = f"It would be {fmt_duration(until_td)} towards {next_name.lower()}."

    # Simple wrap
    y = 88
    for text in (line1, line2):
        x = 6
        max_w = LOGICAL_WIDTH - 12
        words = text.split()
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            tw, th = draw.textbbox((0,0), test, font=FONT_SMALL)[2:]
            if tw <= max_w:
                cur = test
            else:
                draw.text((x, y), cur, font=FONT_SMALL, fill=(255,255,255))
                y += 16
                cur = w
        if cur:
            draw.text((x, y), cur, font=FONT_SMALL, fill=(255,255,255))
            y += 18

    # Footer help
    draw_centered(draw, "A=Color  B=Words  A+B=Backlight", FONT_SMALL, (LOGICAL_WIDTH//2, LOGICAL_HEIGHT-10))

    # Push with rotation
    disp.image(image, rotation)

# ---------------------------
# Main Loop
# ---------------------------
print("A=Color mode, B=Word mode, A+B toggles backlight (rotated 90°).")
last_press_time = 0.0
DEBOUNCE = 0.15

while True:
    a_pressed = (buttonA.value == False)
    b_pressed = (buttonB.value == False)

    now_t = time.monotonic()
    if (a_pressed or b_pressed) and (now_t - last_press_time > DEBOUNCE):
        last_press_time = now_t
        if a_pressed and b_pressed:
            backlight_on = not backlight_on
            backlight.value = backlight_on
        elif a_pressed:
            mode = MODE_COLOR
        elif b_pressed:
            mode = MODE_WORDS

    if backlight_on:
        if mode == MODE_COLOR:
            render_mode_color()
        else:
            render_mode_words()
    else:
        # optional: blank the screen when backlight is off
        clear((0,0,0))
        disp.image(image, rotation)

    time.sleep(0.25)
