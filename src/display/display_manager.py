
import time
import math
import RPi.GPIO as GPIO
import st7789
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# EchoMind TFT Display Configuration
# ==========================================

WIDTH = 320
HEIGHT = 240

DC_PIN = 25
RST_PIN = 24

BACKGROUND = (10, 17, 32)
CYAN = (48, 210, 255)
WHITE = (240, 245, 255)
MUTED = (125, 150, 180)
ROBOT_COLOR = (30, 48, 75)
GREEN = (40, 220, 140)


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
# Text Drawing
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
# Robot Drawing
# ==========================================

def draw_robot(draw, frame):

    # Robot head
    draw.rounded_rectangle(
        (105, 57, 215, 157),
        radius=27,
        fill=ROBOT_COLOR,
        outline=CYAN,
        width=3
    )

    # Antenna
    draw.line(
        (160, 57, 160, 43),
        fill=CYAN,
        width=3
    )

    draw.ellipse(
        (155, 36, 165, 46),
        fill=CYAN
    )

    # Robot ears
    draw.rounded_rectangle(
        (94, 92, 106, 125),
        radius=5,
        fill=CYAN
    )

    draw.rounded_rectangle(
        (214, 92, 226, 125),
        radius=5,
        fill=CYAN
    )

    # Blinking eyes
    blink = frame % 24 in (0, 1)

    if blink:
        draw.line(
            (125, 103, 144, 103),
            fill=CYAN,
            width=3
        )

        draw.line(
            (176, 103, 195, 103),
            fill=CYAN,
            width=3
        )

    else:
        draw.ellipse(
            (125, 91, 144, 112),
            fill=CYAN
        )

        draw.ellipse(
            (176, 91, 195, 112),
            fill=CYAN
        )

    # Smile
    draw.arc(
        (137, 111, 183, 144),
        10,
        170,
        fill=WHITE,
        width=2
    )


# ==========================================
# Create EchoMind Home Screen
# ==========================================

def draw_screen(display, frame):

    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        BACKGROUND
    )

    draw = ImageDraw.Draw(image)

    title_font = load_font(17)
    status_font = load_font(14)
    small_font = load_font(11)

    # Header
    draw.text(
        (13, 10),
        "ECHOMIND",
        font=title_font,
        fill=WHITE
    )

    # Online indicator
    draw.ellipse(
        (277, 16, 286, 25),
        fill=GREEN
    )

    draw.text(
        (291, 12),
        "ON",
        font=small_font,
        fill=GREEN
    )

    # Robot animation
    draw_robot(draw, frame)

    # Listening status
    centered_text(
        draw,
        166,
        "LISTENING",
        status_font,
        CYAN
    )

    # Animated sound waves
    center_x = 160
    center_y = 194

    for i in range(3):

        height = 3 + int(
            abs(math.sin(frame * 0.35 + i * 0.9)) * 7
        )

        x = center_x - 17 + i * 17

        draw.rounded_rectangle(
            (
                x,
                center_y - height,
                x + 6,
                center_y + height
            ),
            radius=3,
            fill=CYAN
        )

    # Current time and date
    now = time.localtime()

    clock = time.strftime(
        "%I:%M:%S %p",
        now
    )

    date = time.strftime(
        "%a, %d %b %Y",
        now
    )

    centered_text(
        draw,
        207,
        clock,
        status_font,
        WHITE
    )

    centered_text(
        draw,
        226,
        date,
        small_font,
        MUTED
    )

    # Send image to TFT
    display.display(image)


# ==========================================
# Main Display Controller
# ==========================================

def main():

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    display = None

    try:

        print("Starting EchoMind TFT display...")

        # Initialise ST7789 using the proven settings
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

        # IMPORTANT: Preserve the initialisation
        # used by the previously working TFT test.
        display.reset()
        time.sleep(0.2)
        display._init()

        print("EchoMind display initialized.")
        print("Showing animated home screen...")
        print("Press CTRL+C to stop.")

        frame = 0

        while True:

            draw_screen(display, frame)

            frame += 1

            time.sleep(0.12)

    except KeyboardInterrupt:

        print("\nEchoMind display stopped.")

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


# ==========================================
# Program Entry Point
# ==========================================

if __name__ == "__main__":
    main()
