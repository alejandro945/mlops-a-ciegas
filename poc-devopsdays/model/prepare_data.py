"""
Builds the fleet audio from MIMII DUE (or from the synthetic set).

  data/station/pump-0N/normal/    normal test clips, source domain
  data/station/pump-0N/fault/     fault test clips, source domain
  data/station/pump-0N/shifted/   normal test clips, target domain (another speed)
  build/clips.json                which clip ended up in each pump

Only uses TEST clips, never training ones, and never the ones that contaminated v2 (the
split is the one in dataset.py, the same as train.py). Five pumps come from three sections:
pump-01 and pump-04 share section 00, pump-02 and pump-05 section 01, with different clips.

With real data it also copies two clips from pump-03's section (source domain) that are
neither in the fleet nor in training: talk/assets/audio/pump-a.wav (normal) and
pump-b.wav (fault). With synthetic audio it does not touch talk/assets.

--scores build/scores.csv (after train.py) picks clips so the demo is repeatable: faults that
v1 detects (on pump-01, also faults that v2 misses) and normal clips without an alert.
The talk's numbers come from the whole test set (metrics.json), not from these clips.

Usage:  python3 model/prepare_data.py --data data/dev_data_pump.zip [--scores build/scores.csv]
        python3 model/prepare_data.py --data data/synthetic
"""
import sys
sys.dont_write_bytecode = True
import argparse, csv, glob, json, os, shutil
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
POC = os.path.dirname(HERE)
REPO = os.path.dirname(POC)
sys.path.insert(0, HERE)
import dataset as D

# fleet folder (= demo mode) → (domain, truth) of its clips
FOLDERS = {"normal": ("source", "normal"), "fault": ("source", "anomaly"), "shifted": ("target", "normal")}


