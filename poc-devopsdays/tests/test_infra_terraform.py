"""
Tests for infra/ (Terraform) and for the fleet's IDENTITY=terraform path. No AWS, no Docker, no terraform.

  python3 -m unittest discover -s poc-devopsdays/tests -p "test_infra*.py" -v

What it covers:
  · the .tf files parse as HCL (if python-hcl2 is installed; otherwise those tests are skipped)
  · Terraform and cloud/setup.sh create the same things: names, rule, the seven filters, alarm, pump policy
  · no SSH anywhere: access to the host is Session Manager only
  · fleet/up.sh with IDENTITY=terraform fetches the identity from Parameter Store, mounts it only for
    the installation and asks for no credentials; the entrypoint installs the nucleus with --init-config
  · fleet/down.sh does not delete by hand what Terraform manages
"""
import sys
sys.dont_write_bytecode = True

import json
import os
import re
import stat
import subprocess
import textwrap
import unittest
from pathlib import Path

import test_infra as T          # environment, shims and helpers from the fleet tests

try:
    import hcl2
except ImportError:
    hcl2 = None

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
INFRA = ROOT / "infra"
SETUP = (ROOT / "cloud" / "setup.sh").read_text()


def tf_text():
    return "\n".join(p.read_text() for p in sorted(INFRA.glob("*.tf")))


def hcl_to_text(s):
    """An HCL string as it is after parsing: \\" → \" ."""
    return s.replace('\\"', '"')


def write(path, text, executable=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IXUSR)


def env_of(call):
    """The -e NAME=value pairs of a `docker run` call."""
    a = call["args"]
    return dict(x.split("=", 1) for i, x in enumerate(a) if i and a[i - 1] == "-e")


