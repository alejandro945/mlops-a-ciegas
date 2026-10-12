"""
Prueba de punta a punta del modelo con el set sintético (sin AWS y sin los datos reales):

  synth.py → prepare_data.py → train.py --rapido → inference.py --local

El audio de la flota y los artefactos quedan de solo lectura, como en el equipo.
Todo corre en una carpeta temporal: no toca build/, data/ ni charla/.

Uso:  python3 -m unittest discover -s poc-devopsdays/tests -p 'test_model*.py' -v
"""
import hashlib, io, json, os, re, shutil, struct, subprocess, sys, tempfile, unittest, wave
sys.dont_write_bytecode = True

TESTS = os.path.dirname(os.path.abspath(__file__))
POC = os.path.dirname(TESTS)
REPO = os.path.dirname(POC)
MODEL = os.path.join(POC, "model")
METRICS_PY = os.path.join(REPO, "charla", "tools", "metrics.py")
EVENTO = ["device", "model_version", "sha256", "seq", "ts", "clip", "domain",
          "score", "threshold", "alert", "input_z", "latency_ms", "truth"]
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def corre(*args, env=None):
    r = subprocess.run([sys.executable, *args], capture_output=True, text=True, env=env or ENV, timeout=900)
    if r.returncode:
        raise AssertionError(f"falló {' '.join(args)}\n{r.stdout}\n{r.stderr}")
    return r.stdout


def lee(ruta, modo="rb"):
    with open(ruta, modo) as f:
        return f.read()


def lee_json(ruta):
    return json.loads(lee(ruta, "r"))


def permisos(raiz, escribir):
    for d, _, fs in os.walk(raiz):
        os.chmod(d, 0o755 if escribir else 0o555)
        for f in fs:
            os.chmod(os.path.join(d, f), 0o644 if escribir else 0o444)


