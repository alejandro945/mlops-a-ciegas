# PoC · The station · MLOps a ciegas

A water utility (made up for the talk) runs pumping stations in rural areas with flaky connectivity. At each station, a small device listens to the pumps through a microphone and a model raises an alert when one starts to sound different. **The audio never leaves the station: what leaves is an event of a few hundred bytes.**

This PoC shows the infrastructure side: how the model reaches a thousand devices, how you see what it decides, what happens when the network drops, and how you roll back when a version hears worse.

**There are no physical devices.** Each "pump" is a Docker container running the real AWS IoT Greengrass V2 nucleus, on a Linux EC2 (AWS requires a Linux host for [Greengrass in Docker](https://docs.aws.amazon.com/greengrass/v2/developerguide/run-greengrass-docker.html)). **Everything else is real AWS:** IoT Core, Greengrass deployments and thing groups, CloudWatch, Lambda, S3 and Parameter Store. There are five pumps: `pump-01` in ring 0 (the canary) and `pump-02` to `pump-05` in ring 1.

It fits in a week.

---

## What you see live

| Act | What you do | What you see |
|---|---|---|
| **1 · Listen** | `./demo/fault.sh pump-03` | Pump 3 sounds like pump B from the start of the talk and the alert shows up |
| **2 · No network** | `./demo/network.sh off pump-03`, wait, `./demo/network.sh on pump-03` | Pump 3 goes quiet while the other four carry on; when it comes back its events arrive "late". Then `./demo/domain.sh pump-05 shifted`: pump 5 changes speed and there is no error at all, but the input drifts away from what the model learned |
| **3 · Deploy by rings and roll back** | `./demo/deploy.sh 2.0.0 ring-0` and `./demo/fault.sh pump-01` | Pump 1 moves to v2 and misses the fault; the alarm triggers the Lambda and pump 1 goes back to v1. Ring 1 never got v2 |

Act 3 punchline: **Greengrass rolls back failed deployments, not wrong models. That gate is yours to build.**

### The model's signals (dashboard `station`)

| Question | Widget | Metric (namespace `Station`) |
|---|---|---|
| What does it decide? | alerts per pump | `Alerts` by `Device` |
| How confident? | score vs threshold, per version | `Score` and `Threshold` by `Version` |
| Does it look like what it learned? | input level | `InputZ` |
| Which version runs where? | inferences per version | `Inferences` by `Version` |
| How fast? | latency | `LatencyMs` |
| What triggers the rollback | faults nobody heard | `MissedFaults` |

---

## Architecture

```
 ONE LINUX EC2 WITH DOCKER · network "station"
 ┌───────────────────────────────────────────────────────────────┐
 │  pump-01       pump-02     pump-03     pump-04     pump-05    │
 │  ring 0        └───────────────── ring 1 ───────────────────┘ │
 │  (canary)                                                     │
 │  each one is a container with the real Greengrass nucleus:    │
 │   · com.station.Listener  (features + ONNX Runtime)           │
 │   · /data/station/<pump>     audio, read-only                 │
 │   · /run/station/mode        normal | fault | shifted         │
 └──────────────┬─────────────────────────────▲──────────────────┘
                │ one event per clip          │ deployment (artifacts
                │ MQTT QoS 1                  │ with digest, from S3)
                ▼                             │
 ┌────────────────────────────┐    ┌──────────┴───────────────────────┐
 │ IoT Core                   │    │ IoT Greengrass + S3              │
 │  rule station_events       │    │  thing groups StationRing0/1     │
 │  (adds arrived_ts)         │    │  component com.station.Listener  │
 └─────────────┬──────────────┘    └──────────▲───────────────────────┘
               ▼                              │ create-deployment with the
 ┌────────────────────────────┐               │ last good version
 │ CloudWatch Logs            │               │ (Parameter Store)
 │  /station/events           │    ┌──────────┴───────────────────────┐
 │  filters → metrics         │    │ Lambda station-rollback          │
 │  dashboard "station"       │ ─▶ │  to ring 0, never to ring 1      │
 │  alarm missed-faults       │    └──────────────────────────────────┘
 └────────────────────────────┘ ALARM
```

### Names

| Thing | Name |
|---|---|
| Component | `com.station.Listener` |
| Things | `pump-01` … `pump-05` |
| Thing groups | `StationRing0` (pump-01) · `StationRing1` (pump-02 to 05) |
| MQTT topic | `station/events` |
| IoT rule | `station_events` → CloudWatch Logs `/station/events` |
| Dashboard · alarm · Lambda | `station` · `station-missed-faults` · `station-rollback` |
| Parameter | `/station/last_good_version` |
| Bucket | `station-<account>-<region>`, prefix `station/<version>/` |
| Docker | network `station`, containers `pump-01`…`pump-05`, volumes `pump-0N-gg`, image `station/greengrass` |

### The event (one per clip heard)

```json
{"device": "pump-03", "model_version": "1.0.0", "sha256": "…", "seq": 1234, "ts": 1760000000000,
 "clip": "section_02_source_test_anomaly_0007", "domain": "source", "score": 0.0123, "threshold": 0.0100,
 "alert": true, "input_z": 1.12, "latency_ms": 3.4, "truth": "anomaly"}
```

`ts` is when the pump decided. The IoT rule adds `arrived_ts` (when it reached the cloud); the difference is how long the pump was offline, and `watch.sh` prints it as "arrived N s late". `input_z` is the mean distance, in standard deviations, between the clip's features and the fingerprint in `stats.json`. `truth` exists only because the demo knows which audio is playing.

---

## The week's plan

| Day | What | Done when |
|---|---|---|
| **1** | Test account, region, the MIMII DUE zip in `data/`, `terraform apply` in `infra/` | The EC2 shows up in Session Manager and `docker run hello-world` works on it |
| **2** | `./infra/upload-to-host.sh`; on the EC2: `fetch-poc`, `./fleet/build.sh`, `IDENTITY=terraform ./fleet/up.sh` | The five pumps show up as *Healthy* in the IoT Greengrass console |
| **3** | Train (`model/train.py`), build the pumps' audio (`model/prepare_data.py`), `./demo/publish.sh` and `./demo/deploy.sh 1.0.0 all` | `./demo/watch.sh` shows events from all five pumps and the dashboard has data |
| **4** | Acts 1 and 2: `fault.sh`, `network.sh`, `domain.sh` | You know how long a pump takes to reconnect and how long the queued events take to arrive |
| **5** | Act 3: `deploy.sh 2.0.0 ring-0`, the alarm and the rollback | You tune `ALARM_THRESHOLD` with your data and time the full rollback |
| **6** | Rehearse the whole talk and record the backup video | You know what to say while you wait for the metrics minute |

---

## Step by step

All commands run from `poc-devopsdays/`. The cloud parts (`cloud/`, `publish.sh`, `deploy.sh`, `watch.sh`) run wherever you have AWS CLI v2; the fleet parts (`fleet/`, `fault.sh`, `domain.sh`, `network.sh`) run **on the EC2**, because they talk to Docker.

### 0 · Before you start

- A **test AWS account** and a region (the scripts use `us-east-1`; change it with `REGION=…`).
- **Permissions.** `cloud/setup.sh` and `cloud/teardown.sh` create and delete roles, policies and resources: run them as an administrator of the test account. `fleet/up.sh` only needs what the Greengrass installer asks for to register the things ([minimal installer policy](https://docs.aws.amazon.com/greengrass/v2/developerguide/provision-minimal-iam-policy.html)); `setup.sh` already creates the token exchange role, its alias and the IoT policies.
- **The EC2.** Linux with Docker (18.09 or later), AWS CLI v2 and `python3`. Outbound internet on 443 and 8883; no inbound ports at all, you get in through Session Manager. Each nucleus is a JVM and each pump adds a process with ONNX Runtime: **measure memory with `docker stats` before picking the size** (a reasonable starting point: an instance with 8 GiB of RAM). If it is Graviton, the image builds for that architecture without changes.

  For example, on Amazon Linux 2023: `sudo dnf install -y docker git && sudo systemctl enable --now docker && sudo usermod -aG docker $USER` (then open a new Session Manager session). With Terraform, the EC2 comes with all of this already set up.
- **The audio.** Download `dev_data_pump.zip` by hand from [Zenodo](https://zenodo.org/records/4740355) and put it at `data/dev_data_pump.zip`. It is MIMII DUE (Hitachi), license CC BY-NC-SA 4.0; the full attribution is in `model/README.md`.

### 1 · The cloud (once)

**With Terraform (recommended).** Creates the cloud, the identity of the five pumps and the EC2 that hosts them; the details are in [`infra/README.md`](infra/README.md).

```bash
cd infra && terraform init -backend-config=backend.hcl && terraform apply && terraform output next_steps
```

The state lives in S3 and the regular `apply` runs in GitHub Actions, with your approval; the one-time preparation (state bucket, OIDC, roles and `backend.hcl`) is in [`infra/README.md`](infra/README.md#with-github-actions).

With Terraform, the pumps never get any AWS credentials: each one boots with its own certificate, which `IDENTITY=terraform ./fleet/up.sh` fetches from Parameter Store only during the installation. To delete everything: `./fleet/down.sh` on the EC2, `./infra/clean-core-devices.sh` and `terraform -chdir=infra destroy`.

**Without Terraform.** The same result in the cloud, without the EC2 or the pumps' identity:

```bash
REGION=us-east-1 ./cloud/setup.sh
```

It creates the bucket, the two thing groups, the token exchange role (allowed to read only this bucket) and its alias, the pumps' minimal IoT policy, the `station_events` rule, the seven metric filters, the dashboard, the Lambda, the alarm and the last-good-version parameter. It is idempotent: you can run it again.

### 2 · The model and the audio

On a machine with Python and the model's libraries (numpy, scikit-learn, skl2onnx, onnx, onnxruntime). The details, the numbers and the license are in [`model/README.md`](model/README.md).

```bash
python3 model/train.py --data data/dev_data_pump.zip                                 # v1.0.0 and v2.0.0 in build/
python3 model/prepare_data.py --data data/dev_data_pump.zip --scores build/scores.csv   # data/station/pump-0N/{normal,fault,shifted}/
```

If you trained on your laptop, take the code, `build/` and the audio to the EC2: with Terraform, `./infra/upload-to-host.sh` on your laptop and `fetch-poc` on the EC2; without Terraform, copy `build/` and `data/station/` to your Linux host however you usually do (for example, `aws s3 sync` through a bucket).

To test only the pipeline without the real audio: `python3 model/synth.py`, then the same two commands with `--data data/synthetic`. Everything is marked `"synthetic": true`, and `publish.sh` refuses to publish it unless you pass `--allow-synthetic`.

### 3 · The fleet (on the EC2)

```bash
./fleet/build.sh                    # image station/greengrass (nucleus 2.18.3, Python and pinned dependencies)
IDENTITY=terraform ./fleet/up.sh    # network "station" + five pumps with the Terraform identity; optional: --small
./fleet/up.sh                       # without Terraform
```

With `IDENTITY=terraform` (on the Terraform EC2 it is already set in the session), each pump is installed with its certificate and no AWS credentials enter the container. Without Terraform, the first boot uses **temporary credentials from your AWS CLI session** to register each pump (thing, certificate, thing group) and deletes them from disk when done. Later boots use no credentials: each pump's identity lives in its `pump-0N-gg` volume. Each nucleus's logs end up in `fleet/logs/pump-0N/`.

`--small` limits each pump to 1 CPU and 1 GB (change it with `CPUS=` and `MEM=`) to look like a small device. Greengrass [does not support per-component resource limits inside Docker](https://docs.aws.amazon.com/greengrass/v2/developerguide/configure-greengrass-core-v2.html#configure-component-system-resource-limits): the limit is the container's. `NUCLEUS_HEAP=256m` caps each JVM's heap (empty = no cap). `WAIT_SECONDS=300` is how long `up.sh` waits for each pump to provision.

Each pump takes a couple of minutes to show up:

```bash
aws greengrassv2 list-core-devices --query 'coreDevices[].[coreDeviceThingName,status]' --output table
```

### 4 · Publish and deploy

```bash
./demo/publish.sh 1.0.0           # uploads build/1.0.0/ to S3 and creates the component version (with the threshold from stats.json)
./demo/publish.sh 2.0.0
./demo/deploy.sh 1.0.0 all        # v1 to both rings; stores /station/last_good_version
./demo/watch.sh                   # in another terminal
```

If no events show up within 2 or 3 minutes: `tail -f fleet/logs/pump-01/com.station.Listener.log` (or `greengrass.log` if the component never started).

A published version is never touched: Greengrass computes each artifact's digest when creating it, and if the file changes in S3 the deployment fails. To change anything, publish a new version.

**The threshold is configuration:** `THRESHOLD=0.02 ./demo/deploy.sh 1.0.0 ring-1` changes it without retraining or republishing.

### 5 · Check which version runs on each pump

```bash
aws greengrassv2 list-installed-components --core-device-thing-name pump-01 \
  --query 'installedComponents[].[componentName,componentVersion,lifecycleState]' --output table
```

### Tests

```bash
python3 -m unittest discover -s tests -p 'test_infra*.py' -v     # infrastructure (no AWS, no Docker)
python3 -m unittest discover -s tests -p 'test_model*.py' -v     # the model
```

---

## The demo on stage

Three windows, large font:

| Left | Top right | Bottom right |
|---|---|---|
| `./demo/watch.sh` | dashboard `station` (15 min, 10 s refresh) | Session Manager terminal on the EC2 |

`watch.sh` prints one line per clip:

```
pump-03  v1.0.0  ALERT  score 0.82 (threshold 0.50)  input 1.1  4 ms  · arrived 40 s late
```

"arrived N s late" shows up when `arrived_ts − ts` goes over 10 s. "missed fault" shows up when the pump sounded faulty and did not alert. `SINCE=10m ./demo/watch.sh` starts with the last 10 minutes (default: 1).

**Act 1 · Listen.** `./demo/fault.sh pump-03`. Point at the alert on screen: the audio never left the station, only that line did. Show pump-03 going up on the dashboard. Leave the fault on: act 2 needs it.

**Act 2 · No network.** `./demo/network.sh off pump-03` and wait 40 to 60 s. Pump 3 goes quiet while the other four carry on; it keeps listening and queues its events locally. Then `./demo/network.sh on pump-03`: they all arrive at once, with "arrived 40 s late". Nothing was lost. Now `./demo/fault.sh pump-03 off`.
Then the drift: `./demo/domain.sh pump-05 shifted`. Pump 5 changed speed. Zero errors, zero exceptions, but the input moves away from what the model learned. To put it back: `./demo/domain.sh pump-05 normal`.

**Act 3 · Deploy by rings and roll back.** `./demo/deploy.sh 2.0.0 ring-0`: a single station gets the new version, the canary. When pump-01 shows v2.0.0 in `watch.sh`, run `./demo/fault.sh pump-01`. Pump 1 runs without errors, with the same latency, and **misses the fault** ("missed fault"). While the alarm gathers data, explain the gate (the dashboard shows "faults nobody heard"). When the alarm fires, the Lambda creates a deployment with the last good version and pump 1 goes back to v1.0.0: ALERT again. Ring 1 never got v2.
Greengrass rolls back failed deployments, not wrong models; that gate is yours to build. When you are done: `./demo/fault.sh pump-01 off`.

The rollback took between 90 and 135 s in the three rehearsals (from `fault.sh pump-01` to the first v1 event); it depends on where in the minute the fault lands, because the metric is per minute. Have something to say meanwhile (annex A2 of the deck). Launch `./demo/deploy.sh 2.0.0 ring-0` while you wait in act 2, so pump-01 is already on v2 when act 3 starts.

**Bring the backup video.** Conference wifi is the worst place in the world to depend on MQTT.

---

## The honest part, for the Q&A

- **`truth` only exists in the demo.** The device knows which folder is playing. In production you don't know it right away: it arrives late, with the maintenance order. There the gate does not count missed faults: it compares the canary against ring 1 (alert rate, score and input distribution) before moving on.
- **One event per clip does not scale.** Every 3 seconds per pump is 5 × 3,600 / 3 = 6,000 messages an hour here, and 8.64 million a day with a thousand pumps at one event every 10 s. In production the device sends a summary per minute and the detail only when something changes. That is not in the PoC.
- **The queue lives in memory.** The nucleus keeps QoS 1 messages while offline in a 2.5 MB queue by default (`mqtt.spooler`). For hours or days without network you need the [`aws.greengrass.DiskSpooler`](https://docs.aws.amazon.com/greengrass/v2/developerguide/disk-spooler-component.html). If the queue fills up, the nucleus rejects new messages.
- **Each nucleus is a JVM.** Five pumps are five JVMs plus five ONNX Runtime processes on a single machine. In real life each device has its own, and it can be nucleus lite if memory is tight.
- **Ring 0 is a single pump.** With a single device the canary has nothing to compare itself against; that is why the signal here is the fault nobody heard.
- **Five pumps come from three MIMII DUE sections.** pump-01 and pump-04 share section 00, and pump-02 and pump-05 share section 01, each with different clips. pump-03 has section 02. The fleet's clips are picked so the demo is repeatable; the numbers on the slides come from the whole test set, not from them.
- **A single threshold** for the three sections, as in the fleet. The pumps in each section sound different.
- **The synthetic audio** (`model/synth.py`) only tests the pipeline. No number from it reaches a slide.
- **The permissions are minimal** and held up in three rehearsals: `StationThingPolicy` only lets a pump connect as `pump-*` and publish to `station/events`. If something fails, start with permissions and region.

---

## What I verified and what I didn't

**Three end-to-end rehearsals on October 12, 2026** (us-east-1, EC2 t3.large, real MIMII DUE audio, Terraform applied from GitHub Actions). The third one ran on the English-named stack, rebuilt from scratch: infra destroyed and re-applied, a brand-new EC2, image built without cache.

| Step | Measured (run 1 · run 2 · run 3) |
|---|---|
| `fleet/build.sh` · `up.sh` on a fresh host | image under 1 min · five pumps installed in 30–40 s · *Healthy* about a minute later |
| `deploy.sh 1.0.0 all` → all five pumps reporting | about 100 s |
| Act 1: `fault.sh pump-03` → ALERT | the next clip (1–4 s). Fault scores 0.35–0.42 against a 0.34 threshold: little margin, but always the same clips |
| Act 2: 45 s offline → queued events arrive | reconnect in ~5 s; up to 50 · 56 · 58 s late; **no `seq` gaps** in any run; 5 duplicates in runs 1 and 2, none in run 3 (QoS 1 is "at least once") |
| Act 2: `domain.sh pump-05 shifted` | input from ~0.8 to 1.6–2.2 from the first clip, plus **false alerts** on 3 of 5 clips |
| Act 3: `deploy.sh 2.0.0 ring-0` → pump-01 on v2 | 15 · 13 · 20 s; no ring 1 pump ever reported v2 |
| Act 3: `fault.sh pump-01` → alarm → Lambda → pump-01 on v1 | **99 · 135 · 90 s**. The Lambda deploys 1 s after the alarm; the pump is back ~15 s later. v2 misses about 12 faults per minute against the threshold of 8 |
| Deployment status in `list-deployments` | thing-group deployments stay `ACTIVE` (not `COMPLETED`) |
| Memory | ~220 MiB per pump; 1.4 GiB used out of 7.8: a t3.medium is enough |

Fixes that came out of the rehearsals: the entrypoint's `--init-config` needs the `.yaml` extension (the nucleus picks the format by extension); `up.sh` cleans the identity folder Docker recreates as root after a crash loop; the dashboard's alarm widget cannot have `metrics`; the Lambda zip has a fixed file mode so its hash matches between a laptop and Actions; the `destroy` workflow cleans the core devices *after* the host is gone (running nuclei re-register them within seconds); the input widget shows the worst pump next to the fleet average, because the average hides one pump's drift.

**Optimization, measured on the device.** `model/bench_device.py`, run inside the pumps' image on the EC2 (Intel Xeon 8259CL, one thread), writes `build/device_bench.json`: FP32 → INT8 goes from 464 to 127 KB, 14.4 → 12.7 ms per clip (4.9 → 3.3 ms of pure inference; feature extraction takes the rest) and makes the same decision on 100 % of the fleet's clips. On an Apple M3 Pro laptop the same script gives 2.6 → 2.0 ms. INT8 is not deployed: on this CPU it saves little.

**SageMaker Neo, tried.** Compiling `model.onnx` for `LINUX X86_64` and `LINUX ARM64` fails with `OperatorNotImplemented: Scaler` (the scikit-learn scaler); the INT8 model also hits `MatMulInteger`. Rewriting `Scaler` as `Sub` + `Mul` (same scores, max difference 4e-8) compiles for both targets in about a minute, but the output needs the DLR runtime (last release 2021). AWS's own guidance after retiring SageMaker Edge Manager (April 2024) is ONNX Runtime on the device and Greengrass V2 to deploy and monitor, which is what this PoC does.

**Still untested:**

- **`"reset": [""]`.** `deploy.sh` and the Lambda send it so each version starts with its own default threshold; the rehearsals used the defaults, so a custom `THRESHOLD=` followed by a new version was never exercised.
- **`abortConfig` and the exponential rollout** with groups of 1 and 4 pumps: the JSON shape matches the [CLI reference](https://docs.aws.amazon.com/cli/latest/reference/greengrassv2/create-deployment.html), but with so few pumps the ramp never shows and nothing ever aborted.
- **`--small`** (CPU and memory limits per container) and the cost (measure it with Cost Explorer).
- **The no-Terraform path** (`cloud/setup.sh`, `IDENTITY=installer`): covered by the unit tests, not run against AWS since the Terraform stack took over.

## Cost

There is no figure here because I haven't measured it. **Measure it with Cost Explorer after the rehearsal.** What bills while it is up:

- **The EC2** (and its disk), per hour running. It is the biggest item; stop it when you are not rehearsing.
- **IoT Core:** messages. With one event every 3 s per pump that is 6,000 an hour.
- **IoT Greengrass:** active core devices (five here); check its pricing page.
- **CloudWatch:** log ingestion and storage (7-day retention), 14 custom metrics (`Alerts` ×5, `Score` ×2, `Threshold` ×2, `Inferences` ×2, `InputZ`, `LatencyMs`, `MissedFaults`), one dashboard and one alarm.
- **Lambda, S3 and Parameter Store:** next to nothing at this scale.

Current prices: [IoT Core](https://aws.amazon.com/iot-core/pricing/) · [IoT Greengrass](https://aws.amazon.com/greengrass/pricing/) · [CloudWatch](https://aws.amazon.com/cloudwatch/pricing/) · [EC2](https://aws.amazon.com/ec2/pricing/on-demand/).

## Shutting everything down

```bash
./fleet/down.sh                   # on the EC2: stops the pumps (keeps their identity)
./fleet/down.sh --delete-things   # also deletes the volumes and the things and certificates in AWS (not with IDENTITY=terraform)
./cloud/teardown.sh               # deletes everything in the cloud, including the bucket (asks for confirmation)
```

With Terraform, use `./infra/clean-core-devices.sh` and `terraform -chdir=infra destroy` instead of the last two. Then stop or terminate the EC2. Check Cost Explorer a day or two later to confirm nothing is still billing.

## If something fails

| Symptom | Where to look |
|---|---|
| The pump does not show up as *Healthy* | `docker logs pump-03` and `fleet/logs/pump-03/greengrass.log`; it is almost always a permission or the region |
| The component does not download artifacts | The `GreengrassV2TokenExchangeRole` role must be able to read `s3://station-<account>-<region>/station/*`; `setup.sh` and Terraform set it up. If you changed a file in S3 after publishing, the digest does not match: new version |
| `fleet/logs/pump-03/com.station.Listener.log` says "could not listen to … Permission denied" | The component runs as `ggc_user`; `up.sh` opens read access to the audio, but if you copied the files afterwards, run `chmod -R a+rX data/station` |
| There are events in `watch.sh` but the dashboard is empty | Metrics take about a minute; check the filters on the `/station/events` log group |
| The alarm fires in act 1 or does not fire in act 3 | Tune `ALARM_THRESHOLD` (missed faults per minute, 8 by default) and run `cloud/setup.sh` again (or `terraform apply`) |
| The pump does not reconnect after `network.sh on` | Wait: the nucleus retries the connection on its own. If several minutes go by, `docker restart pump-03` |

## AWS documentation this PoC uses

- [Greengrass in Docker](https://docs.aws.amazon.com/greengrass/v2/developerguide/run-greengrass-docker.html) · [installer arguments](https://docs.aws.amazon.com/greengrass/v2/developerguide/configure-installer.html) · [nucleus requirements and configuration](https://docs.aws.amazon.com/greengrass/v2/developerguide/greengrass-nucleus-component.html)
- [Publishing components](https://docs.aws.amazon.com/greengrass/v2/developerguide/publish-components.html) · [recipe reference](https://docs.aws.amazon.com/greengrass/v2/developerguide/component-recipe-reference.html) · [creating deployments](https://docs.aws.amazon.com/greengrass/v2/developerguide/create-deployments.html)
- [Authorizing devices to use AWS services](https://docs.aws.amazon.com/greengrass/v2/developerguide/device-service-role.html) · [authentication and minimal IoT policy](https://docs.aws.amazon.com/greengrass/v2/developerguide/device-auth.html)
- [Metric filter syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html)
