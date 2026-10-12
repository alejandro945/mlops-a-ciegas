"""
Features del sonido de la bomba: log-mel con contexto. Solo numpy y la librería estándar.

La MISMA función corre al entrenar (model/train.py) y en el equipo (component/inference.py).
Si cambias algo aquí, reentrena: el modelo solo entiende las features con las que aprendió.
Fuente única: poc-devopsdays/model/features.py. train.py copia este archivo a
component/features.py y a cada build/<versión>/features.py.

  WAV PCM 16 bits, 16 kHz (si trae varios canales, usa el primero)
  → tramas de 1024 muestras cada 512 (64 ms, ventana de Hann)
  → potencia en 64 bandas mel → dB
  → vectores de 5 tramas seguidas = 320 números por vector (≈ 300 vectores en un clip de 10 s)
"""
import io, struct, wave
import numpy as np

SR = 16000          # muestras por segundo
N_FFT = 1024        # muestras por trama
HOP = 512           # salto entre tramas
N_MELS = 64         # bandas mel
FRAMES = 5          # tramas de contexto por vector
DIM = N_MELS * FRAMES
EPS = 1e-12

PARAMS = {"sr": SR, "n_fft": N_FFT, "hop": HOP, "n_mels": N_MELS, "frames": FRAMES, "dim": DIM}


def _mel_filters(sr=SR, n_fft=N_FFT, n_mels=N_MELS):
    """Banco de filtros triangulares en escala mel (fórmula HTK), de 0 Hz a sr/2."""
    mel = lambda f: 2595.0 * np.log10(1.0 + f / 700.0)
    hz = lambda m: 700.0 * (10 ** (m / 2595.0) - 1.0)
    puntos = hz(np.linspace(0.0, mel(sr / 2), n_mels + 2))
    f = np.fft.rfftfreq(n_fft, 1.0 / sr)
    fb = np.zeros((n_mels, len(f)))
    for m in range(n_mels):
        izq, cen, der = puntos[m], puntos[m + 1], puntos[m + 2]
        sube = (f - izq) / (cen - izq)
        baja = (der - f) / (der - cen)
        fb[m] = np.maximum(0.0, np.minimum(sube, baja))
    return fb


_MEL = _mel_filters()
_WIN = np.hanning(N_FFT + 1)[:-1]          # Hann periódica


def _riff(data):
    """Lector mínimo de WAV para cabeceras que `wave` no acepta (WAVE_FORMAT_EXTENSIBLE)."""
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("no es un archivo WAV")
    i, fmt, pcm = 12, None, None
    while i + 8 <= len(data):
        cid, size = data[i:i + 4], struct.unpack("<I", data[i + 4:i + 8])[0]
        if cid == b"fmt ":
            fmt = struct.unpack("<HHIIHH", data[i + 8:i + 24])
        elif cid == b"data":
            pcm = data[i + 8:i + 8 + size]
        i += 8 + size + (size & 1)
    if fmt is None or pcm is None:
        raise ValueError("WAV sin 'fmt ' o sin 'data'")
    _, ch, sr, _, _, bits = fmt
    return ch, bits // 8, sr, pcm


def read_wav(src):
    """Lee un WAV PCM 16 bits. `src`: ruta, bytes o archivo abierto. Devuelve (muestras float32 en [-1, 1], sr)."""
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
        raise ValueError(f"se esperaba PCM de 16 bits y vino de {8 * sw} bits")
    x = np.frombuffer(pcm[: len(pcm) // (2 * ch) * 2 * ch], dtype="<i2")
    if ch > 1:
        x = x.reshape(-1, ch)[:, 0]            # varios canales: el primero
    return x.astype(np.float32) / 32768.0, sr


def logmel(x, sr=SR):
    """Matriz (tramas, 64) en dB."""
    if sr != SR:
        raise ValueError(f"se esperaba audio a {SR} Hz y vino a {sr} Hz")
    x = np.asarray(x, dtype=np.float64)
    if len(x) < N_FFT:
        x = np.pad(x, (0, N_FFT - len(x)))
    tramas = np.lib.stride_tricks.sliding_window_view(x, N_FFT)[::HOP] * _WIN
    potencia = np.abs(np.fft.rfft(tramas, axis=1)) ** 2
    return 10.0 * np.log10(potencia @ _MEL.T + EPS)


def vectors(lm, frames=FRAMES):
    """Pega `frames` tramas seguidas en un vector: (tramas - 4, 320)."""
    n = lm.shape[0] - frames + 1
    if n < 1:
        return np.zeros((0, lm.shape[1] * frames), dtype=np.float32)
    return np.concatenate([lm[t:t + n] for t in range(frames)], axis=1).astype(np.float32)


def clip_features(x, sr=SR):
    """De muestras a la matriz que entra al modelo: (≈300, 320) float32."""
    return vectors(logmel(x, sr))


def wav_features(src):
    """Atajo: de un WAV (ruta, bytes o archivo) a la matriz que entra al modelo."""
    return clip_features(*read_wav(src))


def input_z(X, mean, std):
    """Nivel de la entrada: distancia media, en desviaciones estándar, de las features
    del clip a la huella del entrenamiento (stats.json). Con el audio de entrenamiento queda
    por debajo de 1; sube cuando el sonido cambia (otra velocidad, otro ambiente)."""
    return float(np.mean(np.abs((X - mean) / std)))
