# vague_clock_two_lines.py
# ST7789 (mini PiTFT 240x135) "vague time" clock with your rotation method.
# A => Color mode (background by daypart), B => Word mode (ONLY TWO LINES: "Since ..." and "To ...")
# A+B => toggle backlight

import time
import digitalio
import board
from datetime import datetime, timedelta

from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# ---------------------------
# Display + SPI configuration
# ---------------------------
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None
BAUDRATE = 64_000_000

spi = board.SPI()

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

# Rotate like your snippet (landscape): swap width/height, use rotation=90 on push
height = disp.width   # 135
width  = disp.height  # 240
rotation = 90

# ---------------------------
# Backlight + Buttons
# ---------------------------
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output(value=True)
backlight_on = True

buttonA = digitalio.DigitalInOut(board.D23)
buttonB = digitalio.DigitalInOut(board.D24)
buttonA.switch_to_input(pull=digitalio.Pull.UP)  # active LOW
buttonB.switch_to_input(pull=digitalio.Pull.UP)

# ---------------------------
# Fonts (we'll adapt size to fit width)
# ---------------------------
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def load_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

# ---------------------------
# User-configurable event times (24h)
# ---------------------------
EVENT_DEFAULTS = {
    "get_up":   (9, 0),
    "lunch":    (13, 0),
    "end_day":  (18, 0),
    "dinner":   (19, 30),
    "bed":      (0, 0),   # midnight (next-day boundary)
}

# ---------------------------
# Time helpers
# ---------------------------
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
    bed0    = dt(*EVENT_DEFAULTS["bed"])        # 00:00 today
    bed1    = dt(*EVENT_DEFAULTS["bed"], 1)     # 00:00 next day

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
    total = int(td.total_seconds())
    if total < 0:
        total = 0
    h, rem = divmod(total, 3600)
    m, _ = divmod(rem, 60)
    return f"{h}h {m}m" if h > 0 else f"{m}m"

def daypart_color(now=None):
    if now is None:
        now = datetime.now()
    hr = now.hour
    if 6 <= hr < 12:
        return (255, 236, 179)      # morning: light yellow / soft orange
    elif 12 <= hr < 18:
        return (135, 206, 235)      # afternoon: bright/sky blue
    else:
        return (75, 0, 130)         # night: deep purple

# ---------------------------
# Drawing helpers
# ---------------------------
def center_text(draw, text, font, y, fill=(255,255,255)):
    bbox = draw.textbbox((0,0), text, font=font)
    w = bbox[2] - bbox[0]
    x = (width - w) // 2
    draw.text((x, y), text, font=font, fill=fill)

def fit_line(draw, base_text, max_width, max_font_size=26, min_font_size=12):
    """Return (font, text) with font size reduced until the line fits max_width.
       If still too long at min size, truncate with ellipsis."""
    size = max_font_size
    while size >= min_font_size:
        f = load_font(size)
        tw = draw.textbbox((0,0), base_text, font=f)[2]
        if tw <= max_width:
            return f, base_text
        size -= 2

    # truncate
    f = load_font(min_font_size)
    text = base_text
    while draw.textbbox((0,0), text + "…", font=f)[2] > max_width and len(text) > 0:
        text = text[:-1]
    return f, (text + "…") if text else "…"

# ---------------------------
# Modes
# ---------------------------
MODE_COLOR = 1
MODE_WORDS = 2
mode = MODE_COLOR

def render_color_frame():
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    bg = daypart_color()
    draw.rectangle((0, 0, width, height), fill=bg)
    # Optional small label
    f = load_font(12)
    center_text(draw, "Color Mode", f, 6, fill=(0,0,0) if bg != (0,0,0) else (255,255,255))
    disp.image(img, rotation)

def render_words_frame():
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    # Soft background
    base = daypart_color()
    dim  = tuple(int(c * 0.6) for c in base)
    draw.rectangle((0, 0, width, height), fill=dim)

    now = datetime.now()
    schedule = build_today_schedule(now)
    (prev_name, prev_time), (next_name, next_time) = find_prev_next(schedule, now)

    since_td = now - prev_time
    until_td = next_time - now

    line1 = f"It has been {fmt_duration(since_td)} since {prev_name}."
    line2 = f"There are {fmt_duration(until_td)} until {next_name}."

    # Fit both lines to screen width
    f1, t1 = fit_line(draw, line1, max_width=width - 10, max_font_size=28, min_font_size=12)
    f2, t2 = fit_line(draw, line2, max_width=width - 10, max_font_size=28, min_font_size=12)

    # Vertical placement: center the two lines nicely
    # Estimate heights
    h1 = draw.textbbox((0,0), t1, font=f1)[3]
    h2 = draw.textbbox((0,0), t2, font=f2)[3]
    total_h = h1 + h2 + 8  # 8px gap
    start_y = (height - total_h) // 2

    center_text(draw, t1, f1, start_y, fill=(255,255,255))
    center_text(draw, t2, f2, start_y + h1 + 8, fill=(255,255,255))

    disp.image(img, rotation)

# ---------------------------
# Main loop
# ---------------------------
print("A=Color mode, B=Two-line Words mode, A+B toggles backlight. Using rotation=90 push.")
last_press = 0.0
DEBOUNCE = 0.15

# Clear once
disp.image(Image.new("RGB", (width, height)), rotation)

while True:
    a_pressed = (buttonA.value == False)
    b_pressed = (buttonB.value == False)

    t = time.monotonic()
    if (a_pressed or b_pressed) and (t - last_press > DEBOUNCE):
        last_press = t
        if a_pressed and b_pressed:
            backlight_on = not backlight_on
            backlight.value = backlight_on
        elif a_pressed:
            mode = MODE_COLOR
        elif b_pressed:
            mode = MODE_WORDS

    if backlight_on:
        if mode == MODE_COLOR:
            render_color_frame()
        else:
            render_words_frame()
    else:
        disp.image(Image.new("RGB", (width, height)), rotation)

    time.sleep(0.25)
