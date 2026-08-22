import math
from collections import deque

import numpy as np

from src.config import (
    SAMPLE_RATE,
    BLOCK_SIZE,
    SILENCE_DURATION,
    SPEECH_START_BLOCKS,
    PREBUFFER_BLOCKS,
)


class SpeechListener:

    def __init__(self, microphone, noise_profile):
        self.microphone = microphone
        self.start_threshold = noise_profile["start_threshold"]
        self.continue_threshold = noise_profile["continue_threshold"]

    def listen(self):

        print("\n🎧 Listening...")

        recording = False
        speech_counter = 0
        silence_counter = 0

        required_silence_blocks = math.ceil(
            (SILENCE_DURATION * SAMPLE_RATE) / BLOCK_SIZE
        )

        # Stores the last 0.5 seconds of audio.
        prebuffer = deque(maxlen=PREBUFFER_BLOCKS)
        audio_buffer = []

        while True:

            audio = self.microphone.read()
            prebuffer.append(audio)

            volume = np.sqrt(np.mean(audio ** 2))

            if not recording:
                if volume >= self.start_threshold:
                    speech_counter += 1
                else:
                    speech_counter = 0

                if speech_counter >= SPEECH_START_BLOCKS:
                    recording = True
                    silence_counter = 0

                    print("🟢 Speech Started")

                    # The current block is already in the prebuffer.
                    audio_buffer.extend(prebuffer)

                continue

            # Every block belongs to an active recording.
            audio_buffer.append(audio)

            if volume >= self.continue_threshold:
                silence_counter = 0
                continue

            silence_counter += 1

            if silence_counter >= required_silence_blocks:
                print("🔴 Speech Ended")
                return np.concatenate(audio_buffer, axis=0)
