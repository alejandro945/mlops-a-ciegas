# infra · the station's cloud with Terraform

Creates with Terraform everything the PoC needs in AWS, plus the identity of the five pumps and the EC2 that hosts them. It replaces `cloud/setup.sh`, which stays as the path without Terraform; both use the same names, and `tests/test_infra_terraform.py` checks that they do not drift apart.

The state lives in S3 and is shared by your laptop and GitHub Actions. The usual way is to apply from Actions (see "With GitHub Actions"); applying from your laptop works the same because it is the same state.

| File | What it creates |
|---|---|
| `main.tf` | Artifacts bucket (private, encrypted) and the `/station/last_good_version` parameter |
| `iot.tf` | Thing groups `StationRing0` and `StationRing1`, the token exchange role and its alias, the pumps' IoT policy and, with `manage_identity = true`, the five things with their certificates (stored in Parameter Store as SecureString) |
| `observability.tf` | Log group `/station/events`, IoT rule `station_events` with `arrived_ts`, the seven metric filters (namespace `Station`), the `station` dashboard, the `station-rollback` Lambda and the `station-missed-faults` alarm that invokes it |
| `host.tf` | The pumps' Linux EC2: Amazon Linux 2023 with Docker, no inbound ports (access through Session Manager only), IMDSv2 with a single hop so the containers cannot use the EC2 role |
| `backend.tf` | The state in S3, encrypted and locked (`use_lockfile`). The bucket and the region come through `-backend-config` |
| `github/` | Applied once from your laptop: the state bucket, GitHub's OIDC provider and the roles `github-station-plan` (read only) and `github-station-apply` (everything except IAM; in IAM, only the PoC's roles) |

## With GitHub Actions

Once, from `poc-devopsdays/`, with an administrator user of the test account and `gh` logged in:

```bash
gh repo create <owner>/mlops-a-ciegas --private                 # if the repo does not exist
gh api repos/<owner>/mlops-a-ciegas/actions/oidc/customization/sub --jq .sub_claim_prefix
# repo and sub_prefix (what the previous line printed) go in infra/github/terraform.tfvars
terraform -chdir=infra/github init
terraform -chdir=infra/github apply
./infra/github/connect-repo.sh       # repo variables, the aws-poc environment and infra/backend.hcl
```

New GitHub repos sign the OIDC token with the immutable format (`repo:owner@id/name@id:…`); that is why the roles accept that prefix as well as the classic one. If the first `plan` in Actions fails with "Not authorized to perform sts:AssumeRoleWithWebIdentity", check `sub_prefix`.

From then on, `.github/workflows/infra.yml` does this:

| When | What it does |
|---|---|
| A PR that touches `infra/`, the Lambda or the dashboard | `plan` with the read-only role; the plan goes to the PR and to the job summary |
| A push to `main` | `plan` only: shows what would change |
| *Run workflow* by hand (Actions → infra) | `plan`, `apply` or `destroy`. Destroy first deletes the core devices and empties the artifacts bucket |

`apply` never runs on its own: you trigger it, and only from `main` (the `aws-poc` environment requires it). On a private repo on GitHub's free plan the environment cannot ask for approval; that is why apply is manual.

Repo variables the workflow reads: `AWS_REGION`, `TF_STATE_BUCKET`, `AWS_ROLE_PLAN`, `AWS_ROLE_APPLY` (set by `connect-repo.sh`) and, optionally, `ALARM_THRESHOLD`, which changes `alarm_threshold` without touching the code (default 8). The plan is never uploaded as an artifact: it carries the state, and the state carries the pumps' keys.

`.github/workflows/tests.yml` runs `fmt`, `validate` and every test in `tests/` on each PR, without touching AWS.

## From your laptop

```bash
cd poc-devopsdays/infra
terraform init -backend-config=backend.hcl   # backend.hcl is written by github/connect-repo.sh
terraform plan                               # or: terraform apply -var alarm_threshold=6
terraform output next_steps                  # the next steps, with the EC2 id
```

If you do not have `backend.hcl`, write it by hand:

```hcl
bucket = "station-tfstate-<account>-<region>"
region = "<region>"
```

Then, from the `poc-devopsdays/` folder:

1. `./infra/upload-to-host.sh` uploads the code, `build/` and `data/station/` to the bucket.
2. Open a session on the EC2 with `terraform -chdir=infra output -raw connect_to_host` (you need the [Session Manager plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)).
3. On the EC2: `sudo su - ec2-user`, `fetch-poc`, `cd ~/poc-devopsdays`, `./fleet/build.sh` and `IDENTITY=terraform ./fleet/up.sh` (the variable is already set in the session).
4. The demo is the same: `./demo/publish.sh 1.0.0`, `./demo/deploy.sh 1.0.0 all`, `./demo/watch.sh`.

## Variables you will want to change

| Variable | Default | What for |
|---|---|---|
| `region` | `us-east-1` | The whole PoC |
| `alarm_threshold` | `8` | Missed faults per minute that trigger the rollback; tuned during the rehearsal |
| `instance_type` | `t3.large` | Each pump is a JVM plus the model: measure memory with all five running |
| `manage_identity` | `true` | `false` lets the Greengrass installer register the pumps, as without Terraform |
| `create_host` | `true` | `false` if you already have a Linux host with Docker |
| `subnet_id` | default VPC | If your account has no default VPC, pass a public subnet |
| `force_destroy_bucket` | `false` | `true` so `destroy` deletes the bucket even with artifacts in it |

## What you need to know

- **The state holds the pumps' private keys.** It lives in `s3://station-tfstate-<account>-<region>/poc-devopsdays/infra.tfstate`: private, encrypted, versioned and TLS only. Anyone with S3 permissions in the account can read it: today, your user and the two GitHub roles. If that does not work for you, use `manage_identity = false`.
- **One path applies at a time.** Actions and your laptop share the state and the lock; if both try to `apply` at once, the second one waits or fails with "state locked". If you pass different variables on your laptop (`-var alarm_threshold=6`), the next apply from Actions puts them back: keep your settings in the repo variables.
- **If you already ran `cloud/setup.sh` or the Greengrass installer in this account,** the `GreengrassV2TokenExchangeRole` role, its alias, the policies and the thing groups already exist and `apply` fails with "already exists". Delete them with `./cloud/teardown.sh`, or import them (`terraform import 'aws_iam_role.tes' GreengrassV2TokenExchangeRole`, and so on for each one).
- **To delete everything:** `./fleet/down.sh` on the EC2, then `./infra/clean-core-devices.sh` (the core devices are created by Greengrass, not Terraform) and `terraform -chdir=infra destroy`.
- **What Terraform does not manage:** component versions and deployments. They are the demo: `publish.sh`, `deploy.sh` and the Lambda create them.

## What was verified and what was not

- `terraform fmt`, `init` and `validate` pass in `infra/` and in `infra/github/` (Terraform 1.12.2, AWS provider 5.100.0). The lock file has hashes for Linux and macOS.
- `tests/test_infra_terraform.py` checks that the names, the rule, the seven filter patterns, the alarm and the pumps' policy are the same as in `cloud/setup.sh`, and runs `fleet/up.sh` and the entrypoint with `IDENTITY=terraform` against a fake `aws` and `docker`: they fetch the identity, mount it only during the install, install the nucleus with `--init-config`, and no AWS credential gets into the container.
- **`plan` and `apply` against AWS are not covered by the tests.** The first `plan` in Actions is the test of the GitHub roles' permissions.
- The riskiest part is installing the nucleus with an identity from outside (`--init-config`): if it fails, `docker logs pump-01` and `fleet/logs/pump-01/greengrass.log` say why.
