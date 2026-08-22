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
MIN_START_RMS = 0.00010
MIN_CONTINUE_RMS = 0.00005
START_NOISE_MULTIPLIER = 3.0
CONTINUE_NOISE_MULTIPLIER = 1.5
START_SIGMA_MULTIPLIER = 6.0
CONTINUE_SIGMA_MULTIPLIER = 3.0

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
