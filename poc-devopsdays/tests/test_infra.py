"""
Tests for the PoC infrastructure (fleet, cloud, demo). No AWS, no Docker.

  python3 -m unittest discover -s poc-devopsdays/tests -p "test_infra*.py" -v

What it covers:
  · `bash -n` of every script, and that each one stops at the first error
  · the recipe parses as YAML and its `Run` is the one from PLAN §4.4
  · the dashboard is valid JSON and only uses metrics that setup.sh creates
  · the Lambda, with hand-made fake boto3 clients: on OK it does nothing, on ALARM
    it deploys the last good version to ring 0
  · the scripts with logic (publish, deploy, up, down, setup, teardown, entrypoint) run
    against a fake `aws` and a fake `docker` that record what they are asked
  · the watch.sh format

What it does NOT cover: none of this touches real AWS or real Docker. See "What I verified and what I didn't" in the README.
"""
import sys
sys.dont_write_bytecode = True        # the tests leave no __pycache__ in cloud/ or demo/

import importlib.util
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import tempfile
import textwrap
import time
import types
import unittest
from pathlib import Path
from unittest import mock

try:
    import yaml
except ImportError:          # without PyYAML we do a simple check
    yaml = None

ROOT = Path(__file__).resolve().parents[1]          # poc-devopsdays/
SCRIPTS = sorted(list((ROOT / "fleet").glob("*.sh")) + list((ROOT / "demo").glob("*.sh"))
                 + list((ROOT / "cloud").glob("*.sh")))

# What PLAN §4.4 says the component runs (on one line)
EXPECTED_RUN = (
    "python3 -u {artifacts:path}/inference.py --model {artifacts:path}/model.onnx "
    "--stats {artifacts:path}/stats.json --audio-root /data/station --mode-file /run/station/mode "
    "--version __VERSION__ --topic {configuration:/topic} --threshold {configuration:/threshold} "
    "--interval {configuration:/intervalSeconds}")

METRICS = {"Alerts", "Score", "Threshold", "Inferences", "InputZ", "LatencyMs", "MissedFaults"}


# ─────────────────────────────────────────────────────────────────────
#  A fake `aws` and a fake `docker`: they record each call in a JSON-lines file
# ─────────────────────────────────────────────────────────────────────
SHIM_AWS = r'''#!/usr/bin/env python3
import json, os, re, sys
args = sys.argv[1:]
entry = {"cmd": "aws", "args": args, "files": {}}
for a in args:
    m = re.match(r"^file(?:b)?://(.+)$", a)
    if m and os.path.isfile(m.group(1)) and os.path.getsize(m.group(1)) < 200000:
        entry["files"][a] = open(m.group(1), errors="replace").read()
with open(os.environ["SHIM_LOG"], "a") as f:
    f.write(json.dumps(entry) + "\n")
line = " ".join(args)
missing = os.environ.get("SHIM_MISSING")
if missing and re.search(missing, line):
    sys.stderr.write("An error occurred (ResourceNotFoundException): shim\n")
    sys.exit(254)
if line.startswith("sts get-caller-identity"):
    print("123456789012")
elif line.startswith("configure export-credentials"):
    print(json.dumps({"Version": 1, "AccessKeyId": "ASIAEXAMPLE", "SecretAccessKey": "secret/with%percent",
                      "SessionToken": "temporary-token"}))
elif line.startswith("greengrassv2 describe-component") and "componentState" in line:
    print("DEPLOYABLE")
elif line.startswith("greengrassv2 create-component-version"):
    print("com.station.Listener\t9.9.9\tREQUESTED")
elif line.startswith("greengrassv2 create-deployment"):
    print("dep-" + str(abs(hash(line)) % 1000))
elif line.startswith("ssm get-parameter"):
    print("1.0.0")
elif line.startswith("logs tail"):
    for l in open(os.environ["SHIM_TAIL"]):
        print(l.rstrip("\n"))
sys.exit(0)
'''

SHIM_DOCKER = r'''#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
entry = {"cmd": "docker", "args": args}
for a in args:                                    # which credentials are in the mount during `docker run`?
    if ":/run/aws-bootstrap" in a:
        cred = os.path.join(a.split(":/run/aws-bootstrap")[0], "credentials")
        entry["visible_credentials"] = open(cred).read() if os.path.exists(cred) else None
with open(os.environ["SHIM_LOG"], "a") as f:
    f.write(json.dumps(entry) + "\n")
provisioned = os.environ.get("SHIM_PROVISIONED") == "1"
if args[:2] == ["image", "inspect"]:
    sys.exit(0)
if args[:2] == ["network", "inspect"]:
    sys.exit(1)
if args[:2] == ["volume", "inspect"]:
    sys.exit(0 if provisioned else 1)
if args[:1] == ["run"] and "--entrypoint" in args:
    sys.exit(0 if provisioned else 1)
if args[:1] == ["inspect"]:
    sys.exit(1)
sys.exit(0)
'''


def _write(path, text, executable=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IXUSR)


class Environment:
    """A copy of the PoC in a temporary directory, with a fake `aws` and `docker` first in PATH."""

    def __init__(self, test):
        self.dir = Path(tempfile.mkdtemp(prefix="station-test-"))
        test.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.poc = self.dir / "poc"
        junk = shutil.ignore_patterns("__pycache__", "logs", ".bootstrap", "*.pyc", ".DS_Store", "*.zip")

        def ignore(folder, names):      # nothing big gets copied either (a data zip someone left there)
            big = [n for n in names if os.path.isfile(os.path.join(folder, n))
                   and os.path.getsize(os.path.join(folder, n)) > 1_000_000]
            return set(junk(folder, names)) | set(big)

        for sub in ("fleet", "demo", "cloud", "component"):
            shutil.copytree(ROOT / sub, self.poc / sub, ignore=ignore)
        self.bin = self.dir / "bin"
        _write(self.bin / "aws", SHIM_AWS, True)
        _write(self.bin / "docker", SHIM_DOCKER, True)
        self.log = self.dir / "calls.jsonl"
        self.tail = self.dir / "tail.txt"
        self.tail.write_text("")
        self.env = {**os.environ, "PATH": f"{self.bin}:{os.environ['PATH']}", "SHIM_LOG": str(self.log),
                    "SHIM_TAIL": str(self.tail), "REGION": "us-east-1", "TZ": "UTC"}
        for k in ("SHIM_MISSING", "SHIM_PROVISIONED", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN",
                  "IDENTITY", "THRESHOLD", "SINCE", "WAIT_SECONDS", "STATION_RUN_DIR"):
            self.env.pop(k, None)

    def run(self, script, *args, stdin=None, **env):
        return subprocess.run([str(self.poc / script), *args], cwd=self.poc, input=stdin,
                              env={**self.env, **env}, capture_output=True, text=True, timeout=120)

    def calls(self, cmd=None):
        if not self.log.exists():
            return []
        everything = [json.loads(l) for l in self.log.read_text().splitlines()]
        return [c for c in everything if cmd is None or c["cmd"] == cmd]

    def aws(self, *prefix):
        """Calls to aws whose start matches `prefix` (for example: "iot", "create-topic-rule")."""
        return [c for c in self.calls("aws") if c["args"][:len(prefix)] == list(prefix)]

    def reset_log(self):
        self.log.write_text("")

    def fake_build(self, folder="9.9.9", **stats):
        """A build/<folder>/ like the one model/train.py leaves (stats.json says version=folder unless given)."""
        version = stats.pop("version", folder)
        d = self.poc / "build" / folder
        d.mkdir(parents=True)
        for f in ("inference.py", "features.py"):
            (d / f).write_text("# " + f + "\n")
        model = b"fake-model"
        (d / "model.onnx").write_bytes(model)
        import hashlib
        st = {"version": version, "threshold": 0.0123, "sha256": hashlib.sha256(model).hexdigest(),
              "mean": [0.0], "std": [1.0]}
        st.update(stats)
        (d / "stats.json").write_text(json.dumps(st))
        return d


