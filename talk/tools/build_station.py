"""
Builds talk/estacion.html: the station, live. A single page (it works offline) that replays a real
run of the PoC on AWS, event by event, so the audience sees the whole flow instead of a terminal:

  · the five pumps deciding (score against the threshold, the version each one runs, ALERT),
    the local queue while a pump has no network, and the faults a bad version does not hear;
  · the cloud: the events arriving (late ones too), the metric per minute, the alarm, the Lambda
    and the deployments (the safety net), and the judge (Step Functions) when the run has one;
  · a timeline with the acts; a caption tells what is happening; a ticker shows the events as
    demo/watch.sh prints them.

Keys: space play/pause · → next act · ← previous act · 1 2 3 4 speed · F full screen · Home.

Data: the formatted raw events of a rehearsal (evidencia-e2e/<date>/raw-tail.txt: the output of
`aws logs tail /station/events`, out of the repo), plus the alarm and Lambda times read from the
same folder (alarm-history.txt, lambda.txt). Nothing from the account goes in the page: devices,
versions, scores and times only.

Usage (from the repo root):
    python3 talk/tools/build_station.py [evidencia-e2e/2026-10-18]
"""
import base64, datetime, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TALK = os.path.dirname(HERE)
REPO = os.path.dirname(TALK)
EV = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "evidencia-e2e", "2026-10-18")
OUT = os.path.join(TALK, "estacion.html")
TZ = datetime.timezone(datetime.timedelta(hours=-5))          # Bogotá

os.environ["ISO_THEME"] = "tdc"
sys.path.insert(0, HERE)
from iso import Iso, NAVY, SLATE, BLUE, S300, S400, WHITE, mix   # noqa: E402
from build_iso import _pump                                          # noqa: E402

NAVY, GREEN, YELLOW, ORANGE, TEAL = "#0B132A", "#12D18E", "#FFC700", "#FF5A1F", "#1F8F7A"
SLATE, MIST, PALE, LIGHT = "#5C6B85", "#AAB6CB", "#EAF0F8", "#F6F8FB"


def local(ms):
    return datetime.datetime.fromtimestamp(ms / 1000, TZ)


def data_uri(path):
    mime = {".woff2": "font/woff2", ".png": "image/png", ".jpg": "image/jpeg"}[os.path.splitext(path)[1]]
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()


# ── the events ────────────────────────────────────────────────────────
def events():
    out = []
    for line in open(os.path.join(EV, "raw-tail.txt"), encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line.split(" ", 1)[1])
        except (ValueError, IndexError):
            continue
        if "device" not in e or "score" not in e:
            continue
        out.append(e)
    out.sort(key=lambda e: e["ts"])
    return out


def compact(ev):
    """What the page needs, short keys: d device · v version · t decided · a arrived · s score · h threshold
    · al alert · z input · ms latency · f the pump sounded faulty (truth, demo only) · dom domain
    · sv/sa/sm shadow version, alert, missed (when a candidate runs in shadow)."""
    devs = sorted({e["device"] for e in ev})
    rows = []
    for e in ev:
        r = {"d": devs.index(e["device"]), "v": e["model_version"], "t": e["ts"], "a": e["arrived_ts"],
             "s": round(e["score"], 3), "h": round(e["threshold"], 3), "al": int(bool(e["alert"])),
             "z": round(e.get("input_z") or 0, 2), "ms": round(e.get("latency_ms") or 0),
             "f": int(e.get("truth") == "anomaly"), "dom": 0 if e.get("domain", "source") == "source" else 1}
        if "shadow_version" in e:
            r.update({"sv": e["shadow_version"], "sa": int(bool(e.get("shadow_alert"))),
                      "sm": int(bool(e.get("shadow_missed")))})
        rows.append(r)
    return devs, rows


def cloud_facts():
    """The alarm's ALARM time and the Lambda's rollback, from the evidence folder (local ms). None if absent."""
    alarm = lam = None
    try:
        for line in open(os.path.join(EV, "alarm-history.txt"), encoding="utf-8"):
            m = re.match(r"(\S+)\s+Alarm updated from \w+ to ALARM", line)
            if m:
                t = datetime.datetime.fromisoformat(m.group(1))
                alarm = int(t.timestamp() * 1000)          # the newest comes first
                break
    except OSError:
        pass
    try:
        txt = open(os.path.join(EV, "lambda.txt"), encoding="utf-8").read()
        m = re.search(r'"rolled_back_to": "([\d.]+)".*?"t_ms": (\d+)', txt)
        if m:
            lam = {"to": m.group(1), "t": int(m.group(2))}
    except OSError:
        pass
    deploys = []
    try:
        group = ""
        for line in open(os.path.join(EV, "deployments.txt"), encoding="utf-8"):
            if line.startswith("# "):
                group = line[2:].strip()
            m = re.match(r"\|\s+(\S+)\s+\|\s+\w+\s+\|\s+(\S+)\s+\|", line)
            if m:
                t = datetime.datetime.fromisoformat(m.group(2))
                deploys.append({"name": m.group(1), "t": int(t.timestamp() * 1000), "g": group})
    except OSError:
        pass
    return alarm, lam, deploys


def judge_steps():
    """The judge's executions (Step Functions station-judge), if the folder has them: judge.json =
    [{name, status, input, start, stop, steps: [{state, t, type, output?, error?, cause?}]}] (t = ms)."""
    p = os.path.join(EV, "judge.json")
    if not os.path.exists(p):
        return []
    out = []
    for x in json.load(open(p, encoding="utf-8")):
        enter = {}
        for st in x["steps"]:
            if st["type"] == "enter" and st["state"] not in enter:
                enter[st["state"]] = st["t"]
        verdict = next((st.get("output") for st in x["steps"] if st["state"] == "Verdict" and st["type"] == "exit"), None)
        end = next((st for st in x["steps"] if st["type"] == "end"), None)
        out.append({"name": x["name"], "status": x["status"], "input": x.get("input", {}), "start": x["start"],
                    "stop": x.get("stop"), "enter": enter, "verdict": verdict,
                    "cause": (end or {}).get("cause")})
    return out


