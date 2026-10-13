"""
Reads MIMII DUE (pumps) from the zip, from an already extracted folder or from the synthetic
set, and splits the clips. prepare_data.py and train.py use this same split, so the fleet
never gets a clip the model was trained on.

Split (deterministic, per section):
  train          source normal training clips (90 %)                → v1 (and v2) learn from them
  val            source normal training clips (10 %)                → set the threshold
  contamination  half of the source test faults of pump-01's section
                 → only for v2 (the week the pump was already failing)
  test           every test clip except the contamination           → measure and build the fleet
The three target training clips are not used.
"""
import os, re, zipfile
import numpy as np

PATTERN = re.compile(r"section_(\d+)_(source|target)_(train|test)_(normal|anomaly)_(\d+)")

# five pumps from three sections: pump-01 and pump-04 share section 00; pump-02 and pump-05, section 01
PUMPS = {"pump-01": "00", "pump-02": "01", "pump-03": "02", "pump-04": "00", "pump-05": "01"}
CANARY = "pump-01"        # ring 0: the one that gets v2 in the demo; its section contaminates v2
SCENARIO = "pump-03"      # the one that fails in act 1; the talk audio comes from its section
SEED = 2026
# MIMII / MIMII DUE / DCASE machines: if the audio says another one, it is not pumps
MACHINES = ("fan", "gearbox", "pump", "slider", "valve", "toycar", "toytrain", "bearing", "shaker", "bandsaw",
            "grinder", "toydrone", "toynscale", "vacuum", "toytank")
DOWNLOAD = "https://zenodo.org/records/4740355/files/dev_data_pump.zip?download=1"
MARKER = b"SYNTHETIC"     # synth.py writes it in every WAV header
MARKERS = (MARKER, b"SINTETICO")                  # the old marker still counts
MARKER_FILES = ("SYNTHETIC.txt", "SINTETICO.txt")  # marker file at the root of a synthetic set


class Source:
    """List of clips from a zip or a folder. Each clip is a dict:
    id, section, domain (source|target), part (train|test), truth (normal|anomaly), n, ref."""

    def __init__(self, path, machine="pump"):
        self.path = os.path.abspath(path)
        self.zip = None
        if os.path.isdir(path):
            names = [os.path.relpath(os.path.join(d, f), path)
                     for d, _, fs in os.walk(path) for f in fs]
            self.synthetic = any(os.path.isfile(os.path.join(path, m)) for m in MARKER_FILES)
        elif zipfile.is_zipfile(path):
            self.zip = zipfile.ZipFile(path)
            names = self.zip.namelist()
            self.synthetic = any(os.path.basename(n) in MARKER_FILES for n in names)
        else:
            raise SystemExit(f"cannot find the data at {path} (neither a folder nor a zip)")

        wavs = [n for n in names if n.lower().endswith(".wav")
                and "__MACOSX" not in n and not os.path.basename(n).startswith("._")]
        # if the zip or folder holds other machines, keep the pumps
        parts = lambda n: re.split(r"[\\/]", n.lower())
        if any(machine in parts(n) for n in wavs):
            wavs = [n for n in wavs if machine in parts(n)]

        # Which machine is it? The zip folders say so (pump/…) or the file name does (dev_data_pump.zip).
        # A bare folder (train/, source_test/…) does not: clip names are the same for every machine.
        hints = {p for n in wavs for p in parts(n)[:-1]}
        hints |= set(re.split(r"[^a-z]+", os.path.basename(self.path).lower()))
        found = [m for m in MACHINES if m in hints]
        self.machine = machine if machine in found else (found[0] if found else None)

        seen, self.clips = set(), []
        for n in sorted(wavs):
            m = PATTERN.search(os.path.basename(n))
            if not m:
                continue
            cid = os.path.splitext(os.path.basename(n))[0]
            if cid in seen:
                continue
            seen.add(cid)
            sec, dom, part, truth, num = m.groups()
            self.clips.append(dict(id=cid, section=f"{int(sec):02d}", domain=dom, part=part,
                                   truth=truth, n=int(num), ref=n))
        if not self.clips:
            raise SystemExit(f"{path}: no WAV with MIMII DUE names (section_XX_source_train_normal_XXXX…)")
        self.synthetic = self.synthetic or is_synthetic(self.read(self.clips[0]))
        if self.synthetic:
            self.machine = machine
        elif self.machine and self.machine != machine:
            raise SystemExit(f"{path}: this audio is from «{self.machine}», not pumps ({machine}).\n"
                             f"Download dev_data_pump.zip ({DOWNLOAD}) and leave it, unextracted, in data/.")
        elif self.machine is None:
            print(f"(warning) {path}: cannot confirm these are pumps; the folder does not name the machine.\n"
                  f"          The numbers are marked unconfirmed and do not reach the slides.\n"
                  f"          Use the zip as is: data/dev_data_pump.zip")

    def read(self, clip):
        """WAV bytes, without extracting the rest of the zip."""
        if self.zip is not None:
            return self.zip.read(clip["ref"])
        with open(os.path.join(self.path, clip["ref"]), "rb") as f:
            return f.read()

    def sections(self):
        return sorted({c["section"] for c in self.clips})


def is_synthetic(wav):
    """True if the WAV came from synth.py (it carries the marker in its header)."""
    return any(m in wav[:64] or m in wav[-128:] for m in MARKERS)


def _shuffle(items, seed, label):
    """Deterministic permutation that does not depend on the other sections."""
    rng = np.random.default_rng([seed, sum(map(ord, label))])
    return [items[i] for i in rng.permutation(len(items))]


def split(source, contaminate=0.5, val=0.1, seed=SEED):
    contaminated_section = pump_sections(source.sections())[CANARY]
    rep = {"train": [], "val": [], "contamination": [], "test": [], "contaminated_section": contaminated_section}
    for sec in source.sections():
        of = lambda dom, part, truth: [c for c in source.clips if c["section"] == sec and c["domain"] == dom
                                       and c["part"] == part and c["truth"] == truth]
        # the labels "val…" and "cont…" seed the shuffles: changing them changes the split
        tr = _shuffle(of("source", "train", "normal"), seed, f"val{sec}")
        nval = max(1, int(round(val * len(tr)))) if len(tr) > 1 else 0
        rep["val"] += tr[:nval]
        rep["train"] += tr[nval:]
        test = [c for c in source.clips if c["section"] == sec and c["part"] == "test"]
        if sec == contaminated_section and contaminate > 0:
            faults = _shuffle(of("source", "test", "anomaly"), seed, f"cont{sec}")
            cont = faults[: int(contaminate * len(faults))]
            rep["contamination"] += cont
            ids = {c["id"] for c in cont}
            test = [c for c in test if c["id"] not in ids]
        rep["test"] += test
    return rep


def pump_sections(sections):
    """PUMPS, or a round-robin assignment if the data has other sections."""
    if all(s in sections for s in PUMPS.values()):
        return dict(PUMPS)
    return {p: sections[i % len(sections)] for i, p in enumerate(PUMPS)}
