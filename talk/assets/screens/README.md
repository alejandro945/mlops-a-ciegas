# AWS console screenshots on the slides

One AWS console screenshot per step of the talk, taken right after the end-to-end rehearsal of October 18, 2026: real AWS, real MIMII DUE audio, the three acts of the demo run on the live fleet. Each one appears on the last click of its slide, in a window whose bar says what it is.

| File | Slide | Console page |
|---|---|---|
| `s3-versiones.png` | 16 · Paso 1 | S3 › the bucket › `station/`: the `1.0.0/` and `2.0.0/` folders |
| `gg-componente.png` | 18 · Paso 3 | IoT Greengrass › Components › `com.station.Listener`: both versions, and the threshold in the default configuration |
| `gg-despliegues.png` | 19 · Paso 4 | IoT Greengrass › Deployments (filtered by `StationRing`): ring 0 on `rollback-to-1.0.0`, created by the Lambda; ring 1 still on its first 1.0.0 |
| `gg-equipos.png` | 20 · Paso 5 | IoT Greengrass › Core devices: `pump-01` to `pump-05`, Healthy |
| `cw-dashboard.png` | 21 · Paso 6 | CloudWatch › Dashboards › `station`: the totals and the input per pump (pump-05's drift, pump-01 on v2) |
| `cw-alarma.png` | 25 · Demo | CloudWatch › Alarms › `station-missed-faults`: missed faults crossing 8 and the moment in ALARM |

How they were taken: in Chrome, signed in to the console, with the account id replaced on the page by `‹cuenta›` before each capture (top bar, bucket name, ARNs), the side navigation collapsed and the capture cropped to the page. The dashboard is shown at 55 % zoom so the totals and the input row fit.

To retake them: bring the stack up and run the demo (see `poc-devopsdays/README.md`), then capture the same pages with the same names (`.png` or `.jpg`) and rebuild the deck. The window fits up to 1429 × 490 px at 1×.

[`talk/tools/screens/render.js`](../../tools/screens/render.js) is the fallback: it renders the same six slots from a rehearsal's CLI evidence (`evidencia-e2e/<date>/`, out of the repo because it holds the account id) when no console is at hand.
