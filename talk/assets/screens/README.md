# AWS evidence on the slides

One image per step of the talk, from the end-to-end rehearsal of October 12, 2026 (real AWS, real MIMII DUE audio). Each one appears on the last click of its slide, in a window whose bar says where it comes from.

| File | Slide | What it shows | Source |
|---|---|---|---|
| `s3-versiones.png` | 16 · Paso 1 | `publish.sh` uploading each version to its own S3 prefix | `03-healthy-publish-deploy.txt` |
| `gg-componente.png` | 18 · Paso 3 | `publish.sh` creating `com.station.Listener` 1.0.0 and 2.0.0, threshold as configuration | `03-healthy-publish-deploy.txt` |
| `gg-despliegues.png` | 19 · Paso 4 | `list-deployments` for `StationRing0` (1.0.0 → 2.0.0 → rollback, active) and `StationRing1` (only 1.0.0) | `21-greengrass-deployments.txt` |
| `gg-equipos.png` | 20 · Paso 5 | the five core devices `HEALTHY`, and pump-03's alerts arriving 28–55 s late after 45 s offline | `03-…`, `13-act2-network-back.txt` |
| `cw-dashboard.png` | 21 · Paso 6 | the six widgets of the `station` dashboard during the rehearsal | `40-dashboard-*.png` (`get-metric-widget-image`) |
| `cw-alarma.png` | 25 · Demo | missed faults crossing the threshold of 8, the alarm, the Lambda rolling back to 1.0.0 and pump-01 alerting again | `40-dashboard-6-…`, `20-alarm-and-lambda.txt`, `16-act3-…` |

The source files are in `evidencia-e2e/en/`, which stays out of the repo because it holds the AWS account id. The images mask it (`‹cuenta›`). They are rendered by [`talk/tools/screens/render.js`](../../tools/screens/render.js); the lines are copied as they came out, only trimmed (latency, long ids) to fit.

To use console screenshots instead, save them here with the same names (`.png` or `.jpg`) and rebuild the deck. Hide the account name and id, and crop wide: the window fits up to 1429 × 490 px.
