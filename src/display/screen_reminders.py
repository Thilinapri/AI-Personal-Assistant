
import time
from datetime import datetime, timedelta

import RPi.GPIO as GPIO
import st7789
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# EchoMind Reminder Screen
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

# ==========================================
# DEMO REMINDER
# Used when running this file independently
# ==========================================

REMINDER_TITLE = "Presentation"

REMINDER_TIME = datetime.now() + timedelta(
    hours=2,
    minutes=15
)


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
# Countdown
# ==========================================

def get_countdown(target):

    remaining = target - datetime.now()

    seconds = max(0, int(remaining.total_seconds()))

    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days > 0:
        return f"{days}d {hours:02d}h {minutes:02d}m"

    return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"


# ==========================================
# Parse Reminder Time
# ==========================================

def parse_reminder_time(raw_time):

    if isinstance(raw_time, datetime):
        return raw_time

    if raw_time is None:
        raise ValueError("Reminder has no scheduled time")

    if isinstance(raw_time, str):
        raw_time = raw_time.strip()

        # Support common database datetime formats.
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
                return datetime.strptime(raw_time, date_format)
            except ValueError:
                continue

    raise ValueError(f"Unsupported reminder time: {raw_time!r}")


# ==========================================
# Draw Reminder Screen
# ==========================================

def draw_reminder_screen(display, reminder=None, live_data=False):

    # None in live mode means no upcoming reminder.
    # False also explicitly means no upcoming reminder.
    show_no_reminder = (
        reminder is False or
        (live_data and reminder is None)
    )

    if not show_no_reminder:

        if reminder is not None:
            reminder_title = str(
                reminder.get("title") or "Reminder"
            )

            reminder_time = parse_reminder_time(
                reminder.get("reminder_time")
            )

        else:
            # Standalone demo mode
            reminder_title = REMINDER_TITLE
            reminder_time = REMINDER_TIME

    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        BACKGROUND
    )

    draw = ImageDraw.Draw(image)

    header_font = load_font(16)
    label_font = load_font(11)
    title_font = load_font(27)
    date_font = load_font(14)
    time_font = load_font(24)
    countdown_font = load_font(19)

    # ======================================
    # Header
    # ======================================

    draw.text(
        (13, 10),
        "ECHOMIND",
        font=header_font,
        fill=WHITE
    )

    draw.rounded_rectangle(
        (226, 9, 307, 32),
        radius=10,
        fill=CARD
    )

    draw.text(
        (237, 14),
        "UPCOMING",
        font=label_font,
        fill=CYAN
    )

    # ======================================
    # Main Reminder Card
    # ======================================

    draw.rounded_rectangle(
        (12, 43, 308, 213),
        radius=15,
        fill=CARD,
        outline=CYAN,
        width=2
    )

    if show_no_reminder:

        centered_text(
            draw,
            54,
            "UPCOMING REMINDERS",
            label_font,
            CYAN
        )

        centered_text(
            draw,
            105,
            "NO REMINDERS",
            title_font,
            WHITE
        )

        centered_text(
            draw,
            145,
            "You're all caught up!",
            date_font,
            MUTED
        )

        centered_text(
            draw,
            221,
            "ECHOMIND IS HERE FOR YOU",
            label_font,
            MUTED
        )

        display.display(image)
        return

    # ======================================
    # Reminder Details
    # ======================================

    centered_text(
        draw,
        54,
        "NEXT REMINDER",
        label_font,
        CYAN
    )

    # Reminder title
    centered_text(
        draw,
        76,
        reminder_title,
        title_font,
        WHITE
    )

    # Reminder date
    date_text = reminder_time.strftime("%a, %d %b %Y")

    centered_text(
        draw,
        116,
        date_text,
        date_font,
        MUTED
    )

    # Reminder time
    time_text = reminder_time.strftime("%I:%M %p")

    centered_text(
        draw,
        137,
        time_text,
        time_font,
        CYAN
    )

    # Divider
    draw.line(
        (35, 171, 285, 171),
        fill=(75, 95, 125),
        width=1
    )

    # Countdown label
    centered_text(
        draw,
        174,
        "TIME REMAINING",
        label_font,
        MUTED
    )

    # Live countdown
    countdown = get_countdown(reminder_time)

    centered_text(
        draw,
        187,
        countdown,
        countdown_font,
        WHITE
    )

    # Bottom caption
    centered_text(
        draw,
        221,
        "YOUR NEXT IMPORTANT EVENT",
        label_font,
        MUTED
    )

    display.display(image)


# ==========================================
# Main
# Standalone TFT Test
# ==========================================

def main():

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    display = None

    try:

        print("Starting EchoMind Reminder Screen...")

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

        print("Reminder screen initialized.")
        print("Demo reminder:", REMINDER_TITLE)
        print("Press CTRL+C to stop.")

        while True:

            draw_reminder_screen(display)
            time.sleep(1)

    except KeyboardInterrupt:

        print("\nReminder screen stopped.")

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
