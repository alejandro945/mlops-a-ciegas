#!/usr/bin/env python3
"""
Da formato a los eventos de /estacion/eventos (un JSON por clip escuchado).
Lo usa demo/watch.sh:  aws logs tail ... | python3 formato_eventos.py [bomba]

  bomba-03  v1.0.0  ALERTA  score 0,82 (umbral 0,50)  entrada 1,1  4 ms  · llegó 40 s tarde

· "llegó N s tarde": arrived_ts (cuando llegó a la nube) menos ts (cuando decidió la bomba)
  pasa de 10 s. Es el tiempo que la bomba estuvo sin red.
· "falla no oída": la bomba sonaba con falla (truth, que solo existe en la demo) y no avisó.
"""
import json
import sys
import time

TARDE_S = 10          # a partir de cuántos segundos de retraso se avisa

NEGRITA, ROJO, VERDE, NARANJA, GRIS, FIN = (
    "\033[1m", "\033[1;38;5;196m", "\033[38;5;71m", "\033[38;5;208m", "\033[2m", "\033[0m")


def num(x, dec):
    """Número con coma decimal, como se dice en voz alta."""
    return f"{x:.{dec}f}".replace(".", ",")


def formatear(e, color=True):
    """Una línea de texto para un evento (dict). Devuelve None si no es un evento de la estación."""
    if "device" not in e or "score" not in e:
        return None
    c = (lambda codigo, texto: f"{codigo}{texto}{FIN}") if color else (lambda codigo, texto: texto)

    score, umbral = float(e["score"]), float(e.get("threshold", 0.0))
    dec = 2 if max(score, umbral) >= 0.1 else 4          # los scores chicos necesitan más decimales
    alerta = bool(e.get("alert"))
    ms = float(e.get("latency_ms", 0.0))
    latencia = "<1 ms" if ms < 1 else f"{ms:.0f} ms"

    estado = c(ROJO, "ALERTA") if alerta else c(VERDE, "normal")
    linea = (f"{e['device']}  v{e.get('model_version', '?')}  {estado}"
             f"  score {num(score, dec)} (umbral {num(umbral, dec)})"
             f"  entrada {num(float(e.get('input_z') or 0.0), 1)}  {latencia}")

    tarde = (float(e.get("arrived_ts", 0)) - float(e.get("ts", 0))) / 1000
    if e.get("arrived_ts") and e.get("ts") and tarde > TARDE_S:
        linea += "  " + c(NARANJA, f"· llegó {tarde:.0f} s tarde")
    if e.get("truth") == "anomaly" and not alerta:
        linea += "  " + c(ROJO, "· falla no oída")

    cuando = e.get("arrived_ts") or e.get("ts")
    hora = time.strftime("%H:%M:%S", time.localtime(cuando / 1000)) if cuando else "--:--:--"
    return c(GRIS, hora) + "  " + linea


def main(argv):
    solo = argv[1] if len(argv) > 1 else None
    for crudo in sys.stdin:
        try:
            e = json.loads(crudo[crudo.index("{"):])      # `aws logs tail` antepone la hora
        except ValueError:
            continue
        if solo and e.get("device") != solo:
            continue
        linea = formatear(e)
        if linea:
            print(linea, flush=True)


if __name__ == "__main__":
    main(sys.argv)
