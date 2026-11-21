
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

def draw_robot(draw, frame, listening_enabled=None, animation_time=None):
    """Draw a floating companion within the original centered robot area."""
    del frame  # Kept in the signature for compatibility with existing callers.
    if animation_time is None:
        animation_time = time.monotonic()

    listening = listening_enabled is not False
    float_y = math.sin(animation_time * 1.15) * 1.5
    breathe = (math.sin(animation_time * 1.6) + 1.0) * 0.5
    x_shift = math.sin(animation_time * 0.38) * 1.3
    y_shift = int(round(float_y))
    center_x = int(round(160 + x_shift))
    head_top = int(round(59 + y_shift - breathe))
    head_bottom = int(round(146 + y_shift + breathe))
    shell_width = int(round(96 + breathe))
    left = center_x - shell_width // 2
    right = center_x + shell_width // 2

    # A restrained hover ring and shadow stay below the floating head.
    hover_phase = (math.sin(animation_time * 1.4) + 1.0) * 0.5
    ring_inset = int(round(5 * hover_phase))
    draw.ellipse(
        (125 + ring_inset, 151, 195 - ring_inset, 159),
        fill=(13, 27, 43), outline=(22, 63, 83), width=1
    )
    draw.arc(
        (130 + ring_inset, 152, 190 - ring_inset, 158),
        190, 350, fill=(35, 124, 157), width=1
    )

    # Cyan-lit rounded ear panels, tucked slightly behind the shell.
    ear_top = head_top + 34
    ear_bottom = ear_top + 27
    ear_glow = 0.65 + (0.35 if listening else 0.0) * (
        (math.sin(animation_time * 2.2) + 1.0) * 0.5
    )
    ear_color = (27, int(69 + 35 * ear_glow), int(91 + 45 * ear_glow))
    for x1, x2 in ((left - 9, left + 5), (right - 5, right + 9)):
        draw.rounded_rectangle(
            (x1, ear_top, x2, ear_bottom), radius=6,
            fill=ear_color, outline=(77, 183, 210), width=1
        )
        draw.line(
            (x1 + 4, ear_top + 7, x1 + 4, ear_bottom - 7),
            fill=(91, 221, 239), width=2
        )

    # Short antenna and smoothly pulsing cyan beacon.
    antenna_x = center_x
    pulse = (math.sin(animation_time * 2.0) + 1.0) * 0.5
    if listening:
        pulse = 0.55 + pulse * 0.45
    beacon = (40, int(160 + 75 * pulse), int(205 + 50 * pulse))
    draw.line(
        (antenna_x, head_top + 1, antenna_x, head_top - 10),
        fill=(150, 190, 205), width=3
    )
    draw.ellipse(
        (antenna_x - 6, head_top - 23, antenna_x + 6, head_top - 11),
        fill=(39, 72, 91), outline=(117, 201, 219), width=1
    )
    draw.ellipse(
        (antenna_x - 3, head_top - 20, antenna_x + 3, head_top - 14),
        fill=beacon
    )

    # Pearl shell with layered silver shading and cyan edge accents.
    draw.rounded_rectangle(
        (left, head_top, right, head_bottom), radius=27,
        fill=(150, 177, 194), outline=(92, 198, 220), width=2
    )
    draw.rounded_rectangle(
        (left + 3, head_top + 3, right - 3, head_bottom - 3), radius=24,
        fill=(219, 230, 235), outline=(246, 250, 250), width=1
    )
    draw.arc(
        (left + 9, head_top + 5, right - 9, head_top + 28),
        195, 345, fill=(255, 255, 255), width=2
    )

    # Dark glossy face panel.
    face_left = center_x - 39
    face_right = center_x + 39
    face_top = head_top + 19
    face_bottom = head_top + 68
    draw.rounded_rectangle(
        (face_left, face_top, face_right, face_bottom), radius=17,
        fill=(7, 16, 31), outline=(80, 150, 176), width=1
    )
    draw.arc(
        (face_left + 5, face_top + 2, face_right - 5, face_top + 19),
        195, 345, fill=(36, 72, 94), width=1
    )

    # Gaze follows a slow, smooth path with occasional upward/downward looks.
    gaze_x = int(round(math.sin(animation_time * 0.42) * 2.2))
    gaze_y = int(round(math.sin(animation_time * 0.27 + 1.1) * 1.2))
    eye_y = face_top + 22 + gaze_y
    eye_centers = (center_x - 19, center_x + 19)

    # Regular gentle blink, plus a rare short wink.
    blink_phase = animation_time % 4.8
    blink = max(0.0, 1.0 - abs(blink_phase - 0.13) / 0.13)
    wink_phase = animation_time % 17.0
    wink = max(0.0, 1.0 - abs(wink_phase - 0.18) / 0.18)
    for index, eye_x in enumerate(eye_centers):
        eye_blink = max(blink, wink if index == 0 else 0.0)
        eye_width = max(3, int(round(15 * (1.0 - 0.9 * eye_blink))))
        eye_height = max(2, int(round(17 * (1.0 - 0.92 * eye_blink))))
        eye_glow = int(14 + (10 if listening else 0) + 8 * pulse)
        draw.ellipse(
            (eye_x - eye_width // 2 - 2, eye_y - eye_height // 2 - 2,
             eye_x + eye_width // 2 + 2, eye_y + eye_height // 2 + 2),
            fill=(15, 74 + eye_glow, 103 + eye_glow)
        )
        draw.ellipse(
            (eye_x - eye_width // 2, eye_y - eye_height // 2,
             eye_x + eye_width // 2, eye_y + eye_height // 2),
            fill=(41, int(174 + 45 * pulse), 239)
        )
        if eye_blink < 0.65:
            pupil_x = eye_x + gaze_x
            draw.ellipse(
                (pupil_x - 2, eye_y - 3, pupil_x + 2, eye_y + 3),
                fill=(230, 250, 255)
            )

    # Curved brows follow the gaze; a tiny asymmetry hints at a relaxed tilt.
    brow_tilt = int(round(math.sin(animation_time * 0.31) * 1.0))
    for index, eye_x in enumerate(eye_centers):
        brow_y = face_top + 10 + (brow_tilt if index == 0 else -brow_tilt)
        draw.arc(
            (eye_x - 9, brow_y - 4, eye_x + 9, brow_y + 5),
            195, 345, fill=(157, 226, 244), width=2
        )

    # Small animated smile; listening adds a slightly more attentive lift.
    smile_phase = (math.sin(animation_time * 1.05) + 1.0) * 0.5
    mouth_lift = int(round(smile_phase * (2 if listening else 1)))
    mouth_top = face_top + 36 - mouth_lift
    draw.arc(
        (center_x - 11, mouth_top, center_x + 11, mouth_top + 13),
        15, 165, fill=(151, 224, 241), width=2
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
    draw_robot(draw, frame, listening_enabled, time.monotonic())

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
