# AWS console screenshots on the slides

One AWS console screenshot per step of the talk, and one image per act of the run, taken right after the end-to-end rehearsal of October 18, 2026: real AWS, real MIMII DUE audio, the three acts of the demo run on the live fleet. They all live in block 04, «La evidencia en AWS»: the step slides explain, this block shows.

| File | Slide | Console page |
|---|---|---|
| `s3-versiones.png` | 25 · El modelo, versionado | S3 › the bucket › `station/`: the `1.0.0/` and `2.0.0/` folders |
| `gg-componente.png` | 25 · El modelo, versionado | IoT Greengrass › Components › `com.station.Listener`: both versions, and the threshold in the default configuration |
| `gg-despliegues.png` | 29 · Acto 3, clic 2 | IoT Greengrass › Deployments (filtered by `StationRing`): ring 0 on `rollback-to-1.0.0`, created by the Lambda; ring 1 still on its first 1.0.0 |
| `gg-equipos.png` | (not on the slides now) | IoT Greengrass › Core devices: `pump-01` to `pump-05`, Healthy |
| `cw-dashboard.png` | 26 · La flota, reportando | CloudWatch › Dashboards › `station`: the totals and the input per pump (pump-05's drift, pump-01 on v2) |
| `cw-alarma.png` | 29 · Acto 3, clic 1 | CloudWatch › Alarms › `station-missed-faults`: missed faults crossing 8 and the moment in ALARM |

The three act slides (27–29) replace the live demo. They show the run itself, rendered by [`render.js`](../../tools/screens/render.js) (`ONLY=acto1,acto2,acto3`) from that run's formatted events and dashboard charts:

| File | Slide | What it shows |
|---|---|---|
| `acto1.png` | 27 · Acto 1 | `watch.sh pump-03`: normal, then `fault.sh` at 19:58:36 and ALERT on that same clip |
| `acto2.png` | 28 · Acto 2 | pump-03 offline 45 s while the other four keep reporting, its events arriving late (14, from 11 to 50 s), and the input per pump with pump-05's drift |
| `acto3.png` | 29 · Acto 3 | v2 to ring 0, missed faults, the alarm (20:15:14), the Lambda back to 1.0.0 and pump-01 alerting on v1 (20:15:22): 88 s from the fault |

How they were taken: in Chrome, signed in to the console, with the account id replaced on the page by `‹cuenta›` before each capture (top bar, bucket name, ARNs), the side navigation collapsed and the capture cropped to the page. The dashboard is shown at 55 % zoom so the totals and the input row fit.

To retake them: bring the stack up and run the demo (see `poc-devopsdays/README.md`), then capture the same pages with the same names (`.png` or `.jpg`) and rebuild the deck. The window fits up to 1429 × 490 px at 1×.

[`talk/tools/screens/render.js`](../../tools/screens/render.js) is the fallback: it renders the same six slots from a rehearsal's CLI evidence (`evidencia-e2e/<date>/`, out of the repo because it holds the account id) when no console is at hand.
