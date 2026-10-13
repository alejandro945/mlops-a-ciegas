"""
End-to-end test of the model with the synthetic set (no AWS and no real data):

  synth.py → prepare_data.py → train.py --fast → inference.py --local

The fleet audio and the artifacts are read-only, as on the device.
Everything runs in a temporary folder: it does not touch build/, data/ or talk/.

Usage:  python3 -m unittest discover -s poc-devopsdays/tests -p 'test_model*.py' -v
"""
import hashlib, io, json, os, re, shutil, struct, subprocess, sys, tempfile, unittest, wave
sys.dont_write_bytecode = True

TESTS = os.path.dirname(os.path.abspath(__file__))
POC = os.path.dirname(TESTS)
REPO = os.path.dirname(POC)
MODEL = os.path.join(POC, "model")
METRICS_PY = os.path.join(REPO, "talk", "tools", "metrics.py")
EVENT = ["device", "model_version", "sha256", "seq", "ts", "clip", "domain",
         "score", "threshold", "alert", "input_z", "latency_ms", "truth"]
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def run(*args, env=None):
    r = subprocess.run([sys.executable, *args], capture_output=True, text=True, env=env or ENV, timeout=900)
    if r.returncode:
        raise AssertionError(f"failed: {' '.join(args)}\n{r.stdout}\n{r.stderr}")
    return r.stdout


def read(path, mode="rb"):
    with open(path, mode) as f:
        return f.read()


def read_json(path):
    return json.loads(read(path, "r"))


def set_writable(root, writable):
    for d, _, fs in os.walk(root):
        os.chmod(d, 0o755 if writable else 0o555)
        for f in fs:
            os.chmod(os.path.join(d, f), 0o644 if writable else 0o444)


def pending_text():
    """The text metrics.py prints for a number that is not measured yet."""
    m = re.search(r'^PENDING\s*=\s*"([^"]+)"', read(METRICS_PY, "r"), re.M)
    return m.group(1) if m else "por medir"


class SyntheticPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="station-")
        cls.data = os.path.join(cls.tmp, "synthetic")
        cls.build = os.path.join(cls.tmp, "build")
        cls.fleet = os.path.join(cls.tmp, "station")
        cls.talk = os.path.join(cls.tmp, "talk")
        cls.mode = os.path.join(cls.tmp, "mode")
        run(os.path.join(MODEL, "synth.py"), "--out", cls.data, "--seconds", "4")
        run(os.path.join(MODEL, "prepare_data.py"), "--data", cls.data, "--out", cls.fleet,
            "--build", cls.build, "--talk", cls.talk)
        run(os.path.join(MODEL, "train.py"), "--data", cls.data, "--build", cls.build, "--fast")
        set_writable(cls.fleet, False)
        for v in ("1.0.0", "2.0.0"):
            set_writable(os.path.join(cls.build, v), False)

    @classmethod
    def tearDownClass(cls):
        set_writable(cls.tmp, True)
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def events(self, pump, mode, n=3, version="1.0.0", extra=()):
        if mode is None:
            if os.path.exists(self.mode):
                os.remove(self.mode)
        else:
            with open(self.mode, "w") as f:
                f.write(mode + "\n")
        d = os.path.join(self.build, version)
        out = run(os.path.join(d, "inference.py"), "--model", os.path.join(d, "model.onnx"),
                  "--stats", os.path.join(d, "stats.json"), "--audio-root", self.fleet,
                  "--mode-file", self.mode, "--version", version, "--topic", "station/events",
                  "--interval", "0", "--local", "--max", str(n), *extra,
                  env=dict(ENV, AWS_IOT_THING_NAME=pump))
        return [json.loads(l) for l in out.splitlines() if l.strip()]

    def stats(self, version):
        return read_json(os.path.join(self.build, version, "stats.json"))

    # · the event

    def test_event_has_the_exact_schema(self):
        st = self.stats("1.0.0")
        evs = self.events("pump-03", "fault", n=4)
        self.assertEqual(len(evs), 4)
        for i, e in enumerate(evs, 1):
            self.assertEqual(list(e), EVENT)
            self.assertEqual((e["device"], e["model_version"], e["seq"]), ("pump-03", "1.0.0", i))
            self.assertEqual(e["sha256"], st["sha256"])
            self.assertEqual((e["domain"], e["truth"]), ("source", "anomaly"))
            self.assertRegex(e["clip"], r"^section_\d+_source_test_anomaly_\d+$")
            self.assertIsInstance(e["ts"], int)
            self.assertGreater(e["ts"], 1.7e12)
            for k in ("score", "threshold", "input_z", "latency_ms"):
                self.assertIsInstance(e[k], float)
            self.assertIsInstance(e["alert"], bool)
            self.assertEqual(e["alert"], e["score"] > e["threshold"])
            self.assertAlmostEqual(e["threshold"], st["threshold"], places=3)
            self.assertLess(len(json.dumps(e)), 600)          # a few hundred bytes

    def test_mode_is_read_from_the_file(self):
        for e in self.events("pump-05", "shifted", n=2):
            self.assertEqual((e["domain"], e["truth"]), ("target", "normal"))
        for e in self.events("pump-02", "normal", n=2):
            self.assertEqual((e["domain"], e["truth"]), ("source", "normal"))
        for e in self.events("pump-04", None, n=2):          # no mode file: normal
            self.assertEqual(e["truth"], "normal")
        for e in self.events("pump-04", "anything-else", n=1):
            self.assertEqual(e["truth"], "normal")

    def test_threshold_is_configuration(self):
        for e in self.events("pump-01", "normal", n=2, extra=("--threshold", "0")):
            self.assertEqual((e["threshold"], e["alert"]), (0.0, True))
        st = self.stats("2.0.0")
        for e in self.events("pump-01", "normal", n=1, version="2.0.0", extra=("--threshold", "")):
            self.assertAlmostEqual(e["threshold"], st["threshold"], places=3)
            self.assertEqual(e["model_version"], "2.0.0")

    # · the artifacts

    def test_artifacts_per_version(self):
        files = {"model.onnx", "stats.json", "features.py", "inference.py"}
        self.assertEqual(set(os.listdir(os.path.join(self.build, "1.0.0"))), files | {"model.int8.onnx"})
        self.assertEqual(set(os.listdir(os.path.join(self.build, "2.0.0"))), files)
        source = read(os.path.join(MODEL, "features.py"))
        self.assertEqual(read(os.path.join(POC, "component", "features.py")), source)
        for v in ("1.0.0", "2.0.0"):
            st = self.stats(v)
            for k in ("version", "threshold", "sha256", "mean", "std", "synthetic"):
                self.assertIn(k, st)
            self.assertEqual(st["version"], v)
            self.assertIs(st["synthetic"], True)
            self.assertEqual(len(st["mean"]), 320)
            model = read(os.path.join(self.build, v, "model.onnx"))
            self.assertEqual(st["sha256"], hashlib.sha256(model).hexdigest())
            self.assertEqual(read(os.path.join(self.build, v, "features.py")), source)
            self.assertEqual(read(os.path.join(self.build, v, "inference.py")),
                             read(os.path.join(POC, "component", "inference.py")))

    def test_metrics_complete_and_synthetic(self):
        m = read_json(os.path.join(self.build, "metrics.json"))
        self.assertIs(m["synthetic"], True)
        self.assertIn("synthetic", m["dataset"])
        self.assertEqual(set(m["details"]["clips"]), {"train", "val", "test", "contamination"})
        keys = sorted(set(re.findall(r"\b((?:v1|v2|int8|input)\.[a-z0-9_]+)", read(METRICS_PY, "r"))))
        self.assertGreater(len(keys), 15)
        for k in keys:
            group, leaf = k.split(".")
            self.assertIsNotNone(m.get(group, {}).get(leaf), f"{k} missing from metrics.json")
        out = run(METRICS_PY, "v1.recall_source", env=dict(ENV, METRICS_JSON=os.path.join(self.build, "metrics.json")))
        self.assertIn(f"v1.recall_source → {pending_text()}", out)

    def test_scores_csv_columns(self):
        with open(os.path.join(self.build, "scores.csv"), encoding="utf-8") as f:
            header = f.readline().strip().split(",")
            splits = {line.split(",")[4] for line in f if line.strip()}
        self.assertEqual(header, ["clip", "section", "domain", "truth", "split", "v1", "v2", "int8", "z"])
        self.assertEqual(splits, {"test", "contamination"})

    def test_repo_metrics_do_not_reach_the_talk_if_synthetic(self):
        path = os.path.join(POC, "build", "metrics.json")
        if not os.path.exists(path) or not read_json(path).get("synthetic"):
            self.skipTest("build/metrics.json does not exist or is a real measurement")
        self.assertIn(pending_text(), run(METRICS_PY, "v1.recall_source"))

    # · the data

    def test_fleet_only_has_test_clips(self):
        info = read_json(os.path.join(self.build, "clips.json"))
        self.assertIs(info["synthetic"], True)
        self.assertEqual(sorted(info["pumps"]), [f"pump-0{i}" for i in range(1, 6)])
        contaminated = set(info["contamination"])
        seen = set()
        for p, v in info["pumps"].items():
            for folder in ("normal", "fault", "shifted"):
                ids = v[folder]
                self.assertTrue(ids, f"{p}/{folder} is empty")
                self.assertEqual(sorted(os.path.splitext(f)[0] for f in os.listdir(os.path.join(self.fleet, p, folder))), sorted(ids))
                for c in ids:
                    self.assertIn("_test_", c)
                    self.assertNotIn(c, contaminated)
                    self.assertNotIn(c, seen, "one clip in two pumps")
                    seen.add(c)
        self.assertFalse(os.path.exists(self.talk), "synthetic audio in talk/assets")

    def test_synthetic_marker_old_and_new(self):
        sys.path.insert(0, MODEL)
        import dataset as D
        wav = read(os.path.join(self.fleet, "pump-01", "normal", os.listdir(os.path.join(self.fleet, "pump-01", "normal"))[0]))
        self.assertIn(b"SYNTHETIC", wav[-128:])
        self.assertTrue(D.is_synthetic(wav))
        self.assertTrue(D.is_synthetic(wav.replace(b"SYNTHETIC", b"SINTETICO")))     # sets made before the rename
        self.assertFalse(D.is_synthetic(wav.replace(b"SYNTHETIC", b"XXXXXXXXX")))

    def test_reads_multichannel_and_extensible_wav(self):
        sys.path.insert(0, MODEL)
        import numpy as np
        import features as F
        x = (np.sin(np.arange(16000) / 5) * 8000).astype("<i2")
        stereo = np.stack([x, np.zeros_like(x)], 1)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(16000)
            w.writeframes(stereo.tobytes())
        y, sr = F.read_wav(buf.getvalue())
        self.assertEqual((len(y), sr), (16000, 16000))
        self.assertTrue(np.allclose(y, x / 32768.0))              # the first channel
        # the same signal with a WAVE_FORMAT_EXTENSIBLE header (Python 3.10's wave cannot read it)
        pcm = x.tobytes()
        fmt = struct.pack("<HHIIHHHHIH14s", 0xFFFE, 1, 16000, 32000, 2, 16, 22, 16, 4, 1, b"\x00\x00\x00\x00\x10\x00\x80\x00\x00\xaa\x00\x38\x9b\x71")
        body = b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt + b"data" + struct.pack("<I", len(pcm)) + pcm
        y2, _ = F.read_wav(b"RIFF" + struct.pack("<I", len(body)) + body)
        self.assertTrue(np.allclose(y2, x / 32768.0))
        X = F.clip_features(np.zeros(160000, np.float32))
        self.assertEqual(X.shape, (307, 320))
        with self.assertRaises(ValueError):
            F.logmel(np.zeros(1000), 44100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