class ScriptsBasics(unittest.TestCase):
    def test_scripts_exist(self):
        names = {p.name for p in SCRIPTS}
        for expected in ("build.sh", "up.sh", "down.sh", "entrypoint.sh", "publish.sh", "deploy.sh", "fault.sh",
                         "domain.sh", "network.sh", "watch.sh", "setup.sh", "teardown.sh", "delete-things.sh"):
            self.assertIn(expected, names)

    def test_bash_syntax(self):
        for p in SCRIPTS:
            with self.subTest(script=p.name):
                r = subprocess.run(["bash", "-n", str(p)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)

    def test_stop_at_first_error_and_are_executable(self):
        for p in SCRIPTS:
            with self.subTest(script=p.name):
                self.assertIn("set -euo pipefail", p.read_text())
                self.assertTrue(p.read_text().startswith("#!/usr/bin/env bash"))
                self.assertTrue(os.access(p, os.X_OK), f"{p.name} is not executable")

    def test_old_model_leftovers_are_gone(self):
        self.assertFalse((ROOT / "demo" / "entrada.sh").exists())
        self.assertFalse((ROOT / "cloud" / "grant-device.sh").exists())

    def test_old_spanish_names_are_gone(self):
        for old in ("demo/falla.sh", "demo/red.sh", "demo/dominio.sh", "demo/formato_eventos.py",
                    "cloud/borrar-things.sh"):
            self.assertFalse((ROOT / old).exists(), old)

    def test_writing_rules(self):
        """No kubectl, no Spanish runtime names, no SSH, in what this part of the PoC ships."""
        files = [ROOT / "README.md", ROOT / "component" / "recipe.template.yaml", ROOT / "component" / "inference.py",
                 *SCRIPTS, *(ROOT / "demo").glob("*.py"), *(ROOT / "cloud").glob("*.py"),
                 ROOT / "fleet" / "Dockerfile", ROOT / "cloud" / "dashboard.json"]
        forbidden = re.compile(r"kubectl|estacion|bomba|anillo|umbral|traer-poc|DOCKER_HOST=ssh|IDENTIDAD", re.I)
        for f in files:
            with self.subTest(file=f.name):
                m = forbidden.search(f.read_text())
                self.assertIsNone(m, f"forbidden word in {f}: {m and m.group(0)}")


class Recipe(unittest.TestCase):
    PATH = ROOT / "component" / "recipe.template.yaml"

    def test_parses_and_matches_the_plan(self):
        text = self.PATH.read_text()
        if yaml is None:
            for piece in ("ComponentName: com.station.Listener", "topic: 'station/events'",
                          "intervalSeconds: '3'", "threshold: '__THRESHOLD__'", "aws.greengrass#PublishToIoTCore"):
                self.assertIn(piece, text)
            return
        r = yaml.safe_load(text)
        self.assertEqual(r["ComponentName"], "com.station.Listener")
        cfg = r["ComponentConfiguration"]["DefaultConfiguration"]
        self.assertEqual(cfg["topic"], "station/events")
        self.assertEqual(cfg["intervalSeconds"], "3")                 # number as text, as Greengrass expects
        self.assertEqual(cfg["threshold"], "__THRESHOLD__")
        ipc = cfg["accessControl"]["aws.greengrass.ipc.mqttproxy"]["com.station.Listener:mqttproxy:1"]
        self.assertEqual(ipc["operations"], ["aws.greengrass#PublishToIoTCore"])
        self.assertEqual(ipc["resources"], ["station/events"])
        m = r["Manifests"][0]
        self.assertEqual(m["Platform"]["os"], "linux")
        self.assertNotIn("Install", m["Lifecycle"])                  # dependencies live in the image
        self.assertEqual(" ".join(m["Lifecycle"]["Run"].split()), EXPECTED_RUN)
        uris = [a["URI"] for a in m["Artifacts"]]
        self.assertEqual([u.rsplit("/", 1)[1] for u in uris], ["inference.py", "features.py", "model.onnx", "stats.json"])
        for u in uris:
            self.assertTrue(u.startswith("s3://__BUCKET__/station/__VERSION__/"), u)

    def test_fits_on_one_slide(self):
        lines = self.PATH.read_text().splitlines()
        self.assertLessEqual(len(lines), 40)
        self.assertFalse([l for l in lines if l.strip().startswith("#")], "the recipe has no comments")


class Dashboard(unittest.TestCase):
    def test_valid_json_with_the_six_signals(self):
        text = (ROOT / "cloud" / "dashboard.json").read_text()
        d = json.loads(text)
        used = set()
        kinds = set()
        for w in d["widgets"]:
            kinds.add(w["type"])
            if w["type"] == "text":                       # section headers: no region, no metrics
                self.assertTrue(w["properties"]["markdown"].strip())
                continue
            self.assertEqual(w["properties"]["region"], "__REGION__")
            if w["type"] == "alarm":                      # the gate's status
                self.assertEqual(w["properties"]["alarms"],
                                 ["arn:aws:cloudwatch:__REGION__:__ACCOUNT__:alarm:station-missed-faults"])
                continue
            if w["type"] == "log":                        # Logs Insights over the raw events
                self.assertTrue(w["properties"]["query"].startswith("SOURCE '/station/events' |"))
                continue
            if "alarms" in w["properties"].get("annotations", {}):
                # CloudWatch rejects an alarm widget with "metrics": the series comes from the alarm
                self.assertNotIn("metrics", w["properties"])
                self.assertEqual(w["properties"]["annotations"]["alarms"],
                                 ["arn:aws:cloudwatch:__REGION__:__ACCOUNT__:alarm:station-missed-faults"])
                used.add("MissedFaults")
                continue
            for row in w["properties"]["metrics"]:
                if row[0] != "...":
                    self.assertEqual(row[0], "__NS__")
                    used.add(row[1])
        self.assertEqual(used, METRICS)
        self.assertEqual(kinds, {"text", "alarm", "metric", "log"})
        # with the placeholders filled it is still JSON
        filled = text.replace("__REGION__", "us-east-1").replace("__NS__", "Station").replace("__ACCOUNT__", "123456789012")
        self.assertNotIn("__", filled)
        json.loads(filled)

    def test_setup_creates_every_metric(self):
        setup = (ROOT / "cloud" / "setup.sh").read_text()
        created = {shlex.split(l)[2] for l in setup.splitlines() if l.startswith("metric_filter ")}
        self.assertEqual(created, METRICS)


class Lambda(unittest.TestCase):
    """rollback_lambda.py with hand-made fake boto3 clients."""

    GROUP = "arn:aws:iot:us-east-1:123456789012:thinggroup/StationRing0"

    def load(self):
        class GG:
            def __init__(self): self.calls = []
            def create_deployment(self, **kw):
                self.calls.append(kw)
                return {"deploymentId": "dep-123"}

        class SSM:
            def __init__(self): self.requested = []
            def get_parameter(self, Name):
                self.requested.append(Name)
                return {"Parameter": {"Value": "1.0.0"}}

        self.gg, self.ssm = GG(), SSM()
        fake = types.SimpleNamespace(client=lambda name, **kw: {"greengrassv2": self.gg, "ssm": self.ssm}[name])
        env = {"THING_GROUP_ARN": self.GROUP, "COMPONENT": "com.station.Listener",
               "LAST_GOOD_PARAM": "/station/last_good_version"}
        with mock.patch.dict(sys.modules, {"boto3": fake}), mock.patch.dict(os.environ, env):
            spec = importlib.util.spec_from_file_location("rollback_lambda", ROOT / "cloud" / "rollback_lambda.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self.mod = mod
            self.env = env

    @staticmethod
    def event(state):
        return {"source": "aws.cloudwatch", "alarmData": {"alarmName": "station-missed-faults",
                                                           "state": {"value": state}}}

    def setUp(self):
        # the Lambda prints its logs; the tests don't need them
        null = open(os.devnull, "w")
        quiet = mock.patch("sys.stdout", new=null)
        quiet.start()
        self.addCleanup(null.close)
        self.addCleanup(quiet.stop)

    def test_on_ok_does_nothing(self):
        self.load()
        with mock.patch.dict(os.environ, self.env):
            r = self.mod.handler(self.event("OK"), None)
        self.assertTrue(r["skipped"])
        self.assertEqual(self.gg.calls, [])
        self.assertEqual(self.ssm.requested, [])

    def test_insufficient_data_does_nothing_either(self):
        self.load()
        with mock.patch.dict(os.environ, self.env):
            self.assertTrue(self.mod.handler(self.event("INSUFFICIENT_DATA"), None)["skipped"])
            self.assertTrue(self.mod.handler({}, None)["skipped"])
        self.assertEqual(self.gg.calls, [])

    def test_on_alarm_deploys_the_last_good_version_to_ring_0(self):
        self.load()
        with mock.patch.dict(os.environ, self.env):
            r = self.mod.handler(self.event("ALARM"), None)
        self.assertEqual(self.ssm.requested, ["/station/last_good_version"])
        self.assertEqual(len(self.gg.calls), 1)
        d = self.gg.calls[0]
        self.assertEqual(d["targetArn"], self.GROUP)
        self.assertTrue(d["targetArn"].endswith("thinggroup/StationRing0"))
        self.assertTrue(d["deploymentName"].startswith("rollback-to-1.0.0-"))
        self.assertEqual(d["components"]["com.station.Listener"]["componentVersion"], "1.0.0")
        self.assertEqual(d["deploymentPolicies"]["failureHandlingPolicy"], "ROLLBACK")
        self.assertEqual(r["rolled_back_to"], "1.0.0")
        self.assertEqual(r["deploymentId"], "dep-123")

    def test_setup_points_the_lambda_at_ring_0(self):
        setup = (ROOT / "cloud" / "setup.sh").read_text()
        self.assertIn("THING_GROUP_ARN=arn:aws:iot:$REGION:$ACCOUNT:thinggroup/StationRing0", setup)
        self.assertIn("--alarm-actions \"$LAMBDA_ARN\"", setup)


class Format(unittest.TestCase):
    def setUp(self):
        os.environ["TZ"] = "UTC"
        time.tzset()
        sys.path.insert(0, str(ROOT / "demo"))
        import format_events
        self.f = format_events
        self.base = {"device": "pump-03", "model_version": "1.0.0", "score": 0.82, "threshold": 0.5, "alert": True,
                     "input_z": 1.12, "latency_ms": 3.6, "truth": "anomaly",
                     "ts": 1760000000000, "arrived_ts": 1760000001500}

    def test_the_line_from_the_plan(self):
        self.assertTrue(self.f.format_event(self.base, color=False).endswith(
            "pump-03  v1.0.0  ALERT  score 0.82 (threshold 0.50)  input 1.1  4 ms"))

    def test_late_only_after_10_s(self):
        e = dict(self.base, arrived_ts=self.base["ts"] + 10_000)
        self.assertNotIn("late", self.f.format_event(e, color=False))
        e = dict(self.base, arrived_ts=self.base["ts"] + 40_000)
        self.assertTrue(self.f.format_event(e, color=False).endswith("4 ms  · arrived 40 s late"))

    def test_small_scores_get_more_decimals_and_normal_does_not_alert(self):
        e = dict(self.base, score=0.0031, threshold=0.0123, alert=False, truth="normal", latency_ms=0.4)
        line = self.f.format_event(e, color=False)
        self.assertIn("normal  score 0.0031 (threshold 0.0123)", line)
        self.assertTrue(line.endswith("<1 ms"))

    def test_missed_fault(self):
        e = dict(self.base, alert=False, truth="anomaly")
        self.assertTrue(self.f.format_event(e, color=False).endswith("· missed fault"))
        self.assertNotIn("missed fault", self.f.format_event(dict(self.base, truth="normal"), color=False))

    def test_local_time_of_arrived_ts_and_noise_ignored(self):
        self.assertTrue(self.f.format_event(self.base, color=False).startswith("08:53:21  "))
        self.assertIsNone(self.f.format_event({"hello": 1}))


class ContractWithTheModel(unittest.TestCase):
    """The recipe, the model agent's component, the metric filters and watch.sh speak the same language.
    Skipped if build/1.0.0 or numpy/onnxruntime are missing (runs the real component, with --local)."""

    def test_the_recipe_run_works_and_its_event_feeds_filters_and_format(self):
        build = ROOT / "build" / "1.0.0"
        audio = ROOT / "data" / "station" / "pump-03"
        try:
            import numpy, onnxruntime  # noqa: F401
        except ImportError:
            self.skipTest("numpy/onnxruntime missing")
        if not (build / "model.onnx").exists() or not (audio / "fault").exists():
            self.skipTest("build/1.0.0 or data/station missing (run model/train.py and model/prepare_data.py)")
        recipe = yaml.safe_load((ROOT / "component" / "recipe.template.yaml").read_text()) if yaml else None
        if recipe is None:
            self.skipTest("PyYAML missing")
        cfg = recipe["ComponentConfiguration"]["DefaultConfiguration"]
        stats = json.loads((build / "stats.json").read_text())
        mode = Path(tempfile.mkdtemp()) / "mode"
        mode.write_text("fault\n")
        self.addCleanup(shutil.rmtree, mode.parent, ignore_errors=True)
        run = " ".join(recipe["Manifests"][0]["Lifecycle"]["Run"].split())
        for a, b in (("{artifacts:path}", str(build)), ("__VERSION__", "1.0.0"), ("{configuration:/topic}", cfg["topic"]),
                     ("{configuration:/threshold}", str(stats["threshold"])), ("{configuration:/intervalSeconds}", "0.1"),
                     ("/run/station/mode", str(mode)), ("/data/station", str(ROOT / "data" / "station"))):
            run = run.replace(a, b)
        r = subprocess.run([*shlex.split(run), "--local", "--max", "2"], capture_output=True, text=True, timeout=120,
                           env={**os.environ, "AWS_IOT_THING_NAME": "pump-03"})
        self.assertEqual(r.returncode, 0, r.stderr)
        events = [json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")]
        self.assertEqual(len(events), 2)
        e = events[0]
        # the fields setup.sh's metric filters read
        for field in ("device", "model_version", "score", "threshold", "alert", "input_z", "latency_ms", "truth"):
            self.assertIn(field, e)
        self.assertIsInstance(e["alert"], bool)                       # { $.alert IS TRUE }
        self.assertIn(e["truth"], ("normal", "anomaly"))
        self.assertEqual(e["truth"], "anomaly")                       # the fault folder is an anomaly
        self.assertEqual(e["device"], "pump-03")
        sys.path.insert(0, str(ROOT / "demo"))
        import format_events
        self.assertTrue(format_events.format_event(e, color=False).split("  ")[1] == "pump-03")


class Watch(unittest.TestCase):
    def test_watch_filters_and_formats(self):
        env = Environment(self)
        base = {"device": "pump-03", "model_version": "1.0.0", "score": 0.82, "threshold": 0.5, "alert": True,
                "input_z": 1.12, "latency_ms": 3.6, "truth": "anomaly", "ts": 1760000000000, "arrived_ts": 1760000040000}
        other = dict(base, device="pump-02", alert=False, truth="normal", arrived_ts=1760000000500)
        env.tail.write_text("\n".join(
            "2025-10-09T08:53:20 " + json.dumps(e) for e in (base, other)) + "\nodd line without json\n")
        r = env.run("demo/watch.sh")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(r.stdout.strip().splitlines()), 2)
        self.assertIn("arrived 40 s late", r.stdout)
        r = env.run("demo/watch.sh", "pump-02")
        self.assertEqual(len(r.stdout.strip().splitlines()), 1)
        self.assertIn("pump-02", r.stdout)
        tail = env.aws("logs", "tail")[0]["args"]
        self.assertIn("/station/events", tail)
        self.assertIn("--follow", tail)
        self.assertEqual(tail[tail.index("--since") + 1], "1m")

    def test_since(self):
        env = Environment(self)
        env.run("demo/watch.sh", SINCE="10m")
        tail = env.aws("logs", "tail")[0]["args"]
        self.assertEqual(tail[tail.index("--since") + 1], "10m")


class Publish(unittest.TestCase):
    def setUp(self):
        self.e = Environment(self)

    def test_publishes_with_the_threshold_from_stats(self):
        self.e.fake_build("9.9.9", threshold=0.0123)
        r = self.e.run("demo/publish.sh", "9.9.9", SHIM_MISSING=r"describe-component (?!.*componentState)")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        uploads = [c["args"] for c in self.e.aws("s3", "cp")]
        targets = sorted(a[3] for a in uploads)
        self.assertEqual(targets, [f"s3://station-123456789012-us-east-1/station/9.9.9/{f}"
                                   for f in ("features.py", "inference.py", "model.onnx", "stats.json")])
        create = self.e.aws("greengrassv2", "create-component-version")
        self.assertEqual(len(create), 1)
        recipe = list(create[0]["files"].values())[0]
        self.assertNotIn("__", recipe)                      # no unfilled placeholder
        self.assertIn("threshold: '0.0123'", recipe)
        self.assertIn("ComponentVersion: '9.9.9'", recipe)
        self.assertIn("s3://station-123456789012-us-east-1/station/9.9.9/model.onnx", recipe)
        if yaml:
            self.assertEqual(yaml.safe_load(recipe)["ComponentConfiguration"]["DefaultConfiguration"]["threshold"], "0.0123")

    def test_refuses_synthetic_audio(self):
        self.e.fake_build("9.9.9", synthetic=True)
        r = self.e.run("demo/publish.sh", "9.9.9", SHIM_MISSING=r"describe-component (?!.*componentState)")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("synthetic", r.stdout + r.stderr)
        self.assertEqual(self.e.aws("s3", "cp"), [])
        self.assertEqual(self.e.aws("greengrassv2", "create-component-version"), [])

    def test_with_allow_synthetic_it_publishes(self):
        self.e.fake_build("9.9.9", synthetic=True)
        r = self.e.run("demo/publish.sh", "9.9.9", "--allow-synthetic", SHIM_MISSING=r"describe-component (?!.*componentState)")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(self.e.aws("greengrassv2", "create-component-version")), 1)

    def test_a_published_version_is_left_alone(self):
        self.e.fake_build("9.9.9")
        r = self.e.run("demo/publish.sh", "9.9.9")        # describe-component answers "exists"
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("already published", r.stdout)
        self.assertEqual(self.e.aws("s3", "cp"), [])
        self.assertEqual(self.e.aws("greengrassv2", "create-component-version"), [])

    def test_incomplete_artifacts_or_another_version(self):
        r = self.e.run("demo/publish.sh", "9.9.9")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("build/9.9.9/", r.stdout)
        self.assertIn("missing", r.stdout)
        self.e.fake_build("9.9.9", version="1.0.0")
        r = self.e.run("demo/publish.sh", "9.9.9")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("1.0.0", r.stdout + r.stderr)

    def test_sha256_that_is_not_the_model(self):
        self.e.fake_build("9.9.9", sha256="0" * 64)
        r = self.e.run("demo/publish.sh", "9.9.9")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("sha256", r.stdout + r.stderr)
        self.assertEqual(self.e.aws("s3", "cp"), [])

    def test_badly_written_version(self):
        self.assertNotEqual(self.e.run("demo/publish.sh", "one").returncode, 0)


class Deploy(unittest.TestCase):
    def setUp(self):
        self.e = Environment(self)

    def deployments(self):
        res = []
        for c in self.e.aws("greengrassv2", "create-deployment"):
            doc = json.loads(list(c["files"].values())[0])
            res.append(doc)
        return res

    def test_ring_0_only_touches_the_canary(self):
        r = self.e.run("demo/deploy.sh", "2.0.0", "ring-0")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        (d,) = self.deployments()
        self.assertEqual(d["targetArn"], "arn:aws:iot:us-east-1:123456789012:thinggroup/StationRing0")
        self.assertEqual(d["components"]["com.station.Listener"]["componentVersion"], "2.0.0")
        self.assertEqual(self.e.aws("ssm", "put-parameter"), [])            # only 1.0.0 is the "last good"

    def test_the_shape_of_the_deployment(self):
        self.e.run("demo/deploy.sh", "2.0.0", "ring-1")
        (d,) = self.deployments()
        self.assertEqual(d["targetArn"].rsplit("/", 1)[1], "StationRing1")
        self.assertEqual(d["deploymentPolicies"]["failureHandlingPolicy"], "ROLLBACK")
        job = d["iotJobConfiguration"]
        exp = job["jobExecutionsRolloutConfig"]["exponentialRate"]
        self.assertGreaterEqual(exp["incrementFactor"], 1)
        self.assertIn("numberOfNotifiedThings", exp["rateIncreaseCriteria"])
        crit = job["abortConfig"]["criteriaList"][0]
        self.assertEqual((crit["failureType"], crit["action"]), ("FAILED", "CANCEL"))
        self.assertEqual(crit["minNumberOfExecutedThings"], 2)
        self.assertEqual(d["components"]["com.station.Listener"]["configurationUpdate"], {"reset": [""]})

    def test_1_0_0_to_all_stores_the_last_good_version(self):
        r = self.e.run("demo/deploy.sh", "1.0.0", "all")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual({d["targetArn"].rsplit("/", 1)[1] for d in self.deployments()},
                         {"StationRing0", "StationRing1"})
        (ssm,) = self.e.aws("ssm", "put-parameter")
        self.assertIn("/station/last_good_version", ssm["args"])
        self.assertIn("1.0.0", ssm["args"])

    def test_the_threshold_changes_without_retraining(self):
        self.e.run("demo/deploy.sh", "1.0.0", "ring-1", THRESHOLD="0.02")
        (d,) = self.deployments()
        upd = d["components"]["com.station.Listener"]["configurationUpdate"]
        self.assertEqual(json.loads(upd["merge"]), {"threshold": "0.02"})

    def test_rejects_what_it_does_not_understand(self):
        self.assertNotEqual(self.e.run("demo/deploy.sh", "2.0.0", "ring-9").returncode, 0)
        self.assertNotEqual(self.e.run("demo/deploy.sh", "two", "ring-0").returncode, 0)
        self.assertEqual(self.deployments(), [])

    def test_unpublished_version(self):
        r = self.e.run("demo/deploy.sh", "3.0.0", "ring-0", SHIM_MISSING="describe-component")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("publish.sh", r.stdout)
        self.assertEqual(self.deployments(), [])


class DemoOnThePump(unittest.TestCase):
    def setUp(self):
        self.e = Environment(self)

    def exec_(self):
        return [c["args"] for c in self.e.calls("docker")]

    def test_fault(self):
        self.assertEqual(self.e.run("demo/fault.sh", "pump-03").returncode, 0)
        self.assertEqual(self.e.run("demo/fault.sh", "pump-03", "off").returncode, 0)
        a, b = self.exec_()
        self.assertEqual(a[:2], ["exec", "pump-03"]); self.assertEqual(a[-1], "fault")
        self.assertEqual(b[:2], ["exec", "pump-03"]); self.assertEqual(b[-1], "normal")
        self.assertIn("/run/station/mode", " ".join(a))

    def test_domain(self):
        self.assertEqual(self.e.run("demo/domain.sh", "pump-05", "shifted").returncode, 0)
        self.assertEqual(self.exec_()[0][-1], "shifted")
        self.assertNotEqual(self.e.run("demo/domain.sh", "pump-05", "fault").returncode, 0)

    def test_network(self):
        self.assertEqual(self.e.run("demo/network.sh", "off", "pump-03").returncode, 0)
        self.assertEqual(self.e.run("demo/network.sh", "on", "pump-03").returncode, 0)
        self.assertEqual(self.exec_(), [["network", "disconnect", "station", "pump-03"],
                                        ["network", "connect", "station", "pump-03"]])

    def test_reject_pumps_that_do_not_exist(self):
        for s, args in (("fault", ["pump-09"]), ("domain", ["pump-00", "shifted"]), ("network", ["off", "house"])):
            self.assertNotEqual(self.e.run(f"demo/{s}.sh", *args).returncode, 0, s)
        self.assertEqual(self.exec_(), [])


class Fleet(unittest.TestCase):
    def setUp(self):
        self.e = Environment(self)
        for n in range(1, 6):
            (self.e.poc / "data" / "station" / f"pump-0{n}" / "normal").mkdir(parents=True)

    def runs(self):
        return [c for c in self.e.calls("docker") if c["args"][:2] == ["run", "-d"]]

    @staticmethod
    def env_of(c):
        a = c["args"]
        return dict(x.split("=", 1) for i, x in enumerate(a) if i and a[i - 1] == "-e")

    @staticmethod
    def mounts(c):
        a = c["args"]
        return [x for i, x in enumerate(a) if i and a[i - 1] == "-v"]

    def test_first_boot_five_pumps_in_their_rings(self):
        r = self.e.run("fleet/up.sh")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.e.calls("docker")[0]["args"], ["image", "inspect", "station/greengrass:latest"])
        self.assertIn(["network", "create", "station"], [c["args"] for c in self.e.calls("docker")])
        runs = self.runs()
        self.assertEqual([c["args"][c["args"].index("--name") + 1] for c in runs], [f"pump-0{n}" for n in range(1, 6)])
        for c in runs:
            a, env = c["args"], self.env_of(c)
            p = env["THING_NAME"]
            self.assertEqual(env["THING_GROUP_NAME"], "StationRing0" if p == "pump-01" else "StationRing1")
            self.assertEqual(a[a.index("--network") + 1], "station")
            self.assertIn("--init", a)
            self.assertNotIn("IDENTITY", env)                                       # installer is the default
            self.assertIn(f"{p}-gg:/greengrass/v2", self.mounts(c))                  # one volume per pump
            self.assertTrue(any(m.endswith(f"/fleet/logs/{p}:/greengrass/v2/logs") for m in self.mounts(c)))
            self.assertTrue(any(m.endswith(f"/data/station/{p}:/data/station/{p}:ro") for m in self.mounts(c)))
            self.assertEqual(env["THING_POLICY_NAME"], "StationThingPolicy")
            self.assertNotIn("--cpus", a)
            # on first boot the mount has temporary credentials...
            self.assertIn("aws_session_token = temporary-token", c["visible_credentials"])
        # ...and when it finishes none are left on disk
        self.assertFalse((self.e.poc / "fleet" / ".bootstrap" / "credentials").exists())
        # provisioned one at a time: pump 1's wait happens before pump 2's run
        order = [(c["args"][0], c["args"][1]) for c in self.e.calls("docker") if c["args"][0] in ("run", "exec")]
        self.assertEqual(order[:3], [("run", "-d"), ("exec", "pump-01"), ("run", "-d")])

    def test_later_boots_without_credentials(self):
        r = self.e.run("fleet/up.sh", SHIM_PROVISIONED="1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(self.runs()), 5)
        for c in self.runs():
            self.assertIsNone(c["visible_credentials"])
        self.assertEqual(self.e.aws("configure", "export-credentials"), [])

    def test_small_device_limits_cpu_and_memory(self):
        self.e.run("fleet/up.sh", "--small")
        for c in self.runs():
            a = c["args"]
            self.assertEqual(a[a.index("--cpus") + 1], "1")
            self.assertEqual(a[a.index("--memory") + 1], "1g")
            self.assertEqual(a[a.index("--memory-swap") + 1], "1g")
        self.e.reset_log()
        self.e.run("fleet/up.sh", "--small", CPUS="0.5", MEM="768m")
        a = self.runs()[0]["args"]
        self.assertEqual((a[a.index("--cpus") + 1], a[a.index("--memory") + 1]), ("0.5", "768m"))

    def test_unknown_option(self):
        r = self.e.run("fleet/up.sh", "--pequeno")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.runs(), [])

    def test_audio_stays_readable_for_ggc_user(self):
        d = self.e.poc / "data" / "station" / "pump-02" / "normal"
        d.chmod(0o700)
        (d / "x.wav").write_bytes(b"RIFF")
        (d / "x.wav").chmod(0o600)
        self.e.run("fleet/up.sh")
        self.assertTrue(d.stat().st_mode & stat.S_IROTH and d.stat().st_mode & stat.S_IXOTH)
        self.assertTrue((d / "x.wav").stat().st_mode & stat.S_IROTH)

    def test_without_audio_nothing_starts(self):
        shutil.rmtree(self.e.poc / "data" / "station" / "pump-04")
        r = self.e.run("fleet/up.sh")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("pump-04", r.stdout + r.stderr)
        self.assertEqual(self.runs(), [])

    def test_another_data_directory(self):
        for n in range(1, 6):
            (self.e.poc / "data" / "other" / f"pump-0{n}").mkdir(parents=True)
        shutil.rmtree(self.e.poc / "data" / "station")
        r = self.e.run("fleet/up.sh", DATA="data/other")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(any("/data/other/pump-01:/data/station/pump-01:ro" in m for m in self.mounts(self.runs()[0])))

    def test_nucleus_memory_cap(self):
        self.e.run("fleet/up.sh")
        self.assertEqual(self.env_of(self.runs()[0])["JAVA_TOOL_OPTIONS"], "-Xmx256m -XX:+UseSerialGC")
        self.e.reset_log()
        self.e.run("fleet/up.sh", NUCLEUS_HEAP="")
        self.assertNotIn("JAVA_TOOL_OPTIONS", self.env_of(self.runs()[0]))

    def test_down(self):
        r = self.e.run("fleet/down.sh")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.e.aws("iot"), [])
        docker = [c["args"] for c in self.e.calls("docker")]
        self.assertNotIn(["volume", "rm", "pump-01-gg"], docker)
        self.assertIn(["network", "rm", "station"], docker)

    def test_down_deleting_things(self):
        r = self.e.run("fleet/down.sh", "--delete-things")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(["volume", "rm", "pump-05-gg"], [c["args"] for c in self.e.calls("docker")])
        deleted = [c["args"][c["args"].index("--thing-name") + 1] for c in self.e.aws("iot", "delete-thing")]
        self.assertEqual(deleted, [f"pump-0{n}" for n in range(1, 6)])


