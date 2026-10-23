"""
The race announcer's voice: "Get ready!" and "Go!" in a raspy, playful dinosaur voice.

Made from scratch: espeak-ng speech, slowed and pitched down (a bigger throat), with a
jittery growl (amplitude flutter), a rumble an octave down and a breathy rasp, then soft
clipping. Three voices: a raspy raptor, b big friendly rex, c cheeky little dino.

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
def growl(x, f=38, depth=0.6, drive=2.5, rasp=0.25, sub=0.35, seed=1):
    t=np.arange(len(x))/SR
    # irregular flutter: jittered AM, like a throat rattle
    rng=np.random.default_rng(seed)
    jit=np.cumsum(rng.normal(0,0.04,len(x)))/SR*40
    am=1-depth*0.5*(1+np.sin(2*np.pi*f*t+jit))
    y=x*am
    # sub-octave rumble: rectify + lowpass (adds a growl an octave down)
    b,a=ss.butter(2,260/(SR/2)); rumble=ss.lfilter(b,a,np.abs(x)*np.sign(np.sin(2*np.pi*f*0.5*t)))
    y=y+sub*rumble
    # rasp: band-passed noise shaped by the voice's envelope
    n=rng.normal(0,1,len(x)).astype(np.float32)
    b,a=ss.butter(2,[1800/(SR/2),5200/(SR/2)],'band'); n=ss.lfilter(b,a,n)
    y=y+rasp*n*env(x)*3
    y=np.tanh(drive*y)/np.tanh(drive)
    return y
def finish(y, name, gain=0.9):
    # tidy: high-pass rumble below 70 Hz, fade edges, normalise
    b,a=ss.butter(2,70/(SR/2),'high'); y=ss.lfilter(b,a,y)
    nz=np.where(np.abs(y)>0.01)[0]; y=y[max(0,nz[0]-200):nz[-1]+2000]
    f=int(SR*0.01); y[:f]*=np.linspace(0,1,f); y[-f*4:]*=np.linspace(1,0,f*4)
    y=y/np.max(np.abs(y))*gain
    wf.write(name, SR, (y*32767).astype(np.int16)); return y
V = {
 "a": dict(voice="en-us+croak", pitch=30, ready_speed=150, go_speed=120, fac=0.82, gr=dict(f=36, depth=0.55, drive=2.8, rasp=0.3, sub=0.3)),
 "b": dict(voice="en-us+m3", pitch=20, ready_speed=135, go_speed=110, fac=0.68, gr=dict(f=28, depth=0.5, drive=2.2, rasp=0.18, sub=0.55)),
 "c": dict(voice="en-us+m7", pitch=75, ready_speed=175, go_speed=150, fac=0.95, gr=dict(f=52, depth=0.45, drive=3.2, rasp=0.35, sub=0.15)),
}
os.makedirs(OUT, exist_ok=True)
for k, v in V.items():
    r = growl(stretch_pitch(say("Get ready!", v["voice"], v["pitch"], v["ready_speed"]), v["fac"]), **v["gr"], seed=1)
    g = growl(stretch_pitch(say("Goooh!", v["voice"], v["pitch"] + 25, v["go_speed"]), v["fac"]), **v["gr"], seed=2)
    for word, y in (("ready", r), ("go", g)):
        wav = os.path.join(tempfile.gettempdir(), f"kp_{k}_{word}.wav")
        finish(y, wav)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", wav, "-ac", "1", "-b:a", "64k", f"{OUT}/{k}_{word}.mp3"], check=True)
    print(k, "done")
