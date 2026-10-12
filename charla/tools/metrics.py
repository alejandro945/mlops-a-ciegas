"""
Las cifras medidas del modelo de la bomba, listas para las láminas.

Fuente única: poc-devopsdays/build/metrics.json (lo escribe poc-devopsdays/model/train.py).
Si el archivo no existe, o viene de audio sintético ("synthetic": true), toda cifra sale
como "por medir": ningún número inventado o sintético llega a una lámina.

Uso:
    from metrics import fmt, ready
    fmt("v1.recall_source")   # "92 %"   o "por medir"
    ready()                   # True solo si hay medición real

En deck.src.html y en el guion se escribe {{M:v1.recall_source}}; build_deck.py lo reemplaza.

Claves (contrato con poc-devopsdays/model/train.py):
    dataset                      texto, p. ej. "MIMII DUE · pump · dev"
    synthetic                    bool
    machine                      "pump" (si falta o es otra máquina, no hay cifras)
    v1.auc_source  v1.auc_target                     AUC (0–1) en el dominio de entrenamiento y en el nuevo
    v1.recall_source  v1.recall_target               fallas detectadas al umbral (0–1)
    v1.false_alarm_source  v1.false_alarm_target     clips normales marcados como falla (0–1)
    v1.threshold                                     umbral del score
    v2.auc_source  v2.recall_source  v2.false_alarm_source   la v2 contaminada, con fallas que no vio al entrenar
    v2.alert_rate_source  v1.alert_rate_source       fracción de clips con alerta (0–1)
    int8.size_fp32_kb  int8.size_int8_kb             tamaño del .onnx
    int8.lat_fp32_ms  int8.lat_int8_ms               latencia por clip en CPU, mediana
    int8.agree_pct                                   clips con la misma decisión FP32 e INT8 (0–1)
    int8.auc_delta                                   AUC INT8 menos AUC FP32
    input.z_source  input.z_target                   nivel de la entrada (distancia media a la huella)
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
PATH = os.environ.get("METRICS_JSON", os.path.join(REPO, "poc-devopsdays", "build", "metrics.json"))
PENDING = "por medir"   # sin ⟨⟩ ni U+00A0: Carlito no los trae

_cache = None


def load():
    global _cache
    if _cache is None:
        try:
            _cache = json.load(open(PATH, encoding="utf-8"))
        except (OSError, ValueError):
            _cache = {}
    return _cache


def ready():
    """Solo hay cifras si la medición es real y de bombas confirmadas (no sintética, no de otra máquina)."""
    m = load()
    return bool(m) and not m.get("synthetic", True) and m.get("machine") == "pump"


def raw(key):
    """Valor crudo (o None). Las claves con punto bajan por el JSON: 'v1.auc_source'."""
    if not ready():
        return None
    v = load()
    for part in key.split("."):
        if not isinstance(v, dict) or part not in v:
            return None
        v = v[part]
    return v


def _num(x, dec):
    s = f"{x:,.{dec}f}"                          # 1,234.5
    return s.replace(",", " ").replace(".", ",")   # 1 234,5 (espacio fino, coma decimal)


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
    print("medición real:", ready(), "·", PATH)
    for k in sys.argv[1:]:
        print(k, "→", fmt(k))
