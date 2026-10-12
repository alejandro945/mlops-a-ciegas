"""
Pruebas de infra/ (Terraform) y del camino IDENTIDAD=terraform de la flota. Sin AWS, sin Docker, sin terraform.

  python3 -m unittest discover -s poc-devopsdays/tests -p "test_infra*.py" -v

Qué cubre:
  · los .tf parsean como HCL (si python-hcl2 está instalado; si no, se saltan esas pruebas)
  · Terraform y cloud/setup.sh crean lo mismo: nombres, regla, los siete filtros, alarma, política de las bombas
  · fleet/up.sh con IDENTIDAD=terraform baja la identidad de Parameter Store, la monta solo en la
    instalación y no pide credenciales; el entrypoint instala el nucleus con --init-config
  · fleet/down.sh no borra a mano lo que maneja Terraform
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

import test_infra as T          # Entorno, shims y ayudantes de las pruebas de la flota

try:
    import hcl2
except ImportError:
    hcl2 = None

ROOT = Path(__file__).resolve().parents[1]
INFRA = ROOT / "infra"
SETUP = (ROOT / "cloud" / "setup.sh").read_text()


def tf_texto():
    return "\n".join(p.read_text() for p in sorted(INFRA.glob("*.tf")))


def hcl_a_texto(s):
    """Una cadena de HCL tal como queda después de parsear: \\" → \" ."""
    return s.replace('\\"', '"')


