"""
The race announcer's voice: "Get ready!" and "Go!" in a friendly, playful voice.

Made from scratch: espeak-ng speech, slowed and pitched down a little, softened. No
growl or rasp. Three voices: a friendly dino, b a big gentle one, c a bright little one.

Needs espeak-ng, ffmpeg, numpy and scipy. Run from the repo root:

    python3 tools/voice/make_announcer.py

It writes public/audio/voice/<voice>_ready.mp3 and <voice>_go.mp3.
"""
import os, tempfile
import subprocess, numpy as np, scipy.io.wavfile as wf, scipy.signal as ss
SR = 44100
TMP = os.path.join(tempfile.gettempdir(), "kp_announcer.wav")
OUT = "public/audio/voice"
def say(text, voice, pitch, speed, amp=180):
    subprocess.run(["espeak-ng","-v",voice,"-p",str(pitch),"-s",str(speed),"-a",str(amp),"-w",TMP,text],check=True)
    sr, x = wf.read(TMP); x = x.astype(np.float32)/32768
    if x.ndim>1: x=x.mean(1)
    return ss.resample_poly(x, SR, sr).astype(np.float32)
def stretch_pitch(x, factor):
    # play slower: pitch and formants down by `factor` (<1), longer
    n = int(len(x)/factor)
    return ss.resample(x, n).astype(np.float32)
def env(x, ms=12):
    k=int(SR*ms/1000); a=np.abs(x); return np.convolve(a, np.ones(k)/k, 'same')
def finish(y, name, gain=0.9):
    # tidy: high-pass rumble below 70 Hz, fade edges, normalise
    b,a=ss.butter(2,70/(SR/2),'high'); y=ss.lfilter(b,a,y)
    nz=np.where(np.abs(y)>0.01)[0]; y=y[max(0,nz[0]-200):nz[-1]+2000]
    f=int(SR*0.01); y[:f]*=np.linspace(0,1,f); y[-f*4:]*=np.linspace(1,0,f*4)
    y=y/np.max(np.abs(y))*gain
    wf.write(name, SR, (y*32767).astype(np.int16)); return y
def clean(x, cutoff=6000):
    """No growl, no rasp, no distortion: just soften espeak's buzz a little."""
    b, a = ss.butter(2, cutoff / (SR / 2))
    return ss.lfilter(b, a, x).astype(np.float32)


# Voices: a friendly dino (a touch deeper than a person), b a big gentle one (deeper),
# c a bright little one (higher). Clean, no rasp (Blake found the raspy ones horrifying).
V = {
    "a": dict(voice="en-us+m3", pitch=45, ready_speed=165, go_speed=140, fac=0.9),
    "b": dict(voice="en-us+m1", pitch=30, ready_speed=150, go_speed=125, fac=0.8),
    "c": dict(voice="en-us+f3", pitch=60, ready_speed=180, go_speed=150, fac=1.0),
}
os.makedirs(OUT, exist_ok=True)
for k, v in V.items():
    r = clean(stretch_pitch(say("Get ready!", v["voice"], v["pitch"], v["ready_speed"]), v["fac"]))
    g = clean(stretch_pitch(say("Go!", v["voice"], v["pitch"] + 20, v["go_speed"]), v["fac"]))
    for word, y in (("ready", r), ("go", g)):
        wav = os.path.join(tempfile.gettempdir(), f"kp_{k}_{word}.wav")
        finish(y, wav)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", wav, "-ac", "1", "-b:a", "64k", f"{OUT}/{k}_{word}.mp3"], check=True)
    print(k, "done")
