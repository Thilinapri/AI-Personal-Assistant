
import time
import RPi.GPIO as GPIO
import st7789
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# ==========================================
# EchoMind Notification Screen V2
# ==========================================

WIDTH = 320
HEIGHT = 240

DC_PIN = 25
RST_PIN = 24

BACKGROUND = (10, 17, 32)
CARD = (48, 38, 43)
AMBER = (255, 180, 91)
WHITE = (255, 248, 240)
MUTED = (205, 185, 170)

# ==========================================
# DEMO NOTIFICATION
# ==========================================

NOTIFICATION_TITLE = "Presentation"

NOTIFICATION_MESSAGE = (
    "Your presentation is starting now."
)

NOTIFICATION_TIME = datetime.now().strftime("%I:%M %p")


# ==========================================
# Font Loading
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
# Draw Proper Bell Icon
# ==========================================

def draw_bell(draw, frame):

    # Bell dome and body
    draw.ellipse(
        (140, 53, 180, 94),
        fill=AMBER
    )

    # Lower bell body
    draw.rectangle(
        (140, 73, 180, 91),
        fill=AMBER
    )

    # Flared bottom
    draw.polygon(
        [
            (140, 85),
            (180, 85),
            (188, 99),
            (132, 99)
        ],
        fill=AMBER
    )

    # Bell handle
    draw.arc(
        (153, 47, 167, 61),
        180,
        360,
        fill=AMBER,
        width=3
    )

    # Clapper
    draw.ellipse(
        (153, 99, 167, 111),
        fill=AMBER
    )

    # Small alert motion lines
    if frame % 4 < 2:
        draw.arc(
            (119, 57, 137, 91),
            270,
            90,
            fill=AMBER,
            width=2
        )

        draw.arc(
            (183, 57, 201, 91),
            90,
            270,
            fill=AMBER,
            width=2
        )


# ==========================================
# Draw Notification Screen
# ==========================================

def draw_notification_screen(display, frame, reminder=None):

    # Use demo values when no live reminder is supplied.
    title = NOTIFICATION_TITLE
    message = NOTIFICATION_MESSAGE
    scheduled_time = NOTIFICATION_TIME

    # Use real reminder information when available.
    if reminder is not None:

        title = reminder.get("title") or "Reminder"

        message = reminder.get("content") or ""

        reminder_time = reminder.get("reminder_time")

        if reminder_time:
            try:
                scheduled_time = datetime.strptime(
                    reminder_time,
                    "%Y-%m-%d %H:%M:%S"
                ).strftime("%I:%M %p")

            except ValueError:
                scheduled_time = str(reminder_time)

    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        BACKGROUND
    )

    draw = ImageDraw.Draw(image)

    header_font = load_font(16)
    label_font = load_font(11)
    title_font = load_font(24)
    message_font = load_font(13)
    time_font = load_font(22)

    # --------------------------------------
    # Header
    # --------------------------------------

    draw.text(
        (13, 10),
        "ECHOMIND",
        font=header_font,
        fill=WHITE
    )

    # Alert badge
    draw.rounded_rectangle(
        (244, 9, 307, 32),
        radius=10,
        fill=(75, 51, 38)
    )

    draw.text(
        (256, 14),
        "ALERT",
        font=label_font,
        fill=AMBER
    )

    # --------------------------------------
    # Main notification card
    # --------------------------------------

    draw.rounded_rectangle(
        (12, 43, 308, 213),
        radius=15,
        fill=CARD,
        outline=AMBER,
        width=2
    )

    # --------------------------------------
    # Bell icon
    # --------------------------------------

    draw_bell(draw, frame)

    # --------------------------------------
    # Reminder heading
    # --------------------------------------

    centered_text(
        draw,
        112,
        "REMINDER!",
        label_font,
        AMBER
    )

    # --------------------------------------
    # Reminder title
    # --------------------------------------

    centered_text(
        draw,
        130,
        NOTIFICATION_TITLE,
        title_font,
        WHITE
    )

    # --------------------------------------
    # Reminder message
    # --------------------------------------

    centered_text(
        draw,
        163,
        NOTIFICATION_MESSAGE,
        message_font,
        MUTED
    )

    # --------------------------------------
    # Scheduled time
    # --------------------------------------

    centered_text(
        draw,
        184,
        NOTIFICATION_TIME,
        time_font,
        AMBER
    )

    # --------------------------------------
    # Bottom caption
    # --------------------------------------

    centered_text(
        draw,
        220,
        "DON'T FORGET!",
        label_font,
        AMBER
    )

    display.display(image)


# ==========================================
# Main
# ==========================================

def main():

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    display = None

    try:

        print("Starting EchoMind Notification Screen V2...")

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

        # Previously tested TFT initialization
        display.reset()
        time.sleep(0.2)
        display._init()

        print("Notification screen initialized.")
        print("Showing improved notification design.")
        print("Press CTRL+C to stop.")

        frame = 0

        while True:

            draw_notification_screen(display, frame)

            frame += 1

            time.sleep(0.5)

    except KeyboardInterrupt:

        print("\nNotification screen stopped.")

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