# the console, one capture per act: evidencia-e2e/<date>/console/<name>.png → the page, as JPEG
CONSOLE = {
    "gg-equipos":     "IoT Greengrass › Core devices: las cinco bombas, Healthy",
    "cw-dashboard":   "CloudWatch › Dashboards › station: lo que decide el modelo, por señal",
    "cw-logs":        "CloudWatch › Logs Insights: los eventos que llegaron tarde, con su hora de decisión y de llegada",
    "sfn-sombra":     "Step Functions › station-judge: la ejecución en marcha, horneando con la v2 en sombra",
    "sfn-veredicto":  "Step Functions › station-judge: el veredicto, la v2 rechazada y el aviso por SNS",
    "gg-despliegues": "IoT Greengrass › Deployments: sombra, rechazo, la v2 al ring 0 y la vuelta de la Lambda",
    "cw-alarma":      "CloudWatch › Alarms › station-missed-faults: las fallas no oídas cruzan el umbral",
    "lambda-logs":    "CloudWatch › Logs › station-rollback: la Lambda despliega la última versión buena",
    "gg-componente":  "IoT Greengrass › Components › com.station.Listener: las versiones 1.0.0, 1.1.0 (sombra) y 2.0.0",
    "s3-versiones":   "S3 › station/: una carpeta por versión, y clips/ con los clips que valen la pena",
}
SHOT_BY_ACT = {"inicio": "gg-equipos", "acto1": "cw-dashboard", "acto2": "cw-logs", "vuelve": "cw-logs",
               "deriva": "cw-dashboard", "sombra": "sfn-sombra", "veredicto": "sfn-veredicto", "acto3": "gg-despliegues",
               "noye": "cw-alarma", "alarma": "lambda-logs", "fin": "gg-despliegues"}


def console_shots():
    """{name: {uri, cap}} for the captures that exist (JPEG, at most 1400 px wide, when Pillow is there)."""
    d = os.path.join(EV, "console")
    out = {}
    for name, cap in CONSOLE.items():
        path = next((os.path.join(d, name + ext) for ext in (".png", ".jpg") if os.path.exists(os.path.join(d, name + ext))), None)
        if not path:
            continue
        try:
            from PIL import Image
            import io
            im = Image.open(path).convert("RGB")
            if im.width > 1400:
                im = im.resize((1400, round(im.height * 1400 / im.width)), Image.LANCZOS)
            buf = io.BytesIO(); im.save(buf, "JPEG", quality=82, optimize=True)
            uri = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
        except ImportError:
            uri = data_uri(path)
        out[name] = {"uri": uri, "cap": cap}
    return out


# ── the acts: derived from the events, so another run gets its own markers ──
def markers(ev, alarm, lam, judge=()):
    devs = sorted({e["device"] for e in ev})
    t0, t1 = ev[0]["ts"], max(e["arrived_ts"] for e in ev)

    def first(pred):
        return next((e for e in ev if pred(e)), None)

    M = [{"t": t0, "k": "inicio", "tag": "INICIO", "title": "Las cinco bombas reportan",
          "text": "Cada bomba decide un clip cada 3 segundos con la v1.0.0 y manda una línea de unos cientos "
                  "de bytes: versión, huella, score, umbral y decisión. El audio nunca sale de la estación.",
          "speed": 8}]
    a1 = first(lambda e: e["alert"] and e.get("truth") == "anomaly")
    if a1:
        M.append({"t": a1["ts"] - 9000, "k": "acto1", "tag": "ACTO 1 · ESCUCHAR", "title": f"La {a1['device']} empieza a sonar distinto",
                  "text": f"fault.sh {a1['device']}: la bomba suena como una bomba con falla. En el clip siguiente el score "
                          "pasa el umbral y la decisión es ALERT. Nadie oyó el audio: salió la decisión.", "speed": 1})
    late = [e for e in ev if e["arrived_ts"] - e["ts"] > 10000]
    if late:
        dev = late[0]["device"]
        off = late[0]["ts"]
        back = min(e["arrived_ts"] for e in late)
        M.append({"t": off - 4000, "k": "acto2", "tag": "ACTO 2 · SIN RED", "title": f"La {dev} se queda sin red",
                  "text": f"network.sh off {dev}: la bomba sigue decidiendo, pero sus eventos esperan en la cola local "
                          "del nucleus. Las otras cuatro siguen llegando. En la nube, la bomba se calla.", "speed": 2})
        M.append({"t": back - 3000, "k": "vuelve", "tag": "ACTO 2 · VUELVE LA RED", "title": "Llegan todos, tarde",
                  "text": f"Vuelve la red y los {len(late)} eventos guardados llegan juntos, hasta "
                          f"{max((e['arrived_ts'] - e['ts']) / 1000 for e in late):.0f} s tarde, con su hora de decisión. "
                          "Ninguno se perdió: QoS 1.", "speed": 1})
    d = first(lambda e: e.get("domain", "source") != "source")
    if d:
        dd = [e for e in ev if e["device"] == d["device"] and e.get("domain") != "source"]
        base = [e for e in ev if e["device"] == d["device"] and e.get("domain") == "source" and e["ts"] < d["ts"]]
        z0 = sum(e["input_z"] for e in base[-20:]) / max(1, len(base[-20:]))
        z1 = max(e["input_z"] for e in dd)
        M.append({"t": d["ts"] - 5000, "k": "deriva", "tag": "ACTO 2 · DERIVA", "title": f"La {d['device']} cambia de régimen",
                  "text": f"domain.sh {d['device']}: otra velocidad, otro sonido. No hay un solo error en el panel, pero la entrada "
                          f"salta de {z0:.1f} a {z1:.1f} desviaciones de lo que el modelo aprendió. Eso es deriva, y la "
                          "primera señal que hay que vigilar.", "speed": 2})
    v2 = first(lambda e: e["model_version"] != ev[0]["model_version"] and "shadow_version" not in e)
    sh = first(lambda e: "shadow_version" in e)
    if sh:
        bake = next((x["input"].get("bakeSeconds") for x in judge if x.get("input")), 120)
        M.append({"t": sh["ts"] - 5000, "k": "sombra", "tag": "ACTO 3 · EL JUEZ", "title": f"La v{sh['shadow_version']} escucha en sombra",
                  "text": f"judge.sh {sh['shadow_version']}: Step Functions despliega al canary la versión nueva en sombra. Decide la "
                          f"v{sh['model_version']}; la nueva solo dice qué habría hecho. El juez hornea {bake} s y mide en Logs Insights.", "speed": 2})
    for x in judge:
        if not x.get("stop"):
            continue
        v, inp = x.get("verdict") or {}, x.get("input", {})
        clips, missed = int(v.get("clips", 0)), int(v.get("missed", 0))
        if x["status"] == "SUCCEEDED":
            title, text = f"El juez promueve la v{inp.get('candidate')}", \
                f"Sobre {clips} clips la v{inp.get('candidate')} oyó lo mismo que la v{inp.get('active')}: pasa al ring 0, al ring 1 y queda como la última versión buena."
        else:
            title = f"El juez rechaza la v{inp.get('candidate')}"
            text = (f"Sobre {clips} clips, la v{inp.get('candidate')} no oyó {missed} fallas que la v{inp.get('active')} sí oyó. "
                    f"El canary vuelve a la v{inp.get('active')} sola y llega el aviso por SNS. La v{inp.get('candidate')} nunca decidió.")
        M.append({"t": x["stop"] - 15000, "k": "veredicto", "tag": "ACTO 3 · EL VEREDICTO", "title": title, "text": text, "speed": 2})
    if v2:
        M.append({"t": v2["ts"] - 12000, "k": "acto3", "tag": "ACTO 3 · LA RED DE SEGURIDAD", "title": f"La v{v2['model_version']} llega al canary",
                  "text": f"deploy.sh {v2['model_version']} ring-0: la versión nueva llega solo a la {v2['device']}. Instala, arranca y "
                          "reporta: para Greengrass, un despliegue exitoso. El ring 1 sigue con la v1.", "speed": 4})
    mf = [e for e in ev if e.get("truth") == "anomaly" and not e["alert"] and (v2 is None or e["ts"] >= v2["ts"])]
    if mf:
        M.append({"t": mf[0]["ts"] - 6000, "k": "noye", "tag": "ACTO 3 · FALLAS NO OÍDAS", "title": f"La {mf[0]['device']} falla y la v{mf[0]['model_version']} dice «normal»",
                  "text": f"fault.sh {mf[0]['device']}: la bomba falla y la versión nueva no lo oye. Cada evento lleva la verdad del clip "
                          "(solo en la demo), y la nube cuenta por minuto las fallas que nadie oyó.", "speed": 2})
    if alarm:
        M.append({"t": alarm - 8000, "k": "alarma", "tag": "ACTO 3 · LA VUELTA", "title": "La alarma, la Lambda y la última buena",
                  "text": "La métrica cruza el umbral: la alarma pasa a ALARM e invoca la Lambda, que despliega al ring 0 la "
                          "última versión buena. La bomba vuelve a la v1 y vuelve a alertar. Nadie tocó el equipo.", "speed": 1})
    M.append({"t": t1 - 20000, "k": "fin", "tag": "FIN", "title": "La estación, como la encontramos",
              "text": "Las cinco bombas con la v1.0.0, el despliegue de la vuelta activo y el de la v2 inactivo. "
                      "El ring 1 nunca recibió la v2.", "speed": 8})
    for m in M:
        m["shot"] = SHOT_BY_ACT.get(m["k"])
    M.sort(key=lambda m: m["t"])
    return M


