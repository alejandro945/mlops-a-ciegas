# AWS console screenshots on the slides

One AWS console screenshot per step of the talk, and one image per act of the run, taken right after the end-to-end rehearsal of October 18, 2026: real AWS, real MIMII DUE audio, the three acts of the demo run on the live fleet. They all live in block 04, «La evidencia en AWS»: the step slides explain, this block shows.

| File | Slide | Console page |
|---|---|---|
| `s3-versiones.png` | 25 · El modelo, versionado | S3 › the bucket › `station/`: the `1.0.0/` and `2.0.0/` folders |
| `gg-componente.png` | 25 · El modelo, versionado | IoT Greengrass › Components › `com.station.Listener`: both versions, and the threshold in the default configuration |
| `gg-despliegues.png` | 30 · Acto 3, clic 2 | IoT Greengrass › Deployments (filtered by `StationRing`): ring 0 on `rollback-to-1.0.0`, created by the Lambda; ring 1 still on its first 1.0.0 |
| `gg-equipos.png` | 26 · La flota, en línea | IoT Greengrass › Core devices: `pump-01` to `pump-05`, Healthy |
| `cw-dashboard.png` | 27 · Lo que reporta | CloudWatch › Dashboards › `station`: the totals and the input per pump (pump-05's drift, pump-01 on v2) |
| `cw-alarma.png` | 30 · Acto 3, clic 1 | CloudWatch › Alarms › `station-missed-faults`: missed faults crossing 8 and the moment in ALARM |

The three act slides (28–30) replace the live demo. They show the run itself, rendered by [`render.js`](../../tools/screens/render.js) (`ONLY=acto1,acto2,acto3`) from that run's formatted events and dashboard charts:

| File | Slide | What it shows |
|---|---|---|
| `acto1.png` | 28 · Acto 1 | `watch.sh pump-03`: normal, then `fault.sh` at 19:58:36 and ALERT on that same clip |
| `acto2.png` | 29 · Acto 2 | pump-03 offline 45 s while the other four keep reporting, its events arriving late (14, from 11 to 50 s), and the input per pump with pump-05's drift |
| `acto3.png` | 30 · Acto 3 | v2 to ring 0, missed faults, the alarm (20:15:14), the Lambda back to 1.0.0 and pump-01 alerting on v1 (20:15:22): 88 s from the fault |

How they were taken: in Chrome, signed in to the console, with the account id replaced on the page by `‹cuenta›` before each capture (top bar, bucket name, ARNs), the side navigation collapsed and the capture cropped to the page. The dashboard is shown at 55 % zoom so the totals and the input row fit.

To retake them: bring the stack up and run the demo (see `poc-devopsdays/README.md`), then capture the same pages with the same names (`.png` or `.jpg`) and rebuild the deck. The window fits up to 1429 × 490 px at 1×.

[`talk/tools/screens/render.js`](../../tools/screens/render.js) is the fallback: it renders the same six slots from a rehearsal's CLI evidence (`evidencia-e2e/<date>/`, out of the repo because it holds the account id) when no console is at hand.

## Tech Day Cali (`cali/`)

The Cali deck (`DECK_THEME=tdc`) looks in `cali/` first, then here. These come from the end-to-end run of November 16, 2026, the first one with the judge (Step Functions `station-judge`): the console captured in Chrome with the account id replaced by `‹cuenta›` on the page, and the station page itself (`talk/estacion.html`, key D in the deck) rendered at the act's moment.

| File | Slide | What it shows |
|---|---|---|
| `s3-versiones.jpg` | El modelo, versionado | S3 › `station/`: `1.0.0/`, `1.1.0/` (the carrier: 1.0.0 deciding with 2.0.0 in shadow) and `2.0.0/` |
| `gg-componente.jpg` | El modelo, versionado | IoT Greengrass › Components › `com.station.Listener`: the three versions and the threshold in the default configuration |
| `gg-equipos.jpg` | La flota, en línea | IoT Greengrass › Core devices: `pump-01` to `pump-05`, Healthy |
| `cw-dashboard.jpg` | Lo que reporta | CloudWatch › Dashboards › `station` over the run |
| `st-acto1.png` | Acto 1 | the station page: pump-03 goes to ALERT |
| `st-vuelve.png` · `st-deriva.png` | Acto 2 | the station page: the queued events arrive late; pump-05 drifts |
| `cw-logs.jpg` | Acto 2 | Logs Insights: the late events, with decision and arrival times |
| `st-sombra.png` · `sfn-sombra.jpg` | Acto 3 | the station page with 2.0.0 in shadow on the canary and the judge baking; the same execution in Step Functions |
| `st-veredicto.png` · `sfn-veredicto.jpg` | Acto 3 | the judge rejects 2.0.0; the execution's Reject → Notify → CandidateRejected |
| `st-alarma.png` | Acto 3b | the station page: without the judge, the alarm, the Lambda and the way back to 1.0.0 |
| `cw-alarma.jpg` | Acto 3b | CloudWatch › Alarms › `station-missed-faults` in ALARM |
| `gg-despliegues.jpg` | Acto 3b | IoT Greengrass › Deployments: shadow, reject, 2.0.0 to ring 0 and the rollback |

To retake them: `python3 talk/tools/build_station.py evidencia-e2e/<date>` and the capture script in the session notes render the `st-*.png`; the console pages are captured by hand (or with Claude in Chrome) with the same names.
