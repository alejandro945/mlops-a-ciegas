"""
SYNTHETIC pump set, with the same file names as MIMII DUE (pump, dev).

Only for testing the pipeline (synth → prepare_data → train → inference) without the real
data. Nothing that comes out of here is a measurement: train.py marks everything with
"synthetic": true and talk/tools/metrics.py shows it as not measured yet.

  <root>/pump/train/section_00_source_train_normal_0000_synthetic.wav
  <root>/pump/train/section_00_target_train_normal_0000_synthetic.wav
  <root>/pump/source_test/section_00_source_test_{normal,anomaly}_0000.wav
  <root>/pump/target_test/section_00_target_test_{normal,anomaly}_0000.wav
  <root>/SYNTHETIC.txt        (marker: prepare_data and train recognize it)
Each WAV also carries a «SYNTHETIC» comment in its header (LIST/INFO chunk): even if someone
zips the folder without the marker file, the audio still says it is synthetic.

The sound: rotor rotation with its harmonics, blade pass, 120 Hz motor hum, water noise and
ambient noise. Each section is a different pump. The target domain spins 12 % faster and has
a different environment. Faults: knocks, modulation or imbalance.

Usage:  python3 model/synth.py                      → data/synthetic/
        python3 model/synth.py --out /tmp/s --seconds 4
"""
import argparse, io, os, shutil, struct, sys, wave
import numpy as np

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dataset import MARKER, MARKER_FILES

SR = 16000
HERE = os.path.dirname(os.path.abspath(__file__))
POC = os.path.dirname(HERE)

# one pump per section: rotation speed (Hz), blades, harmonics, water noise band
SECTIONS = {
    "00": dict(rot=24.6, blades=5, harm=[1.0, 0.55, 0.35, 0.22, 0.12, 0.08], band=(400, 2200)),
    "01": dict(rot=29.3, blades=6, harm=[0.8, 0.70, 0.25, 0.30, 0.10, 0.10], band=(600, 3000)),
    "02": dict(rot=19.8, blades=7, harm=[1.0, 0.40, 0.45, 0.15, 0.15, 0.05], band=(300, 1800)),
}
FAULTS = ["knocks", "modulation", "imbalance"]


def colored_noise(rng, n, shape):
    """White noise filtered in frequency: shape(f) gives the amplitude per frequency."""
    spectrum = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1.0 / SR)
    y = np.fft.irfft(spectrum * shape(f), n)
    return y / (np.std(y) + 1e-12)


def clip(rng, p, domain, fault=None, seconds=10.0):
    n = int(SR * seconds)
    t = np.arange(n) / SR
    rot = p["rot"] * (1.12 if domain == "target" else 1.0) * (1 + rng.normal(0, 0.003))
    f_inst = rot * (1 + 0.002 * np.sin(2 * np.pi * 0.13 * t + rng.uniform(0, 6.3)))
    phase = 2 * np.pi * np.cumsum(f_inst) / SR

    rotor = sum(a * (1 + 0.1 * rng.standard_normal()) * np.sin((k + 1) * phase + rng.uniform(0, 6.3))
                for k, a in enumerate(p["harm"]))
    blades = 0.6 * np.sin(p["blades"] * phase) + 0.25 * np.sin(2 * p["blades"] * phase + 1.0)
    motor = 0.3 * np.sin(2 * np.pi * 120 * t) + 0.1 * np.sin(2 * np.pi * 240 * t + 0.5)
    lo, hi = p["band"]
    water = colored_noise(rng, n, lambda f: np.exp(-0.5 * ((f - (lo + hi) / 2) / ((hi - lo) / 2)) ** 2))
    water *= 1 + 0.2 * np.sin(p["blades"] * phase)
    if domain == "target":        # another environment: louder and lower
        ambient = 0.35 * colored_noise(rng, n, lambda f: np.maximum(f, 20.0) ** -0.8)
    else:
        ambient = 0.25 * colored_noise(rng, n, lambda f: 1 / np.sqrt(np.maximum(f, 20.0)))

    tonal = rotor + blades
    if fault:
        g = rng.uniform(0.7, 1.2)                     # severity
        if fault == "modulation":                     # the rotation "breathes"
            tonal = tonal * (1 + 0.5 * g * np.sin(2 * np.pi * rot / 3 * t))
        elif fault == "imbalance":                    # strong 1× and a subharmonic
            tonal = tonal + g * (1.4 * np.sin(phase) + 0.6 * np.sin(0.5 * phase))
        elif fault == "knocks":                       # knocks with a resonance at ~2.8 kHz
            m = np.arange(int(0.006 * SR))
            knock = np.exp(-m / (0.0015 * SR)) * np.sin(2 * np.pi * 2800 * m / SR)
            pulses = np.zeros(n)
            turns = np.searchsorted(phase, np.arange(2 * np.pi, phase[-1], 2 * np.pi))
            for i in turns[rng.random(len(turns)) < 0.7]:
                pulses[i] = rng.uniform(0.5, 1.0)
            water = water + 5.0 * g * np.convolve(pulses, knock)[:n]
    y = 0.05 * (tonal + motor + 0.5 * water + ambient)
    return np.clip(y, -1, 1)


