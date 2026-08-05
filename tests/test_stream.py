from src.audio.microphone import Microphone

mic = Microphone()

mic.start()

try:
    while True:
        audio = mic.read()
        print(audio.shape)

except KeyboardInterrupt:
    mic.stop()