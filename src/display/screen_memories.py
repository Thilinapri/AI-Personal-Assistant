
import time
from datetime import datetime

import RPi.GPIO as GPIO
import st7789
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# EchoMind Recently Added Memory Screen
# ==========================================

WIDTH = 320
HEIGHT = 240

DC_PIN = 25
RST_PIN = 24

BACKGROUND = (10, 17, 32)
CARD = (30, 48, 75)
CYAN = (48, 210, 255)
WHITE = (240, 245, 255)
MUTED = (145, 165, 190)
GREEN = (65, 230, 145)

# ==========================================
# DEMO MEMORY
# Used when running this file independently
# ==========================================

MEMORY_TITLE = "Team meeting"
MEMORY_CONTENT = "Discuss the new project plans with the team."
MEMORY_CATEGORY = "NOTE"
SAVED_AT = datetime.now()


# ==========================================
# Fonts
# ==========================================

def load_font(size):

    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"
    ]

    for path in paths:

        try:
            return ImageFont.truetype(path, size)

        except OSError:
            pass

    return ImageFont.load_default()


# ==========================================
# Centered Text
# ==========================================

def centered_text(draw, y, text, font, color):

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]

    draw.text(
        ((WIDTH - text_width) // 2, y),
        text,
        font=font,
        fill=color
    )


# ==========================================
# Text Wrapping
# ==========================================

def wrap_text(draw, text, font, max_width):

    words = str(text).split()

    lines = []
    current_line = ""

    for word in words:

        test_line = (
            word if not current_line
            else current_line + " " + word
        )

        bbox = draw.textbbox(
            (0, 0),
            test_line,
            font=font
        )

        text_width = bbox[2] - bbox[0]

        if text_width <= max_width:

            current_line = test_line

        else:

            if current_line:
                lines.append(current_line)

            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


# ==========================================
# Parse Saved Date
# ==========================================

def parse_saved_time(raw_time):

    if isinstance(raw_time, datetime):
        return raw_time

    if raw_time is None:
        return datetime.now()

    if isinstance(raw_time, str):

        raw_time = raw_time.strip()

        try:
            return datetime.fromisoformat(raw_time)

        except ValueError:
            pass

        for date_format in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%dT%H:%M:%S"
        ):

            try:
                return datetime.strptime(
                    raw_time,
                    date_format
                )

            except ValueError:
                continue

    return datetime.now()


# ==========================================
# Draw Memory Screen
# ==========================================

