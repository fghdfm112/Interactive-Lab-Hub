# vague_clock.py
# Raspberry Pi + Adafruit mini PiTFT ST7789 (1.14" 240x135 with x/y offsets shown below)
# Two-button, two-mode "vague time" clock:
#   A => Mode 1 (color fill by day part), B => Mode 2 (word clock between events), A+B => backlight toggle

import time
import digitalio
import board
from datetime import datetime, timedelta

from adafruit_rgb_display.rgb import color565
import adafruit_rgb_display.st7789 as st7789

# Pillow for text rendering
from PIL import Image, ImageDraw, ImageFont

# ---------------
# SPI + Display
# ---------------
cs_pin = digitalio.DigitalInOut(board.D5)     # GPIO5  (PIN 29)  <-- wire display CS here
dc_pin = digitalio.DigitalInOut(board.D25)    # GPIO25 (PIN 22)
reset_pin = None
BAUDRATE = 64_000_000
spi = board.SPI()

# Mini PiTFT 240x135 w/ offsets; rotate if you like (uncomment rotation)
display = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
    # rotation=0,
)

# ---------------
# Backlight + Buttons
# ---------------
backlight = digitalio.DigitalInOut(board.D22)  # GPIO22 (PIN 15)
backlight.switch_to_output(value=True)

buttonA = digitalio.DigitalInOut(board.D23)    # GPIO23 (PIN 16)
buttonB = digitalio.DigitalInOut(board.D24)    # GPIO24 (PIN 18)
buttonA.switch_to_input(pull=digitalio.Pull.UP)  # active LOW
buttonB.switch_to_input(pull=digitalio.Pull.UP)

# ---------------
# Fonts
# ---------------
try:
    # If you have a TTF on your Pi, point to it for nicer text
    font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    font_med = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
except Exception:
    # Fallback to default PIL bitmap fonts
    font_big = ImageFont.load_default()
    font_med = ImageFont.load_default()
    font_small = ImageFont.load_default()

# ---------------
# User-configurable event times (24h)
# ---------------
# All interpreted for "today" local time; 'bed' is treated as midnight (next day).
EVENT_DEFAULTS = {
    "get_up":   (9, 0),    # 09:00
    "lunch":    (13, 0),   # 13:00
    "end_day":  (18, 0),   # 18:00
    "dinner":   (19, 30),  # 19:30
    "bed":      (0, 0),    # 00:00 (midnight)
}

# Friendly labels (in order)
EVENT_ORDER = [
    ("get_up",  "Since get up"),
    ("lunch",   "Towards lunch"),
    ("lunch",   "Past lunch"),
    ("end_day", "Till the end of work"),
    ("end_day", "After the end of work"),
    ("dinner",  "Towards the dinner"),
    ("dinner",  "Past the dinner"),
    ("bed",     "Towards the time for go to bed"),
]

# ---------------
# Helpers
# ---------------
def build_today_schedule(now=None):
    """Return an ordered list of (label, datetime) for today's cycle:
       00:00 bed (from previous midnight) -> 09:00 get up -> 13:00 lunch -> 18:00 end ->
       19:30 dinner -> 24:00 bed (next midnight).
    """
    if now is None:
        now = datetime.now()

    today = now.date()
    def dt(h, m, day_offset=0):
        return datetime(today.year, today.month, today.day, h, m) + timedelta(days=day_offset)

    get_up  = dt(*EVENT_DEFAULTS["get_up"])
    lunch   = dt(*EVENT_DEFAULTS["lunch"])
    end_day = dt(*EVENT_DEFAULTS["end_day"])
    dinner  = dt(*EVENT_DEFAULTS["dinner"])
    bed0    = dt(*EVENT_DEFAULTS["bed"])      # 00:00 today
    bed1    = dt(*EVENT_DEFAULTS["bed"], 1)   # 00:00 next day (i.e., tonight's bed)

    # Ordered checkpoints spanning the whole day:
    # start from 00:00 today -> get_up -> lunch -> end_day -> dinner -> 24:00 (next day 00:00)
    schedule = [
        ("Go to bed", bed0),
        ("Get up", get_up),
        ("Lunch", lunch),
        ("End of work", end_day),
        ("Dinner", dinner),
        ("Go to bed", bed1),
    ]
    # Ensure monotonic in time (it is), but if now < bed0 (shouldn't happen), handle anyway
    schedule.sort(key=lambda x: x[1])
    return schedule

def find_prev_next(schedule, now=None):
    """Given a schedule [(name, dt), ...], find previous and next event for 'now'."""
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
        # If after last event before bed1:
        if now >= schedule[-2][1]:
            prev_evt = schedule[-2]
            next_evt = schedule[-1]
    return prev_evt, next_evt

def fmt_duration(td):
    """Format a timedelta as Hh Mm (omit zeros nicely)."""
    total_seconds = int(td.total_seconds())
    if total_seconds < 0:
        total_seconds = 0
    h, rem = divmod(total_seconds, 3600)
    m, _ = divmod(rem, 60)
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"