class Image(unittest.TestCase):
    def test_pinned_versions_and_official_url(self):
        d = (ROOT / "fleet" / "Dockerfile").read_text()
        for dep in ("numpy", "onnxruntime", "awsiotsdk", "awscrt"):
            self.assertRegex(d, rf"{dep}==\d+\.\d+\.\d+")
        self.assertIn("https://d2s8p88vqu9w66.cloudfront.net/releases/greengrass-${GREENGRASS_VERSION}.zip", d)
        version = re.search(r"ARG GREENGRASS_VERSION=(\d+\.\d+\.\d+)", d).group(1)
        self.assertIn(f'GREENGRASS_VERSION:-{version}', (ROOT / "fleet" / "build.sh").read_text())   # build.sh and Dockerfile agree
        self.assertIn("openjdk", d)                       # Java for the nucleus
        self.assertIn("ENTRYPOINT", d)
        self.assertIn("/data/station /run/station", d)

    def test_image_dependencies_are_the_model_ones(self):
        """The component imports numpy, onnxruntime and awsiot: the recipe installs nothing, so the image must bring them."""
        d = (ROOT / "fleet" / "Dockerfile").read_text()
        code = (ROOT / "component" / "inference.py").read_text()
        for mod, package in (("numpy", "numpy"), ("onnxruntime", "onnxruntime"), ("awsiot", "awsiotsdk")):
            if re.search(rf"^\s*(import|from) {mod}\b", code, re.M):
                self.assertIn(package + "==", d)


