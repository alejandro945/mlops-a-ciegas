"""
The pump model's measured numbers, ready for the slides.

Single source: poc-devopsdays/build/metrics.json (written by poc-devopsdays/model/train.py).
If the file does not exist, or comes from synthetic audio ("synthetic": true), every number
shows as "por medir": no made-up or synthetic number ever reaches a slide.

Usage:
    from metrics import fmt, ready
    fmt("v1.recall_source")   # "92 %"   or "por medir"
    ready()                   # True only with a real measurement

deck.src.html and the speaker script use {{M:v1.recall_source}}; build_deck.py replaces it.
Formatting follows the slides (Spanish): comma decimals, thin-space thousands, "por medir".

Keys (contract with poc-devopsdays/model/train.py):
    dataset                      text, e.g. "MIMII DUE · pump · dev"
    synthetic                    bool
    machine                      "pump" (missing or another machine: no numbers)
    v1.auc_source  v1.auc_target                     AUC (0–1) in the training domain and in the new one
    v1.recall_source  v1.recall_target               faults detected at the threshold (0–1)
    v1.false_alarm_source  v1.false_alarm_target     normal clips flagged as faults (0–1)
    v1.threshold                                     score threshold
    v2.auc_source  v2.recall_source  v2.false_alarm_source   the contaminated v2, with faults it did not see in training
    v2.alert_rate_source  v1.alert_rate_source       fraction of clips with an alert (0–1)
    int8.size_fp32_kb  int8.size_int8_kb             .onnx size
    int8.lat_fp32_ms  int8.lat_int8_ms               per-clip CPU latency, median
    int8.agree_pct                                   clips with the same FP32 and INT8 decision (0–1)
    int8.auc_delta                                   INT8 AUC minus FP32 AUC
    input.z_source  input.z_target                   input level (mean distance to the fingerprint)
    details.*                                        training details (old name: "detalle", still accepted)
    device.lat_fp32_ms  device.lat_int8_ms           per-clip latency on the demo's device (build/device_bench.json,
    device.agree_pct  device.machine  …              written by poc-devopsdays/model/bench_device.py on the pump host)
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
PATH = os.environ.get("METRICS_JSON", os.path.join(REPO, "poc-devopsdays", "build", "metrics.json"))
DEVICE = os.environ.get("DEVICE_BENCH_JSON", os.path.join(os.path.dirname(PATH), "device_bench.json"))
PENDING = "por medir"   # slide text; no ⟨⟩ nor U+00A0: Carlito does not have them

# Old Spanish key → new English key (metrics.json written before the English refactor).
_LEGACY = {"detalle": "details"}

_cache = None


def load():
    global _cache
    if _cache is None:
        try:
            _cache = json.load(open(PATH, encoding="utf-8"))
        except (OSError, ValueError):
            _cache = {}
        for old, new in _LEGACY.items():
            if old in _cache and new not in _cache:
                _cache[new] = _cache.pop(old)
        try:                                   # measured on the device itself: "measure on the chip"
            _cache.setdefault("device", json.load(open(DEVICE, encoding="utf-8")))
        except (OSError, ValueError):
            pass
    return _cache


def ready():
    """Numbers only with a real measurement of confirmed pumps (not synthetic, not another machine)."""
    m = load()
    return bool(m) and not m.get("synthetic", True) and m.get("machine") == "pump"


def raw(key):
    """Raw value (or None). Dotted keys walk down the JSON: 'v1.auc_source'."""
    if not ready():
        return None
    v = load()
    parts = key.split(".")
    parts[0] = _LEGACY.get(parts[0], parts[0])
    for part in parts:
        if not isinstance(v, dict) or part not in v:
            return None
        v = v[part]
    return v


def details():
    """The training details block ('details', or the old 'detalle'); {} when missing."""
    return load().get("details") or {}


def _num(x, dec):
    s = f"{x:,.{dec}f}"                            # 1,234.5
    return s.replace(",", " ").replace(".", ",")   # 1 234,5 (thin space, comma decimal: slide text)


def fmt(key):
    v = raw(key)
    if v is None:
        return PENDING
    if isinstance(v, str):
        return v
    leaf = key.split(".")[-1]
    if leaf.startswith(("recall", "false_alarm", "alert_rate")) or leaf.endswith("_pct"):
        return f"{_num(100 * v, 0)} %"
    if leaf.startswith("auc"):
        return _num(v, 2) if leaf != "auc_delta" else ("+" if v >= 0 else "−") + _num(abs(v), 3)
    if leaf.endswith("_kb"):
        return f"{_num(v, 0)} KB"
    if leaf.endswith("_ms"):
        return f"{_num(v, 1)} ms"
    if leaf.startswith(("z_", "threshold")):
        return _num(v, 2)
    return _num(v, 2) if isinstance(v, float) else str(v)


if __name__ == "__main__":
    import sys
    print("real measurement:", ready(), "·", PATH)
    for k in sys.argv[1:]:
        print(k, "→", fmt(k))
