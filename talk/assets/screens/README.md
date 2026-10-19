# AWS evidence on the slides

One image per step of the talk, from the end-to-end rehearsal of October 18, 2026: real AWS, real MIMII DUE audio, the three acts of the demo run on the live fleet. Each one appears on the last click of its slide, in a window whose bar says where it comes from.

| File | Slide | What it shows |
|---|---|---|
| `s3-versiones.png` | 16 · Paso 1 | `aws s3 ls`: each version in its own prefix, `station/1.0.0/` and `station/2.0.0/` |
| `gg-componente.png` | 18 · Paso 3 | `list-component-versions`: `com.station.Listener` 1.0.0 and 2.0.0 |
| `gg-despliegues.png` | 19 · Paso 4 | `list-deployments`: ring 0 went 1.0.0 → 2.0.0 → rollback (active); ring 1 only ever had 1.0.0 |
| `gg-equipos.png` | 20 · Paso 5 | the five core devices `HEALTHY`, and pump-03's alerts arriving 17–44 s late after 45 s offline |
| `cw-dashboard.png` | 21 · Paso 6 | the `station` dashboard by signal: input per pump (pump-05's drift), score vs threshold, alerts, clips per version, the gate, and the Logs Insights fleet table (version and fingerprint per pump) |
| `cw-alarma.png` | 25 · Demo | missed faults crossing the threshold of 8, the alarm, the Lambda rolling back to 1.0.0 and pump-01 alerting again (109 s from the fault) |

The evidence is collected with the AWS CLI after the run (`s3 ls`, `list-component-versions`, `list-core-devices`, `list-deployments`, the alarm history, the Lambda's log, the formatted events, `get-metric-widget-image` for the dashboard's charts and the dashboard's Logs Insights queries). It lives in `evidencia-e2e/<date>/`, which stays out of the repo because it holds the AWS account id; the images mask it (`‹cuenta›`). [`talk/tools/screens/render.js`](../../tools/screens/render.js) renders them; the lines are copied as they came out, only trimmed (latency, the threshold, long ids) to fit.

To use console screenshots instead, save them here with the same names (`.png` or `.jpg`) and rebuild the deck. Hide the account name and id, and crop wide: the window fits up to 1429 × 490 px.
