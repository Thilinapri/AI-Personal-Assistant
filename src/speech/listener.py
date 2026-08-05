import numpy as np
from collections import deque

from src.config import (
    SAMPLE_RATE,
    BLOCK_SIZE,
    SILENCE_DURATION,
    SPEECH_START_BLOCKS,
    PREBUFFER_BLOCKS,
)


class SpeechListener:

    def __init__(self, microphone, threshold):
        self.microphone = microphone
        self.threshold = threshold

    def listen(self):

        print("\n🎧 Listening...")

        recording = False

        speech_counter = 0
        silence_counter = 0

        required_silence_blocks = int(
            (SILENCE_DURATION * SAMPLE_RATE) / BLOCK_SIZE
        )

        # Stores the last 0.5 seconds of audio
        prebuffer = deque(maxlen=PREBUFFER_BLOCKS)

        audio_buffer = []

        try:

            while True:

                audio = self.microphone.read()

                prebuffer.append(audio)

                volume = np.sqrt(np.mean(audio ** 2))

                # --------------------
                # Speech Detected
                # --------------------
                if volume > self.threshold:

                    speech_counter += 1

                    if not recording and speech_counter >= SPEECH_START_BLOCKS:

                        recording = True
                        silence_counter = 0

                        print("🟢 Speech Started")

                        # Include previous audio
                        audio_buffer.extend(prebuffer)

                    if recording:
                        audio_buffer.append(audio)

                # --------------------
                # Silence
                # --------------------
                else:

                    speech_counter = 0

                    if recording:

                        audio_buffer.append(audio)

                        silence_counter += 1

                        if silence_counter >= required_silence_blocks:

                            print("🔴 Speech Ended")

                            sentence = np.concatenate(audio_buffer, axis=0)

                            return sentence

        except KeyboardInterrupt:

            print("\n👋 Listener stopped.")

            return None