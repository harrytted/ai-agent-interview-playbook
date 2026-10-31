"""Generate an original 4-second PCM cue, not recorded speech or synthesized TTS."""
from pathlib import Path
import math
import struct
import wave


def create(path):
    rate, seconds = 16000, 4
    frames = bytearray()
    for i in range(rate*seconds):
        t = i/rate
        # Quiet pulses make playback progress audible without pretending to be words.
        envelope = min(1, (t % 1)*20, (1-t % 1)*20)
        sample = int(5000*envelope*math.sin(2*math.pi*(440 if t < 2 else 660)*t))
        frames.extend(struct.pack("<h", sample))
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(frames)


if __name__ == "__main__":
    create(Path(__file__).parent / "assets/playback-tone.wav")
