import sounddevice as sd
from scipy.io.wavfile import write

fs = 44100
seconds = 5

print("Recording... Speak into the microphone.")

audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
sd.wait()

write("test.wav", fs, audio)

print("Recording finished.")
print("Audio saved as test.wav")