# ── the pump, isometric, as a small SVG symbol ──────────────────────
def pump_symbol():
    g = Iso(80, 28, 30)
    g.add('<symbol id="pump" viewBox="0 0 160 100">')
    _pump(g, 0, 0, 1.0, body=SLATE, casing=BLUE)
    g.add("</symbol>")
    return g.svg()


# ── the page ─────────────────────────────────────────────────────────
def fonts_css():
    d = os.path.join(TALK, "assets", "fonts", "montserrat")
    return "".join(f"@font-face{{font-family:Montserrat;font-weight:{w};font-style:normal;font-display:block;"
                   f"src:url({data_uri(os.path.join(d, f'Montserrat-{n}.woff2'))}) format('woff2')}}\n"
                   for w, n in ((400, "Regular"), (500, "Medium"), (600, "SemiBold"), (700, "Bold"), (800, "ExtraBold")))


CSS = """
*{margin:0;padding:0;box-sizing:border-box}
:root{--navy:#0B132A;--green:#12D18E;--yellow:#FFC700;--orange:#FF5A1F;--teal:#1F8F7A;--slate:#5C6B85;--mist:#AAB6CB;
  --pale:#EAF0F8;--light:#F6F8FB;--line:#D5DEEA;--red:#E03A2F;--mono:"Courier New",ui-monospace,Menlo,monospace}
html,body{height:100%;overflow:hidden;background:var(--navy);font-family:Montserrat,Helvetica,Arial,sans-serif;color:var(--navy)}
#stage{position:absolute;left:50%;top:50%;width:1600px;height:900px;transform-origin:center;background:var(--light);overflow:hidden}
.bg{position:absolute;inset:0;background-size:cover;background-position:center}
h1{position:absolute;left:40px;top:22px;font-size:26px;font-weight:800;letter-spacing:-.01em}
h1 b{color:var(--orange);font-weight:800}
.sub{position:absolute;left:40px;top:56px;font-size:13px;color:var(--slate);font-weight:500}
#clock{position:absolute;left:50%;top:14px;transform:translateX(-50%);font-family:var(--mono);font-size:44px;font-weight:700;letter-spacing:.02em}
#ctl{position:absolute;right:40px;top:22px;display:flex;gap:8px;align-items:center}
#ctl button{height:38px;padding:0 14px;border:1.5px solid var(--line);border-radius:9px;background:#fff;font:600 14px Montserrat;color:var(--navy);cursor:pointer}
#ctl button.on{background:var(--navy);color:#fff;border-color:var(--navy)}
#ctl button.play{width:46px;font-size:18px}
#ctl .k{font-size:11px;color:var(--mist);margin-left:4px}
.panel{position:absolute;background:#fff;border:1.5px solid var(--line);border-radius:14px}
.panel .ph{position:absolute;left:20px;top:14px;font-size:12px;font-weight:700;letter-spacing:.14em;color:var(--slate)}
.panel .ph b{color:var(--orange)}
#station{left:40px;top:92px;width:700px;height:560px}
#cloud{left:860px;top:92px;width:700px;height:560px}
.ring{position:absolute;left:20px;width:660px;border:1.5px dashed var(--line);border-radius:12px}
.ring .rl{position:absolute;left:14px;top:-9px;padding:0 8px;background:#fff;font-size:11px;font-weight:700;letter-spacing:.1em;color:var(--slate)}
.ring.r0{top:48px;height:150px}.ring.r0 .rl{color:var(--orange)}
.ring.r1{top:214px;height:326px}
.pump{position:absolute;width:300px;height:122px;border:1.5px solid var(--line);border-radius:12px;background:#fff;transition:border-color .3s,box-shadow .3s}
.pump.alert{border-color:var(--orange);box-shadow:0 0 0 3px rgba(255,90,31,.15)}
.pump.miss{border-color:var(--red);box-shadow:0 0 0 3px rgba(224,58,47,.15)}
.pump.off{border-style:dashed;border-color:var(--mist)}
.pump svg.ic{position:absolute;left:8px;top:14px;width:120px;height:75px}
.pump .nm{position:absolute;left:134px;top:12px;font-size:17px;font-weight:800}
.pump .ver{position:absolute;left:134px;top:38px;font-family:var(--mono);font-size:12px;font-weight:700;padding:2px 7px;border-radius:6px;border:1.5px solid var(--navy)}
.pump .ver.v2{border-color:var(--orange);color:var(--orange)}
.pump .ver.sh{border-color:var(--teal);color:var(--teal);left:auto;right:14px;top:36px;font-size:9.5px;padding:1px 5px;white-space:nowrap}
.pump .dec{position:absolute;right:14px;top:12px;font-size:13px;font-weight:800;letter-spacing:.08em;color:var(--teal)}
.pump.alert .dec{color:var(--orange)}
.pump.miss .dec{color:var(--red)}
.pump .bar{position:absolute;left:134px;top:72px;width:150px;height:9px;background:var(--pale);border-radius:5px;overflow:hidden}
.pump .bar i{position:absolute;left:0;top:0;bottom:0;width:0;background:var(--teal);border-radius:5px;transition:width .25s}
.pump.alert .bar i{background:var(--orange)}
.pump .thr{position:absolute;top:69px;width:2px;height:15px;background:var(--navy)}
.pump .sc{position:absolute;left:134px;top:86px;font-family:var(--mono);font-size:11px;color:var(--slate);white-space:nowrap}
.pump .z{position:absolute;left:134px;top:102px;font-size:11px;color:var(--slate)}
.pump .z b{color:var(--navy)}
.pump .z.hot b{color:var(--orange)}
.pump .q{position:absolute;right:14px;top:36px;font-size:11px;font-weight:700;color:var(--mist);text-align:right;line-height:1.3}
.pump .q i{display:inline-block;width:6px;height:6px;border-radius:2px;background:var(--mist);margin-left:2px}
.pump .q b{color:var(--orange)}
.pump .tag{position:absolute;left:8px;bottom:8px;font-size:10px;font-weight:700;letter-spacing:.08em;color:var(--mist)}
.pump .tag.f{color:var(--orange)}.pump .tag.d{color:var(--yellow);filter:brightness(.85)}
/* the link */
#link{position:absolute;left:740px;top:92px;width:120px;height:560px;pointer-events:none}
#link svg{width:100%;height:100%;overflow:visible}
/* the cloud */
.row{position:absolute;left:20px;width:660px}
.svc{position:absolute;top:0;width:140px;text-align:center;font-size:12px;font-weight:700}
.svc small{display:block;font-weight:500;color:var(--slate);font-size:11px;margin-top:2px}
.svc .box{width:46px;height:46px;margin:0 auto 6px;border-radius:10px;background:var(--pale);display:flex;align-items:center;justify-content:center;font-size:20px}
.kpi{position:absolute;top:0;width:150px;height:72px;border:1.5px solid var(--line);border-radius:10px;padding:10px 14px}
.kpi .n{font-size:30px;font-weight:800;line-height:1}
.kpi .l{font-size:11px;color:var(--slate);font-weight:600;margin-top:4px}
.kpi.o .n{color:var(--orange)}.kpi.r .n{color:var(--red)}.kpi.y .n{color:#C99600}
#chart{position:absolute;left:20px;top:200px;width:660px;height:150px}
#chart svg{width:100%;height:100%;overflow:visible}
.ct{position:absolute;left:0;top:-4px;font-size:11px;font-weight:700;letter-spacing:.1em;color:var(--slate)}
.gate{position:absolute;left:20px;top:372px;width:660px;height:168px;border:1.5px dashed var(--line);border-radius:12px}
.gate .rl{position:absolute;left:14px;top:-9px;padding:0 8px;background:#fff;font-size:11px;font-weight:700;letter-spacing:.1em;color:var(--slate)}
.gate .gl{position:absolute;left:12px;font-size:9.5px;font-weight:700;letter-spacing:.1em;color:var(--mist)}
.gate .gl b{color:var(--slate)}
.st{position:absolute;height:52px;border:1.5px solid var(--line);border-radius:9px;padding:6px 9px;font-size:11px;background:#fff}
.st .t{font-weight:800;font-size:11.5px;white-space:nowrap}
.st .s{margin-top:3px;font-family:var(--mono);font-size:9.5px;color:var(--slate);line-height:1.25;white-space:nowrap;overflow:hidden}
.st.on{border-color:var(--orange);background:#FFF3EE}
.st.on .s{color:var(--orange);font-weight:700}
.st.ok{border-color:var(--green);background:#EEFCF6}
.st.ok .s{color:var(--teal);font-weight:700}
.st.bad{border-color:var(--red);background:#FDEEED}
.st.bad .s{color:var(--red);font-weight:700}
.st.dim{opacity:.45}
.arr{position:absolute;width:14px;height:2px;background:var(--line)}
.arr::after{content:"";position:absolute;right:-1px;top:-4px;border-left:7px solid var(--line);border-top:5px solid transparent;border-bottom:5px solid transparent}
.arr.on{background:var(--orange)}.arr.on::after{border-left-color:var(--orange)}
.arr.ok{background:var(--green)}.arr.ok::after{border-left-color:var(--green)}
.j .st{top:30px;width:116px}.j .arr{top:55px}
.n .st{top:106px;width:150px}.n .arr{top:131px}
/* the console, as the act looks in AWS */
#aw{position:absolute;right:16px;top:16px;width:212px;height:118px;border-radius:9px;overflow:hidden;border:1.5px solid var(--line);cursor:pointer;background:var(--pale);display:none}
#aw img{width:100%;height:100%;object-fit:cover;object-position:top left}
#aw .l{position:absolute;left:0;right:0;bottom:0;padding:4px 8px;background:rgba(11,19,42,.78);color:#fff;font-size:9.5px;font-weight:700;letter-spacing:.08em}
#aw .l b{color:var(--yellow)}
#ov{position:absolute;inset:0;background:rgba(11,19,42,.93);display:none;z-index:9;cursor:pointer}
#ov img{position:absolute;left:50%;top:40px;transform:translateX(-50%);max-width:1480px;max-height:760px;border-radius:8px;box-shadow:0 20px 60px rgba(0,0,0,.5)}
#ov .c{position:absolute;left:0;right:0;bottom:36px;text-align:center;color:#fff;font-size:18px;font-weight:600}
#ov .c b{color:var(--yellow);font-weight:800;letter-spacing:.1em;font-size:12px;display:block;margin-bottom:8px}
/* the bottom */
#tl{position:absolute;left:40px;top:668px;width:1520px;height:40px}
#tl .bar{position:absolute;left:0;right:0;top:18px;height:4px;background:var(--line);border-radius:2px}
#tl .done{position:absolute;left:0;top:18px;height:4px;background:var(--orange);border-radius:2px;width:0}
#tl .mk{position:absolute;top:9px;width:22px;height:22px;margin-left:-11px;border-radius:50%;background:#fff;border:2.5px solid var(--mist);cursor:pointer;z-index:2}
#tl .mk.done{background:var(--orange);border-color:var(--orange)}
#tl .mk.cur{border-color:var(--orange);box-shadow:0 0 0 4px rgba(255,90,31,.2)}
#tl .ml{position:absolute;top:-10px;font-size:10px;font-weight:700;letter-spacing:.06em;color:var(--slate);transform:translateX(-50%);white-space:nowrap}
#tl .ml.lo{top:34px}
#cap{position:absolute;left:40px;top:724px;width:900px;height:150px;background:#fff;border:1.5px solid var(--line);border-radius:14px;padding:18px 24px}
#cap .tag{font-size:12px;font-weight:700;letter-spacing:.14em;color:var(--orange)}
#cap .tt{font-size:24px;font-weight:800;margin-top:6px;letter-spacing:-.01em}
#cap .tx{font-size:15px;line-height:1.45;color:var(--slate);margin-top:8px;font-weight:500}
#cap .tt,#cap .tx{max-width:610px}
#cap .sw{position:absolute;right:248px;top:18px;font-family:var(--mono);font-size:13px;font-weight:700;color:var(--orange);display:none}
#tick{position:absolute;left:960px;top:724px;width:600px;height:150px;background:var(--navy);border-radius:14px;padding:14px 18px;overflow:hidden;color:#fff;font-family:var(--mono);font-size:12.5px;line-height:1.55}
#tick .h{color:var(--mist);font-family:Montserrat;font-size:11px;font-weight:700;letter-spacing:.14em;margin-bottom:4px}
#tick .l{white-space:nowrap}
#tick .al{color:var(--orange);font-weight:700}
#tick .ok{color:var(--green)}
#tick .lt{color:var(--yellow)}
#tick .mf{color:#FF7A6B;font-weight:700}
#tick .sh{color:#7FE3D0}
#tick .dim{color:var(--mist)}
#help{position:absolute;right:40px;bottom:6px;font-size:11px;color:var(--mist)}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
"""


