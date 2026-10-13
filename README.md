# MLOps a ciegas

Alejandro Varela's talk at DevOpsDays Bogotá 2026 (October 23, Compensar Av. 68). The talk is in Spanish; the code is in English.

How to take a model from the cloud to devices you cannot see, and keep it governed. The case is a rural pumping station, made up for the talk: a model listens to the pumps and raises an alert when one starts to sound different. The audio never leaves the station; what leaves is an event of a few hundred bytes.

## What is here

| Folder | What it is |
|---|---|
| [`poc-devopsdays/`](poc-devopsdays/) | The full demo: the model, the IoT Greengrass component, five simulated pumps in Docker, the demo commands and the cloud with Terraform. Start with its [README](poc-devopsdays/README.md) |
| [`talk/`](talk/) | The talk materials, in Spanish: the slides (`devopsdays.html` opens offline), the script with speaker notes and the figure generators |
| [`.github/workflows/`](.github/workflows/) | `tests` on every PR, and `infra`: Terraform `plan` / `apply` with OIDC (no AWS keys in the repo) |

## Try it

The tests need neither AWS nor Docker:

```bash
cd poc-devopsdays
python3.12 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

To set up the station in your AWS account, follow [`poc-devopsdays/README.md`](poc-devopsdays/README.md). Use a test account: the EC2 is billed for every hour it is running.

## The data

The sounds come from **MIMII DUE** (Tanabe et al., Hitachi, 2021), pumps, licensed [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). They are not in the repo: download them from [Zenodo](https://zenodo.org/records/4740355). The company, the villages and the boss are made up.
