
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
# Robot Layout Scaling
# ==========================================

class _RobotDrawTransform:
    """Scale robot primitives uniformly into the compact greeting layout."""

    SCALE = 0.8
    SOURCE_CENTER = (160, 93)
    TARGET_CENTER = (160, 80)

    def __init__(self, draw):
        self.draw = draw

    def _point(self, x, y):
        scale = self.SCALE
        source_x, source_y = self.SOURCE_CENTER
        target_x, target_y = self.TARGET_CENTER
        return (
            int(round(target_x + (x - source_x) * scale)),
            int(round(target_y + (y - source_y) * scale)),
        )

    def _box(self, box):
        x1, y1 = self._point(box[0], box[1])
        x2, y2 = self._point(box[2], box[3])
        return x1, y1, x2, y2

    def _width(self, width):
        return max(1, int(round(width * self.SCALE)))

    def line(self, points, **kwargs):
        mapped = [self._point(x, y) for x, y in zip(points[::2], points[1::2])]
        kwargs["width"] = self._width(kwargs.get("width", 1))
        self.draw.line([coordinate for point in mapped for coordinate in point], **kwargs)

    def ellipse(self, box, **kwargs):
        kwargs["width"] = self._width(kwargs.get("width", 1))
        self.draw.ellipse(self._box(box), **kwargs)

    def rounded_rectangle(self, box, radius=0, **kwargs):
        kwargs["width"] = self._width(kwargs.get("width", 1))
        self.draw.rounded_rectangle(
            self._box(box), radius=self._width(radius), **kwargs
        )

    def arc(self, box, start, end, **kwargs):
        kwargs["width"] = self._width(kwargs.get("width", 1))
        self.draw.arc(self._box(box), start, end, **kwargs)


# ==========================================
# Robot Drawing
# ==========================================

def _smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def _idle_gaze(animation_time):
    """Return a slowly changing, clearly visible idle gaze."""
    phase = animation_time % 12.0
    if 1.5 <= phase < 3.5:
        amount = _smoothstep((phase - 1.5) / 0.35)
        amount *= 1.0 - _smoothstep((phase - 3.15) / 0.35)
        return -5.0 * amount, 0.0
    if 4.0 <= phase < 6.0:
        amount = _smoothstep((phase - 4.0) / 0.35)
        amount *= 1.0 - _smoothstep((phase - 5.65) / 0.35)
        return 5.0 * amount, 0.0
    if 7.0 <= phase < 8.8:
        amount = _smoothstep((phase - 7.0) / 0.3)
        amount *= 1.0 - _smoothstep((phase - 8.5) / 0.3)
        return 0.0, -3.5 * amount
    return 0.0, 0.0