def page(devs, rows, M, alarm, lam, deploys, judge, day, shots):
    data = json.dumps({"devs": devs, "ev": rows, "M": M, "alarm": alarm, "lam": lam, "deploys": deploys,
                       "judge": judge, "day": day, "shots": shots}, ensure_ascii=False, separators=(",", ":"))
    tdc = os.path.join(TALK, "assets", "cali", "tdc")
    logo = data_uri(os.path.join(tdc, "logo-navy.png"))
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>La estación · MLOps a ciegas</title>
<style>{fonts_css()}{CSS}</style></head>
<body>
<svg width="0" height="0" style="position:absolute">{pump_symbol()}</svg>
<div id="stage">
  <h1>La estación, <b>en vivo</b></h1>
  <div class="sub">Ensayo real en AWS us-east-1 · {day} · cinco bombas con el agente de Greengrass en una EC2 · reproducción de los eventos tal como llegaron</div>
  <div id="clock">00:00:00</div>
  <div id="ctl">
    <button class="play" id="play" title="espacio">▶</button>
    <button data-sp="1">1×</button><button data-sp="2">2×</button><button data-sp="4" class="on">4×</button><button data-sp="8">8×</button>
    <span class="k">← → actos</span>
  </div>
  <div class="panel" id="station"><div class="ph">ESTACIÓN · <b>EC2 con Greengrass</b> · una bomba, un contenedor</div>
    <div class="ring r0"><div class="rl">RING 0 · EL CANARY · StationRing0</div></div>
    <div class="ring r1"><div class="rl">RING 1 · EL RESTO DE LA FLOTA · StationRing1</div></div>
  </div>
  <div id="link"><svg viewBox="0 0 120 560"><path id="bus" d="M0,320 C60,320 60,320 120,320" fill="none" stroke="#D5DEEA" stroke-width="2"/><g id="pk"></g></svg></div>
  <div class="panel" id="cloud"><div class="ph">AWS · <b>us-east-1</b> · IoT Core → regla → CloudWatch</div>
    <div class="row" style="top:48px">
      <div class="kpi" style="left:0"><div class="n" id="k-ev">0</div><div class="l">eventos recibidos</div></div>
      <div class="kpi o" style="left:170px"><div class="n" id="k-al">0</div><div class="l">alertas</div></div>
      <div class="kpi y" style="left:340px"><div class="n" id="k-late">0</div><div class="l">llegaron tarde</div></div>
      <div class="kpi r" style="left:510px"><div class="n" id="k-mf">0</div><div class="l">fallas no oídas</div></div>
    </div>
    <div id="chart"><div class="ct">FALLAS NO OÍDAS POR MINUTO · <span id="ct-thr"></span></div><svg viewBox="0 0 660 150"></svg></div>
    <div class="gate"><div class="rl">EL GATE · ¿CUÁNDO VOLVER ATRÁS?</div>
      <div class="gl" style="top:14px"><b>EL JUEZ</b> · Step Functions station-judge · decide antes de que la versión nueva decida</div>
      <div class="j">
        <div class="st" id="j0" style="left:0"><div class="t">Sombra</div><div class="s">DeployInShadow<br>—</div></div>
        <div class="arr" id="ja0" style="left:118px"></div>
        <div class="st" id="j1" style="left:136px"><div class="t">Hornear</div><div class="s">Bake<br>—</div></div>
        <div class="arr" id="ja1" style="left:254px"></div>
        <div class="st" id="j2" style="left:272px"><div class="t">Medir</div><div class="s">Logs Insights<br>—</div></div>
        <div class="arr" id="ja2" style="left:390px"></div>
        <div class="st" id="j3" style="left:408px"><div class="t">¿Pasa?</div><div class="s">Passes?<br>—</div></div>
        <div class="arr" id="ja3" style="left:526px"></div>
        <div class="st" id="j4" style="left:544px"><div class="t">Veredicto</div><div class="s">—<br>—</div></div>
      </div>
      <div class="gl" style="top:92px"><b>LA RED DE SEGURIDAD</b> · CloudWatch + Lambda · para lo que se le escape al juez</div>
      <div class="n">
        <div class="st" id="s-alarm" style="left:0"><div class="t">Alarma</div><div class="s">station-missed-faults<br>OK</div></div>
        <div class="arr" id="a1" style="left:152px"></div>
        <div class="st" id="s-lambda" style="left:170px"><div class="t">Lambda</div><div class="s">station-rollback<br>en espera</div></div>
        <div class="arr" id="a2" style="left:322px"></div>
        <div class="st" id="s-gg" style="left:340px"><div class="t">Greengrass</div><div class="s" id="s-dep">despliegues<br>—</div></div>
        <div class="st" id="s-ssm" style="left:510px"><div class="t">Parameter Store</div><div class="s">last_good_version<br><b id="s-lg">1.0.0</b></div></div>
      </div>
    </div>
  </div>
  <div id="tl"><div class="bar"></div><div class="done" id="tl-done"></div></div>
  <div id="cap"><div class="tag" id="c-tag"></div><div class="tt" id="c-tt"></div><div class="tx" id="c-tx"></div><div class="sw" id="c-sw"></div>
    <div id="aw" title="tecla A"><img alt=""><div class="l">ASÍ SE VE EN AWS · <b>tecla A</b></div></div></div>
  <div id="ov"><img alt=""><div class="c"><b>LA CONSOLA DE AWS · ESC CIERRA</b><span id="ov-c"></span></div></div>
  <div id="tick"><div class="h">LO QUE SALE DE LA ESTACIÓN · demo/watch.sh</div><div id="tk"></div></div>
  <div id="help">espacio · reproducir  ·  ← → · actos  ·  1 2 4 8 · velocidad  ·  A · la consola de AWS  ·  F · pantalla completa</div>