class TuberiaSintetica(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="estacion-")
        cls.datos = os.path.join(cls.tmp, "synthetic")
        cls.build = os.path.join(cls.tmp, "build")
        cls.flota = os.path.join(cls.tmp, "estacion")
        cls.charla = os.path.join(cls.tmp, "charla")
        cls.modo = os.path.join(cls.tmp, "modo")
        corre(os.path.join(MODEL, "synth.py"), "--out", cls.datos, "--segundos", "4")
        corre(os.path.join(MODEL, "prepare_data.py"), "--data", cls.datos, "--out", cls.flota,
              "--build", cls.build, "--charla", cls.charla)
        corre(os.path.join(MODEL, "train.py"), "--data", cls.datos, "--build", cls.build, "--rapido")
        permisos(cls.flota, False)
        for v in ("1.0.0", "2.0.0"):
            permisos(os.path.join(cls.build, v), False)

    @classmethod
    def tearDownClass(cls):
        permisos(cls.tmp, True)
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def eventos(self, bomba, modo, n=3, version="1.0.0", extra=()):
        if modo is None:
            if os.path.exists(self.modo):
                os.remove(self.modo)
        else:
            with open(self.modo, "w") as f:
                f.write(modo + "\n")
        d = os.path.join(self.build, version)
        out = corre(os.path.join(d, "inference.py"), "--model", os.path.join(d, "model.onnx"),
                    "--stats", os.path.join(d, "stats.json"), "--audio-root", self.flota,
                    "--mode-file", self.modo, "--version", version, "--topic", "estacion/eventos",
                    "--interval", "0", "--local", "--max", str(n), *extra,
                    env=dict(ENV, AWS_IOT_THING_NAME=bomba))
        return [json.loads(l) for l in out.splitlines() if l.strip()]

    def stats(self, version):
        return lee_json(os.path.join(self.build, version, "stats.json"))

    # · el evento

    def test_evento_con_el_esquema_exacto(self):
        st = self.stats("1.0.0")
        evs = self.eventos("bomba-03", "falla", n=4)
        self.assertEqual(len(evs), 4)
        for i, e in enumerate(evs, 1):
            self.assertEqual(list(e), EVENTO)
            self.assertEqual((e["device"], e["model_version"], e["seq"]), ("bomba-03", "1.0.0", i))
            self.assertEqual(e["sha256"], st["sha256"])
            self.assertEqual((e["domain"], e["truth"]), ("source", "anomaly"))
            self.assertRegex(e["clip"], r"^section_\d+_source_test_anomaly_\d+$")
            self.assertIsInstance(e["ts"], int)
            self.assertGreater(e["ts"], 1.7e12)
            for k in ("score", "threshold", "input_z", "latency_ms"):
                self.assertIsInstance(e[k], float)
            self.assertIsInstance(e["alert"], bool)
            self.assertEqual(e["alert"], e["score"] > e["threshold"])
            self.assertAlmostEqual(e["threshold"], st["threshold"], places=3)
            self.assertLess(len(json.dumps(e)), 600)          # unos cientos de bytes

    def test_modo_se_lee_de_la_carpeta(self):
        for e in self.eventos("bomba-05", "nuevo", n=2):
            self.assertEqual((e["domain"], e["truth"]), ("target", "normal"))
        for e in self.eventos("bomba-02", "normal", n=2):
            self.assertEqual((e["domain"], e["truth"]), ("source", "normal"))
        for e in self.eventos("bomba-04", None, n=2):        # sin archivo de modo: normal
            self.assertEqual(e["truth"], "normal")
        for e in self.eventos("bomba-04", "cualquier-cosa", n=1):
            self.assertEqual(e["truth"], "normal")

    def test_umbral_es_configuracion(self):
        for e in self.eventos("bomba-01", "normal", n=2, extra=("--threshold", "0")):
            self.assertEqual((e["threshold"], e["alert"]), (0.0, True))
        st = self.stats("2.0.0")
        for e in self.eventos("bomba-01", "normal", n=1, version="2.0.0", extra=("--threshold", "")):
            self.assertAlmostEqual(e["threshold"], st["threshold"], places=3)
            self.assertEqual(e["model_version"], "2.0.0")

    # · los artefactos

    def test_artefactos_por_version(self):
        archivos = {"model.onnx", "stats.json", "features.py", "inference.py"}
        self.assertEqual(set(os.listdir(os.path.join(self.build, "1.0.0"))), archivos | {"model.int8.onnx"})
        self.assertEqual(set(os.listdir(os.path.join(self.build, "2.0.0"))), archivos)
        fuente = lee(os.path.join(MODEL, "features.py"))
        self.assertEqual(lee(os.path.join(POC, "component", "features.py")), fuente)
        for v in ("1.0.0", "2.0.0"):
            st = self.stats(v)
            for k in ("version", "threshold", "sha256", "mean", "std", "synthetic"):
                self.assertIn(k, st)
            self.assertEqual(st["version"], v)
            self.assertIs(st["synthetic"], True)
            self.assertEqual(len(st["mean"]), 320)
            modelo = lee(os.path.join(self.build, v, "model.onnx"))
            self.assertEqual(st["sha256"], hashlib.sha256(modelo).hexdigest())
            self.assertEqual(lee(os.path.join(self.build, v, "features.py")), fuente)
            self.assertEqual(lee(os.path.join(self.build, v, "inference.py")),
                             lee(os.path.join(POC, "component", "inference.py")))

    def test_metrics_completo_y_sintetico(self):
        m = lee_json(os.path.join(self.build, "metrics.json"))
        self.assertIs(m["synthetic"], True)
        self.assertIn("sintético", m["dataset"])
        claves = sorted(set(re.findall(r"\b((?:v1|v2|int8|input)\.[a-z0-9_]+)", lee(METRICS_PY, "r"))))
        self.assertGreater(len(claves), 15)
        for k in claves:
            grupo, hoja = k.split(".")
            self.assertIsNotNone(m.get(grupo, {}).get(hoja), f"falta {k} en metrics.json")
        out = corre(METRICS_PY, "v1.recall_source", env=dict(ENV, METRICS_JSON=os.path.join(self.build, "metrics.json")))
        self.assertIn("v1.recall_source → por medir", out)

    def test_metrics_del_repo_no_llega_a_la_charla_si_es_sintetico(self):
        ruta = os.path.join(POC, "build", "metrics.json")
        if not os.path.exists(ruta) or not lee_json(ruta).get("synthetic"):
            self.skipTest("build/metrics.json no existe o es una medición real")
        self.assertIn("por medir", corre(METRICS_PY, "v1.recall_source"))

    # · los datos

    def test_flota_solo_con_clips_de_prueba(self):
        info = lee_json(os.path.join(self.build, "clips.json"))
        self.assertIs(info["synthetic"], True)
        self.assertEqual(sorted(info["bombas"]), [f"bomba-0{i}" for i in range(1, 6)])
        contaminados = set(info["contaminacion"])
        vistos = set()
        for b, v in info["bombas"].items():
            for carpeta in ("normal", "falla", "nuevo"):
                ids = v[carpeta]
                self.assertTrue(ids, f"{b}/{carpeta} vacía")
                self.assertEqual(sorted(os.path.splitext(f)[0] for f in os.listdir(os.path.join(self.flota, b, carpeta))), sorted(ids))
                for c in ids:
                    self.assertIn("_test_", c)
                    self.assertNotIn(c, contaminados)
                    self.assertNotIn(c, vistos, "un clip en dos bombas")
                    vistos.add(c)
        self.assertFalse(os.path.exists(self.charla), "audio sintético en charla/assets")

    def test_lee_wav_de_varios_canales_y_extensible(self):
        sys.path.insert(0, MODEL)
        import numpy as np
        import features as F
        x = (np.sin(np.arange(16000) / 5) * 8000).astype("<i2")
        estereo = np.stack([x, np.zeros_like(x)], 1)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(16000)
            w.writeframes(estereo.tobytes())
        y, sr = F.read_wav(buf.getvalue())
        self.assertEqual((len(y), sr), (16000, 16000))
        self.assertTrue(np.allclose(y, x / 32768.0))              # el primer canal
        # la misma señal con cabecera WAVE_FORMAT_EXTENSIBLE (wave de Python 3.10 no la lee)
        pcm = x.tobytes()
        fmt = struct.pack("<HHIIHHHHIH14s", 0xFFFE, 1, 16000, 32000, 2, 16, 22, 16, 4, 1, b"\x00\x00\x00\x00\x10\x00\x80\x00\x00\xaa\x00\x38\x9b\x71")
        cuerpo = b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt + b"data" + struct.pack("<I", len(pcm)) + pcm
        y2, _ = F.read_wav(b"RIFF" + struct.pack("<I", len(cuerpo)) + cuerpo)
        self.assertTrue(np.allclose(y2, x / 32768.0))
        X = F.clip_features(np.zeros(160000, np.float32))
        self.assertEqual(X.shape, (307, 320))
        with self.assertRaises(ValueError):
            F.logmel(np.zeros(1000), 44100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
