# ===========================
# Audio Settings
# ===========================

SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 512

# ===========================
# Noise Calibration
# ===========================

CALIBRATION_DURATION = 2.0      # seconds
NOISE_MARGIN = 0.004            # added to measured background noise

# Speech Detection
SILENCE_DURATION = 1.0
SPEECH_START_BLOCKS = 3

# ===========================
# Whisper
# ===========================

WHISPER_MODEL = "base"

# Circular Buffer
PREBUFFER_BLOCKS = 16

GEMINI_MODEL = "gemini-3.6-flash"