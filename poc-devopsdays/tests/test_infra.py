"""
Pruebas de la infraestructura de la PoC (flota, nube, demo). Sin AWS, sin Docker.

  python3 -m unittest discover -s poc-devopsdays/tests -p "test_infra*.py" -v

Qué cubre:
  · `bash -n` de todos los scripts, y que cada uno falle ante el primer error
  · la receta parsea como YAML y su `run` es el del PLAN §4.4
  · el dashboard es JSON válido y solo usa métricas que setup.sh crea
  · la Lambda, con clientes de boto3 simulados a mano: en OK no hace nada, en ALARM
    despliega la última versión buena al anillo 0
  · los scripts con lógica (publish, deploy, up, down, setup, teardown, entrypoint) corren
    contra un `aws` y un `docker` falsos que anotan lo que se les pide
  · el formato de watch.sh

Lo que NO cubre: nada de esto toca AWS ni Docker de verdad. Ver "Qué verifiqué y qué no" en el README.
"""
import sys
sys.dont_write_bytecode = True        # las pruebas no dejan __pycache__ en cloud/ ni en demo/

import importlib.util
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
import time
import types
import unittest
from pathlib import Path
from unittest import mock

try:
    import yaml
except ImportError:          # sin PyYAML hacemos un chequeo simple
    yaml = None

ROOT = Path(__file__).resolve().parents[1]          # poc-devopsdays/
SCRIPTS = sorted(list((ROOT / "fleet").glob("*.sh")) + list((ROOT / "demo").glob("*.sh"))
                 + list((ROOT / "cloud").glob("*.sh")))

# Lo que el PLAN §4.4 dice que corre el componente (en una línea)
RUN_ESPERADO = (
    "python3 -u {artifacts:path}/inference.py --model {artifacts:path}/model.onnx "
    "--stats {artifacts:path}/stats.json --audio-root /data/estacion --mode-file /run/estacion/modo "
    "--version __VERSION__ --topic {configuration:/topic} --threshold {configuration:/threshold} "
    "--interval {configuration:/intervalSeconds}")


# ─────────────────────────────────────────────────────────────────────
#  Un `aws` y un `docker` falsos: anotan cada llamada en un archivo JSON-lines
# ─────────────────────────────────────────────────────────────────────
SHIM_AWS = r'''#!/usr/bin/env python3
import json, os, re, sys
args = sys.argv[1:]
entry = {"cmd": "aws", "args": args, "files": {}}
for a in args:
    m = re.match(r"^file(?:b)?://(.+)$", a)
    if m and os.path.isfile(m.group(1)) and os.path.getsize(m.group(1)) < 200000:
        entry["files"][a] = open(m.group(1), errors="replace").read()
with open(os.environ["SHIM_LOG"], "a") as f:
    f.write(json.dumps(entry) + "\n")
linea = " ".join(args)
falta = os.environ.get("SHIM_MISSING")
if falta and re.search(falta, linea):
    sys.stderr.write("An error occurred (ResourceNotFoundException): shim\n")
    sys.exit(254)
if linea.startswith("sts get-caller-identity"):
    print("123456789012")
elif linea.startswith("configure export-credentials"):
    print(json.dumps({"Version": 1, "AccessKeyId": "ASIAEJEMPLO", "SecretAccessKey": "secreto/con%porcentaje",
                      "SessionToken": "token-temporal"}))
elif linea.startswith("greengrassv2 describe-component") and "componentState" in linea:
    print("DEPLOYABLE")
elif linea.startswith("greengrassv2 create-component-version"):
    print("com.estacion.Escucha\t9.9.9\tREQUESTED")
elif linea.startswith("greengrassv2 create-deployment"):
    print("dep-" + str(abs(hash(linea)) % 1000))
elif linea.startswith("ssm get-parameter"):
    print("1.0.0")
elif linea.startswith("logs tail"):
    for l in open(os.environ["SHIM_TAIL"]):
        print(l.rstrip("\n"))
sys.exit(0)
'''

SHIM_DOCKER = r'''#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
entry = {"cmd": "docker", "args": args}
for a in args:                                    # ¿qué credenciales hay en el montaje durante `docker run`?
    if ":/run/aws-bootstrap" in a:
        cred = os.path.join(a.split(":/run/aws-bootstrap")[0], "credentials")
        entry["credenciales_visibles"] = open(cred).read() if os.path.exists(cred) else None
with open(os.environ["SHIM_LOG"], "a") as f:
    f.write(json.dumps(entry) + "\n")
aprovisionada = os.environ.get("SHIM_PROVISIONED") == "1"
if args[:2] == ["image", "inspect"]:
    sys.exit(0)
if args[:2] == ["network", "inspect"]:
    sys.exit(1)
if args[:2] == ["volume", "inspect"]:
    sys.exit(0 if aprovisionada else 1)
if args[:1] == ["run"] and "--entrypoint" in args:
    sys.exit(0 if aprovisionada else 1)
if args[:1] == ["inspect"]:
    sys.exit(1)
sys.exit(0)
'''