</div>
<script>
const D={data};
const $=s=>document.querySelector(s);
const EV=D.ev, DEVS=D.devs, M=D.M, N=EV.length;
const T0=M[0].t, T1=Math.max(...EV.map(e=>e.a))+5000;
const TZ=-5*3600*1000;
function hms(ms){{ const d=new Date(ms+TZ); return d.toISOString().slice(11,19); }}
function fit(){{ const s=Math.min(innerWidth/1600,innerHeight/900); $('#stage').style.transform=`translate(-50%,-50%) scale(${{s}})`; }}
addEventListener('resize',fit); fit();

/* the pumps */
const pumps=[];
const POS=[[180,16],[20,20],[340,20],[20,176],[340,176]];
DEVS.forEach((d,i)=>{{
  const el=document.createElement('div'); el.className='pump'; const ring=i===0?'.ring.r0':'.ring.r1';
  el.style.left=POS[i][0]+'px'; el.style.top=POS[i][1]+'px';
  el.innerHTML=`<svg class="ic"><use href="#pump"/></svg><div class="nm">${{d}}</div><div class="ver">v—</div><div class="dec">—</div>
    <div class="bar"><i></i></div><div class="thr"></div><div class="sc">score — · umbral —</div><div class="z">entrada <b>—</b></div><div class="q"></div><div class="tag"></div>`;
  $('#station '+ring).appendChild(el); pumps.push(el);
}});
const SMAX=.6;      /* the score bar's scale */

