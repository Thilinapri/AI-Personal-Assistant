# src/config.py


# ===========================
# Audio Settings
# ===========================

SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 512


# ===========================
# Speech-to-Text Settings
# ===========================

STT_LANGUAGE = "en"
STT_MODEL = "universal-3-5-pro"


# ===========================
# Gemini Settings
# ===========================

# Keep Gemini disabled during development/testing.
# The API key can remain safely inside .env.
ENABLE_GEMINI = False

GEMINI_MODEL = "gemini-3.6-flash"


# ===========================
# Privacy
# ===========================

# Master switch for the complete Privacy Gateway.
#
# True:
# Transcript
# -> Context Selector
# -> Privacy Gateway
# -> Gemini
#
# False:
# Transcript
# -> Context Selector
# -> Gemini
#
# Context relevance selection remains active
# even when the Privacy Gateway is disabled.
ENABLE_PRIVACY_GATEWAY = False


# Optional semantic privacy screening.
#
# Used only when ENABLE_PRIVACY_GATEWAY is True.
#
# Uses EchoMind's existing shared MiniLM model.
# It does not load a second transformer model.
ENABLE_SEMANTIC_PRIVACY = False


# Optional local NER remains disabled until
# Raspberry Pi memory and latency benchmarking
# proves sufficient headroom.
ENABLE_LOCAL_NER = False


# ===========================
# Memory Retrieval
# ===========================

MEMORY_SEARCH_MIN_SCORE = 0.15