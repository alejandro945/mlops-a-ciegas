"""
The numbers behind the Tech Day Cali figures, in one small file (data.json, committed).

  · the October 18 rehearsal on AWS: the formatted events (evidencia-e2e/<date>/watch.txt, out of
    the repo because the folder holds the account id; the lines themselves do not)
  · the shadow: v1.0.0 decides and v2.0.0 runs in shadow on pump-01's real fault and normal clips,
    with the same component the pumps run (component/inference.py --local)

Usage:  poc-devopsdays/.venv/bin/python talk/tools/cali/extract.py [evidencia-e2e/2026-10-18]
"""
import json, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
POC = os.path.join(REPO, "poc-devopsdays")
EV = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "evidencia-e2e", "2026-10-18")

LINE = re.compile(r"^(\d\d:\d\d:\d\d)\s+(pump-\d\d)\s+v(\S+)\s+(ALERT|normal)\s+score ([\d.]+) \(threshold ([\d.]+)\)"
                  r"\s+input ([\d.]+)\s+\S+ ms(?:\s+· arrived (\d+) s late)?")


def events():
    out = []
    for raw in open(os.path.join(EV, "watch.txt"), encoding="utf-8"):
        m = LINE.match(raw.strip())
        if m:
            t, dev, ver, dec, score, thr, inp, late = m.groups()
            out.append({"t": t, "device": dev, "version": ver, "alert": dec == "ALERT", "score": float(score),
                        "threshold": float(thr), "input": float(inp), "late": int(late) if late else 0})
    return out


def shadow(mode, n=40):
    """v1.0.0 decides, v2.0.0 in shadow, on pump-01's clips of one folder."""
    b = os.path.join(POC, "build")
    with tempfile.TemporaryDirectory() as tmp:
        mf = os.path.join(tmp, "mode")
        open(mf, "w").write(mode + "\n")
        r = subprocess.run([sys.executable, os.path.join(POC, "component", "inference.py"),
                            "--model", f"{b}/1.0.0/model.onnx", "--stats", f"{b}/1.0.0/stats.json",
                            "--shadow-model", f"{b}/2.0.0/model.onnx", "--shadow-stats", f"{b}/2.0.0/stats.json",
                            "--audio-root", os.path.join(POC, "data", "station"), "--mode-file", mf,
                            "--interval", "0", "--local", "--max", str(n)],
                           capture_output=True, text=True, check=True,
                           env=dict(os.environ, AWS_IOT_THING_NAME="pump-01"))
    evs = [json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")]
    return [{"v1": e["alert"], "v2": e["shadow_alert"], "score": e["score"], "shadow_score": e["shadow_score"]}
            for e in evs]


def main():
    ev = events()
    p3 = [e for e in ev if e["device"] == "pump-03"]
    act1 = [e for e in p3 if "19:58:00" <= e["t"] <= "19:59:00"]
    late = [e["late"] for e in ev if e["late"]]
    off = ("19:59:26", "20:00:11")
    during = [e for e in ev if off[0] < e["t"] < off[1]]
    p5 = [e for e in ev if e["device"] == "pump-05" and "19:59:30" <= e["t"] <= "20:03:00"]
    data = {
        "source": "October 18, 2026 rehearsal on AWS (us-east-1), real MIMII DUE audio; times in Bogotá",
        "threshold": act1[0]["threshold"],
        "act1": [{"t": e["t"], "score": e["score"], "alert": e["alert"]} for e in act1],
        "act2": {
            "offline": list(off),
            "late_seconds": late,
            "during": {d: sum(1 for e in during if e["device"] == d) for d in sorted({e["device"] for e in ev})},
            "pump05": [{"t": e["t"], "input": e["input"], "alert": e["alert"]} for e in p5],
            # every event around the cut, by arrival time (what the cloud saw)
            "window": [{"t": e["t"], "device": e["device"], "late": e["late"], "alert": e["alert"]}
                       for e in ev if "19:59:00" <= e["t"] <= "20:00:40"],
        },
        "shadow": {"fault": shadow("fault"), "normal": shadow("normal"),
                   "note": "measured with component/inference.py --local on pump-01's clips; v1.0.0 decides, v2.0.0 in shadow"},
    }
    out = os.path.join(HERE, "data.json")
    json.dump(data, open(out, "w"), ensure_ascii=False, indent=1)
    f = data["shadow"]["fault"]
    print(f"✔ {out}: act1 {len(act1)} clips · {len(late)} late events · pump-05 {len(p5)} · "
          f"shadow on the fault: v1 {sum(x['v1'] for x in f)}/{len(f)}, v2 {sum(x['v2'] for x in f)}/{len(f)}")


if __name__ == "__main__":
    main()