/* replay state */
let t=T0, playing=false, speed=4, last=null, cur=-1;
let iDec=0, iArr=0;                                    /* cursors over the events, by decision and by arrival */
const byArr=EV.map((e,i)=>i).sort((a,b)=>EV[a].a-EV[b].a);
let dec=DEVS.map(()=>null), q=DEVS.map(()=>0), arrived=0, alerts=0, late=0, missed=0, perMin={{}}, lines=[];
const THR=8; $('#ct-thr').textContent='umbral de la alarma: '+THR;

function reset(){{ iDec=0; iArr=0; dec=DEVS.map(()=>null); q=DEVS.map(()=>0); arrived=0; alerts=0; late=0; missed=0; perMin={{}}; lines=[]; $('#pk').innerHTML=''; }}
function step(to){{
  if(to<t) {{ reset(); t=T0; }}
  while(iDec<N && EV[iDec].t<=to){{ const e=EV[iDec++]; dec[e.d]=e; q[e.d]++; }}
  while(iArr<N && EV[byArr[iArr]].a<=to){{ const e=EV[byArr[iArr++]]; q[e.d]--; arrived++; if(e.al) alerts++;
    const lt=(e.a-e.t)/1000; if(lt>10) late++; if(e.f&&!e.al){{ missed++; const m=Math.floor(e.a/60000); perMin[m]=(perMin[m]||0)+1; }}
    lines.push(e); if(lines.length>7) lines.shift(); packet(e.d, e.al, e.f&&!e.al); }}
  t=to;
}}
function packet(d,al,mf){{
  if(playing && speed>4) return;
  const y=[88,106,106,262,262][d]+ (d===0?0:0) + 60;        /* roughly the card's middle */
  const c=document.createElementNS('http://www.w3.org/2000/svg','circle');
  c.setAttribute('r',mf?6:4.5); c.setAttribute('fill',mf?'#E03A2F':al?'#FF5A1F':'#1F8F7A'); c.setAttribute('cx',0); c.setAttribute('cy',y);
  $('#pk').appendChild(c); const t0=performance.now();
  (function an(){{ const u=(performance.now()-t0)/650; if(u>=1){{ c.remove(); return; }} c.setAttribute('cx',120*u); c.setAttribute('cy',y+(320-y)*u*u); requestAnimationFrame(an); }})();
}}
function paint(){{
  $('#clock').textContent=hms(t);
  DEVS.forEach((d,i)=>{{
    const el=pumps[i], e=dec[i]; if(!e) return;
    const v=el.querySelector('.ver'); v.textContent='v'+e.v; v.className='ver'+(e.v!==EV[0].v?' v2':'');
    if(e.sv){{ let s=el.querySelector('.ver.sh'); if(!s){{ s=document.createElement('div'); s.className='ver sh'; s.style.position='absolute'; el.appendChild(s); }} s.textContent='sombra: '+(e.sa?'ALERT':'normal'); }}
    else {{ const s=el.querySelector('.ver.sh'); if(s) s.remove(); }}
    const miss=e.f&&!e.al, off=q[i]>3;
    el.className='pump'+(e.al?' alert':'')+(miss?' miss':'')+(off?' off':'');
    el.querySelector('.dec').textContent=miss?'NO LA OYÓ':e.al?'ALERT':'normal';
    el.querySelector('.bar i').style.width=Math.min(100,e.s/SMAX*100)+'%';
    el.querySelector('.thr').style.left=(134+150*Math.min(1,e.h/SMAX))+'px';
    el.querySelector('.sc').textContent='score '+e.s.toFixed(2)+' · umbral '+e.h.toFixed(2);
    const z=el.querySelector('.z'); z.innerHTML='entrada <b>'+e.z.toFixed(1)+'</b> σ · '+e.ms+' ms'; z.className='z'+(e.z>1.5?' hot':'');
    const qq=el.querySelector('.q'); qq.innerHTML=off?'<b>sin red</b><br>'+q[i]+' en cola<br>'+'<i></i>'.repeat(Math.min(q[i],14)):'';
    const tg=el.querySelector('.tag'); tg.textContent=e.f?'SUENA CON FALLA':e.dom?'OTRO RÉGIMEN':''; tg.className='tag'+(e.f?' f':e.dom?' d':'');
  }});
  $('#k-ev').textContent=arrived; $('#k-al').textContent=alerts; $('#k-late').textContent=late; $('#k-mf').textContent=missed;
  chart();
  /* the judge */
  const jx=(D.judge||[]).filter(x=>x.start<=t).pop();
  const J=['j0','j1','j2','j3','j4'];
  if(!jx){{ J.forEach(id=>{{ $('#'+id).className='st dim'; }}); for(let i=0;i<4;i++) $('#ja'+i).className='arr'; $('#j4 .s').innerHTML='—<br>—'; }}
  else {{
    const en=jx.enter, at=k=>en[k]!==undefined&&en[k]<=t, v=jx.verdict||{{}}, inp=jx.input||{{}};
    const done=jx.stop&&t>=jx.stop, rej=jx.status!=='SUCCEEDED';
    const bakeOn=at('Bake')&&!(at('Measure')), bakeS=at('Bake')?Math.min(inp.bakeSeconds||120,Math.round(((at('Measure')?en.Measure:t)-en.Bake)/1000)):0;
    const set=(id,cls,s)=>{{ const e=$('#'+id); e.className='st '+cls; e.querySelector('.s').innerHTML=s; }};
    set('j0',at('DeployInShadow')?(at('Bake')?'ok':'on'):'dim','DeployInShadow<br>'+(at('DeployInShadow')?'v'+inp.candidate+' en sombra · ring 0':'—'));
    set('j1',at('Bake')?(bakeOn?'on':'ok'):'dim','Bake<br>'+(at('Bake')?bakeS+' s de '+(inp.bakeSeconds||120):'—'));
    set('j2',at('Measure')?(at('Verdict')?'ok':'on'):'dim','Logs Insights<br>'+(at('Verdict')?'clips '+(v.clips??'?')+' · no oídas '+(v.missed??'?'):at('Measure')?'consultando…':'—'));
    set('j3',at('Passes?')?(done?(rej?'bad':'ok'):'on'):'dim','Passes?<br>'+(at('Passes?')?('≥'+(inp.minClips||20)+' clips · ≤'+Math.round((inp.maxMissedRate||.1)*100)+'% no oídas'):'—'));
    set('j4',done?(rej?'bad':'ok'):'dim',(done?(rej?'RECHAZADA':'PROMOVIDA'):'—')+'<br>'+(done?(rej?'ring 0 → v'+inp.active+' · SNS':'ring 0, ring 1, última buena'):'—'));
    [['ja0','Bake'],['ja1','Measure'],['ja2','Passes?'],['ja3',null]].forEach(([id,k],i)=>{{ const o=k?at(k):done; $('#'+id).className='arr'+(o?(i===3&&rej?' on':' ok'):''); }});
  }}
  /* the safety net */
  const on=D.alarm&&t>=D.alarm, lam=D.lam&&t>=D.lam.t;
  const sa=$('#s-alarm'); sa.className='st'+(on?' on':''); sa.querySelector('.s').innerHTML='station-missed-faults<br>'+(on?'ALARM':'OK');
  $('#a1').className='arr'+(on?' on':'');
  const sl=$('#s-lambda'); sl.className='st'+(lam?' on':''); sl.querySelector('.s').innerHTML='station-rollback<br>'+(lam?'rollback → '+D.lam.to:'en espera');
  $('#a2').className='arr'+(lam?' on':'');
  const deps=D.deploys.filter(x=>x.t<=t&&x.t>=T0-600000&&(x.g?x.g==='StationRing0':/Ring0/.test(x.name))).sort((a,b)=>b.t-a.t).slice(0,2);
  const sg=$('#s-gg'); sg.className='st'+(lam?' on':deps.length?' ok':'');
  $('#s-dep').innerHTML='ring 0<br>'+(deps.length?deps.map((x,k)=>'<span style="'+(k?'color:#AAB6CB;font-weight:400':'')+'">'+x.name.replace(/-StationRing0/,'').replace(/-\\d{{10}}$/,'')+(k?' · inactivo':' · activo')+'</span>').join('<br>'):'—');
  /* ticker */
  $('#tk').innerHTML=lines.map(e=>{{ const lt=(e.a-e.t)/1000; return '<div class="l"><span class="dim">'+hms(e.a)+'</span>  '+DEVS[e.d]+'  v'+e.v+'  '+(e.al?'<span class="al">ALERT</span>':'<span class="ok">normal</span>')+'  score '+e.s.toFixed(2)+' ('+e.h.toFixed(2)+')  input '+e.z.toFixed(1)+(lt>10?'  <span class="lt">· llegó '+lt.toFixed(0)+' s tarde</span>':'')+(e.f&&!e.al?'  <span class="mf">· falla no oída</span>':'')+(e.sv?'  <span class="sh">· sombra v'+e.sv+' '+(e.sa?'ALERT':'normal')+(e.sm?' · no la oyó':'')+'</span>':'')+'</div>'; }}).join('');
  /* timeline and caption */
  $('#tl-done').style.width=pos(t)+'%';
  let k=0; while(k+1<M.length && M[k+1].t<=t) k++;
  document.querySelectorAll('#tl .mk').forEach((m,j)=>{{ m.className='mk'+(M[j].t<=t?' done':'')+(j===k?' cur':''); }});
  if(k!==cur){{ cur=k; $('#c-tag').textContent=M[k].tag; $('#c-tt').textContent=M[k].title; $('#c-tx').textContent=M[k].text;
    const sh=M[k].shot&&D.shots[M[k].shot]; $('#aw').style.display=sh?'block':'none'; if(sh){{ $('#aw img').src=sh.uri; }}
    if($('#ov').style.display==='block') showOv(); }}
  /* the stopwatch since the fault nobody heard */
  const mf0=M.find(m=>m.k==='noye'), sw=$('#c-sw');
  if(mf0 && t>=mf0.t+6000 && M[k].k!=='fin'){{ const back=D.lam?D.lam.t:null; const end=back&&t>back?back:t; sw.style.display='block'; sw.textContent='desde la falla: '+Math.max(0,Math.round((end-(mf0.t+6000))/1000))+' s'+(back&&t>back?' · vuelta':''); }} else sw.style.display='none';
}}
function chart(){{
  const svg=$('#chart svg'); const m0=Math.floor(T0/60000), m1=Math.floor(T1/60000), n=m1-m0+1, w=660/n, H=120, mx=Math.max(12,...Object.values(perMin));
  let s=`<line x1="0" y1="${{H-THR/mx*H}}" x2="660" y2="${{H-THR/mx*H}}" stroke="#E03A2F" stroke-dasharray="5 4" stroke-width="1.5"/><text x="4" y="${{H-THR/mx*H-5}}" font-size="10" fill="#E03A2F" font-weight="700">umbral ${{THR}}/min</text>`;
  for(let m=m0;m<=m1;m++){{ const v=perMin[m]||0, x=(m-m0)*w, h=v/mx*H; const cur=m===Math.floor(t/60000);
    s+=`<rect x="${{x+2}}" y="${{H-h}}" width="${{Math.max(2,w-4)}}" height="${{h}}" fill="${{v>=THR?'#E03A2F':'#FF9C78'}}" rx="2"/>`;
    if(cur) s+=`<rect x="${{x+2}}" y="0" width="${{Math.max(2,w-4)}}" height="${{H}}" fill="rgba(11,19,42,.05)"/>`;
    if((m-m0)%3===0) s+=`<text x="${{x+w/2}}" y="${{H+16}}" font-size="10" fill="#5C6B85" text-anchor="middle">${{hms(m*60000).slice(0,5)}}</text>`; }}
  svg.innerHTML=s;
}}
/* markers: the bar compresses the waits between acts (a gap counts at most 2 minutes) */
const GAP=120000, KN=[...M.map(m=>m.t),T1];
const KX=[0]; for(let j=1;j<KN.length;j++) KX.push(KX[j-1]+Math.min(GAP,KN[j]-KN[j-1]));
function pos(tt){{ let j=0; while(j+1<KN.length && KN[j+1]<=tt) j++; const seg=Math.min(GAP,KN[j+1]-KN[j]); const u=Math.min(1,(tt-KN[j])/(KN[j+1]-KN[j])); return (KX[j]+u*seg)/KX[KX.length-1]*100; }}
M.forEach((m,j)=>{{ const d=document.createElement('div'); d.className='mk'; d.style.left=pos(m.t)+'%'; d.title=m.tag; d.onclick=()=>goto(j);
  const l=document.createElement('div'); l.className='ml'+(j%2?' lo':''); l.style.left=pos(m.t)+'%'; l.textContent=m.tag.replace(/^ACTO \\d · /,''); $('#tl').appendChild(d); $('#tl').appendChild(l); }});
