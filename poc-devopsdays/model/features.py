"""
Pump sound features: log-mel with context. Only numpy and the standard library.

The SAME function runs at training time (model/train.py) and on the device (component/inference.py).
If you change anything here, retrain: the model only understands the features it learned with.
Single source: poc-devopsdays/model/features.py. train.py copies this file to
component/features.py and to every build/<version>/features.py.

  16-bit PCM WAV, 16 kHz (if it has several channels, the first one is used)
  → frames of 1024 samples every 512 (64 ms, Hann window)
  → power in 64 mel bands → dB
  → vectors of 5 consecutive frames = 320 numbers per vector (≈ 300 vectors in a 10 s clip)
"""
import io, struct, wave
import numpy as np

SR = 16000          # samples per second
N_FFT = 1024        # samples per frame
HOP = 512           # hop between frames
N_MELS = 64         # mel bands
FRAMES = 5          # context frames per vector
DIM = N_MELS * FRAMES
EPS = 1e-12

PARAMS = {"sr": SR, "n_fft": N_FFT, "hop": HOP, "n_mels": N_MELS, "frames": FRAMES, "dim": DIM}


def _mel_filters(sr=SR, n_fft=N_FFT, n_mels=N_MELS):
    """Triangular mel-scale filter bank (HTK formula), from 0 Hz to sr/2."""
    mel = lambda f: 2595.0 * np.log10(1.0 + f / 700.0)
    hz = lambda m: 700.0 * (10 ** (m / 2595.0) - 1.0)
    points = hz(np.linspace(0.0, mel(sr / 2), n_mels + 2))
    f = np.fft.rfftfreq(n_fft, 1.0 / sr)
    fb = np.zeros((n_mels, len(f)))
    for m in range(n_mels):
        left, center, right = points[m], points[m + 1], points[m + 2]
        rise = (f - left) / (center - left)
        fall = (right - f) / (right - center)
        fb[m] = np.maximum(0.0, np.minimum(rise, fall))
    return fb


_MEL = _mel_filters()
_WIN = np.hanning(N_FFT + 1)[:-1]          # periodic Hann


def _riff(data):
    """Minimal WAV reader for headers that `wave` rejects (WAVE_FORMAT_EXTENSIBLE)."""
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("not a WAV file")
    i, fmt, pcm = 12, None, None
    while i + 8 <= len(data):
        cid, size = data[i:i + 4], struct.unpack("<I", data[i + 4:i + 8])[0]
        if cid == b"fmt ":
            fmt = struct.unpack("<HHIIHH", data[i + 8:i + 24])
        elif cid == b"data":
            pcm = data[i + 8:i + 8 + size]
        i += 8 + size + (size & 1)
    if fmt is None or pcm is None:
        raise ValueError("WAV without 'fmt ' or 'data' chunk")
    _, ch, sr, _, _, bits = fmt
    return ch, bits // 8, sr, pcm


def read_wav(src):
    """Reads a 16-bit PCM WAV. `src`: path, bytes or open file. Returns (float32 samples in [-1, 1], sr)."""
    if isinstance(src, (bytes, bytearray)):
        data = bytes(src)
    elif hasattr(src, "read"):
        data = src.read()
    else:
        with open(src, "rb") as f:
            data = f.read()
    try:
        with wave.open(io.BytesIO(data), "rb") as w:
            ch, sw, sr = w.getnchannels(), w.getsampwidth(), w.getframerate()
            pcm = w.readframes(w.getnframes())
    except (wave.Error, EOFError):
        ch, sw, sr, pcm = _riff(data)
    if sw != 2:
        raise ValueError(f"expected 16-bit PCM, got {8 * sw}-bit")
    x = np.frombuffer(pcm[: len(pcm) // (2 * ch) * 2 * ch], dtype="<i2")
    if ch > 1:
        x = x.reshape(-1, ch)[:, 0]            # several channels: the first one
    return x.astype(np.float32) / 32768.0, sr


def logmel(x, sr=SR):
    """Matrix (frames, 64) in dB."""
    if sr != SR:
        raise ValueError(f"expected audio at {SR} Hz, got {sr} Hz")
    x = np.asarray(x, dtype=np.float64)
    if len(x) < N_FFT:
        x = np.pad(x, (0, N_FFT - len(x)))
    frames = np.lib.stride_tricks.sliding_window_view(x, N_FFT)[::HOP] * _WIN
    power = np.abs(np.fft.rfft(frames, axis=1)) ** 2
    return 10.0 * np.log10(power @ _MEL.T + EPS)


def vectors(lm, frames=FRAMES):
    """Stacks `frames` consecutive frames into one vector: (frames - 4, 320)."""
    n = lm.shape[0] - frames + 1
    if n < 1:
        return np.zeros((0, lm.shape[1] * frames), dtype=np.float32)
    return np.concatenate([lm[t:t + n] for t in range(frames)], axis=1).astype(np.float32)


def clip_features(x, sr=SR):
    """From samples to the matrix the model takes: (≈300, 320) float32."""
    return vectors(logmel(x, sr))


def wav_features(src):
    """Shortcut: from a WAV (path, bytes or file) to the matrix the model takes."""
    return clip_features(*read_wav(src))


def input_z(X, mean, std):
    """Input level: mean distance, in standard deviations, from the clip's features to the
    training fingerprint (stats.json). With training audio it stays below 1; it rises when
    the sound changes (another speed, another environment)."""
    return float(np.mean(np.abs((X - mean) / std)))
