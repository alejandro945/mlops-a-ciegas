"""
Listener component that runs on the station's device (Greengrass v2).

Listens to a pump clip by clip: extracts the features (features.py), computes the score with
the ONNX autoencoder and, for each clip, publishes an EVENT to IoT Core. The audio never leaves
the device; what leaves is a JSON of a few hundred bytes:

  device, model_version, sha256      · where, and with which version
  seq, ts, clip, domain              · which clip it heard and when it decided (ts in ms)
  score, threshold, alert            · what it decided and how confident it was
  input_z                            · input level: mean distance, in standard deviations,
                                       to the fingerprint in stats.json
  latency_ms                         · features + inference
  truth                              · demo only: the folder says whether the audio is a fault

With a candidate in SHADOW (--shadow-model): the active model still decides; the candidate only says
what it would have done, on the same clip. The event adds
  shadow_version, shadow_score, shadow_threshold, shadow_alert
  shadow_missed                      · 1 if the active model alerted and the candidate did not
  shadow_extra                       · 1 if the candidate alerted and the active model did not
and the judge (Step Functions) compares them before the candidate ever decides.

With --upload-bucket: the clips worth keeping (an alert, a score near the threshold, a disagreement
with the shadow, one normal clip in --sample-every) go to S3 in batches through stream manager, which
keeps them on disk while there is no network. The event adds  upload  (why the clip was kept).

Demo audio (read-only):  <audio-root>/<device>/{normal,fault,shifted}/*.wav
The --mode-file says which folder is playing (normal, fault or shifted; normal by default) and is
re-read on every clip: demo/fault.sh and demo/domain.sh change it without restarting anything.

Usage on the device (the recipe builds it):
  python3 -u inference.py --model model.onnx --stats stats.json --audio-root /data/station \\
      --mode-file /run/station/mode --version 1.0.0 --topic station/events --threshold 0.83 --interval 3
Without AWS:  AWS_IOT_THING_NAME=pump-03 python3 inference.py ... --local    (prints the events)
"""
import sys
sys.dont_write_bytecode = True               # Greengrass artifacts are read-only
import argparse, hashlib, json, os, re, shutil, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import onnxruntime as ort
import features as F

MODES = ("normal", "fault", "shifted")
TRUTH = {"normal": "normal", "fault": "anomaly", "shifted": "normal"}

p = argparse.ArgumentParser(description="Listens to a pump and publishes one event per clip.")
p.add_argument("--model", required=True)
p.add_argument("--stats", required=True, help="stats.json: feature fingerprint, threshold, version and sha256")
p.add_argument("--audio-root", default="/data/station")
p.add_argument("--mode-file", default="/run/station/mode")
p.add_argument("--version", default="", help="defaults to the one in stats.json")
p.add_argument("--topic", default="station/events")
p.add_argument("--threshold", default="", help="score threshold; empty = the one in stats.json")
p.add_argument("--interval", type=float, default=3.0, help="seconds between clips")
p.add_argument("--local", action="store_true", help="print the events instead of publishing them")
p.add_argument("--max", type=int, default=0, help="stop after N events (0 = never)")
p.add_argument("--shadow-model", default="", help="candidate model that runs in shadow: it never decides")
p.add_argument("--shadow-stats", default="", help="the candidate's stats.json (its threshold and version)")
p.add_argument("--upload-bucket", default="", help="bucket for the clips worth keeping (empty = none)")
p.add_argument("--near", type=float, default=0.15, help="a score this close to the threshold (relative) is kept")
p.add_argument("--sample-every", type=int, default=100, help="also keep one normal clip in N (0 = none)")
a = p.parse_args()


def log(msg):
    print(f"[station] {msg}", file=sys.stderr, flush=True)


stats = json.load(open(a.stats, encoding="utf-8"))
MU = np.array(stats["mean"], dtype=np.float32)
SD = np.array(stats["std"], dtype=np.float32)
version = a.version or stats.get("version", "?")
sha = hashlib.sha256(open(a.model, "rb").read()).hexdigest()
if stats.get("sha256") and stats["sha256"] != sha:
    log(f"WARNING: the sha256 of {a.model} does not match stats.json (artifacts from another version?)")
try:
    threshold = float(a.threshold)
except ValueError:
    threshold = float(stats["threshold"])     # no configuration (or empty): this version's own

so = ort.SessionOptions()
so.intra_op_num_threads = so.inter_op_num_threads = 1
sess = ort.InferenceSession(a.model, so, providers=["CPUExecutionProvider"])
input_name = sess.get_inputs()[0].name
device = os.environ.get("AWS_IOT_THING_NAME", "local-device")
folder = os.path.join(a.audio_root, device)

shadow = None
if a.shadow_model:
    sst = json.load(open(a.shadow_stats, encoding="utf-8"))
    shadow = {"sess": ort.InferenceSession(a.shadow_model, so, providers=["CPUExecutionProvider"]),
              "version": sst.get("version", "?"), "threshold": float(sst["threshold"])}
    shadow["input"] = shadow["sess"].get_inputs()[0].name

if a.local:
    def publish(evt):
        print(json.dumps(evt, ensure_ascii=False), flush=True)
else:
    from awsiot.greengrasscoreipc.clientv2 import GreengrassCoreIPCClientV2
    from awsiot.greengrasscoreipc.model import QOS
    ipc = GreengrassCoreIPCClientV2()

    def _on_done(fut):
        if fut.exception() is not None:
            log(f"could not publish: {fut.exception()}")

    def publish(evt):
        # QoS 1: with no network, the nucleus queue keeps the event and sends it when it comes back.
        # Async: the device keeps listening and deciding even if the network does not answer.
        fut = ipc.publish_to_iot_core_async(topic_name=a.topic, qos=QOS.AT_LEAST_ONCE,
                                            payload=json.dumps(evt).encode())
        fut.add_done_callback(_on_done)