def draw_robot(draw, frame, listening_enabled=None, animation_time=None, state=None):
    """Draw the minimalist home mascot with lightweight timed expressions."""
    del frame  # The public caller still passes frame; timing is elapsed-time based.
    if animation_time is None:
        animation_time = time.monotonic()

    draw = _RobotDrawTransform(draw)
    listening = listening_enabled is True or state == "listening"
    state = state or ("listening" if listening else "idle")

    # Keep the small centered silhouette inside the original robot area.
    float_y = int(round(math.sin(animation_time * 1.15) * 1.5))
    tilt = math.sin(animation_time * 0.34) * 0.8
    center_x = int(round(160 + math.sin(animation_time * 0.32) * 1.0))
    top = 59 + float_y
    bottom = 147 + float_y
    left = center_x - 49
    right = center_x + 49

    # Antenna light pulses; listening has a brighter, steadier glow.
    pulse = (math.sin(animation_time * (1.5 if state == "thinking" else 2.0)) + 1.0) * 0.5
    if listening:
        pulse = 0.68 + pulse * 0.32
    antenna_color = (25, int(150 + 80 * pulse), int(190 + 65 * pulse))
    antenna_x = center_x + int(round(tilt * 4))
    draw.line((antenna_x, top + 1, antenna_x, top - 9), fill=CYAN, width=2)
    draw.ellipse(
        (antenna_x - 5, top - 20, antenna_x + 5, top - 10),
        fill=(16, 54, 75), outline=(54, 192, 226), width=1
    )
    draw.ellipse(
        (antenna_x - 3, top - 18, antenna_x + 3, top - 12),
        fill=antenna_color
    )

    # Simple rounded head, cyan outline, and dark face panel.
    draw.rounded_rectangle(
        (left, top, right, bottom), radius=24,
        fill=(15, 30, 48), outline=CYAN, width=2
    )
    face_left, face_right = center_x - 40, center_x + 40
    face_top, face_bottom = top + 15, bottom - 13
    draw.rounded_rectangle(
        (face_left, face_top, face_right, face_bottom), radius=18,
        fill=(5, 13, 27), outline=(22, 79, 108), width=1
    )

    # Compact illuminated side elements remain within the original footprint.
    ear_y = top + 31
    ear_color = (24, 115, 151) if listening else (20, 70, 98)
    for ear_box in (
        (left - 8, ear_y, left + 2, ear_y + 24),
        (right - 2, ear_y, right + 8, ear_y + 24),
    ):
        draw.rounded_rectangle(
            ear_box, radius=5, fill=ear_color, outline=CYAN, width=1
        )

    gaze_x, gaze_y = _idle_gaze(animation_time)
    if state == "looking_left":
        gaze_x = -5.0
    elif state == "looking_right":
        gaze_x = 5.0
    elif state == "thinking":
        gaze_y = -4.0
    if listening:
        gaze_x *= 0.35
        gaze_y = min(gaze_y, -1.0)

    blink_phase = animation_time % 5.1
    blink_amount = 0.0
    if blink_phase < 0.22:
        blink_amount = math.sin(math.pi * blink_phase / 0.22)
    wink_phase = animation_time % 17.0
    wink_amount = max(0.0, 1.0 - abs(wink_phase - 0.18) / 0.18)
    happy_phase = animation_time % 15.0
    happy = state == "happy" or (
        state == "idle" and 10.8 <= happy_phase < 12.0
    )
    wink = state in ("wink", "winking")

    eye_y = int(round(top + 43 + gaze_y))
    eye_centers = (center_x - 20, center_x + 20)
    for index, eye_x in enumerate(eye_centers):
        eye_tilt = tilt if index == 0 else -tilt
        this_blink = max(blink_amount, wink_amount if index == 0 else 0.0)
        if wink or (not listening and wink_amount > 0 and index == 0):
            this_blink = max(this_blink, 1.0)
        eye_center_y = int(round(eye_y + eye_tilt))

        if happy and this_blink < 0.7:
            draw.arc(
                (eye_x - 10, eye_center_y - 4, eye_x + 10, eye_center_y + 8),
                195, 345, fill=CYAN, width=3
            )
            continue

        eye_height = max(2, int(round(18 * (1.0 - 0.9 * this_blink))))
        eye_box = (
            eye_x - 8, eye_center_y - eye_height // 2,
            eye_x + 8, eye_center_y + eye_height // 2,
        )
        draw.ellipse(eye_box, fill=(43, 199, 244))
        if this_blink < 0.62:
            pupil_x = eye_x + int(round(gaze_x))
            pupil_y = eye_center_y + 1
            draw.ellipse(
                (pupil_x - 4, pupil_y - 5, pupil_x + 4, pupil_y + 5),
                fill=(7, 35, 56)
            )
            draw.ellipse(
                (pupil_x - 2, pupil_y - 4, pupil_x + 1, pupil_y - 1),
                fill=WHITE
            )

    # Friendly default smile; explicit speaking state opens and closes it.
    mouth_x = center_x
    mouth_y = top + 65
    if state == "speaking":
        mouth_open = 2 + int((math.sin(animation_time * 9.0) + 1.0) * 3)
        draw.ellipse(
            (mouth_x - 5, mouth_y - mouth_open, mouth_x + 5, mouth_y + mouth_open),
            fill=CYAN
        )
    else:
        smile_height = 12 if happy else 9
        draw.arc(
            (mouth_x - 12, mouth_y - 5, mouth_x + 12, mouth_y + smile_height),
            15, 165, fill=(113, 224, 250), width=2
        )

    # Listening waves pulse at the sides only while the real app flag is on.
    if listening:
        wave_height = 3 + int((math.sin(animation_time * 4.0) + 1.0) * 2)
        wave_y = ear_y + 12
        for direction in (-1, 1):
            wave_x = center_x + direction * 61
            draw.arc(
                (wave_x - 4, wave_y - wave_height,
                 wave_x + 4, wave_y + wave_height),
                270 if direction < 0 else 90,
                90 if direction < 0 else 270,
                fill=CYAN, width=2
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

    # Thin cyan rule below the header.
    draw.line(
        (12, 31, WIDTH - 12, 31),
        fill=(33, 103, 132),
        width=1
    )

    # Robot animation
    draw_robot(draw, frame, listening_enabled, time.monotonic())

    # Short greeting stack below the compact robot.
    centered_text(
        draw,
        126,
        "Hello! I'm EchoMind",
        status_font,
        CYAN
    )

    centered_text(
        draw,
        143,
        "Your AI companion",
        small_font,
        WHITE
    )

    # Divider separates the mascot from live microphone status.
    draw.line(
        (12, 159, WIDTH - 12, 159),
        fill=(33, 103, 132),
        width=1
    )

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
