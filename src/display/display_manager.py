
import time
import math
from functools import lru_cache
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
RED = (235, 105, 105)


# ==========================================
# Font Loading
# ==========================================

@lru_cache(maxsize=8)
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

def draw_robot(draw, frame, animation_time=None):
    """Draw the compact home-screen robot using elapsed-time animation."""
    if animation_time is None:
        animation_time = time.monotonic()

    # Keep motion within the existing centered robot area.
    float_y = math.sin(animation_time * 1.25) * 1.5
    breath = (math.sin(animation_time * 1.7) + 1.0) * 0.5
    x_shift = math.sin(animation_time * 0.42) * 1.5
    y_shift = int(round(float_y))
    left = int(round(106 + x_shift))
    right = int(round(214 + x_shift))
    top = int(round(61 + y_shift - breath))
    bottom = int(round(153 + y_shift + breath))
    center_x = int(round(160 + x_shift))

    # Antenna stem and softly pulsing beacon.
    pulse = (math.sin(animation_time * 2.4) + 1.0) * 0.5
    beacon = (48, int(170 + 55 * pulse), 220 + int(35 * pulse))
    draw.line((center_x, top, center_x, top - 13), fill=(70, 145, 185), width=3)
    draw.ellipse(
        (center_x - 7, top - 25, center_x + 7, top - 11),
        fill=(24, 55, 78), outline=(65, 145, 185), width=1
    )
    draw.ellipse(
        (center_x - 4, top - 22, center_x + 4, top - 14), fill=beacon
    )

    # Side modules retain the original ear footprint.
    ear_top = top + 31
    ear_bottom = ear_top + 30
    for x1, x2, direction in (
        (left - 12, left + 1, -1), (right - 1, right + 12, 1)
    ):
        draw.rounded_rectangle(
            (x1, ear_top, x2, ear_bottom), radius=5,
            fill=(28, 77, 103), outline=(48, 160, 195), width=1
        )
        grille_x = x1 + 4 if direction < 0 else x2 - 4
        draw.line(
            (grille_x, ear_top + 8, grille_x, ear_bottom - 8),
            fill=CYAN, width=2
        )

    # Layered shell and a subtle upper highlight.
    draw.rounded_rectangle(
        (left, top, right, bottom), radius=24,
        fill=(19, 35, 57), outline=(57, 157, 194), width=2
    )
    draw.rounded_rectangle(
        (left + 5, top + 5, right - 5, bottom - 5), radius=20,
        fill=ROBOT_COLOR, outline=(39, 72, 101), width=1
    )
    draw.arc(
        (left + 9, top + 7, right - 9, top + 31),
        195, 345, fill=(85, 130, 157), width=1
    )

    # Blinks and gaze changes use monotonic elapsed time, independent of FPS.
    blink_phase = animation_time % 4.7
    blink = max(0.0, 1.0 - abs(blink_phase - 0.12) / 0.12)
    gaze_x = int(round(math.sin(animation_time * 0.55) * 2.0))
    eye_y = top + 39
    eye_color = (75, int(190 + 35 * pulse), 235)
    for eye_x in (center_x - 25, center_x + 25):
        eye_width = max(2, int(round(17 * (1.0 - 0.92 * blink))))
        eye_height = max(2, int(round(16 * (1.0 - 0.92 * blink))))
        draw.rounded_rectangle(
            (eye_x - eye_width // 2, eye_y - eye_height // 2,
             eye_x + eye_width // 2, eye_y + eye_height // 2),
            radius=min(5, eye_width // 2, eye_height // 2),
            fill=eye_color
        )
        if blink < 0.65:
            pupil_x = eye_x + gaze_x
            draw.ellipse(
                (pupil_x - 2, eye_y - 3, pupil_x + 2, eye_y + 3),
                fill=(226, 250, 255)
            )

    # A small smile variation adds expression without drawing attention.
    smile_lift = int(round(math.sin(animation_time * 1.1) * 1.2))
    mouth_top = top + 56 - smile_lift
    draw.arc(
        (center_x - 14, mouth_top, center_x + 14, mouth_top + 17),
        15, 165, fill=(151, 205, 220), width=2
    )


# ==========================================
# Create EchoMind Home Screen
# ==========================================

def draw_screen(display, frame, listening_enabled=None):

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
    draw_robot(draw, frame, time.monotonic())

    # Microphone status
    if listening_enabled is None:

        centered_text(
            draw,
            166,
            "LISTENING",
            status_font,
            CYAN
        )

    elif listening_enabled:

        centered_text(
            draw,
            166,
            "MIC: ON",
            status_font,
            GREEN
        )

    else:

        centered_text(
            draw,
            166,
            "MIC: OFF",
            status_font,
            RED
        )

    # Animated sound waves
    center_x = 160
    center_y = 194

    if listening_enabled is not False:

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