class Uploader:
    """Clips worth keeping → S3, in batches, through stream manager (it keeps them on disk while offline)."""
    STREAM = "station-clips"

    def __init__(self, bucket):
        from stream_manager import (ExportDefinition, MessageStreamDefinition, Persistence,
                                    S3ExportTaskExecutorConfig, StrategyOnFull, StreamManagerClient)
        from stream_manager.data import S3ExportTaskDefinition
        from stream_manager.util import Util
        self.bucket, self.Task, self.Util = bucket, S3ExportTaskDefinition, Util
        self.outbox = os.path.join(os.getcwd(), "outbox")      # the component's work folder
        os.makedirs(self.outbox, exist_ok=True)
        self.client = StreamManagerClient()
        try:
            self.client.create_message_stream(MessageStreamDefinition(
                name=self.STREAM, strategy_on_full=StrategyOnFull.OverwriteOldestData, persistence=Persistence.File,
                export_definition=ExportDefinition(s3_task_executor=[S3ExportTaskExecutorConfig(identifier="clips-to-s3")])))
        except Exception as e:                    # it already exists (the component restarted)
            log(f"stream {self.STREAM}: {e}")

    def keep(self, path, reason, ts):
        day = time.strftime("%Y-%m-%d", time.gmtime(ts / 1000))
        name = f"{ts}_{reason}_{os.path.basename(path)}"
        local = os.path.join(self.outbox, name)
        shutil.copyfile(path, local)
        task = self.Task(input_url="file://" + local, bucket=self.bucket,
                         key=f"clips/device={device}/date={day}/{name}")
        self.client.append_message(self.STREAM, self.Util.validate_and_serialize_to_json_bytes(task))
        old = sorted(os.listdir(self.outbox))[:-500]           # the copies of the last 500 are enough
        for f in old:
            os.remove(os.path.join(self.outbox, f))


uploader = None
if a.upload_bucket and not a.local:
    try:
        uploader = Uploader(a.upload_bucket)
    except Exception as e:                        # without stream manager the pump still listens and decides
        log(f"no clip upload: {e}")


def worth_keeping(evt):
    if evt["alert"]:
        return "alert"
    if evt.get("shadow_missed") or evt.get("shadow_extra"):
        return "disagree"
    if abs(evt["score"] - evt["threshold"]) <= a.near * evt["threshold"]:
        return "near"
    if a.sample_every and evt["seq"] % a.sample_every == 0:
        return "sample"
    return None


def mode():
    try:
        m = open(a.mode_file).read().strip().lower()
    except OSError:
        return "normal"
    return m if m in MODES else "normal"


def clips(m):
    d = os.path.join(folder, m)
    try:
        return sorted(os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith(".wav"))
    except OSError:
        return []


def domain(name, m):
    r = re.search(r"_(source|target)_", name)
    return r.group(1) if r else ("target" if m == "shifted" else "source")


log(f"{device} · model {version} sha256={sha[:12]}… · threshold {threshold:.4g} · audio {folder}")
pos = {m: 0 for m in MODES}
warned = set()
seq = 0
while True:
    start = time.monotonic()
    m = mode()
    playlist = clips(m)
    if not playlist:
        if m not in warned:
            log(f"no clips in {os.path.join(folder, m)}; waiting")
            warned.add(m)
        time.sleep(max(a.interval, 1.0))
        continue
    path = playlist[pos[m] % len(playlist)]
    pos[m] += 1
    try:
        x, sr = F.read_wav(path)
        t0 = time.perf_counter()
        X = F.clip_features(x, sr)
        score = float(sess.run(None, {input_name: X})[0].mean())
        ms = (time.perf_counter() - t0) * 1000
        s_score = float(shadow["sess"].run(None, {shadow["input"]: X})[0].mean()) if shadow else None
    except Exception as e:                    # a broken clip does not take the component down
        log(f"could not listen to {path}: {e}")
        time.sleep(a.interval)
        continue
    seq += 1
    name = os.path.splitext(os.path.basename(path))[0]
    evt = {
        "device": device,
        "model_version": version,
        "sha256": sha,
        "seq": seq,
        "ts": int(time.time() * 1000),
        "clip": name,
        "domain": domain(name, m),
        "score": float(f"{score:.4g}"),
        "threshold": float(f"{threshold:.4g}"),
        "alert": score > threshold,
        "input_z": round(F.input_z(X, MU, SD), 3),
        "latency_ms": round(ms, 2),
        "truth": TRUTH[m],
    }
    if shadow:
        s_alert = s_score > shadow["threshold"]
        evt.update({
            "shadow_version": shadow["version"],
            "shadow_score": float(f"{s_score:.4g}"),
            "shadow_threshold": float(f"{shadow['threshold']:.4g}"),
            "shadow_alert": s_alert,
            "shadow_missed": int(evt["alert"] and not s_alert),
            "shadow_extra": int(s_alert and not evt["alert"]),
        })
    if uploader:
        reason = worth_keeping(evt)
        if reason:
            try:
                uploader.keep(path, reason, evt["ts"])
                evt["upload"] = reason
            except Exception as e:
                log(f"could not keep {name}: {e}")
    publish(evt)
    if a.max and seq >= a.max:
        break
    time.sleep(max(0.0, a.interval - (time.monotonic() - start)))