class Entrypoint(unittest.TestCase):
    """The image entrypoint, with a fake `java` and a fake `loader`."""

    def prepare(self):
        self.e = Environment(self)
        self.ggc = self.e.dir / "gg"
        self.ggc.mkdir()
        self.creds = self.e.dir / "boot" / "credentials"
        self.creds.parent.mkdir()
        _write(self.e.bin / "java", textwrap.dedent(f"""\
            #!/usr/bin/env bash
            echo "$@" > {self.e.dir}/java.args
            env | grep '^AWS_' | sort > {self.e.dir}/java.env
            mkdir -p {self.ggc}/alts/current/distro/bin
            printf '#!/usr/bin/env bash\\nenv | grep "^AWS_" | sort > {self.e.dir}/loader.env\\necho started > {self.e.dir}/loader.ok\\n' \\
                > {self.ggc}/alts/current/distro/bin/loader
            chmod +x {self.ggc}/alts/current/distro/bin/loader
            """), True)
        self.env_extra = {"GGC_ROOT_PATH": str(self.ggc), "CREDS_FILE": str(self.creds),
                          "STATION_RUN_DIR": str(self.e.dir / "run"), "INSTALLER_JAR": "/opt/fake/Greengrass.jar",
                          "THING_NAME": "pump-02", "THING_GROUP_NAME": "StationRing1", "AWS_REGION": "us-east-1",
                          "THING_POLICY_NAME": "StationThingPolicy"}

    def boot(self):
        return subprocess.run([str(self.e.poc / "fleet" / "entrypoint.sh")], cwd=self.e.poc,
                              env={**self.e.env, **self.env_extra}, capture_output=True, text=True, timeout=60)

    def test_first_boot_provisions_and_the_nucleus_does_not_see_the_credentials(self):
        self.prepare()
        self.creds.write_text("[default]\naws_access_key_id = ASIAEXAMPLE\naws_secret_access_key = secret/with%percent\n"
                              "aws_session_token = temporary-token\n")
        r = self.boot()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        args = (self.e.dir / "java.args").read_text().split()
        for expected in ("--provision", "true", "--setup-system-service", "false", "--start", "--thing-name", "pump-02",
                         "--thing-group-name", "StationRing1", "--thing-policy-name", "StationThingPolicy",
                         "--aws-region", "us-east-1", "--component-default-user", "ggc_user:ggc_group", "/opt/fake/Greengrass.jar"):
            self.assertIn(expected, args)
        self.assertEqual(args[args.index("--start") + 1], "false")
        self.assertIn("AWS_SESSION_TOKEN=temporary-token", (self.e.dir / "java.env").read_text())
        self.assertIn("AWS_SECRET_ACCESS_KEY=secret/with%percent", (self.e.dir / "java.env").read_text())
        self.assertTrue((self.ggc / ".station-provisioned").exists())
        self.assertTrue((self.e.dir / "loader.ok").exists())
        visible = (self.e.dir / "loader.env").read_text()                # the nucleus starts without credentials
        for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
            self.assertNotIn(name, visible)
        self.assertEqual((self.e.dir / "run" / "mode").read_text().strip(), "normal")

    def test_second_boot_asks_for_no_credentials_and_does_not_reinstall(self):
        self.prepare()
        (self.ggc / ".station-provisioned").write_text("x")
        loader = self.ggc / "alts" / "current" / "distro" / "bin" / "loader"
        _write(loader, f"#!/usr/bin/env bash\necho ok > {self.e.dir}/loader.ok\n", True)
        (self.e.dir / "run").mkdir()
        (self.e.dir / "run" / "mode").write_text("fault\n")                # the mode survives the restart
        r = self.boot()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse((self.e.dir / "java.args").exists())
        self.assertTrue((self.e.dir / "loader.ok").exists())
        self.assertEqual((self.e.dir / "run" / "mode").read_text().strip(), "fault")

    def test_no_identity_and_no_credentials_stops_with_a_clear_message(self):
        self.prepare()
        r = self.boot()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("./fleet/up.sh", r.stdout + r.stderr)
        self.assertFalse((self.e.dir / "loader.ok").exists())

    def test_unknown_identity(self):
        self.prepare()
        self.env_extra["IDENTITY"] = "other"
        r = self.boot()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("installer or terraform", r.stdout + r.stderr)


