from src.audio.microphone import Microphone

mic = Microphone()

audio = mic.record(5)

print(audio.shape)