class Sintaxis(unittest.TestCase):
    def test_hay_terraform(self):
        for f in ("versions.tf", "variables.tf", "main.tf", "iot.tf", "observabilidad.tf", "host.tf", "outputs.tf"):
            self.assertTrue((INFRA / f).is_file(), f)

    @unittest.skipIf(hcl2 is None, "python-hcl2 no está instalado")
    def test_los_tf_parsean(self):
        for p in sorted(INFRA.glob("*.tf")):
            with open(p) as f:
                hcl2.load(f)                       # lanza si la sintaxis está mal

    def test_scripts_de_infra(self):
        for p in sorted(INFRA.glob("*.sh")):
            r = subprocess.run(["bash", "-n", str(p)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"{p.name}: {r.stderr}")
            self.assertTrue(p.stat().st_mode & stat.S_IXUSR, f"{p.name} no es ejecutable")
            self.assertIn("set -euo pipefail", p.read_text())

    def test_user_data_solo_usa_sus_dos_variables(self):
        t = (INFRA / "host-user-data.sh.tftpl").read_text()
        self.assertEqual(sorted(set(re.findall(r"(?<!\$)\$\{(\w+)\}", t))), ["bucket", "region"])
        self.assertIn("export IDENTIDAD=terraform", t)

    def test_el_estado_y_lo_generado_no_van_al_repo(self):
        gi = (ROOT.parent / ".gitignore").read_text()
        for x in ("*.tfstate", ".terraform", "infra/.build"):
            self.assertIn(x, gi)


class MismoQueSetup(unittest.TestCase):
    """Terraform y cloud/setup.sh no pueden separarse: la figura de la lámina 24 y la demo leen estos nombres."""

    def test_nombres(self):
        tf = tf_texto()
        for nombre in ("com.estacion.Escucha", "/estacion/eventos", "Estacion", "estacion_eventos",
                       "estacion-fallas-no-oidas", "estacion-rollback", "/estacion/last_good_version",
                       "GreengrassV2TokenExchangeRole", "GreengrassCoreTokenExchangeRoleAlias", "EstacionThingPolicy",
                       "EstacionAnillo0", "EstacionAnillo1", "EstacionIotToLogs", "EstacionRollback",
                       "estacion-dispositivo", "estacion/eventos"):
            self.assertIn(nombre, tf, nombre)
            self.assertIn(nombre, SETUP, nombre)

    def test_la_regla(self):
        sql_setup = re.search(r'"sql":"([^"]+)"', SETUP).group(1)
        self.assertEqual(sql_setup, "SELECT *, timestamp() AS arrived_ts FROM 'estacion/eventos'")
        self.assertIn("SELECT *, timestamp() AS arrived_ts FROM '${local.tema}'", tf_texto())
        self.assertIn('tema            = "estacion/eventos"', (INFRA / "main.tf").read_text())

    def test_los_siete_filtros(self):
        setup = {}
        for m in re.finditer(r"^filtro\s+(\w+)\s+(\w+)\s+'([^']+)'\s+(\S+)\s+(\S+)\s+(\S+)\s*$", SETUP, re.M):
            nombre, metrica, patron, valor, dims, defecto = m.groups()
            setup[nombre] = (metrica, patron, valor.strip("'"), dims.strip("'"), defecto)
        self.assertEqual(len(setup), 7)
        tf = (INFRA / "observabilidad.tf").read_text()
        for nombre, (metrica, patron, valor, dims, defecto) in setup.items():
            m = re.search(rf'^\s*{nombre}\s*=\s*\{{\s*metrica = "(\w+)", patron = "((?:[^"\\]|\\.)*)", valor = "([^"]*)", '
                          rf'dim = "([^"]*)", dim_valor = "([^"]*)", defecto = "([^"]*)" \}}', tf, re.M)
            self.assertIsNotNone(m, f"filtro {nombre} no está en observabilidad.tf")
            t_metrica, t_patron, t_valor, t_dim, t_dim_valor, t_defecto = m.groups()
            self.assertEqual(t_metrica, metrica, nombre)
            self.assertEqual(hcl_a_texto(t_patron), patron, nombre)
            self.assertEqual(t_valor, valor, nombre)
            if dims == "-":
                self.assertEqual(t_dim, "", nombre)
            else:
                self.assertEqual({t_dim: t_dim_valor}, json.loads(dims), nombre)
            self.assertEqual(t_defecto or "-", defecto, nombre)

    def test_la_alarma(self):
        tf = (INFRA / "observabilidad.tf").read_text()
        for clave, valor in (("metric_name", '"FallasNoOidas"'), ("statistic", '"Sum"'), ("period", "60"),
                             ("evaluation_periods", "1"), ("datapoints_to_alarm", "1"),
                             ("comparison_operator", '"GreaterThanOrEqualToThreshold"'), ("treat_missing_data", '"notBreaching"')):
            self.assertRegex(tf, rf"\b{clave}\s*=\s*{re.escape(valor)}")
        self.assertIn("--period 60 --evaluation-periods 1 --datapoints-to-alarm 1", SETUP)
        self.assertIn('default     = 8', (INFRA / "variables.tf").read_text())
        self.assertIn('ALARM_THRESHOLD="${ALARM_THRESHOLD:-8}"', SETUP)
        self.assertIn('principal      = "lambda.alarms.cloudwatch.amazonaws.com"', tf)

    def test_la_lambda_apunta_al_anillo_0(self):
        tf = (INFRA / "observabilidad.tf").read_text()
        self.assertIn('THING_GROUP_ARN = aws_iot_thing_group.anillo["EstacionAnillo0"].arn', tf)
        self.assertIn('handler          = "rollback_lambda.handler"', tf)

    def test_misma_politica_de_bombas(self):
        acciones = lambda t: set(re.findall(r'"((?:iot|greengrass):\w+)"', t))
        doc = SETUP.split('thing-policy.json" <<\'JSON\'')[1].split("JSON")[0]
        tf = (INFRA / "iot.tf").read_text().split('resource "aws_iot_policy" "bombas"')[1].split("resource ")[0]
        self.assertEqual(acciones(tf), acciones(doc))
        for recurso in ("client/bomba-*", "topic/$aws/things/bomba-*/jobs/*", "topicfilter/$aws/things/bomba-*/shadow/*"):
            self.assertIn(recurso, tf)
            self.assertIn(recurso, doc)

    def test_la_bomba_solo_lee_los_artefactos(self):
        self.assertIn('"${aws_s3_bucket.artefactos.arn}/estacion/*"', (INFRA / "iot.tf").read_text())
        self.assertIn("arn:aws:s3:::__BUCKET__/estacion/*", SETUP)

    def test_el_dashboard_queda_sin_marcadores(self):
        tf = (INFRA / "observabilidad.tf").read_text()
        marcadores = set(re.findall(r"__[A-Z]+__", (ROOT / "cloud" / "dashboard.json").read_text()))
        for m in marcadores:
            self.assertIn(f'"{m}"', tf)


# ─────────────────────────────────────────────────────────────────────
#  El camino IDENTIDAD=terraform de la flota
# ─────────────────────────────────────────────────────────────────────
SHIM_AWS_TF = T.SHIM_AWS.replace(
    'elif linea.startswith("ssm get-parameter"):\n    print("1.0.0")',
    'elif linea.startswith("ssm get-parameter") and "/estacion/bombas/" in linea and "/cert" in linea:\n'
    '    print("-----BEGIN CERTIFICATE-----\\nMIIcert\\n-----END CERTIFICATE-----")\n'
    'elif linea.startswith("ssm get-parameter") and "/estacion/bombas/" in linea and "/key" in linea:\n'
    '    print("-----BEGIN RSA PRIVATE KEY-----\\nMIIkey\\n-----END RSA PRIVATE KEY-----")\n'
    'elif linea.startswith("ssm get-parameter") and "data_endpoint" in linea:\n'
    '    print("abc123-ats.iot.us-east-1.amazonaws.com")\n'
    'elif linea.startswith("ssm get-parameter") and "cred_endpoint" in linea:\n'
    '    print("xyz789.credentials.iot.us-east-1.amazonaws.com")\n'
    'elif linea.startswith("ssm get-parameter"):\n    print("1.0.0")')

# El docker falso, además, guarda lo que ve montado en /run/estacion-id durante `docker run`
SHIM_DOCKER_TF = T.SHIM_DOCKER.replace(
    'with open(os.environ["SHIM_LOG"], "a") as f:',
    'for a in args:\n'
    '    if a.endswith(":/run/estacion-id:ro"):\n'
    '        d = a[: -len(":/run/estacion-id:ro")]\n'
    '        entry["identidad_visible"] = sorted(os.listdir(d)) if os.path.isdir(d) else None\n'
    '        entry["llave_privada_600"] = (oct(os.stat(os.path.join(d, "private.pem.key")).st_mode & 0o777) == "0o600"\n'
    '                                      if os.path.isdir(d) else None)\n'
    'with open(os.environ["SHIM_LOG"], "a") as f:', 1)


class FlotaConTerraform(unittest.TestCase):
    def setUp(self):
        self.assertIn("identidad_visible", SHIM_DOCKER_TF)
        self.assertIn("BEGIN CERTIFICATE", SHIM_AWS_TF)
        self.e = T.Entorno(self)
        T._escribir(self.e.bin / "aws", SHIM_AWS_TF, True)
        T._escribir(self.e.bin / "docker", SHIM_DOCKER_TF, True)
        for n in range(1, 6):
            (self.e.poc / "data" / "estacion" / f"bomba-0{n}" / "normal").mkdir(parents=True)

    def runs(self):
        return [c for c in self.e.llamadas("docker") if c["args"][:2] == ["run", "-d"]]

    def test_primer_arranque_con_la_identidad_de_terraform(self):
        r = self.e.correr("fleet/up.sh", IDENTIDAD="terraform")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.e.aws("configure", "export-credentials"), [])      # ninguna credencial de AWS
        pedidos = [c["args"][c["args"].index("--name") + 1] for c in self.e.aws("ssm", "get-parameter")]
        for n in range(1, 6):
            self.assertIn(f"/estacion/bombas/bomba-0{n}/cert", pedidos)
            self.assertIn(f"/estacion/bombas/bomba-0{n}/key", pedidos)
        for c in self.e.aws("ssm", "get-parameter"):
            self.assertIn("--with-decryption", c["args"])
        runs = self.runs()
        self.assertEqual(len(runs), 5)
        for c in runs:
            env = T.Flota.env_de(c)
            self.assertEqual(env["IDENTIDAD"], "terraform")
            self.assertEqual(c["identidad_visible"], ["device.pem.crt", "endpoints.env", "private.pem.key"])
            self.assertTrue(c["llave_privada_600"])
            self.assertIsNone(c["credenciales_visibles"])
        # al terminar no queda ninguna identidad en el disco del host
        boot = self.e.poc / "fleet" / ".bootstrap"
        self.assertEqual([p.name for p in boot.iterdir()] if boot.exists() else [], [])

    def test_sin_terraform_apply_se_detiene_con_un_mensaje_claro(self):
        T._escribir(self.e.bin / "aws", T.SHIM_AWS, True)                      # Parameter Store sin la identidad
        r = self.e.correr("fleet/up.sh", IDENTIDAD="terraform")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("terraform apply", r.stdout + r.stderr)
        self.assertEqual(self.runs(), [])

    def test_arranques_siguientes_no_bajan_nada(self):
        r = self.e.correr("fleet/up.sh", IDENTIDAD="terraform", SHIM_PROVISIONED="1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.e.aws("ssm", "get-parameter"), [])
        for c in self.runs():
            self.assertNotIn("identidad_visible", c)

    def test_identidad_desconocida(self):
        r = self.e.correr("fleet/up.sh", IDENTIDAD="otra")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("instalador o terraform", r.stdout + r.stderr)

    def test_down_no_borra_lo_de_terraform(self):
        r = self.e.correr("fleet/down.sh", "--borrar-things", IDENTIDAD="terraform")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("terraform -chdir=infra destroy", r.stdout + r.stderr)
        self.assertEqual(self.e.aws("iot", "delete-thing"), [])


class EntrypointConTerraform(unittest.TestCase):
    def preparar(self):
        self.e = T.Entorno(self)
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
        # java falso: guarda sus argumentos y una copia del --init-config, y deja un loader
        T._escribir(self.e.bin / "java", textwrap.dedent(f"""\
            #!/usr/bin/env bash
            echo "$@" > {self.e.dir}/java.args
            env | grep '^AWS_' | sort > {self.e.dir}/java.env || true
            prev=""; for a in "$@"; do [ "$prev" = "--init-config" ] && cp "$a" {self.e.dir}/config.yaml; prev="$a"; done
            mkdir -p {self.ggc}/alts/current/distro/bin
            printf '#!/usr/bin/env bash\\necho arrancó > {self.e.dir}/loader.ok\\n' > {self.ggc}/alts/current/distro/bin/loader
            chmod +x {self.ggc}/alts/current/distro/bin/loader
            """), True)
        self.env_extra = {"GGC_ROOT_PATH": str(self.ggc), "ESTACION_RUN_DIR": str(self.e.dir / "run"),
                          "INSTALLER_JAR": "/opt/falso/Greengrass.jar", "ID_DIR": str(self.ident), "CA_RAIZ": str(self.ca),
                          "IDENTIDAD": "terraform", "GREENGRASS_VERSION": "2.18.3",
                          "THING_NAME": "bomba-01", "THING_GROUP_NAME": "EstacionAnillo0", "AWS_REGION": "us-east-1"}

    def arrancar(self):
        return subprocess.run([str(self.e.poc / "fleet" / "entrypoint.sh")], cwd=self.e.poc,
                              env={**self.e.env, **self.env_extra}, capture_output=True, text=True, timeout=60)

    def test_instala_con_init_config_y_sin_credenciales(self):
        self.preparar()
        r = self.arrancar()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        args = (self.e.dir / "java.args").read_text().split()
        self.assertIn("--init-config", args)
        # el nucleus elige el formato por la extensión («File format 'tmp.X' is not supported»)
        self.assertTrue(args[args.index("--init-config") + 1].endswith(".yaml"))
        self.assertNotIn("--provision", args)
        self.assertEqual(args[args.index("--start") + 1], "false")
        self.assertEqual(args[args.index("--setup-system-service") + 1], "false")
        cfg = (self.e.dir / "config.yaml").read_text()
        for esperado in ('thingName: "bomba-01"', 'version: "2.18.3"', 'awsRegion: "us-east-1"',
                         'iotRoleAlias: "GreengrassCoreTokenExchangeRoleAlias"',
                         'iotDataEndpoint: "abc123-ats.iot.us-east-1.amazonaws.com"',
                         'iotCredEndpoint: "xyz789.credentials.iot.us-east-1.amazonaws.com"',
                         f'privateKeyPath: "{self.ggc}/private.pem.key"'):
            self.assertIn(esperado, cfg)
        if yaml := T.yaml:
            self.assertEqual(yaml.safe_load(cfg)["system"]["thingName"], "bomba-01")
        self.assertEqual(oct((self.ggc / "private.pem.key").stat().st_mode & 0o777), "0o600")
        self.assertTrue((self.ggc / "AmazonRootCA1.pem").exists())
        self.assertNotIn("AWS_ACCESS_KEY_ID", (self.e.dir / "java.env").read_text())
        self.assertTrue((self.ggc / ".estacion-aprovisionado").exists())
        self.assertTrue((self.e.dir / "loader.ok").exists())

    def test_sin_identidad_montada_se_detiene(self):
        self.preparar()
        (self.ident / "private.pem.key").unlink()
        r = self.arrancar()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("IDENTIDAD=terraform ./fleet/up.sh", r.stdout + r.stderr)
        self.assertFalse((self.e.dir / "loader.ok").exists())


if __name__ == "__main__":
    unittest.main()