def draw_memory_screen(display, memory=None, live_data=False):

    # In live mode, None means the database has no memories.
    # False explicitly means there is no memory to display.

    show_no_memory = (
        memory is False or
        (live_data and memory is None)
    )

    if not show_no_memory:

        if memory is not None:

            memory_category = str(
                memory.get("category") or "MEMORY"
            )

            memory_title = str(
                memory.get("title") or "Untitled"
            )

            memory_content = str(
                memory.get("content") or ""
            )

            saved_at = parse_saved_time(
                memory.get("created_at")
            )

        else:

            # Standalone demo mode
            memory_category = MEMORY_CATEGORY
            memory_title = MEMORY_TITLE
            memory_content = MEMORY_CONTENT
            saved_at = SAVED_AT

    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        BACKGROUND
    )

    draw = ImageDraw.Draw(image)

    header_font = load_font(16)
    label_font = load_font(11)
    title_font = load_font(25)
    content_font = load_font(13)
    detail_font = load_font(11)

    # ======================================
    # Header
    # ======================================

    draw.text(
        (13, 10),
        "ECHOMIND",
        font=header_font,
        fill=WHITE
    )

    # Saved indicator

    draw.rounded_rectangle(
        (248, 9, 307, 32),
        radius=10,
        fill=(22, 65, 65)
    )

    draw.ellipse(
        (256, 16, 264, 24),
        fill=GREEN
    )

    draw.text(
        (268, 14),
        "SAVED",
        font=label_font,
        fill=GREEN
    )

    # ======================================
    # Main Memory Card
    # ======================================

    draw.rounded_rectangle(
        (12, 43, 308, 213),
        radius=15,
        fill=CARD,
        outline=CYAN,
        width=2
    )

    # ======================================
    # Empty Memory State
    # ======================================

    if show_no_memory:

        centered_text(
            draw,
            75,
            "RECENTLY REMEMBERED",
            label_font,
            CYAN
        )

        centered_text(
            draw,
            115,
            "NO MEMORIES YET",
            title_font,
            WHITE
        )

        centered_text(
            draw,
            151,
            "I'll remember things for you!",
            content_font,
            MUTED
        )

        centered_text(
            draw,
            220,
            "YOUR MEMORIES STAY WITH ECHOMIND",
            label_font,
            MUTED
        )

        display.display(image)
        return

    # ======================================
    # Section Label
    # ======================================

    centered_text(
        draw,
        53,
        "RECENTLY REMEMBERED",
        label_font,
        CYAN
    )

    # ======================================
    # Memory Category
    # ======================================

    category_text = memory_category.upper()

    # Keep long category names inside the badge.
    category_font = load_font(10)

    category_bbox = draw.textbbox(
        (0, 0),
        category_text,
        font=category_font
    )

    category_width = category_bbox[2] - category_bbox[0]

    badge_width = min(
        max(82, category_width + 24),
        276
    )

    badge_left = (WIDTH - badge_width) // 2

    draw.rounded_rectangle(
        (
            badge_left,
            75,
            badge_left + badge_width,
            97
        ),
        radius=9,
        fill=(18, 65, 88)
    )

    centered_text(
        draw,
        80,
        category_text,
        category_font,
        CYAN
    )

    # ======================================
    # Memory Title
    # ======================================

    title_lines = wrap_text(
        draw,
        memory_title,
        title_font,
        270
    )

    title_y = 104

    for line in title_lines[:1]:

        centered_text(
            draw,
            title_y,
            line,
            title_font,
            WHITE
        )

    # ======================================
    # Memory Description
    # ======================================

    lines = wrap_text(
        draw,
        memory_content,
        content_font,
        250
    )

    y = 143

    for line in lines[:2]:

        centered_text(
            draw,
            y,
            line,
            content_font,
            MUTED
        )

        y += 18

    # ======================================
    # Divider
    # ======================================

    draw.line(
        (35, 177, 285, 177),
        fill=(75, 95, 125),
        width=1
    )

    # ======================================
    # Saved Date and Time
    # ======================================

    saved_date = saved_at.strftime("%d %b %Y")
    saved_time = saved_at.strftime("%I:%M %p")

    draw.text(
        (30, 188),
        "SAVED",
        font=detail_font,
        fill=MUTED
    )

    draw.text(
        (75, 188),
        saved_date,
        font=detail_font,
        fill=WHITE
    )

    bbox = draw.textbbox(
        (0, 0),
        saved_time,
        font=detail_font
    )

    time_width = bbox[2] - bbox[0]

    draw.text(
        (290 - time_width, 188),
        saved_time,
        font=detail_font,
        fill=CYAN
    )

    # ======================================
    # Bottom Caption
    # ======================================

    centered_text(
        draw,
        220,
        "I'VE REMEMBERED THIS FOR YOU",
        label_font,
        MUTED
    )

    # Send image to display
    display.display(image)


# ==========================================
# Main Display Test
# ==========================================

def main():

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    display = None

    try:

        print("Starting EchoMind Memory Screen...")

        display = st7789.ST7789(
            port=0,
            cs=0,
            dc=DC_PIN,
            rst=RST_PIN,
            backlight=None,
            width=WIDTH,
            height=HEIGHT,
            rotation=0,
            invert=True,
            spi_speed_hz=4000000,
            offset_left=0,
            offset_top=0
        )

        # Previously tested display initialization
        display.reset()
        time.sleep(0.2)
        display._init()

        print("Memory screen initialized.")
        print("Demo memory:", MEMORY_TITLE)
        print("Press CTRL+C to stop.")

        while True:

            draw_memory_screen(display)
            time.sleep(2)

    except KeyboardInterrupt:

        print("\nMemory screen stopped.")

    except Exception as error:

        print("Display error:", repr(error))

    finally:

        if display is not None:

            try:

                display.display(
                    Image.new(
                        "RGB",
                        (WIDTH, HEIGHT),
                        BACKGROUND
                    )
                )

            except Exception:
                pass

        GPIO.cleanup()

        print("GPIO cleanup complete.")


if __name__ == "__main__":
    main()