def _escribir(path, texto, ejecutable=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(texto)
    if ejecutable:
        path.chmod(path.stat().st_mode | stat.S_IXUSR)


class Entorno:
    """Copia de la PoC en un directorio temporal, con `aws` y `docker` falsos al frente del PATH."""

    def __init__(self, test):
        self.dir = Path(tempfile.mkdtemp(prefix="estacion-test-"))
        test.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.poc = self.dir / "poc"
        basura = shutil.ignore_patterns("__pycache__", "logs", ".bootstrap", "*.pyc", ".DS_Store", "*.zip")

        def ignorar(carpeta, nombres):      # tampoco se copia nada grande (un zip de datos que alguien dejó ahí)
            grandes = [n for n in nombres if os.path.isfile(os.path.join(carpeta, n))
                       and os.path.getsize(os.path.join(carpeta, n)) > 1_000_000]
            return set(basura(carpeta, nombres)) | set(grandes)

        for sub in ("fleet", "demo", "cloud", "component"):
            shutil.copytree(ROOT / sub, self.poc / sub, ignore=ignorar)
        self.bin = self.dir / "bin"
        _escribir(self.bin / "aws", SHIM_AWS, True)
        _escribir(self.bin / "docker", SHIM_DOCKER, True)
        self.log = self.dir / "llamadas.jsonl"
        self.tail = self.dir / "tail.txt"
        self.tail.write_text("")
        self.env = {**os.environ, "PATH": f"{self.bin}:{os.environ['PATH']}", "SHIM_LOG": str(self.log),
                    "SHIM_TAIL": str(self.tail), "REGION": "us-east-1", "TZ": "UTC"}
        for k in ("SHIM_MISSING", "SHIM_PROVISIONED", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
            self.env.pop(k, None)

    def correr(self, script, *args, entrada=None, **env):
        return subprocess.run([str(self.poc / script), *args], cwd=self.poc, input=entrada,
                              env={**self.env, **env}, capture_output=True, text=True, timeout=120)

    def llamadas(self, cmd=None):
        if not self.log.exists():
            return []
        todas = [json.loads(l) for l in self.log.read_text().splitlines()]
        return [c for c in todas if cmd is None or c["cmd"] == cmd]

    def aws(self, *prefijo):
        """Llamadas a aws cuyo comienzo coincide con `prefijo` (por ejemplo: "iot", "create-topic-rule")."""
        return [c for c in self.llamadas("aws") if c["args"][:len(prefijo)] == list(prefijo)]

    def reiniciar_log(self):
        self.log.write_text("")

    def build_falso(self, carpeta="9.9.9", **stats):
        """Un build/<carpeta>/ como el que deja model/train.py (stats.json dice version=carpeta salvo que se indique)."""
        version = stats.pop("version", carpeta)
        d = self.poc / "build" / carpeta
        d.mkdir(parents=True)
        for f in ("inference.py", "features.py"):
            (d / f).write_text("# " + f + "\n")
        modelo = b"modelo-falso"
        (d / "model.onnx").write_bytes(modelo)
        import hashlib
        st = {"version": version, "threshold": 0.0123, "sha256": hashlib.sha256(modelo).hexdigest(),
              "mean": [0.0], "std": [1.0]}
        st.update(stats)
        (d / "stats.json").write_text(json.dumps(st))
        return d


class ScriptsBase(unittest.TestCase):
    def test_hay_scripts(self):
        nombres = {p.name for p in SCRIPTS}
        for esperado in ("build.sh", "up.sh", "down.sh", "entrypoint.sh", "publish.sh", "deploy.sh", "falla.sh",
                         "dominio.sh", "red.sh", "watch.sh", "setup.sh", "teardown.sh"):
            self.assertIn(esperado, nombres)

    def test_sintaxis_bash(self):
        for p in SCRIPTS:
            with self.subTest(script=p.name):
                r = subprocess.run(["bash", "-n", str(p)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)

    def test_fallan_al_primer_error_y_son_ejecutables(self):
        for p in SCRIPTS:
            with self.subTest(script=p.name):
                self.assertIn("set -euo pipefail", p.read_text())
                self.assertTrue(p.read_text().startswith("#!/usr/bin/env bash"))
                self.assertTrue(os.access(p, os.X_OK), f"{p.name} no es ejecutable")

    def test_no_queda_lo_del_modelo_viejo(self):
        self.assertFalse((ROOT / "demo" / "entrada.sh").exists())
        self.assertFalse((ROOT / "cloud" / "grant-device.sh").exists())

    def test_reglas_de_escritura(self):
        """Sin 'plata', sin kubectl, sin voseo, en lo que escribe este agente."""
        archivos = [ROOT / "README.md", ROOT / "component" / "recipe.template.yaml",
                    *SCRIPTS, *(ROOT / "demo").glob("*.py"), *(ROOT / "cloud").glob("*.py"),
                    ROOT / "fleet" / "Dockerfile", ROOT / "cloud" / "dashboard.json"]
        prohibidas = re.compile(r"\bplata\b|kubectl|\b(vos|tenés|podés|querés|hacé|mirá|definí|fijate|sabés)\b", re.I)
        for a in archivos:
            with self.subTest(archivo=a.name):
                self.assertIsNone(prohibidas.search(a.read_text()), f"palabra prohibida en {a}")


class Receta(unittest.TestCase):
    RUTA = ROOT / "component" / "recipe.template.yaml"

    def test_parsea_y_tiene_lo_del_plan(self):
        texto = self.RUTA.read_text()
        if yaml is None:
            for pedazo in ("ComponentName: com.estacion.Escucha", "topic: 'estacion/eventos'",
                           "intervalSeconds: '3'", "threshold: '__THRESHOLD__'", "aws.greengrass#PublishToIoTCore"):
                self.assertIn(pedazo, texto)
            return
        r = yaml.safe_load(texto)
        self.assertEqual(r["ComponentName"], "com.estacion.Escucha")
        cfg = r["ComponentConfiguration"]["DefaultConfiguration"]
        self.assertEqual(cfg["topic"], "estacion/eventos")
        self.assertEqual(cfg["intervalSeconds"], "3")                 # número como texto, como pide Greengrass
        self.assertEqual(cfg["threshold"], "__THRESHOLD__")
        ipc = cfg["accessControl"]["aws.greengrass.ipc.mqttproxy"]["com.estacion.Escucha:mqttproxy:1"]
        self.assertEqual(ipc["operations"], ["aws.greengrass#PublishToIoTCore"])
        self.assertEqual(ipc["resources"], ["estacion/eventos"])
        m = r["Manifests"][0]
        self.assertEqual(m["Platform"]["os"], "linux")
        self.assertNotIn("Install", m["Lifecycle"])                  # las dependencias van en la imagen
        self.assertEqual(" ".join(m["Lifecycle"]["Run"].split()), RUN_ESPERADO)
        uris = [a["URI"] for a in m["Artifacts"]]
        self.assertEqual([u.rsplit("/", 1)[1] for u in uris], ["inference.py", "features.py", "model.onnx", "stats.json"])
        for u in uris:
            self.assertTrue(u.startswith("s3://__BUCKET__/estacion/__VERSION__/"), u)

    def test_cabe_en_una_lamina(self):
        lineas = self.RUTA.read_text().splitlines()
        self.assertLessEqual(len(lineas), 40)
        self.assertFalse([l for l in lineas if l.strip().startswith("#")], "la receta no lleva comentarios")


class Dashboard(unittest.TestCase):
    def test_json_valido_y_con_las_seis_senales(self):
        texto = (ROOT / "cloud" / "dashboard.json").read_text()
        d = json.loads(texto)
        usadas = set()
        for w in d["widgets"]:
            self.assertEqual(w["properties"]["region"], "__REGION__")
            if "alarms" in w["properties"].get("annotations", {}):
                # CloudWatch rechaza un widget de alarma con "metrics": la serie sale de la alarma
                self.assertNotIn("metrics", w["properties"])
                self.assertEqual(w["properties"]["annotations"]["alarms"],
                                 ["arn:aws:cloudwatch:__REGION__:__ACCOUNT__:alarm:estacion-fallas-no-oidas"])
                usadas.add("FallasNoOidas")
                continue
            for fila in w["properties"]["metrics"]:
                if fila[0] != "...":
                    self.assertEqual(fila[0], "__NS__")
                    usadas.add(fila[1])
        self.assertEqual(usadas, {"Alertas", "Score", "Umbral", "Inferencias", "InputZ", "LatencyMs", "FallasNoOidas"})
        # con los marcadores llenos sigue siendo JSON
        lleno = texto.replace("__REGION__", "us-east-1").replace("__NS__", "Estacion").replace("__ACCOUNT__", "123456789012")
        self.assertNotIn("__", lleno)
        json.loads(lleno)

    def test_todas_las_metricas_las_crea_setup(self):
        setup = (ROOT / "cloud" / "setup.sh").read_text()
        creadas = {shlex.split(l)[2] for l in setup.splitlines() if l.startswith("filtro ")}
        self.assertEqual(creadas, {"Alertas", "Score", "Umbral", "Inferencias", "InputZ", "LatencyMs", "FallasNoOidas"})


class Lambda(unittest.TestCase):
    """rollback_lambda.py con clientes de boto3 simulados a mano."""

    GRUPO = "arn:aws:iot:us-east-1:123456789012:thinggroup/EstacionAnillo0"

    def cargar(self):
        class GG:
            def __init__(self): self.llamadas = []
            def create_deployment(self, **kw):
                self.llamadas.append(kw)
                return {"deploymentId": "dep-123"}

        class SSM:
            def __init__(self): self.pedidos = []
            def get_parameter(self, Name):
                self.pedidos.append(Name)
                return {"Parameter": {"Value": "1.0.0"}}

        self.gg, self.ssm = GG(), SSM()
        falso = types.SimpleNamespace(client=lambda nombre, **kw: {"greengrassv2": self.gg, "ssm": self.ssm}[nombre])
        env = {"THING_GROUP_ARN": self.GRUPO, "COMPONENT": "com.estacion.Escucha",
               "LAST_GOOD_PARAM": "/estacion/last_good_version"}
        with mock.patch.dict(sys.modules, {"boto3": falso}), mock.patch.dict(os.environ, env):
            spec = importlib.util.spec_from_file_location("rollback_lambda", ROOT / "cloud" / "rollback_lambda.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self.mod = mod
            self.env = env

    @staticmethod
    def evento(estado):
        return {"source": "aws.cloudwatch", "alarmData": {"alarmName": "estacion-fallas-no-oidas",
                                                           "state": {"value": estado}}}

    def setUp(self):
        # la Lambda imprime sus logs; en las pruebas no hacen falta
        nulo = open(os.devnull, "w")
        silencio = mock.patch("sys.stdout", new=nulo)
        silencio.start()
        self.addCleanup(nulo.close)
        self.addCleanup(silencio.stop)

    def test_en_ok_no_hace_nada(self):
        self.cargar()
        with mock.patch.dict(os.environ, self.env):
            r = self.mod.handler(self.evento("OK"), None)
        self.assertTrue(r["skipped"])
        self.assertEqual(self.gg.llamadas, [])
        self.assertEqual(self.ssm.pedidos, [])

    def test_sin_datos_suficientes_tampoco(self):
        self.cargar()
        with mock.patch.dict(os.environ, self.env):
            self.assertTrue(self.mod.handler(self.evento("INSUFFICIENT_DATA"), None)["skipped"])
            self.assertTrue(self.mod.handler({}, None)["skipped"])
        self.assertEqual(self.gg.llamadas, [])

    def test_en_alarm_despliega_la_ultima_version_buena_al_anillo_0(self):
        self.cargar()
        with mock.patch.dict(os.environ, self.env):
            r = self.mod.handler(self.evento("ALARM"), None)
        self.assertEqual(self.ssm.pedidos, ["/estacion/last_good_version"])
        self.assertEqual(len(self.gg.llamadas), 1)
        d = self.gg.llamadas[0]
        self.assertEqual(d["targetArn"], self.GRUPO)
        self.assertTrue(d["targetArn"].endswith("thinggroup/EstacionAnillo0"))
        self.assertEqual(d["components"]["com.estacion.Escucha"]["componentVersion"], "1.0.0")
        self.assertEqual(d["deploymentPolicies"]["failureHandlingPolicy"], "ROLLBACK")
        self.assertEqual(r["rolled_back_to"], "1.0.0")
        self.assertEqual(r["deploymentId"], "dep-123")

    def test_setup_apunta_la_lambda_al_anillo_0(self):
        setup = (ROOT / "cloud" / "setup.sh").read_text()
        self.assertIn("THING_GROUP_ARN=arn:aws:iot:$REGION:$ACCOUNT:thinggroup/EstacionAnillo0", setup)
        self.assertIn("--alarm-actions \"$LAMBDA_ARN\"", setup)


class Formato(unittest.TestCase):
    def setUp(self):
        os.environ["TZ"] = "UTC"
        time.tzset()
        sys.path.insert(0, str(ROOT / "demo"))
        import formato_eventos
        self.f = formato_eventos
        self.base = {"device": "bomba-03", "model_version": "1.0.0", "score": 0.82, "threshold": 0.5, "alert": True,
                     "input_z": 1.12, "latency_ms": 3.6, "truth": "anomaly",
                     "ts": 1760000000000, "arrived_ts": 1760000001500}

    def test_la_linea_del_plan(self):
        self.assertTrue(self.f.formatear(self.base, color=False).endswith(
            "bomba-03  v1.0.0  ALERTA  score 0,82 (umbral 0,50)  entrada 1,1  4 ms"))

    def test_llego_tarde_solo_pasados_10_s(self):
        e = dict(self.base, arrived_ts=self.base["ts"] + 10_000)
        self.assertNotIn("tarde", self.f.formatear(e, color=False))
        e = dict(self.base, arrived_ts=self.base["ts"] + 40_000)
        self.assertTrue(self.f.formatear(e, color=False).endswith("4 ms  · llegó 40 s tarde"))

    def test_scores_chicos_llevan_mas_decimales_y_lo_normal_no_alerta(self):
        e = dict(self.base, score=0.0031, threshold=0.0123, alert=False, truth="normal", latency_ms=0.4)
        linea = self.f.formatear(e, color=False)
        self.assertIn("normal  score 0,0031 (umbral 0,0123)", linea)
        self.assertTrue(linea.endswith("<1 ms"))

    def test_falla_no_oida(self):
        e = dict(self.base, alert=False, truth="anomaly")
        self.assertTrue(self.f.formatear(e, color=False).endswith("· falla no oída"))
        self.assertNotIn("falla no oída", self.f.formatear(dict(self.base, truth="normal"), color=False))

    def test_hora_local_del_arrived_ts_y_ruido_ignorado(self):
        self.assertTrue(self.f.formatear(self.base, color=False).startswith("08:53:21  "))
        self.assertIsNone(self.f.formatear({"hola": 1}))


class ContratoConElModelo(unittest.TestCase):
    """La receta, el componente del agente Modelo, los filtros de métrica y watch.sh hablan el mismo idioma.
    Se salta si faltan build/1.0.0 o numpy/onnxruntime (corre el componente de verdad, con --local)."""

    def test_el_run_de_la_receta_corre_y_su_evento_alimenta_filtros_y_formato(self):
        build = ROOT / "build" / "1.0.0"
        audio = ROOT / "data" / "estacion" / "bomba-03"
        try:
            import numpy, onnxruntime  # noqa: F401
        except ImportError:
            self.skipTest("faltan numpy/onnxruntime")
        if not (build / "model.onnx").exists() or not (audio / "falla").exists():
            self.skipTest("faltan build/1.0.0 o data/estacion (corre model/train.py y model/prepare_data.py)")
        receta = yaml.safe_load((ROOT / "component" / "recipe.template.yaml").read_text()) if yaml else None
        if receta is None:
            self.skipTest("falta PyYAML")
        cfg = receta["ComponentConfiguration"]["DefaultConfiguration"]
        stats = json.loads((build / "stats.json").read_text())
        modo = Path(tempfile.mkdtemp()) / "modo"
        modo.write_text("falla\n")
        self.addCleanup(shutil.rmtree, modo.parent, ignore_errors=True)
        run = " ".join(receta["Manifests"][0]["Lifecycle"]["Run"].split())
        for a, b in (("{artifacts:path}", str(build)), ("__VERSION__", "1.0.0"), ("{configuration:/topic}", cfg["topic"]),
                     ("{configuration:/threshold}", str(stats["threshold"])), ("{configuration:/intervalSeconds}", "0.1"),
                     ("/run/estacion/modo", str(modo)), ("/data/estacion", str(ROOT / "data" / "estacion"))):
            run = run.replace(a, b)
        r = subprocess.run([*shlex.split(run), "--local", "--max", "2"], capture_output=True, text=True, timeout=120,
                           env={**os.environ, "AWS_IOT_THING_NAME": "bomba-03"})
        self.assertEqual(r.returncode, 0, r.stderr)
        eventos = [json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")]
        self.assertEqual(len(eventos), 2)
        e = eventos[0]
        # los campos que leen los filtros de métrica de setup.sh
        for campo in ("device", "model_version", "score", "threshold", "alert", "input_z", "latency_ms", "truth"):
            self.assertIn(campo, e)
        self.assertIsInstance(e["alert"], bool)                       # { $.alert IS TRUE }
        self.assertIn(e["truth"], ("normal", "anomaly"))
        self.assertEqual(e["device"], "bomba-03")
        sys.path.insert(0, str(ROOT / "demo"))
        import formato_eventos
        self.assertTrue(formato_eventos.formatear(e, color=False).split("  ")[1] == "bomba-03")


class Watch(unittest.TestCase):
    def test_watch_filtra_y_formatea(self):
        env = Entorno(self)
        base = {"device": "bomba-03", "model_version": "1.0.0", "score": 0.82, "threshold": 0.5, "alert": True,
                "input_z": 1.12, "latency_ms": 3.6, "truth": "anomaly", "ts": 1760000000000, "arrived_ts": 1760000040000}
        otra = dict(base, device="bomba-02", alert=False, truth="normal", arrived_ts=1760000000500)
        env.tail.write_text("\n".join(
            "2025-10-09T08:53:20 " + json.dumps(e) for e in (base, otra)) + "\nlinea rara sin json\n")
        r = env.correr("demo/watch.sh")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(r.stdout.strip().splitlines()), 2)
        self.assertIn("llegó 40 s tarde", r.stdout)
        r = env.correr("demo/watch.sh", "bomba-02")
        self.assertEqual(len(r.stdout.strip().splitlines()), 1)
        self.assertIn("bomba-02", r.stdout)
        tail = env.aws("logs", "tail")[0]["args"]
        self.assertIn("/estacion/eventos", tail)
        self.assertIn("--follow", tail)


class Publish(unittest.TestCase):
    def setUp(self):
        self.e = Entorno(self)

    def test_publica_con_el_umbral_de_stats(self):
        self.e.build_falso("9.9.9", threshold=0.0123)
        r = self.e.correr("demo/publish.sh", "9.9.9", SHIM_MISSING=r"describe-component (?!.*componentState)")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        subidas = [c["args"] for c in self.e.aws("s3", "cp")]
        destinos = sorted(a[3] for a in subidas)
        self.assertEqual(destinos, [f"s3://estacion-123456789012-us-east-1/estacion/9.9.9/{f}"
                                    for f in ("features.py", "inference.py", "model.onnx", "stats.json")])
        crear = self.e.aws("greengrassv2", "create-component-version")
        self.assertEqual(len(crear), 1)
        receta = list(crear[0]["files"].values())[0]
        self.assertNotIn("__", receta)                      # ningún marcador sin llenar
        self.assertIn("threshold: '0.0123'", receta)
        self.assertIn("ComponentVersion: '9.9.9'", receta)
        self.assertIn("s3://estacion-123456789012-us-east-1/estacion/9.9.9/model.onnx", receta)
        if yaml:
            self.assertEqual(yaml.safe_load(receta)["ComponentConfiguration"]["DefaultConfiguration"]["threshold"], "0.0123")

    def test_se_niega_con_audio_sintetico(self):
        self.e.build_falso("9.9.9", synthetic=True)
        r = self.e.correr("demo/publish.sh", "9.9.9", SHIM_MISSING=r"describe-component (?!.*componentState)")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("synthetic", r.stdout + r.stderr)
        self.assertEqual(self.e.aws("s3", "cp"), [])
        self.assertEqual(self.e.aws("greengrassv2", "create-component-version"), [])

    def test_con_allow_synthetic_publica(self):
        self.e.build_falso("9.9.9", synthetic=True)
        r = self.e.correr("demo/publish.sh", "9.9.9", "--allow-synthetic", SHIM_MISSING=r"describe-component (?!.*componentState)")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(self.e.aws("greengrassv2", "create-component-version")), 1)

    def test_una_version_publicada_no_se_toca(self):
        self.e.build_falso("9.9.9")
        r = self.e.correr("demo/publish.sh", "9.9.9")        # describe-component responde "existe"
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("ya está publicada", r.stdout)
        self.assertEqual(self.e.aws("s3", "cp"), [])
        self.assertEqual(self.e.aws("greengrassv2", "create-component-version"), [])

    def test_artefactos_incompletos_o_de_otra_version(self):
        r = self.e.correr("demo/publish.sh", "9.9.9")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("falta build/9.9.9/", r.stdout)
        self.e.build_falso("9.9.9", version="1.0.0")
        r = self.e.correr("demo/publish.sh", "9.9.9")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("1.0.0", r.stdout + r.stderr)

    def test_sha256_que_no_es_el_del_modelo(self):
        self.e.build_falso("9.9.9", sha256="0" * 64)
        r = self.e.correr("demo/publish.sh", "9.9.9")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("sha256", r.stdout + r.stderr)
        self.assertEqual(self.e.aws("s3", "cp"), [])

    def test_version_mal_escrita(self):
        self.assertNotEqual(self.e.correr("demo/publish.sh", "uno").returncode, 0)


class Deploy(unittest.TestCase):
    def setUp(self):
        self.e = Entorno(self)

    def despliegues(self):
        res = []
        for c in self.e.aws("greengrassv2", "create-deployment"):
            doc = json.loads(list(c["files"].values())[0])
            res.append(doc)
        return res

    def test_anillo_0_solo_toca_el_canario(self):
        r = self.e.correr("demo/deploy.sh", "2.0.0", "anillo-0")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        (d,) = self.despliegues()
        self.assertEqual(d["targetArn"], "arn:aws:iot:us-east-1:123456789012:thinggroup/EstacionAnillo0")
        self.assertEqual(d["components"]["com.estacion.Escucha"]["componentVersion"], "2.0.0")
        self.assertEqual(self.e.aws("ssm", "put-parameter"), [])            # solo la 1.0.0 es "última buena"

    def test_la_forma_del_despliegue(self):
        self.e.correr("demo/deploy.sh", "2.0.0", "anillo-1")
        (d,) = self.despliegues()
        self.assertEqual(d["targetArn"].rsplit("/", 1)[1], "EstacionAnillo1")
        self.assertEqual(d["deploymentPolicies"]["failureHandlingPolicy"], "ROLLBACK")
        job = d["iotJobConfiguration"]
        exp = job["jobExecutionsRolloutConfig"]["exponentialRate"]
        self.assertGreaterEqual(exp["incrementFactor"], 1)
        self.assertIn("numberOfNotifiedThings", exp["rateIncreaseCriteria"])
        crit = job["abortConfig"]["criteriaList"][0]
        self.assertEqual((crit["failureType"], crit["action"]), ("FAILED", "CANCEL"))
        self.assertEqual(d["components"]["com.estacion.Escucha"]["configurationUpdate"], {"reset": [""]})

    def test_la_1_0_0_a_todas_guarda_la_ultima_version_buena(self):
        r = self.e.correr("demo/deploy.sh", "1.0.0", "todas")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual({d["targetArn"].rsplit("/", 1)[1] for d in self.despliegues()},
                         {"EstacionAnillo0", "EstacionAnillo1"})
        (ssm,) = self.e.aws("ssm", "put-parameter")
        self.assertIn("/estacion/last_good_version", ssm["args"])
        self.assertIn("1.0.0", ssm["args"])

    def test_el_umbral_se_cambia_sin_reentrenar(self):
        self.e.correr("demo/deploy.sh", "1.0.0", "anillo-1", UMBRAL="0.02")
        (d,) = self.despliegues()
        upd = d["components"]["com.estacion.Escucha"]["configurationUpdate"]
        self.assertEqual(json.loads(upd["merge"]), {"threshold": "0.02"})

    def test_rechaza_lo_que_no_entiende(self):
        self.assertNotEqual(self.e.correr("demo/deploy.sh", "2.0.0", "anillo-9").returncode, 0)
        self.assertNotEqual(self.e.correr("demo/deploy.sh", "dos", "anillo-0").returncode, 0)
        self.assertEqual(self.despliegues(), [])

    def test_version_no_publicada(self):
        r = self.e.correr("demo/deploy.sh", "3.0.0", "anillo-0", SHIM_MISSING="describe-component")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("publish.sh", r.stdout)
        self.assertEqual(self.despliegues(), [])


class DemoEnLaBomba(unittest.TestCase):
    def setUp(self):
        self.e = Entorno(self)

    def exec_(self):
        return [c["args"] for c in self.e.llamadas("docker")]

    def test_falla(self):
        self.assertEqual(self.e.correr("demo/falla.sh", "bomba-03").returncode, 0)
        self.assertEqual(self.e.correr("demo/falla.sh", "bomba-03", "off").returncode, 0)
        a, b = self.exec_()
        self.assertEqual(a[:2], ["exec", "bomba-03"]); self.assertEqual(a[-1], "falla")
        self.assertEqual(b[:2], ["exec", "bomba-03"]); self.assertEqual(b[-1], "normal")
        self.assertIn("/run/estacion/modo", " ".join(a))

    def test_dominio(self):
        self.assertEqual(self.e.correr("demo/dominio.sh", "bomba-05", "nuevo").returncode, 0)
        self.assertEqual(self.exec_()[0][-1], "nuevo")
        self.assertNotEqual(self.e.correr("demo/dominio.sh", "bomba-05", "falla").returncode, 0)

    def test_red(self):
        self.assertEqual(self.e.correr("demo/red.sh", "off", "bomba-03").returncode, 0)
        self.assertEqual(self.e.correr("demo/red.sh", "on", "bomba-03").returncode, 0)
        self.assertEqual(self.exec_(), [["network", "disconnect", "estacion", "bomba-03"],
                                        ["network", "connect", "estacion", "bomba-03"]])

    def test_rechazan_bombas_que_no_existen(self):
        for s, args in (("falla", ["bomba-09"]), ("dominio", ["bomba-00", "nuevo"]), ("red", ["off", "casa"])):
            self.assertNotEqual(self.e.correr(f"demo/{s}.sh", *args).returncode, 0, s)
        self.assertEqual(self.exec_(), [])


class Flota(unittest.TestCase):
    def setUp(self):
        self.e = Entorno(self)
        for n in range(1, 6):
            (self.e.poc / "data" / "estacion" / f"bomba-0{n}" / "normal").mkdir(parents=True)

    def runs(self):
        return [c for c in self.e.llamadas("docker") if c["args"][:2] == ["run", "-d"]]

    @staticmethod
    def env_de(c):
        a = c["args"]
        return dict(x.split("=", 1) for i, x in enumerate(a) if i and a[i - 1] == "-e")

    @staticmethod
    def montajes(c):
        a = c["args"]
        return [x for i, x in enumerate(a) if i and a[i - 1] == "-v"]

    def test_primer_arranque_cinco_bombas_en_sus_anillos(self):
        r = self.e.correr("fleet/up.sh")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.e.llamadas("docker")[0]["args"], ["image", "inspect", "estacion/greengrass:latest"])
        self.assertIn(["network", "create", "estacion"], [c["args"] for c in self.e.llamadas("docker")])
        runs = self.runs()
        self.assertEqual([c["args"][c["args"].index("--name") + 1] for c in runs], [f"bomba-0{n}" for n in range(1, 6)])
        for c in runs:
            a, env = c["args"], self.env_de(c)
            b = env["THING_NAME"]
            self.assertEqual(env["THING_GROUP_NAME"], "EstacionAnillo0" if b == "bomba-01" else "EstacionAnillo1")
            self.assertEqual(a[a.index("--network") + 1], "estacion")
            self.assertIn("--init", a)
            self.assertIn(f"{b}-gg:/greengrass/v2", self.montajes(c))                 # volumen por bomba
            self.assertTrue(any(m.endswith(f"/fleet/logs/{b}:/greengrass/v2/logs") for m in self.montajes(c)))
            self.assertTrue(any(m.endswith(f"/data/estacion/{b}:/data/estacion/{b}:ro") for m in self.montajes(c)))
            self.assertEqual(env["THING_POLICY_NAME"], "EstacionThingPolicy")
            self.assertNotIn("--cpus", a)
            # en el primer arranque el montaje tiene credenciales temporales...
            self.assertIn("aws_session_token = token-temporal", c["credenciales_visibles"])
        # ...y al terminar no queda ninguna en el disco
        self.assertFalse((self.e.poc / "fleet" / ".bootstrap" / "credentials").exists())
        # se aprovisiona de a una: el wait de la 1 ocurre antes del run de la 2
        orden = [(c["args"][0], c["args"][1]) for c in self.e.llamadas("docker") if c["args"][0] in ("run", "exec")]
        self.assertEqual(orden[:3], [("run", "-d"), ("exec", "bomba-01"), ("run", "-d")])

    def test_arranques_siguientes_sin_credenciales(self):
        r = self.e.correr("fleet/up.sh", SHIM_PROVISIONED="1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(self.runs()), 5)
        for c in self.runs():
            self.assertIsNone(c["credenciales_visibles"])
        self.assertEqual(self.e.aws("configure", "export-credentials"), [])

    def test_equipo_pequeno_limita_cpu_y_memoria(self):
        self.e.correr("fleet/up.sh", "--pequeno")
        for c in self.runs():
            a = c["args"]
            self.assertEqual(a[a.index("--cpus") + 1], "1")
            self.assertEqual(a[a.index("--memory") + 1], "1g")
            self.assertEqual(a[a.index("--memory-swap") + 1], "1g")
        self.e.reiniciar_log()
        self.e.correr("fleet/up.sh", "--pequeno", CPUS="0.5", MEM="768m")
        a = self.runs()[0]["args"]
        self.assertEqual((a[a.index("--cpus") + 1], a[a.index("--memory") + 1]), ("0.5", "768m"))

    def test_el_audio_queda_legible_para_ggc_user(self):
        d = self.e.poc / "data" / "estacion" / "bomba-02" / "normal"
        d.chmod(0o700)
        (d / "x.wav").write_bytes(b"RIFF")
        (d / "x.wav").chmod(0o600)
        self.e.correr("fleet/up.sh")
        self.assertTrue(d.stat().st_mode & stat.S_IROTH and d.stat().st_mode & stat.S_IXOTH)
        self.assertTrue((d / "x.wav").stat().st_mode & stat.S_IROTH)

    def test_sin_audio_no_arranca_nada(self):
        shutil.rmtree(self.e.poc / "data" / "estacion" / "bomba-04")
        r = self.e.correr("fleet/up.sh")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("bomba-04", r.stdout + r.stderr)
        self.assertEqual(self.runs(), [])

    def test_otro_directorio_de_datos(self):
        for n in range(1, 6):
            (self.e.poc / "data" / "otra" / f"bomba-0{n}").mkdir(parents=True)
        shutil.rmtree(self.e.poc / "data" / "estacion")
        r = self.e.correr("fleet/up.sh", DATA="data/otra")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(any("/data/otra/bomba-01:/data/estacion/bomba-01:ro" in m for m in self.montajes(self.runs()[0])))

    def test_tope_de_memoria_del_nucleus(self):
        self.e.correr("fleet/up.sh")
        self.assertEqual(self.env_de(self.runs()[0])["JAVA_TOOL_OPTIONS"], "-Xmx256m -XX:+UseSerialGC")
        self.e.reiniciar_log()
        self.e.correr("fleet/up.sh", NUCLEUS_HEAP="")
        self.assertNotIn("JAVA_TOOL_OPTIONS", self.env_de(self.runs()[0]))

    def test_down(self):
        r = self.e.correr("fleet/down.sh")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.e.aws("iot"), [])
        self.assertNotIn(["volume", "rm", "bomba-01-gg"], [c["args"] for c in self.e.llamadas("docker")])

    def test_down_borrando_things(self):
        r = self.e.correr("fleet/down.sh", "--borrar-things")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(["volume", "rm", "bomba-05-gg"], [c["args"] for c in self.e.llamadas("docker")])
        borrados = [c["args"][c["args"].index("--thing-name") + 1] for c in self.e.aws("iot", "delete-thing")]
        self.assertEqual(borrados, [f"bomba-0{n}" for n in range(1, 6)])


class Imagen(unittest.TestCase):
    def test_versiones_fijas_y_url_oficial(self):
        d = (ROOT / "fleet" / "Dockerfile").read_text()
        for dep in ("numpy", "onnxruntime", "awsiotsdk", "awscrt"):
            self.assertRegex(d, rf"{dep}==\d+\.\d+\.\d+")
        self.assertIn("https://d2s8p88vqu9w66.cloudfront.net/releases/greengrass-${GREENGRASS_VERSION}.zip", d)
        version = re.search(r"ARG GREENGRASS_VERSION=(\d+\.\d+\.\d+)", d).group(1)
        self.assertIn(f'GREENGRASS_VERSION:-{version}', (ROOT / "fleet" / "build.sh").read_text())   # build.sh y Dockerfile coinciden
        self.assertIn("openjdk", d)                       # Java para el nucleus
        self.assertIn("ENTRYPOINT", d)

    def test_dependencias_de_la_imagen_son_las_del_modelo(self):
        """El componente importa numpy, onnxruntime y awsiot: la receta no instala nada, así que la imagen tiene que traerlos."""
        d = (ROOT / "fleet" / "Dockerfile").read_text()
        codigo = (ROOT / "component" / "inference.py").read_text()
        for mod, paquete in (("numpy", "numpy"), ("onnxruntime", "onnxruntime"), ("awsiot", "awsiotsdk")):
            if re.search(rf"^\s*(import|from) {mod}\b", codigo, re.M):
                self.assertIn(paquete + "==", d)


class Entrypoint(unittest.TestCase):
    """El entrypoint de la imagen, con un `java` y un `loader` falsos."""

    def preparar(self):
        self.e = Entorno(self)
        self.ggc = self.e.dir / "gg"
        self.ggc.mkdir()
        self.creds = self.e.dir / "boot" / "credentials"
        self.creds.parent.mkdir()
        _escribir(self.e.bin / "java", textwrap.dedent(f"""\
            #!/usr/bin/env bash
            echo "$@" > {self.e.dir}/java.args
            env | grep '^AWS_' | sort > {self.e.dir}/java.env
            mkdir -p {self.ggc}/alts/current/distro/bin
            printf '#!/usr/bin/env bash\\nenv | grep "^AWS_" | sort > {self.e.dir}/loader.env\\necho arrancó > {self.e.dir}/loader.ok\\n' \\
                > {self.ggc}/alts/current/distro/bin/loader
            chmod +x {self.ggc}/alts/current/distro/bin/loader
            """), True)
        self.env_extra = {"GGC_ROOT_PATH": str(self.ggc), "CREDS_FILE": str(self.creds),
                          "ESTACION_RUN_DIR": str(self.e.dir / "run"), "INSTALLER_JAR": "/opt/falso/Greengrass.jar",
                          "THING_NAME": "bomba-02", "THING_GROUP_NAME": "EstacionAnillo1", "AWS_REGION": "us-east-1",
                          "THING_POLICY_NAME": "EstacionThingPolicy"}

    def arrancar(self):
        return subprocess.run([str(self.e.poc / "fleet" / "entrypoint.sh")], cwd=self.e.poc,
                              env={**self.e.env, **self.env_extra}, capture_output=True, text=True, timeout=60)

    def test_primer_arranque_aprovisiona_y_el_nucleus_no_ve_las_credenciales(self):
        self.preparar()
        self.creds.write_text("[default]\naws_access_key_id = ASIAEJEMPLO\naws_secret_access_key = secreto/con%porcentaje\n"
                              "aws_session_token = token-temporal\n")
        r = self.arrancar()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        args = (self.e.dir / "java.args").read_text().split()
        for esperado in ("--provision", "true", "--setup-system-service", "false", "--start", "--thing-name", "bomba-02",
                         "--thing-group-name", "EstacionAnillo1", "--thing-policy-name", "EstacionThingPolicy",
                         "--aws-region", "us-east-1", "--component-default-user", "ggc_user:ggc_group", "/opt/falso/Greengrass.jar"):
            self.assertIn(esperado, args)
        self.assertEqual(args[args.index("--start") + 1], "false")
        self.assertIn("AWS_SESSION_TOKEN=token-temporal", (self.e.dir / "java.env").read_text())
        self.assertIn("AWS_SECRET_ACCESS_KEY=secreto/con%porcentaje", (self.e.dir / "java.env").read_text())
        self.assertTrue((self.ggc / ".estacion-aprovisionado").exists())
        self.assertTrue((self.e.dir / "loader.ok").exists())
        visibles = (self.e.dir / "loader.env").read_text()                # el nucleus arranca sin credenciales
        for nombre in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
            self.assertNotIn(nombre, visibles)
        self.assertEqual((self.e.dir / "run" / "modo").read_text().strip(), "normal")

    def test_segundo_arranque_no_pide_credenciales_ni_reinstala(self):
        self.preparar()
        (self.ggc / ".estacion-aprovisionado").write_text("x")
        loader = self.ggc / "alts" / "current" / "distro" / "bin" / "loader"
        _escribir(loader, f"#!/usr/bin/env bash\necho ok > {self.e.dir}/loader.ok\n", True)
        (self.e.dir / "run").mkdir()
        (self.e.dir / "run" / "modo").write_text("falla\n")                # el modo sobrevive al reinicio
        r = self.arrancar()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse((self.e.dir / "java.args").exists())
        self.assertTrue((self.e.dir / "loader.ok").exists())
        self.assertEqual((self.e.dir / "run" / "modo").read_text().strip(), "falla")

    def test_sin_identidad_y_sin_credenciales_se_detiene_con_un_mensaje_claro(self):
        self.preparar()
        r = self.arrancar()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("./fleet/up.sh", r.stdout + r.stderr)
        self.assertFalse((self.e.dir / "loader.ok").exists())


class Setup(unittest.TestCase):
    """setup.sh y teardown.sh contra un `aws` falso: cada documento que manda debe ser JSON válido."""

    def correr_setup(self, falta=None, **env):
        e = Entorno(self)
        r = e.correr("cloud/setup.sh", SHIM_MISSING=falta or "", **env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return e

    CUENTA_NUEVA = (r"head-bucket|get-role |describe-thing-group|describe-role-alias|get-policy |get-topic-rule|"
                    r"get-function|ssm get-parameter")

    def test_cuenta_nueva(self):
        e = self.correr_setup(self.CUENTA_NUEVA)
        self.revisar(e)
        self.assertEqual(len(e.aws("iot", "create-thing-group")), 2)
        self.assertEqual(len(e.aws("lambda", "create-function")), 1)
        self.assertEqual(len(e.aws("iot", "create-topic-rule")), 1)
        self.assertEqual(len(e.aws("iot", "create-policy")), 2)
        self.assertEqual(len(e.aws("ssm", "put-parameter")), 1)

    def test_repetir_no_rompe_y_actualiza(self):
        e = self.correr_setup(None)
        self.revisar(e)
        self.assertEqual(e.aws("iot", "create-thing-group"), [])
        self.assertEqual(e.aws("lambda", "create-function"), [])
        self.assertEqual(len(e.aws("iot", "replace-topic-rule")), 1)
        self.assertEqual(e.aws("ssm", "put-parameter"), [])           # no pisa la última versión buena

    def revisar(self, e):
        # todo documento que se manda a AWS es JSON y no trae marcadores sin llenar
        docs = {}
        for c in e.llamadas("aws"):
            for k, v in c["files"].items():
                if k.startswith("file://") and not c["args"][0] == "lambda":
                    docs[k] = json.loads(v)
                    self.assertNotIn("__", v, k)
        self.assertGreaterEqual(len(docs), 8)
        # la política de las bombas conserva sus $aws y deja publicar solo en el tema de la estación
        pol = [c for c in e.llamadas("aws") if c["args"][:2] in (["iot", "create-policy"], ["iot", "create-policy-version"])
               and "EstacionThingPolicy" in c["args"]]
        texto = list(pol[0]["files"].values())[0]
        self.assertIn("topic/$aws/things/bomba-*/jobs/*", texto)
        self.assertIn("topic/estacion/eventos", texto)
        # la regla suma arrived_ts y escribe en el grupo de logs de la estación
        regla = json.loads(list(e.aws("iot", "create-topic-rule" if e.aws("iot", "create-topic-rule") else "replace-topic-rule")[0]["files"].values())[0])
        self.assertEqual(regla["sql"], "SELECT *, timestamp() AS arrived_ts FROM 'estacion/eventos'")
        self.assertEqual(regla["actions"][0]["cloudwatchLogs"]["logGroupName"], "/estacion/eventos")
        # filtros de métrica: siete, en el namespace Estacion, FallasNoOidas con valor por defecto y sin dimensiones
        filtros = {c["args"][c["args"].index("--filter-name") + 1]:
                   json.loads(c["args"][c["args"].index("--metric-transformations") + 1])[0] for c in e.aws("logs", "put-metric-filter")}
        self.assertEqual(len(filtros), 7)
        self.assertEqual({f["metricNamespace"] for f in filtros.values()}, {"Estacion"})
        self.assertEqual(filtros["alertas"]["dimensions"], {"Device": "$.device"})
        self.assertEqual(filtros["score"]["dimensions"], {"Version": "$.model_version"})
        self.assertEqual(filtros["fallas"]["defaultValue"], 0)
        self.assertNotIn("dimensions", filtros["fallas"])
        for f in filtros.values():
            self.assertFalse("dimensions" in f and "defaultValue" in f)    # CloudWatch no lo admite
        patron = [c["args"][c["args"].index("--filter-pattern") + 1] for c in e.aws("logs", "put-metric-filter")
                  if c["args"][c["args"].index("--filter-name") + 1] == "fallas"][0]
        self.assertEqual(patron, '{ ($.truth = "anomaly") && ($.alert IS FALSE) }')
        # dashboard
        (dash,) = e.aws("cloudwatch", "put-dashboard")
        self.assertEqual(dash["args"][dash["args"].index("--dashboard-name") + 1], "estacion")
        json.loads(list(dash["files"].values())[0])
        # alarma → Lambda
        (alarma,) = e.aws("cloudwatch", "put-metric-alarm")
        a = alarma["args"]
        self.assertEqual(a[a.index("--alarm-name") + 1], "estacion-fallas-no-oidas")
        self.assertEqual(a[a.index("--metric-name") + 1], "FallasNoOidas")
        self.assertTrue(a[a.index("--alarm-actions") + 1].endswith(":function:estacion-rollback"))
        (permiso,) = e.aws("lambda", "add-permission")
        self.assertIn("lambda.alarms.cloudwatch.amazonaws.com", permiso["args"])

    def test_umbral_de_la_alarma_se_puede_cambiar(self):
        e = self.correr_setup(None, ALARM_THRESHOLD="12")
        (alarma,) = e.aws("cloudwatch", "put-metric-alarm")
        self.assertEqual(alarma["args"][alarma["args"].index("--threshold") + 1], "12")

    def test_teardown_borra_todo(self):
        e = Entorno(self)
        r = e.correr("cloud/teardown.sh", "--yes")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for prefijo in (("cloudwatch", "delete-alarms"), ("lambda", "delete-function"), ("iot", "delete-topic-rule"),
                        ("logs", "delete-log-group"), ("cloudwatch", "delete-dashboards"), ("iot", "delete-role-alias"),
                        ("ssm", "delete-parameter"), ("s3", "rb")):
            self.assertEqual(len(e.aws(*prefijo)), 1, prefijo)
        self.assertEqual(len(e.aws("iot", "delete-thing")), 5)
        self.assertEqual(len(e.aws("iot", "delete-thing-group")), 2)
        self.assertEqual(len(e.aws("iam", "delete-role")), 3)

    def test_teardown_pide_confirmacion(self):
        e = Entorno(self)
        r = e.correr("cloud/teardown.sh", entrada="no\n")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(e.aws("lambda", "delete-function"), [])


if __name__ == "__main__":
    unittest.main()
