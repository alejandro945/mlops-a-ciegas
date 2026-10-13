# The pump model

A small device listens to a pump through a microphone. The model learned **only from normal sound**: when it cannot reconstruct what it hears, the error goes up and the device raises an alert. The audio never leaves the device; what leaves is an event of a few hundred bytes.

```
WAV 16 kHz ──► log-mel (64 bands, 5 frames = 320 numbers per vector) ──► ONNX autoencoder
          ──► reconstruction error per vector ──► clip score (the mean) ──► score > threshold? ──► alert
```

| File | What it does |
|---|---|
| `features.py` | The features: WAV → log-mel → 320-number vectors. Only numpy and the standard library. The same function runs at training time and on the device (it is copied to `component/features.py` and to every `build/<version>/`). |
| `dataset.py` | Reads MIMII DUE from the zip (without extracting it), from a folder or from the synthetic set, and splits the clips. `train.py` and `prepare_data.py` use the same split. |
| `train.py` | Trains v1.0.0 and v2.0.0, quantizes v1 to INT8, measures everything and writes `build/`. |
| `prepare_data.py` | Builds the audio for the five pumps (`data/station/`) and the two clips for slide 2 (`talk/assets/audio/`). |
| `synth.py` | A synthetic set with the same file names, only for testing the pipeline. |
| `bench_device.py` | FP32 versus INT8 on the device itself (run it inside the pumps' image on the host); writes `build/device_bench.json`, which the deck reads as `device.*`. |
| `../component/inference.py` | The component that runs on the device: listens, decides and publishes one event per clip. |

## The model

- **Autoencoder** from scikit-learn (`MLPRegressor`, layers 320 → 128 → 128 → 8 → 128 → 128 → 320, ReLU) with a `StandardScaler` in front, in a `Pipeline` exported with skl2onnx. Three nodes are appended to the graph (subtract, square, mean) so the `.onnx` returns the error of each vector directly: the contract is "features in, error out".
- **Clip score** = mean reconstruction error over its ≈ 300 vectors.
- **Threshold** = 95th percentile of the scores of the normal validation clips (10 % of the normal training clips, which the model did not see). It means: you accept that about 5 % of normal sound raises an alert. It is a single threshold for the three sections, as in the fleet. Change it with `--percentile`. On the device it is component configuration: it changes without retraining.
- **v1.0.0**: learns from normal sound of the *source* domain.
- **v2.0.0** ("the bad version with a story"): the same model, but its training includes the week a pump was already failing: half of the *source* fault clips from pump-01's section (section 00), with all their frames. It learns that failing is normal. It is measured on faults it did **not** see.
- **INT8**: `onnxruntime.quantization.quantize_dynamic` on v1's ONNX (INT8 weights, activations quantized on the fly). Only for measuring: the component uses `model.onnx`.
- **Training with little RAM**: each training clip contributes 48 random vectors (`--frames`), not all ≈ 300.

## The data and its license

**MIMII DUE** (Hitachi, Ltd.), pump development set: `dev_data_pump.zip`. License **CC BY-NC-SA 4.0** (attribution, non-commercial, share-alike). https://zenodo.org/records/4740355

> Tanabe, R., Purohit, H., Dohi, K., Endo, T., Nikaido, Y., Nakamura, T., and Kawaguchi, Y. (2021). *MIMII DUE: Sound Dataset for Malfunctioning Industrial Machine Investigation and Inspection with Domain Shifts due to Changes in Operational and Environmental Conditions*. arXiv:2105.02702.

10 s clips, 16 kHz, mono. Three sections (00, 01, 02); each one is a group of pumps. The *source* domain is the training condition; *target* is another operating speed and another ambient noise. Per section there are about a thousand *source* normal clips for training, three *target* ones and, for testing, normal and fault clips of each domain. `train.py` prints how many it found.

Names are discovered with `section_(\d+)_(source|target)_(train|test)_(normal|anomaly)_(\d+)`, so it does not matter whether the zip has a root folder or extra attributes at the end of the name. If the zip holds other machines, it keeps `pump`.

### The split (`dataset.py`, deterministic)

| Split | Clips | What for |
|---|---|---|
| train | 90 % of the *source* normal training clips | v1 (and v2) learn from them |
| val | 10 % of the *source* normal training clips | sets the threshold |
| contamination | half of the *source* test faults of section 00 | only goes into v2 |
| test | every test clip except the contamination | measure and build the fleet |

The three *target* training clips are not used: the model never heard the other speed.

### The fleet (`prepare_data.py`)

`data/station/pump-0N/{normal,fault,shifted}/`, five clips per folder, all **test** clips, never training or contamination ones:

- `normal`: *source* normal · `fault`: *source* faults · `shifted`: *target* normal (the pump changed speed).
- Five pumps come from three sections: **pump-01 and pump-04 share section 00, and pump-02 and pump-05 share section 01**, each with different clips. pump-03 has section 02.
- `build/clips.json` says which clip ended up in each folder.
- With `--scores build/scores.csv` (after training) it picks clips so the demo looks the same every time: faults that v1 detects (and, on pump-01, that v2 misses) and normal clips without an alert. The `shifted` folders are picked at random. **The talk's numbers come from the whole test set, not from these clips.**
- The two clips for slide 2 come from pump-03's section, *source* domain, outside the fleet and the training set: `talk/assets/audio/pump-a.wav` (normal) and `pump-b.wav` (fault), copied unchanged, with `ATTRIBUTION.txt` next to them. With `--scores`, B is the clearest fault for v1 and A a typical normal clip. **With synthetic audio it does not touch `talk/assets/`.**

## Running it with the real data

Put the zip (manual download from Zenodo) at `poc-devopsdays/data/dev_data_pump.zip`. From `poc-devopsdays/`:

```bash
python3 model/train.py --data data/dev_data_pump.zip                                  # models, metrics, scores
python3 model/prepare_data.py --data data/dev_data_pump.zip --scores build/scores.csv  # fleet and talk audio
python3 ../talk/tools/metrics.py v1.recall_source v1.recall_target v2.recall_source int8.agree_pct
python3 -m unittest discover -s tests -p 'test_model*.py' -v                          # the pipeline, with synthetic audio
```

If you already extracted it, `--data` also takes the folder (for example `data/pump/`, with `train/`, `source_test/` and `target_test/`). Measured in the sandbox (4 CPUs, 3 GB of RAM) with a synthetic set the expected size of the real one (4,209 clips of 10 s): `train.py` takes **≈ 1 minute** and uses **≈ 1 GB** of peak memory; `prepare_data.py`, seconds. Reading the real zip adds the time to decompress the audio, clip by clip.

To listen to a pump on your machine, without AWS:

```bash
echo fault > /tmp/mode
AWS_IOT_THING_NAME=pump-03 python3 build/1.0.0/inference.py --model build/1.0.0/model.onnx \
    --stats build/1.0.0/stats.json --audio-root data/station --mode-file /tmp/mode --interval 1 --local
```

Without the real data (only tests the pipeline; everything is marked `"synthetic": true`):

```bash
python3 model/synth.py                                   # data/synthetic/, 141 clips
python3 model/train.py --data data/synthetic
python3 model/prepare_data.py --data data/synthetic --scores build/scores.csv
```

## What ends up in `build/`

| File | What it is |
|---|---|
| `<version>/model.onnx` | The autoencoder. Input `features` (N × 320, float32), output `score` (N): error per vector. |
| `<version>/stats.json` | The fingerprint of normal sound (mean and standard deviation of the 320 features), the threshold, the percentile, the version, the sha256 of `model.onnx` and `"synthetic"`. |
| `<version>/features.py`, `inference.py` | The code that runs on the device, copied as is. |
| `1.0.0/model.int8.onnx` | v1 in INT8, only for measuring. |
| `metrics.json` | The numbers on the slides (below). |
| `scores.csv` | The score of every test clip with v1, v2 and INT8, and its `input_z`. Columns `clip, section, domain, truth, split, v1, v2, int8, z`; `split` is `test` or `contamination`. |
| `clips.json` | The map of the fleet (`pumps`) and of the talk audio (`talk`). |

## What each `metrics.json` key means

Raw values: fractions from 0 to 1, AUC from 0 to 1, KB and ms. `talk/tools/metrics.py` formats them for the slides and returns the slide placeholder «por medir» (not measured yet) if `"synthetic"` is `true`. Everything is measured on the test clips minus the ones that contaminated v2, with the three sections together and a single threshold.

| Key | What it is |
|---|---|
| `dataset`, `synthetic` | Where the audio came from. With `true`, no number reaches a slide. |
| `v1.auc_source`, `v1.auc_target` | v1's AUC (normal vs fault) in the training domain and in the new one. 0.5 is chance. |
| `v1.recall_source`, `v1.recall_target` | Detected faults at the threshold: fraction of fault clips with an alert. |
| `v1.false_alarm_source`, `v1.false_alarm_target` | False alarms: fraction of normal clips with an alert. |
| `v1.threshold` | v1's threshold. |
| `v1.alert_rate_source`, `v2.alert_rate_source` | Fraction of *source* clips (normal and fault) with an alert. v2 raises fewer alerts. |
| `v2.auc_source`, `v2.recall_source`, `v2.false_alarm_source` | The same for v2, on faults it did not see in training. `v2.threshold` is its threshold. |
| `int8.size_fp32_kb`, `int8.size_int8_kb` | Size of the `.onnx` in FP32 and in INT8. |
| `int8.lat_fp32_ms`, `int8.lat_int8_ms` | Latency per 10 s clip: features + inference, median, CPU, one thread, not counting the disk read. The features cost the same in both. |
| `int8.agree_pct` | Fraction of test clips (*source* and *target*) with the same decision in FP32 and INT8, with the same threshold. |
| `int8.auc_delta` | INT8 *source* AUC minus FP32 *source* AUC. |
| `input.z_source`, `input.z_target` | Input level: mean `input_z` of the normal clips of each domain (see below). `input.z_val` is the reference with the normal validation clips. |
| `details` | Does not go to slides: counts, epochs, times, peak memory and the same metrics per section (`details.per_section`). |

`input_z` = mean of |(feature − mean) / std| over all the clip's vectors, using the fingerprint in `stats.json`. With training audio it stays below 1; it rises when the sound changes even if the model raises no error.

## The honest part, for the Q&A

- **`truth` only exists in the demo.** The device knows which folder is playing (`fault` → `anomaly`; `normal` and `shifted` → `normal`). In production you do not know it at that moment: it arrives late, with the maintenance work order.
- **v2 is contaminated on purpose.** It simulates a typical mistake (retraining on data nobody reviewed), not something that happened to a customer. v2 runs without errors, with the same latency; it just decides worse.
- **The fleet clips are picked** (with `--scores`) so the demo is repeatable. The slide numbers are not: they come from the whole test set.
- **One threshold for three sections.** The pumps in each section sound different; a threshold per section would improve the numbers. The AUC mixes the sections, so it is not comparable with DCASE 2021 task 2, which is reported per section (that is in `details.per_section`).
- **The model is small on purpose** (≈ 118k parameters, a scikit-learn MLP with no GPU). It is not the state of the art; it is just enough to show the lifecycle.
- **`input_z` is a simple summary.** In production you would use per-window distribution tests (PSI, KS) computed on the device.
- **Synthetic audio:** `synth.py` is for testing the pipeline. Its WAVs carry the `SYNTHETIC` marker in the header (sets made before the rename carry `SINTETICO`, which still counts), `train.py` marks everything with `"synthetic": true` and `prepare_data.py` refuses to copy it to the talk.
- **`data/` should not go to git:** the zip weighs more than 1 GB and the license asks for attribution and share-alike.