def daypart_color(now=None):
    """Return an RGB tuple for morning/afternoon/night."""
    if now is None:
        now = datetime.now()
    hr = now.hour

    # Define day parts (edit as you wish)
    # Morning: 06:00-11:59, Afternoon: 12:00-17:59, Night: otherwise
    if 6 <= hr < 12:
        # Light Yellow / Soft Orange
        return (255, 236, 179)  # light warm yellow
    elif 12 <= hr < 18:
        # Bright Blue / Sky Blue
        return (135, 206, 235)  # sky blue
    else:
        # Deep Purple
        return (75, 0, 130)     # indigo/deep purple

def draw_centered(draw, text, font, xy_center, fill=(255,255,255)):
    w, h = draw.textbbox((0,0), text, font=font)[2:]
    draw.text((xy_center[0] - w/2, xy_center[1] - h/2), text, font=font, fill=fill)

# ---------------
# Mode logic
# ---------------
MODE_COLOR = 1
MODE_WORDS = 2
mode = MODE_COLOR
backlight_on = True

def render_mode_color():
    rgb = daypart_color()
    display.fill(color565(*rgb))

def render_mode_words():
    # Prepare canvas
    width = display.width
    height = display.height
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)

    # Background color faintly based on daypart
    base = daypart_color()
    bg = tuple(int(c * 0.6) for c in base)  # dim it
    draw.rectangle((0, 0, width, height), fill=bg)

    now = datetime.now()
    schedule = build_today_schedule(now)
    (prev_name, prev_time), (next_name, next_time) = find_prev_next(schedule, now)

    since_td = now - prev_time
    until_td = next_time - now

    # Choose current phase line based on where we are:
    # Map prev/next to "Since/Towards/Past/Till/After..." lines
    phase_line = ""
    # Build a simple mapping ring:
    timeline = ["Go to bed", "Get up", "Lunch", "End of work", "Dinner", "Go to bed"]
    idx_next = timeline.index(next_name)
    idx_prev = timeline.index(prev_name)

    # A readable status by pair:
    # prev -> next  => label
    pair_to_label = {
        ("Go to bed", "Get up"):           "Since get up" if now >= schedule[1][1] else "Towards the time for go to bed",
        ("Get up", "Lunch"):               "Towards lunch",
        ("Lunch", "End of work"):          "Past lunch",
        ("End of work", "Dinner"):         "Till the end of work",
        ("Dinner", "Go to bed"):           "Past the dinner",
        ("Go to bed", "Get up"):           "Towards the time for go to bed",  # early morning hours
    }
    phase_line = pair_to_label.get((prev_name, next_name), "Vague time")

    # Title
    draw_centered(draw, "Vague Clock", font_big, (width//2, 26), fill=(255,255,255))

    # Phase (bigger)
    draw_centered(draw, phase_line, font_big, (width//2, 60), fill=(255,255,255))

    # Event rows
    # Current local time
    now_str = now.strftime("%-I:%M %p") if hasattr(now, "strftime") else now.strftime("%I:%M %p")
    draw_centered(draw, f"Now: {now_str}", font_med, (width//2, 88))

    # Lines requested:
    # "It has been xxx since 1st event , and it would be xxx time towards 2nd event."
    line1 = f"It has been {fmt_duration(since_td)} since {prev_name.lower()}."
    line2 = f"It would be {fmt_duration(until_td)} towards {next_name.lower()}."
    # Wrap manually if narrow
    def draw_wrapped(y, text, font, line_height):
        max_w = width - 10
        words = text.split()
        line = ""
        cur_y = y
        for w in words:
            test = (line + " " + w).strip()
            tw, th = draw.textbbox((0,0), test, font=font)[2:]
            if tw <= max_w:
                line = test
            else:
                draw.text((5, cur_y), line, font=font, fill=(255,255,255))
                cur_y += line_height
                line = w
        if line:
            draw.text((5, cur_y), line, font=font, fill=(255,255,255))
        return cur_y + line_height

    y = 112
    y = draw_wrapped(y, line1, font_small, 16)
    y = draw_wrapped(y, line2, font_small, 16)

    # Footer: hint
    draw_centered(draw, "A=Color  B=Words  A+B=Backlight", font_small, (width//2, height-12), fill=(230,230,230))

    # Push to display
    display.image(image)

# ---------------
# Main loop
# ---------------
print("A=Color mode, B=Word mode, A+B toggles backlight.")
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

    # Render current mode ~4fps; update content every frame (cheap)
    if backlight_on:
        if mode == MODE_COLOR:
            render_mode_color()
        else:
            render_mode_words()
    else:
        # Optional: blank when backlight off so next on is fresh
        display.fill(color565(0, 0, 0))

    time.sleep(0.25)
