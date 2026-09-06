# ===========================
# Audio Settings
# ===========================

SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 512

# ===========================
# Whisper
# ===========================

WHISPER_MODEL = "base"
WHISPER_LANGUAGE = "en"
WHISPER_BEAM_SIZE = 5
WHISPER_MIN_SILENCE_MS = 500

# ===========================
# Gemini
# ===========================

ENABLE_GEMINI = False
GEMINI_MODEL = "gemini-3.6-flash"

# ===========================
# Privacy
# ===========================

# Optional semantic privacy screening.
#
# Uses EchoMind's existing shared MiniLM model.
# It does not load a second transformer model.
ENABLE_SEMANTIC_PRIVACY = True

# Optional local NER remains disabled until Raspberry Pi
# memory and latency benchmarking proves sufficient headroom.
ENABLE_LOCAL_NER = False