class Syntax(unittest.TestCase):
    def test_terraform_files_exist(self):
        for f in ("versions.tf", "variables.tf", "main.tf", "iot.tf", "observability.tf", "host.tf", "outputs.tf"):
            self.assertTrue((INFRA / f).is_file(), f)

    @unittest.skipIf(hcl2 is None, "python-hcl2 is not installed")
    def test_tf_files_parse(self):
        for p in sorted(INFRA.glob("*.tf")) + sorted((INFRA / "github").glob("*.tf")):
            with open(p) as f:
                hcl2.load(f)                       # raises if the syntax is wrong

    def test_infra_scripts(self):
        for p in sorted(INFRA.glob("*.sh")) + sorted((INFRA / "github").glob("*.sh")):
            r = subprocess.run(["bash", "-n", str(p)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"{p.name}: {r.stderr}")
            self.assertTrue(p.stat().st_mode & stat.S_IXUSR, f"{p.name} is not executable")
            self.assertIn("set -euo pipefail", p.read_text())

    def test_user_data_only_uses_its_two_variables(self):
        t = (INFRA / "host-user-data.sh.tftpl").read_text()
        self.assertEqual(sorted(set(re.findall(r"(?<!\$)\$\{(\w+)\}", t))), ["bucket", "region"])
        self.assertIn("export IDENTITY=terraform", t)
        self.assertIn("/etc/profile.d/station.sh", t)
        self.assertIn("alias fetch-poc=", t)

    def test_upload_ships_the_fleet_audio(self):
        t = (INFRA / "upload-to-host.sh").read_text()
        self.assertIn("aws s3 sync data/station ", t)
        for excluded in ("'data/*'", "'infra/*'", "'tests/*'"):
            self.assertIn(f"--exclude {excluded}", t)

    def test_state_and_generated_files_stay_out_of_the_repo(self):
        gi = (ROOT.parent / ".gitignore").read_text()
        for x in ("*.tfstate", ".terraform", "infra/.build"):
            self.assertIn(x, gi)


class NoSsh(unittest.TestCase):
    """The host is reached through Session Manager only: no port 22, no key pair, no SSH variables."""

    def test_no_ssh(self):
        tf = tf_text()
        for word in ("key_name", "cidr_ssh", "from_port   = 22", "ingress"):
            self.assertNotIn(word, tf, word)
        self.assertNotRegex(tf.lower(), r"\bssh\b")
        self.assertIn("AmazonSSMManagedInstanceCore", tf)


class SameAsSetup(unittest.TestCase):
    """Terraform and cloud/setup.sh must not drift apart: the slide's figure and the demo read these names."""

    def test_names(self):
        tf = tf_text()
        for name in ("com.station.Listener", "/station/events", "Station", "station_events",
                     "station-missed-faults", "station-rollback", "/station/last_good_version",
                     "GreengrassV2TokenExchangeRole", "GreengrassCoreTokenExchangeRoleAlias", "StationThingPolicy",
                     "StationRing0", "StationRing1", "StationIotToLogs", "StationRollback",
                     "station-device", "station/events"):
            self.assertIn(name, tf, name)
            self.assertIn(name, SETUP, name)

    def test_the_rule(self):
        sql_setup = re.search(r'"sql":"([^"]+)"', SETUP).group(1)
        self.assertEqual(sql_setup, "SELECT *, timestamp() AS arrived_ts FROM 'station/events'")
        self.assertIn("SELECT *, timestamp() AS arrived_ts FROM '${local.topic}'", tf_text())
        self.assertRegex((INFRA / "main.tf").read_text(), r'\btopic\s*=\s*"station/events"')

    def test_the_seven_filters(self):
        setup = {}
        for m in re.finditer(r"^metric_filter\s+(\w+)\s+(\w+)\s+'([^']+)'\s+(\S+)\s+(\S+)\s+(\S+)\s*$", SETUP, re.M):
            name, metric, pattern, value, dims, default = m.groups()
            setup[name] = (metric, pattern, value.strip("'"), dims.strip("'"), default)
        self.assertEqual(len(setup), 7)
        tf = (INFRA / "observability.tf").read_text()
        for name, (metric, pattern, value, dims, default) in setup.items():
            m = re.search(rf'^\s*{name}\s*=\s*\{{\s*metric = "(\w+)", pattern = "((?:[^"\\]|\\.)*)", value = "([^"]*)", '
                          rf'dim = "([^"]*)", dim_value = "([^"]*)", default = "([^"]*)" \}}', tf, re.M)
            self.assertIsNotNone(m, f"filter {name} is not in observability.tf")
            t_metric, t_pattern, t_value, t_dim, t_dim_value, t_default = m.groups()
            self.assertEqual(t_metric, metric, name)
            self.assertEqual(hcl_to_text(t_pattern), pattern, name)
            self.assertEqual(t_value, value, name)
            if dims == "-":
                self.assertEqual(t_dim, "", name)
            else:
                self.assertEqual({t_dim: t_dim_value}, json.loads(dims), name)
            self.assertEqual(t_default or "-", default, name)

    def test_the_alarm(self):
        tf = (INFRA / "observability.tf").read_text()
        for key, value in (("metric_name", '"MissedFaults"'), ("statistic", '"Sum"'), ("period", "60"),
                           ("evaluation_periods", "1"), ("datapoints_to_alarm", "1"),
                           ("comparison_operator", '"GreaterThanOrEqualToThreshold"'), ("treat_missing_data", '"notBreaching"')):
            self.assertRegex(tf, rf"\b{key}\s*=\s*{re.escape(value)}")
        self.assertIn("--period 60 --evaluation-periods 1 --datapoints-to-alarm 1", SETUP)
        self.assertRegex((INFRA / "variables.tf").read_text(), r'variable "alarm_threshold" \{[^}]*default\s*=\s*8\b')
        self.assertIn('ALARM_THRESHOLD="${ALARM_THRESHOLD:-8}"', SETUP)
        self.assertIn('principal      = "lambda.alarms.cloudwatch.amazonaws.com"', tf)

    def test_the_lambda_targets_ring_0(self):
        tf = (INFRA / "observability.tf").read_text()
        self.assertIn('THING_GROUP_ARN = aws_iot_thing_group.ring["StationRing0"].arn', tf)
        self.assertIn('handler          = "rollback_lambda.handler"', tf)
        self.assertIn("thinggroup/StationRing0", SETUP)

    def test_same_pump_policy(self):
        actions = lambda t: set(re.findall(r'"((?:iot|greengrass):\w+)"', t))
        doc = SETUP.split('thing-policy.json" <<\'JSON\'')[1].split("JSON")[0]
        tf = (INFRA / "iot.tf").read_text().split('resource "aws_iot_policy" "pumps"')[1].split("resource ")[0]
        self.assertEqual(actions(tf), actions(doc))
        for resource in ("client/pump-*", "topic/$aws/things/pump-*/jobs/*", "topicfilter/$aws/things/pump-*/shadow/*"):
            self.assertIn(resource, tf)
            self.assertIn(resource, doc)

    def test_the_pump_only_reads_the_artifacts(self):
        self.assertIn('"${aws_s3_bucket.artifacts.arn}/station/*"', (INFRA / "iot.tf").read_text())
        self.assertIn("arn:aws:s3:::__BUCKET__/station/*", SETUP)

    def test_the_dashboard_has_no_placeholders_left(self):
        tf = (INFRA / "observability.tf").read_text()
        placeholders = set(re.findall(r"__[A-Z]+__", (ROOT / "cloud" / "dashboard.json").read_text()))
        for p in placeholders:
            self.assertIn(f'"{p}"', tf)


# ─────────────────────────────────────────────────────────────────────
#  The fleet's IDENTITY=terraform path
# ─────────────────────────────────────────────────────────────────────
# A fake `aws` in front of the fleet tests' one: that one logs the call; this one answers the
# pumps' identity and the IoT endpoints as Parameter Store would after `terraform apply`.
SHIM_AWS_TF = r'''#!/usr/bin/env python3
import os, subprocess, sys
args = sys.argv[1:]
line = " ".join(args)
r = subprocess.run([os.path.join(os.path.dirname(os.path.abspath(__file__)), "aws-base")] + args,
                   capture_output=True, text=True)
answer = None
if r.returncode == 0 and line.startswith("ssm get-parameter"):
    if "/station/pumps/" in line and "/cert" in line:
        answer = "-----BEGIN CERTIFICATE-----\nMIIcert\n-----END CERTIFICATE-----"
    elif "/station/pumps/" in line and "/key" in line:
        answer = "-----BEGIN RSA PRIVATE KEY-----\nMIIkey\n-----END RSA PRIVATE KEY-----"
    elif "data_endpoint" in line:
        answer = "abc123-ats.iot.us-east-1.amazonaws.com"
    elif "cred_endpoint" in line:
        answer = "xyz789.credentials.iot.us-east-1.amazonaws.com"
sys.stdout.write(answer + "\n" if answer is not None else r.stdout)
sys.stderr.write(r.stderr)
sys.exit(r.returncode)
'''

# A fake `docker` in front of the fleet tests' one: on every `docker run -d` it also records (in
# SHIM_ID_LOG) what it sees mounted at /run/station-id and whether there are credentials in /run/aws-bootstrap.
SHIM_DOCKER_TF = r'''#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
ID_MOUNT, CREDS_MOUNT = ":/run/station-id:ro", ":/run/aws-bootstrap"
if args[:2] == ["run", "-d"]:
    entry = {"args": args, "identity_visible": None, "private_key_600": None, "credentials_visible": None}
    for a in args:
        if a.endswith(ID_MOUNT):
            d = a[: -len(ID_MOUNT)]
            if os.path.isdir(d):
                entry["identity_visible"] = sorted(os.listdir(d))
                key = os.path.join(d, "private.pem.key")
                entry["private_key_600"] = os.path.exists(key) and oct(os.stat(key).st_mode & 0o777) == "0o600"
        elif CREDS_MOUNT in a:
            cred = os.path.join(a.split(CREDS_MOUNT)[0], "credentials")
            entry["credentials_visible"] = open(cred).read() if os.path.exists(cred) else None
    with open(os.environ["SHIM_ID_LOG"], "a") as f:
        f.write(json.dumps(entry) + "\n")
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docker-base")
os.execv(base, [base] + args)
'''


class FleetWithTerraform(unittest.TestCase):
    def setUp(self):
        self.e = T.Environment(self)
        write(self.e.bin / "aws-base", T.SHIM_AWS, True)
        write(self.e.bin / "aws", SHIM_AWS_TF, True)
        write(self.e.bin / "docker-base", T.SHIM_DOCKER, True)
        write(self.e.bin / "docker", SHIM_DOCKER_TF, True)
        self.id_log = self.e.dir / "identity.jsonl"
        self.e.env["SHIM_ID_LOG"] = str(self.id_log)
        for n in range(1, 6):
            (self.e.poc / "data" / "station" / f"pump-0{n}" / "normal").mkdir(parents=True)

    def runs(self):
        return [c for c in self.e.calls("docker") if c["args"][:2] == ["run", "-d"]]

    def seen(self):
        """What the fake docker saw mounted on each `docker run -d`."""
        return [json.loads(l) for l in self.id_log.read_text().splitlines()] if self.id_log.exists() else []

    def test_first_start_with_the_terraform_identity(self):
        r = self.e.run("fleet/up.sh", IDENTITY="terraform")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.e.aws("configure", "export-credentials"), [])      # no AWS credentials at all
        requested = [c["args"][c["args"].index("--name") + 1] for c in self.e.aws("ssm", "get-parameter")]
        for n in range(1, 6):
            self.assertIn(f"/station/pumps/pump-0{n}/cert", requested)
            self.assertIn(f"/station/pumps/pump-0{n}/key", requested)
        for c in self.e.aws("ssm", "get-parameter"):
            self.assertIn("--with-decryption", c["args"])
        runs = self.runs()
        self.assertEqual(len(runs), 5)
        for c in runs:
            self.assertEqual(env_of(c)["IDENTITY"], "terraform")
        seen = self.seen()
        self.assertEqual(len(seen), 5)
        for c in seen:
            self.assertEqual(c["identity_visible"], ["device.pem.crt", "endpoints.env", "private.pem.key"])
            self.assertTrue(c["private_key_600"])
            self.assertIsNone(c["credentials_visible"])
        # when it finishes, no identity is left on the host's disk
        boot = self.e.poc / "fleet" / ".bootstrap"
        self.assertEqual([p.name for p in boot.iterdir()] if boot.exists() else [], [])

    def test_without_terraform_apply_it_stops_with_a_clear_message(self):
        write(self.e.bin / "aws", T.SHIM_AWS, True)                       # Parameter Store without the identity
        r = self.e.run("fleet/up.sh", IDENTITY="terraform")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("terraform apply", r.stdout + r.stderr)
        self.assertEqual(self.runs(), [])

    def test_later_starts_fetch_nothing(self):
        r = self.e.run("fleet/up.sh", IDENTITY="terraform", SHIM_PROVISIONED="1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.e.aws("ssm", "get-parameter"), [])
        for c in self.seen():
            self.assertIsNone(c["identity_visible"])

    def test_unknown_identity(self):
        r = self.e.run("fleet/up.sh", IDENTITY="other")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("installer or terraform", r.stdout + r.stderr)

    def test_down_does_not_delete_what_terraform_manages(self):
        r = self.e.run("fleet/down.sh", "--delete-things", IDENTITY="terraform")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("terraform -chdir=infra destroy", r.stdout + r.stderr)
        self.assertEqual(self.e.aws("iot", "delete-thing"), [])


class EntrypointWithTerraform(unittest.TestCase):
    def prepare(self):
        self.e = T.Environment(self)
        self.ggc = self.e.dir / "gg"
        self.ggc.mkdir()
        self.ident = self.e.dir / "id"
        self.ident.mkdir()
        (self.ident / "device.pem.crt").write_text("-----BEGIN CERTIFICATE-----\nMIIcert\n-----END CERTIFICATE-----\n")
        (self.ident / "private.pem.key").write_text("-----BEGIN RSA PRIVATE KEY-----\nMIIkey\n-----END RSA PRIVATE KEY-----\n")
        (self.ident / "endpoints.env").write_text("IOT_DATA_ENDPOINT=abc123-ats.iot.us-east-1.amazonaws.com\n"
                                                  "IOT_CRED_ENDPOINT=xyz789.credentials.iot.us-east-1.amazonaws.com\n")
        self.ca = self.e.dir / "AmazonRootCA1.pem"
        self.ca.write_text("-----BEGIN CERTIFICATE-----\nca\n-----END CERTIFICATE-----\n")
        # fake java: saves its arguments and a copy of the --init-config, and leaves a loader behind
        write(self.e.bin / "java", textwrap.dedent(f"""\
            #!/usr/bin/env bash
            echo "$@" > {self.e.dir}/java.args
            env | grep '^AWS_' | sort > {self.e.dir}/java.env || true
            prev=""; for a in "$@"; do [ "$prev" = "--init-config" ] && cp "$a" {self.e.dir}/config.yaml; prev="$a"; done
            mkdir -p {self.ggc}/alts/current/distro/bin
            printf '#!/usr/bin/env bash\\necho started > {self.e.dir}/loader.ok\\n' > {self.ggc}/alts/current/distro/bin/loader
            chmod +x {self.ggc}/alts/current/distro/bin/loader
            """), True)
        self.env_extra = {"GGC_ROOT_PATH": str(self.ggc), "STATION_RUN_DIR": str(self.e.dir / "run"),
                          "INSTALLER_JAR": "/opt/fake/Greengrass.jar", "ID_DIR": str(self.ident), "ROOT_CA": str(self.ca),
                          "IDENTITY": "terraform", "GREENGRASS_VERSION": "2.18.3",
                          "THING_NAME": "pump-01", "THING_GROUP_NAME": "StationRing0", "AWS_REGION": "us-east-1"}

    def start(self):
        return subprocess.run([str(self.e.poc / "fleet" / "entrypoint.sh")], cwd=self.e.poc,
                              env={**self.e.env, **self.env_extra}, capture_output=True, text=True, timeout=60)

    def test_installs_with_init_config_and_no_credentials(self):
        self.prepare()
        r = self.start()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        args = (self.e.dir / "java.args").read_text().split()
        self.assertIn("--init-config", args)
        # the nucleus picks the format from the extension ("File format 'tmp.X' is not supported")
        self.assertTrue(args[args.index("--init-config") + 1].endswith(".yaml"))
        self.assertNotIn("--provision", args)
        self.assertEqual(args[args.index("--start") + 1], "false")
        self.assertEqual(args[args.index("--setup-system-service") + 1], "false")
        cfg = (self.e.dir / "config.yaml").read_text()
        for expected in ('thingName: "pump-01"', 'version: "2.18.3"', 'awsRegion: "us-east-1"',
                         'iotRoleAlias: "GreengrassCoreTokenExchangeRoleAlias"',
                         'iotDataEndpoint: "abc123-ats.iot.us-east-1.amazonaws.com"',
                         'iotCredEndpoint: "xyz789.credentials.iot.us-east-1.amazonaws.com"',
                         f'privateKeyPath: "{self.ggc}/private.pem.key"'):
            self.assertIn(expected, cfg)
        if yaml:
            self.assertEqual(yaml.safe_load(cfg)["system"]["thingName"], "pump-01")
        self.assertEqual(oct((self.ggc / "private.pem.key").stat().st_mode & 0o777), "0o600")
        self.assertTrue((self.ggc / "AmazonRootCA1.pem").exists())
        self.assertNotIn("AWS_ACCESS_KEY_ID", (self.e.dir / "java.env").read_text())
        self.assertTrue((self.ggc / ".station-provisioned").exists())
        self.assertTrue((self.e.dir / "loader.ok").exists())

    def test_stops_without_a_mounted_identity(self):
        self.prepare()
        (self.ident / "private.pem.key").unlink()
        r = self.start()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("IDENTITY=terraform ./fleet/up.sh", r.stdout + r.stderr)
        self.assertFalse((self.e.dir / "loader.ok").exists())


if __name__ == "__main__":
    unittest.main()