def threshold(build, version):
    try:
        return json.load(open(os.path.join(build, version, "stats.json")))["threshold"]
    except (OSError, ValueError, KeyError):
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(POC, "data", "dev_data_pump.zip"))
    ap.add_argument("--synthetic", action="store_true", help="treat the data as synthetic")
    ap.add_argument("--out", default=os.path.join(POC, "data", "station"))
    ap.add_argument("--build", default=os.path.join(POC, "build"))
    ap.add_argument("--talk", default=os.path.join(REPO, "talk", "assets", "audio"))
    ap.add_argument("--per-folder", type=int, default=5, help="clips per folder and per pump")
    ap.add_argument("--scores", default="", help="scores.csv from train.py to pick repeatable clips")
    ap.add_argument("--contaminate", type=float, default=0.5, help="the same value you used in train.py")
    ap.add_argument("--seed", type=int, default=D.SEED)
    a = ap.parse_args()

    source = D.Source(a.data)
    synthetic = bool(a.synthetic or source.synthetic)
    rep = D.split(source, contaminate=a.contaminate, seed=a.seed)
    pumps = D.pump_sections(source.sections())
    rng = np.random.default_rng(a.seed + 1)

    # optional scores (from train.py): to prefer clips where the demo looks the same every time
    sc, u1, u2 = {}, threshold(a.build, "1.0.0"), threshold(a.build, "2.0.0")
    if a.scores:
        sc = {r["clip"]: r for r in csv.DictReader(open(a.scores, encoding="utf-8"))}
        if u1 is None or u2 is None:
            raise SystemExit("--scores needs build/1.0.0/stats.json and build/2.0.0/stats.json (run train.py)")
        if not all(c["id"] in sc for c in rep["test"]):
            raise SystemExit(f"{a.scores} does not match this data: run train.py with the same --data")
        if json.load(open(os.path.join(a.build, "1.0.0", "stats.json"))).get("synthetic") != synthetic:
            raise SystemExit("the models in build/ and this data are not of the same kind (real vs synthetic)")
    alert = lambda c, v, u: c["id"] in sc and float(sc[c["id"]][v]) > u

    def preference(c, folder, pump):
        """Lower is better. Without scores everything ties and chance decides."""
        if not sc or folder == "shifted":
            return 0
        canary = pump == D.CANARY
        if folder == "fault":
            return (not alert(c, "v1", u1)) * 2 + (canary and alert(c, "v2", u2))
        return alert(c, "v1", u1) * 2 + (canary and alert(c, "v2", u2))

    free = {}   # (section, folder) → available test clips
    for c in rep["test"]:
        for folder, (dom, truth) in FOLDERS.items():
            if c["domain"] == dom and c["truth"] == truth:
                free.setdefault((c["section"], folder), []).append(c)
    for k in free:
        free[k] = [free[k][i] for i in rng.permutation(len(free[k]))]

    # 1 · the two talk audio clips (pump-03's section, source domain), outside the fleet
    talk_section = pumps[D.SCENARIO]
    talk = {}
    for name, folder in (("pump-a", "normal"), ("pump-b", "fault")):
        pool = free.get((talk_section, folder), [])
        if not pool:
            continue
        if sc and all(c["id"] in sc for c in pool):
            v = lambda c: float(sc[c["id"]]["v1"])
            if folder == "fault":    # the clearest fault that v1 detects
                chosen = max(pool, key=v)
            else:                    # a typical normal clip, without an alert
                quiet = [c for c in pool if v(c) <= u1] or pool
                med = float(np.median([v(c) for c in quiet]))
                chosen = min(quiet, key=lambda c: abs(v(c) - med))
        else:
            chosen = pool[0]
        pool.remove(chosen)
        talk[name] = chosen

    # 2 · the fleet: pump-01 picks first (it has the most conditions)
    order = sorted(pumps, key=lambda p: (p != D.CANARY, p))
    per_section = {s: sum(1 for p in pumps if pumps[p] == s) for s in set(pumps.values())}
    fleet = {p: {"section": pumps[p]} for p in sorted(pumps)}
    for p in order:
        sec = pumps[p]
        for folder in FOLDERS:
            pool = free.get((sec, folder), [])
            k = min(a.per_folder, max(1, len(pool) // max(1, per_section[sec]))) if pool else 0
            pool.sort(key=lambda c: preference(c, folder, p))     # stable sort: chance breaks ties
            chosen, free[(sec, folder)] = pool[:k], pool[k:]
            fleet[p][folder] = chosen
            if sc and folder != "shifted":
                bad = sum(1 for c in chosen if preference(c, folder, p))
                if bad:
                    print(f"  warning: {p}/{folder}: {bad} of {k} clips do not meet the preference (not enough clips)")
            if not chosen:
                print(f"  warning: {p}/{folder} is empty")
        per_section[sec] -= 1

    # 3 · copy, readable by everyone: in the container the component runs as another user
    for old in glob.glob(os.path.join(a.out, "pump-*", "*", "*.wav")):
        os.remove(old)
    for p, info in fleet.items():
        for folder in FOLDERS:
            d = os.path.join(a.out, p, folder)
            os.makedirs(d, exist_ok=True)
            for c in info[folder]:
                path = os.path.join(d, c["id"] + ".wav")
                with open(path, "wb") as f:
                    f.write(source.read(c))
                os.chmod(path, 0o644)
            os.chmod(d, 0o755)
        os.chmod(os.path.join(a.out, p), 0o755)
    os.chmod(a.out, 0o755)

    copied = []
    if not synthetic and source.machine == "pump" and talk:   # only confirmed pumps reach the talk
        os.makedirs(a.talk, exist_ok=True)
        for name, c in talk.items():
            wav = source.read(c)
            if D.is_synthetic(wav):         # double check: never synthetic audio in the talk
                raise SystemExit(f"{c['id']} is synthetic: not copying it to {a.talk}")
            with open(os.path.join(a.talk, name + ".wav"), "wb") as f:
                f.write(wav)
            copied.append(f"{name}.wav = {c['id']}")
        with open(os.path.join(a.talk, "ATTRIBUTION.txt"), "w", encoding="utf-8") as f:
            f.write("Real industrial pump sounds: MIMII DUE (Hitachi, Ltd.), development set, pump.\n"
                    "License CC BY-NC-SA 4.0 · https://zenodo.org/records/4740355\n"
                    "Tanabe et al., 2021, «MIMII DUE: Sound Dataset for Malfunctioning Industrial Machine\n"
                    "Investigation and Inspection with Domain Shifts due to Changes in Operational and\n"
                    "Environmental Conditions», arXiv:2105.02702.\n"
                    "Copied unchanged by poc-devopsdays/model/prepare_data.py:\n"
                    + "".join(f"  {x}\n" for x in copied))

    info = {
        "dataset": ("synthetic (MIMII DUE structure · pump)" if synthetic else
                    f"MIMII DUE · {source.machine or 'unconfirmed machine'} · dev"),
        "synthetic": synthetic,
        "data": a.data,
        "curated_with_scores": bool(sc),
        "contaminated_section": rep["contaminated_section"],
        "contamination": [c["id"] for c in rep["contamination"]],
        "talk": {n: {"clip": c["id"], "section": c["section"], "copied": not synthetic} for n, c in talk.items()},
        "pumps": {p: {"section": v["section"], **{k: [c["id"] for c in v[k]] for k in FOLDERS}}
                  for p, v in fleet.items()},
    }
    os.makedirs(a.build, exist_ok=True)
    with open(os.path.join(a.build, "clips.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=1)
        f.write("\n")

    for p, v in fleet.items():
        print(f"  {p} (section {v['section']}): " + " · ".join(f"{k} {len(v[k])}" for k in FOLDERS))
    if copied:
        print(f"  talk audio in {a.talk}: " + " · ".join(copied))
    elif synthetic:
        print("  synthetic audio: talk/assets/audio left untouched")
    print(f"fleet in {a.out} · map in {os.path.join(a.build, 'clips.json')}")


if __name__ == "__main__":
    main()