function goto(j){{ j=Math.max(0,Math.min(M.length-1,j)); step(M[j].t); setSpeed(M[j].speed); paint(); if(!playing) toggle(true); }}
function setSpeed(s){{ speed=s; document.querySelectorAll('#ctl [data-sp]').forEach(b=>b.classList.toggle('on',+b.dataset.sp===s)); }}
function showOv(){{ const sh=M[cur]&&M[cur].shot&&D.shots[M[cur].shot]; if(!sh) return; $('#ov img').src=sh.uri; $('#ov-c').textContent=sh.cap; $('#ov').style.display='block'; }}
function hideOv(){{ $('#ov').style.display='none'; }}
$('#aw').onclick=showOv; $('#ov').onclick=hideOv;
function toggle(on){{ playing=on===undefined?!playing:on; $('#play').textContent=playing?'❚❚':'▶'; last=null; if(playing) requestAnimationFrame(tick); }}
function tick(now){{ if(!playing) return; if(last!==null){{ step(Math.min(T1,t+(now-last)*speed)); paint(); if(t>=T1) toggle(false); }} last=now; requestAnimationFrame(tick); }}
$('#play').onclick=()=>toggle();
document.querySelectorAll('#ctl [data-sp]').forEach(b=>b.onclick=()=>setSpeed(+b.dataset.sp));
addEventListener('keydown',e=>{{ const k=e.key;
  if(k===' '){{ e.preventDefault(); toggle(); }}
  else if(k==='ArrowRight'||k==='PageDown'){{ e.preventDefault(); goto(cur+1); }}
  else if(k==='ArrowLeft'||k==='PageUp'){{ e.preventDefault(); goto(cur-1); }}
  else if(k==='Home'){{ step(T0); paint(); }}
  else if('1248'.includes(k)&&k){{ setSpeed(+k); }}
  else if(k.toLowerCase()==='a'){{ e.preventDefault(); $('#ov').style.display==='block'?hideOv():showOv(); }}
  else if(k==='Escape'){{ hideOv(); }}
  else if(k.toLowerCase()==='f'){{ document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen(); }}
}});
window.__st={{seek:ms=>{{ step(ms); paint(); }}, goto, M, T0, T1, toggle}};
step(T0); paint();
</script>
</body></html>
"""


def main():
    ev = events()
    if not ev:
        sys.exit(f"no events in {EV}/raw-tail.txt")
    devs, rows = compact(ev)
    alarm, lam, deploys = cloud_facts()
    judge = judge_steps()
    M = markers(ev, alarm, lam, judge)
    day = local(ev[0]["ts"]).strftime("%-d de %B de %Y").replace("October", "octubre").replace("November", "noviembre")
    html = page(devs, rows, M, alarm, lam, deploys, judge, day, console_shots())
    open(OUT, "w", encoding="utf-8").write(html)
    print(f"✔ {OUT}  ({len(html.encode()) / 1024:.0f} KB · {len(rows)} events · {len(M)} markers: "
          + ", ".join(m["k"] for m in M) + ")")


if __name__ == "__main__":
    main()
