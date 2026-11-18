from PIL import Image, ImageDraw, ImageFont

# ==========================================
# EchoMind Latest Transcript Screen
# ==========================================

WIDTH = 320
HEIGHT = 240

BACKGROUND = (10, 17, 32)
CARD = (30, 48, 75)
CYAN = (48, 210, 255)
WHITE = (240, 245, 255)
MUTED = (145, 165, 190)
GREEN = (40, 220, 140)
RED = (235, 105, 105)


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
# Draw Latest Transcript Screen
# ==========================================

def draw_transcript_screen(
    display,
    transcription=None,
    listening_enabled=None
):

    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        BACKGROUND
    )

    draw = ImageDraw.Draw(image)

    header_font = load_font(16)
    label_font = load_font(11)
    heading_font = load_font(20)
    content_font = load_font(14)

    # ======================================
    # Header
    # ======================================

    draw.text(
        (13, 10),
        "ECHOMIND",
        font=header_font,
        fill=WHITE
    )

    draw.text(
        (247, 12),
        "TRANSCRIPT",
        font=label_font,
        fill=CYAN
    )

    # ======================================
    # Microphone Status Badge
    # ======================================

    if listening_enabled is not None:

        if listening_enabled:
            mic_text = "MIC: ON"
            mic_color = GREEN
        else:
            mic_text = "MIC: OFF"
            mic_color = RED

        mic_font = load_font(10)

        bbox = draw.textbbox((0, 0), mic_text, font=mic_font)
        mic_text_width = bbox[2] - bbox[0]

        badge_right = 308
        badge_left = badge_right - (mic_text_width + 16)

        draw.rounded_rectangle(
            (badge_left, 24, badge_right, 40),
            radius=8,
            fill=(22, 34, 52),
            outline=mic_color,
            width=1
        )

        draw.text(
            (badge_left + 8, 27),
            mic_text,
            font=mic_font,
            fill=mic_color
        )

    # ======================================
    # Main Transcript Card
    # ======================================

    draw.rounded_rectangle(
        (12, 43, 308, 228),
        radius=15,
        fill=CARD,
        outline=CYAN,
        width=2
    )

    # ======================================
    # Heading
    # ======================================

    centered_text(
        draw,
        61,
        "LATEST TRANSCRIPT",
        heading_font,
        CYAN
    )

    draw.line(
        (64, 92, 256, 92),
        fill=CYAN,
        width=1
    )

    # ======================================
    # Transcript Text
    # ======================================

    if transcription is None or str(transcription).strip() == "":
        transcript_text = "No transcript yet"
        text_color = MUTED
    else:
        transcript_text = str(transcription).strip()
        text_color = WHITE

    lines = wrap_text(
        draw,
        transcript_text,
        content_font,
        236
    )

    y = 108

    for line in lines:

        if y > 213:
            break

        draw.text(
            (42, y),
            line,
            font=content_font,
            fill=text_color
        )

        bbox = draw.textbbox((0, 0), line, font=content_font)
        line_height = bbox[3] - bbox[1]

        y += line_height + 6

    display.display(image)