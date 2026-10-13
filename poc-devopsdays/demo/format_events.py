#!/usr/bin/env python3
"""
Formats the events in /station/events (one JSON per clip heard).
Used by demo/watch.sh:  aws logs tail ... | python3 format_events.py [pump]

  pump-03  v1.0.0  ALERT  score 0.82 (threshold 0.50)  input 1.1  4 ms  · arrived 40 s late

· "arrived N s late": arrived_ts (when it reached the cloud) minus ts (when the pump decided)
  is over 10 s. That is the time the pump was offline.
· "missed fault": the pump sounded faulty (truth, which only exists in the demo) and did not alert.
"""
import json
import sys
import time

LATE_S = 10          # how many seconds of delay before it is flagged

BOLD, RED, GREEN, ORANGE, GREY, RESET = (
    "\033[1m", "\033[1;38;5;196m", "\033[38;5;71m", "\033[38;5;208m", "\033[2m", "\033[0m")


def num(x, dec):
    """Number with a dot decimal separator."""
    return f"{x:.{dec}f}"


def format_event(e, color=True):
    """One line of text for an event (dict). Returns None if it is not a station event."""
    if "device" not in e or "score" not in e:
        return None
    c = (lambda code, text: f"{code}{text}{RESET}") if color else (lambda code, text: text)

    score, threshold = float(e["score"]), float(e.get("threshold", 0.0))
    dec = 2 if max(score, threshold) >= 0.1 else 4          # small scores need more decimals
    alert = bool(e.get("alert"))
    ms = float(e.get("latency_ms", 0.0))
    latency = "<1 ms" if ms < 1 else f"{ms:.0f} ms"

    decision = c(RED, "ALERT") if alert else c(GREEN, "normal")
    line = (f"{e['device']}  v{e.get('model_version', '?')}  {decision}"
            f"  score {num(score, dec)} (threshold {num(threshold, dec)})"
            f"  input {num(float(e.get('input_z') or 0.0), 1)}  {latency}")

    late = (float(e.get("arrived_ts", 0)) - float(e.get("ts", 0))) / 1000
    if e.get("arrived_ts") and e.get("ts") and late > LATE_S:
        line += "  " + c(ORANGE, f"· arrived {late:.0f} s late")
    if e.get("truth") == "anomaly" and not alert:
        line += "  " + c(RED, "· missed fault")

    when = e.get("arrived_ts") or e.get("ts")
    clock = time.strftime("%H:%M:%S", time.localtime(when / 1000)) if when else "--:--:--"
    return c(GREY, clock) + "  " + line


def main(argv):
    only = argv[1] if len(argv) > 1 else None
    for raw in sys.stdin:
        try:
            e = json.loads(raw[raw.index("{"):])      # `aws logs tail` prepends the time
        except ValueError:
            continue
        if only and e.get("device") != only:
            continue
        line = format_event(e)
        if line:
            print(line, flush=True)


if __name__ == "__main__":
    main(sys.argv)