def write(path, y):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((y * 32767).astype("<i2").tobytes())
    text = MARKER + b" poc-devopsdays/model/synth.py\0"
    text += b"\0" * (len(text) % 2)
    info = b"INFO" + b"ICMT" + struct.pack("<I", len(text)) + text
    data = buf.getvalue() + b"LIST" + struct.pack("<I", len(info)) + info
    data = data[:4] + struct.pack("<I", len(data) - 8) + data[8:]      # RIFF size
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(POC, "data", "synthetic"))
    ap.add_argument("--seconds", type=float, default=10.0)
    ap.add_argument("--train", type=int, default=16, help="source normal training clips per section")
    ap.add_argument("--test", type=int, default=8, help="source normal and fault test clips per section")
    ap.add_argument("--target", type=int, default=6, help="target normal and fault test clips per section")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()

    if any(os.path.isfile(os.path.join(a.out, m)) for m in MARKER_FILES):
        shutil.rmtree(a.out)              # only deletes a previous synthetic set
    elif os.path.isdir(a.out) and os.listdir(a.out):
        raise SystemExit(f"{a.out} is not empty and is not a synthetic set: pick another folder")
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, MARKER_FILES[0]), "w", encoding="utf-8") as f:
        f.write("Synthetic audio generated by poc-devopsdays/model/synth.py.\n"
                "Only for testing the pipeline. It is not MIMII DUE and it is not a measurement.\n")
    rng = np.random.default_rng(a.seed)
    root = os.path.join(a.out, "pump")
    n = 0
    for sec, p in SECTIONS.items():
        for i in range(a.train):
            write(f"{root}/train/section_{sec}_source_train_normal_{i:04d}_synthetic.wav", clip(rng, p, "source", None, a.seconds))
        for i in range(3):            # as in MIMII DUE: only three target clips for training
            write(f"{root}/train/section_{sec}_target_train_normal_{i:04d}_synthetic.wav", clip(rng, p, "target", None, a.seconds))
        for dom, k in (("source", a.test), ("target", a.target)):
            for i in range(k):
                write(f"{root}/{dom}_test/section_{sec}_{dom}_test_normal_{i:04d}.wav", clip(rng, p, dom, None, a.seconds))
                write(f"{root}/{dom}_test/section_{sec}_{dom}_test_anomaly_{i:04d}.wav", clip(rng, p, dom, FAULTS[i % 3], a.seconds))
        n += a.train + 3 + 2 * (a.test + a.target)
    print(f"{n} synthetic clips of {a.seconds:g} s in {a.out}")


if __name__ == "__main__":
    main()
