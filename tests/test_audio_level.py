import numpy as np
from src.audio.microphone import Microphone

mic = Microphone()
mic.start()

print("Speak into the microphone...")
print("Press Ctrl+C to stop.\n")

try:
    while True:
        audio = mic.read()

        # Calculate volume (Root Mean Square)
        volume = np.sqrt(np.mean(audio ** 2))

        print(f"Volume: {volume:.5f}")

except KeyboardInterrupt:
    mic.stop()