class Setup(unittest.TestCase):
    """setup.sh and teardown.sh against a fake `aws`: every document they send must be valid JSON."""

    def run_setup(self, missing=None, **env):
        e = Environment(self)
        r = e.run("cloud/setup.sh", SHIM_MISSING=missing or "", **env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return e

    NEW_ACCOUNT = (r"head-bucket|get-role |describe-thing-group|describe-role-alias|get-policy |get-topic-rule|"
                   r"get-function|ssm get-parameter")

    def test_new_account(self):
        e = self.run_setup(self.NEW_ACCOUNT)
        self.check(e)
        self.assertEqual(len(e.aws("iot", "create-thing-group")), 2)
        self.assertEqual(len(e.aws("lambda", "create-function")), 1)
        self.assertEqual(len(e.aws("iot", "create-topic-rule")), 1)
        self.assertEqual(len(e.aws("iot", "create-policy")), 2)
        self.assertEqual(len(e.aws("ssm", "put-parameter")), 1)

    def test_repeating_does_not_break_and_updates(self):
        e = self.run_setup(None)
        self.check(e)
        self.assertEqual(e.aws("iot", "create-thing-group"), [])
        self.assertEqual(e.aws("lambda", "create-function"), [])
        self.assertEqual(len(e.aws("iot", "replace-topic-rule")), 1)
        self.assertEqual(e.aws("ssm", "put-parameter"), [])           # does not overwrite the last good version

    def check(self, e):
        # every document sent to AWS is JSON and carries no unfilled placeholders
        docs = {}
        for c in e.calls("aws"):
            for k, v in c["files"].items():
                if k.startswith("file://") and not c["args"][0] == "lambda":
                    docs[k] = json.loads(v)
                    self.assertNotIn("__", v, k)
        self.assertGreaterEqual(len(docs), 8)
        # names
        groups = [c["args"][c["args"].index("--thing-group-name") + 1] for c in e.aws("iot", "describe-thing-group")]
        self.assertEqual(groups, ["StationRing0", "StationRing1"])
        roles = {c["args"][c["args"].index("--role-name") + 1] for c in e.aws("iam", "put-role-policy")}
        self.assertEqual(roles, {"GreengrassV2TokenExchangeRole", "StationIotToLogs", "StationRollback"})
        # the pumps' policy keeps its $aws and only allows publishing to the station topic
        pol = [c for c in e.calls("aws") if c["args"][:2] in (["iot", "create-policy"], ["iot", "create-policy-version"])
               and "StationThingPolicy" in c["args"]]
        text = list(pol[0]["files"].values())[0]
        self.assertIn("topic/$aws/things/pump-*/jobs/*", text)
        self.assertIn("client/pump-*", text)
        self.assertIn("topic/station/events", text)
        # the TES role reads only the station prefix of the bucket
        tes = [c for c in e.aws("iam", "put-role-policy") if "GreengrassV2TokenExchangeRole" in c["args"]][0]
        self.assertIn("arn:aws:s3:::station-123456789012-us-east-1/station/*", list(tes["files"].values())[0])
        # the rule adds arrived_ts and writes to the station's log group
        rule = json.loads(list(e.aws("iot", "create-topic-rule" if e.aws("iot", "create-topic-rule") else "replace-topic-rule")[0]["files"].values())[0])
        self.assertEqual(rule["sql"], "SELECT *, timestamp() AS arrived_ts FROM 'station/events'")
        self.assertEqual(rule["actions"][0]["cloudwatchLogs"]["logGroupName"], "/station/events")
        # metric filters: eight, in the Station namespace, MissedFaults with a default value and no dimensions
        filters = {c["args"][c["args"].index("--filter-name") + 1]:
                   json.loads(c["args"][c["args"].index("--metric-transformations") + 1])[0] for c in e.aws("logs", "put-metric-filter")}
        self.assertEqual(len(filters), 8)
        self.assertEqual({f["metricNamespace"] for f in filters.values()}, {"Station"})
        self.assertEqual({f["metricName"] for f in filters.values()}, METRICS)
        self.assertEqual(filters["alerts"]["dimensions"], {"Device": "$.device"})
        self.assertEqual(filters["score"]["dimensions"], {"Version": "$.model_version"})
        self.assertEqual(filters["input_by_device"]["dimensions"], {"Device": "$.device"})
        self.assertEqual(filters["missed_faults"]["defaultValue"], 0)
        self.assertNotIn("dimensions", filters["missed_faults"])
        for f in filters.values():
            self.assertFalse("dimensions" in f and "defaultValue" in f)    # CloudWatch does not allow it
        pattern = [c["args"][c["args"].index("--filter-pattern") + 1] for c in e.aws("logs", "put-metric-filter")
                   if c["args"][c["args"].index("--filter-name") + 1] == "missed_faults"][0]
        self.assertEqual(pattern, '{ ($.truth = "anomaly") && ($.alert IS FALSE) }')
        # dashboard
        (dash,) = e.aws("cloudwatch", "put-dashboard")
        self.assertEqual(dash["args"][dash["args"].index("--dashboard-name") + 1], "station")
        body = json.loads(list(dash["files"].values())[0])
        alarm_widget = [w for w in body["widgets"] if "alarms" in w["properties"].get("annotations", {})][0]
        self.assertEqual(alarm_widget["properties"]["annotations"]["alarms"],
                         ["arn:aws:cloudwatch:us-east-1:123456789012:alarm:station-missed-faults"])
        # alarm → Lambda
        (alarm,) = e.aws("cloudwatch", "put-metric-alarm")
        a = alarm["args"]
        self.assertEqual(a[a.index("--alarm-name") + 1], "station-missed-faults")
        self.assertEqual(a[a.index("--namespace") + 1], "Station")
        self.assertEqual(a[a.index("--metric-name") + 1], "MissedFaults")
        self.assertTrue(a[a.index("--alarm-actions") + 1].endswith(":function:station-rollback"))
        (permission,) = e.aws("lambda", "add-permission")
        self.assertIn("lambda.alarms.cloudwatch.amazonaws.com", permission["args"])

    def test_alarm_threshold_can_be_changed(self):
        e = self.run_setup(None, ALARM_THRESHOLD="12")
        (alarm,) = e.aws("cloudwatch", "put-metric-alarm")
        self.assertEqual(alarm["args"][alarm["args"].index("--threshold") + 1], "12")

    def test_teardown_deletes_everything(self):
        e = Environment(self)
        r = e.run("cloud/teardown.sh", "--yes")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for prefix in (("cloudwatch", "delete-alarms"), ("lambda", "delete-function"), ("iot", "delete-topic-rule"),
                       ("logs", "delete-log-group"), ("cloudwatch", "delete-dashboards"), ("iot", "delete-role-alias"),
                       ("ssm", "delete-parameter"), ("s3", "rb")):
            self.assertEqual(len(e.aws(*prefix)), 1, prefix)
        self.assertEqual(len(e.aws("iot", "delete-thing")), 5)
        self.assertEqual(len(e.aws("iot", "delete-thing-group")), 2)
        self.assertEqual(len(e.aws("iam", "delete-role")), 3)
        self.assertIn("station-missed-faults", e.aws("cloudwatch", "delete-alarms")[0]["args"])
        self.assertIn("/station/events", e.aws("logs", "delete-log-group")[0]["args"])
        self.assertIn("s3://station-123456789012-us-east-1", e.aws("s3", "rb")[0]["args"])

    def test_teardown_asks_for_confirmation(self):
        e = Environment(self)
        r = e.run("cloud/teardown.sh", stdin="no\n")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(e.aws("lambda", "delete-function"), [])


if __name__ == "__main__":
    unittest.main()
