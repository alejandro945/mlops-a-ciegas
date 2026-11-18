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


def cert_icon():
    """The AWS IoT certificate icon (AWS_ICONS, the official set) as a data URI; empty if the set is not there."""
    p = os.path.join(os.environ.get("AWS_ICONS", os.path.expanduser("~/Downloads/aws-icon-set")),
                     "Resource-Icons_07312026", "Res_IoT", "Res_AWS-IoT_Certificate_48.svg")
    return data_uri(p) if os.path.exists(p) else ""


def sfn_icons():
    """The service icons the Step Functions graph shows on each Task state (the official set, 16 px)."""
    base = os.path.join(os.environ.get("AWS_ICONS", os.path.expanduser("~/Downloads/aws-icon-set")), "Architecture-Service-Icons_07312026")
    f = {"gg": "Arch_Internet-of-Things/16/Arch_AWS-IoT-Greengrass_16.svg", "cwl": "Arch_Management-Tools/16/Arch_Amazon-CloudWatch_16.svg",
         "sns": "Arch_Application-Integration/16/Arch_Amazon-Simple-Notification-Service_16.svg",
         "ssm": "Arch_Management-Tools/16/Arch_AWS-Systems-Manager_16.svg"}
    return {k: data_uri(os.path.join(base, v)) for k, v in f.items() if os.path.exists(os.path.join(base, v))}


def data_uri(path):
    mime = {".woff2": "font/woff2", ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml"}[os.path.splitext(path)[1]]
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
        enter, exit_ = {}, {}
        for st in x["steps"]:
            if st["type"] == "enter" and st["state"] not in enter:
                enter[st["state"]] = st["t"]
            elif st["type"] == "exit":
                exit_[st["state"]] = st["t"]
        verdict = next((st.get("output") for st in x["steps"] if st["state"] == "Verdict" and st["type"] == "exit"), None)
        end = next((st for st in x["steps"] if st["type"] == "end"), None)
        out.append({"name": x["name"], "status": x["status"], "input": x.get("input", {}), "start": x["start"],
                    "stop": x.get("stop"), "enter": enter, "exit": exit_, "verdict": verdict,
                    "cause": (end or {}).get("cause")})
    return out


# the AWS console, redrawn from the run's data (station-console.js): one panel per act
CON_BY_ACT = {"inicio": "mqtt", "acto1": "insights", "acto2": "insights", "vuelve": "insights", "deriva": "metric",
              "sombra": "sfn", "veredicto": "sfn", "acto3": "deploys", "noye": "salida", "alarma": "lambda", "fin": "deploys"}


def alarm_history():
    """Every state change of the alarm in the folder: [{t, s}] (local ms)."""
    out = []
    try:
        for line in open(os.path.join(EV, "alarm-history.txt"), encoding="utf-8"):
            m = re.match(r"(\S+)\s+(Alarm updated from \S+ to \S+)", line)
            if m:
                out.append({"t": int(datetime.datetime.fromisoformat(m.group(1)).timestamp() * 1000), "s": m.group(2)})
    except OSError:
        pass
    return out


def s3_and_component(rows):
    """The artifacts bucket (s3-station.txt), the clips kept (s3-clips.txt) and the component's versions,
    with the threshold each version decided with (from the events)."""
    vers = {}
    try:
        for line in open(os.path.join(EV, "s3-station.txt"), encoding="utf-8"):
            m = re.match(r"(\S+ \S+)\s+(\d+)\s+station/([\d.]+)/(\S+)", line.strip())
            if m:
                t = int(datetime.datetime.fromisoformat(m.group(1)).replace(tzinfo=TZ).timestamp() * 1000)
                v = vers.setdefault(m.group(3), {"v": m.group(3), "files": [], "t": t})
                v["files"].append({"name": m.group(4), "size": int(m.group(2))})
                v["t"] = max(v["t"], t)
    except OSError:
        pass
    clips = {"n": 0, "reason": {}, "device": {}}
    try:
        for line in open(os.path.join(EV, "s3-clips.txt"), encoding="utf-8"):
            m = re.search(r"clips/device=([^/]+)/.*?/\d+_([a-z]+)_section", line)
            if m:
                clips["n"] += 1
                clips["reason"][m.group(2)] = clips["reason"].get(m.group(2), 0) + 1
                clips["device"][m.group(1)] = clips["device"].get(m.group(1), 0) + 1
    except OSError:
        pass
    thr = {}
    for r in rows:
        thr.setdefault(r["v"], r["h"])
    for v in vers.values():
        names = {f["name"] for f in v["files"]}
        v["shadow"] = "shadow.onnx" in names
        v["thr"] = thr.get(v["v"]) or thr.get("1.0.0")
    return {"versions": sorted(vers.values(), key=lambda x: x["v"]), "clips": clips, "thr": thr}


PROV_DUR = 64000                                    # the prologue, in replay ms before the first event
PROV_GROUPS = [("S3", ("aws_s3_",)), ("IAM", ("aws_iam_",)), ("IoT Core", ("aws_iot_",)), ("Parameter Store", ("aws_ssm_",)),
               ("CloudWatch", ("aws_cloudwatch_",)), ("Lambda", ("aws_lambda_",)), ("Step Functions · SNS", ("aws_sfn_", "aws_sns_")),
               ("EC2", ("aws_instance", "aws_security_group"))]


def provision(first_ts):
    """The prologue: what Terraform created (terraform-apply.txt, in the order it finished) and when the fleet,
    the publish and the deploy happened (provision.json). None if the folder has neither."""
    try:
        res = [m.group(1) for m in (re.match(r"(\S+?)(\[|:)", l) for l in open(os.path.join(EV, "terraform-apply.txt"), encoding="utf-8")
                                    if "Creation complete" in l) if m]
        pj = json.load(open(os.path.join(EV, "provision.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return None
    ms = lambda iso: int(datetime.datetime.fromisoformat(iso).timestamp() * 1000)
    groups = []
    for name, pre in PROV_GROUPS:
        idx = [i for i, r in enumerate(res) if r.startswith(pre)]
        if idx:                                          # each resource ticks in, in the order it finished, over 1-21 s
            groups.append({"name": name, "n": len(idx), "ats": [round(1 + 20 * i / max(1, len(res) - 1), 2) for i in idx]})
    return {"t0": first_ts - PROV_DUR, "dur": PROV_DUR, "groups": groups, "total": len(res),
            "applyEnd": ms(pj["apply_end"]), "fleet": ms(pj["fleet_start"]), "publish": [[v, ms(t)] for v, t in pj["publish"]],
            "deploy": ms(pj["deploy"]), "start": first_ts}


def lambda_lines(lam):
    """The Lambda's log, line by line, timed around the rollback (lam.t): REPORT gives the duration and the init."""
    if not lam:
        return []
    try:
        raw = [l.strip() for l in open(os.path.join(EV, "lambda.txt"), encoding="utf-8") if l.strip()]
    except OSError:
        return []
    txt = "\n".join(raw)
    dur = float((re.search(r"\bDuration: ([\d.]+) ms", txt) or [0, 800])[1])
    init = float((re.search(r"Init Duration: ([\d.]+) ms", txt) or [0, 500])[1])
    start = lam["t"] - round(dur)
    out = []
    for l in raw:
        l = re.sub(r":\d{12}:", "::", l).replace("\t", "  ")
        l = re.sub(r"\s+Runtime Version ARN: \S+", "", l)
        t = (start - round(init) if l.startswith("INIT_START") else start if l.startswith("START") else
             start + 1 if "alarm_state" in l else lam["t"])
        out.append({"t": t, "msg": l})
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
                  "text": f"Un despliegue de Greengrass al ring 0: la v{v2['model_version']} llega solo a la {v2['device']}. Instala, arranca y "
                          "reporta: para Greengrass, un despliegue exitoso. El ring 1 sigue con la v1.", "speed": 4})
    mf = [e for e in ev if e.get("truth") == "anomaly" and not e["alert"] and (v2 is None or e["ts"] >= v2["ts"])]
    if mf:
        M.append({"t": mf[0]["ts"] - 6000, "k": "noye", "tag": "ACTO 3 · LA SALIDA CAMBIA", "title": f"La {mf[0]['device']} falla y la v{mf[0]['model_version']} apenas la oye",
                  "text": f"fault.sh {mf[0]['device']}: la bomba falla y la versión nueva casi no alerta. Sin saber qué clip es una falla, "
                          "la nube ve que cambió lo que decide: sus scores se alejan de la referencia y el PSI se dispara.", "speed": 2})
    if alarm:
        M.append({"t": alarm - 8000, "k": "alarma", "tag": "ACTO 3 · LA VUELTA", "title": "La alarma, la Lambda y la última buena",
                  "text": "La alarma pasa a ALARM e invoca la Lambda, que despliega al ring 0 la "
                          "última versión buena. La bomba vuelve a la v1 y vuelve a alertar. Nadie tocó el equipo.", "speed": 1})
    M.append({"t": t1 - 20000, "k": "fin", "tag": "FIN", "title": "La estación, como la encontramos",
              "text": "Las cinco bombas con la v1.0.0, el despliegue de la vuelta activo y el de la v2 inactivo. "
                      "El ring 1 nunca recibió la v2.", "speed": 8})
    for m in M:
        m["con"] = CON_BY_ACT.get(m["k"])
        if m["k"] == "acto1" and a1:
            m["dev"] = a1["device"]
    M.sort(key=lambda m: m["t"])
    HOLD = {"inicio": 12000, "acto1": 15000, "acto2": 15000, "vuelve": 15000, "deriva": 15000, "sombra": 20000,
            "veredicto": 25000, "acto3": 21000, "noye": 20000, "fin": 8000}
    for m in M:
        m["hold"] = HOLD.get(m["k"], 15000)
        if m["k"] == "alarma" and lam:                   # the alarm, then the Lambda and the pump back on v1
            m["hold"] = max(15000, lam["t"] - m["t"] + 20000)
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
#ctl{position:absolute;right:40px;top:22px;display:none;gap:8px;align-items:center}   /* the clicks drive the replay: no buttons on the stage */
#ctl button{height:38px;padding:0 14px;border:1.5px solid var(--line);border-radius:9px;background:#fff;font:600 14px Montserrat;color:var(--navy);cursor:pointer}
#ctl button.on{background:var(--navy);color:#fff;border-color:var(--navy)}
#ctl button.play{width:46px;font-size:18px}
#ctl .k{font-size:11px;color:var(--mist);margin-left:4px}
.panel{position:absolute;background:#fff;border:1.5px solid var(--line);border-radius:14px}
.panel .ph{position:absolute;left:20px;top:14px;font-size:12px;font-weight:700;letter-spacing:.14em;color:var(--slate)}
.panel .ph b{color:var(--orange)}
#station{left:40px;top:92px;width:700px;height:560px}
#cloud{left:860px;top:92px;width:700px;height:560px;display:none}
#dock{left:860px;top:92px;width:700px;height:560px;overflow:hidden;background:#F8F8F8;cursor:zoom-in}
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
.pump .cert{position:absolute;left:8px;top:6px;width:26px;height:26px;z-index:2}
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
/* the bottom */
#tl{position:absolute;left:40px;top:668px;width:1520px;height:40px}
#tl .bar{position:absolute;left:0;right:0;top:18px;height:4px;background:var(--line);border-radius:2px}
#tl .done{position:absolute;left:0;top:18px;height:4px;background:var(--orange);border-radius:2px;width:0}
#tl .mk{position:absolute;top:9px;width:22px;height:22px;margin-left:-11px;border-radius:50%;background:#fff;border:2.5px solid var(--mist);cursor:pointer;z-index:2}
#tl .mk.done{background:var(--orange);border-color:var(--orange)}
#tl .mk.cur{border-color:var(--orange);box-shadow:0 0 0 4px rgba(255,90,31,.2)}
#tl .ml{position:absolute;top:-10px;font-size:10px;font-weight:700;letter-spacing:.06em;color:var(--slate);transform:translateX(-50%);white-space:nowrap}
#tl .ml.lo{top:34px}
#cap{position:absolute;left:40px;top:724px;width:1520px;height:150px;background:#fff;border:1.5px solid var(--line);border-radius:14px;padding:18px 24px}
#cap .tag{font-size:12px;font-weight:700;letter-spacing:.14em;color:var(--orange)}
#cap .tt{font-size:24px;font-weight:800;margin-top:6px;letter-spacing:-.01em}
#cap .tx{font-size:15px;line-height:1.45;color:var(--slate);margin-top:8px;font-weight:500}
#cap .tt,#cap .tx{max-width:1180px}
#cap .sw{position:absolute;right:24px;top:18px;font-family:var(--mono);font-size:13px;font-weight:700;color:var(--orange);display:none}
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
/* inside the deck (an iframe): transparent page, the stage as a card, no help line */
html.embed,html.embed body{background:transparent}
html.embed #stage{border-radius:16px;box-shadow:0 18px 50px rgba(11,19,42,.16);border:1.5px solid var(--line)}
html.embed #help{display:none}
/* console only (?con=…): the stage is the console window, nothing else */
html.cononly #stage{width:1488px;height:622px;background:transparent;overflow:visible}
html.cononly #stage > *:not(#ov){display:none}
html.cononly #ov{display:block;background:transparent;cursor:default}
html.cononly #ov .c{display:none}
html.cononly #cw{left:0;top:0;width:1488px;height:622px;border:1.5px solid #D5DEEA;box-shadow:0 16px 44px rgba(11,19,42,.16)}
html.cononly.embed #stage{border:0;box-shadow:none;border-radius:0}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
"""


def page(devs, rows, M, alarm, lam, deploys, judge, day, alarm_hist, prov=None):
    data = json.dumps({"devs": devs, "ev": rows, "M": M, "alarm": alarm, "lam": lam, "deploys": deploys,
                       "judge": judge, "day": day, "alarmHist": alarm_hist, "s3": s3_and_component(rows),
                       "prov": prov},
                      ensure_ascii=False, separators=(",", ":"))
    con_css = open(os.path.join(HERE, "station-console.css"), encoding="utf-8").read()
    con_js = open(os.path.join(HERE, "station-console.js"), encoding="utf-8").read() + \
        open(os.path.join(HERE, "station-prov.js"), encoding="utf-8").read()
    tdc = os.path.join(TALK, "assets", "cali", "tdc")
    logo = data_uri(os.path.join(tdc, "logo-navy.png"))
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>La estación · MLOps a ciegas</title>
<style>{fonts_css()}{CSS}{con_css}</style></head>
<body>
<svg width="0" height="0" style="position:absolute">{pump_symbol()}</svg>
<div id="stage">
  <h1>La estación, <b>en vivo</b></h1>
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
  <div class="panel" id="dock" title="la consola de AWS · clic o A para ampliar"></div>
  <div id="prov"></div>
  <div id="tl"><div class="bar"></div><div class="done" id="tl-done"></div></div>
  <div id="cap"><div class="tag" id="c-tag"></div><div class="tt" id="c-tt"></div><div class="tx" id="c-tx"></div><div class="sw" id="c-sw"></div></div>
  <div id="ov"><div id="cw"><div class="tb"><div class="lg">aws<i></i></div><div class="sr">Search</div><div class="rg">United States (N. Virginia)</div></div>
    <div class="bc" id="cw-bc"></div><div class="bd" id="cw-bd"></div></div>
    <div class="c"><b>LA CONSOLA DE AWS, REDIBUJADA CON LOS DATOS DEL ENSAYO</b>{day} · <span id="ov-t"></span> · Esc cierra</div></div>
  <div id="help">espacio · reproducir  ·  ← → · actos  ·  1 2 4 8 · velocidad  ·  A · la consola de AWS  ·  F · pantalla completa</div>
</div>
<script>
const D={data};
const $=s=>document.querySelector(s);
const EV=D.ev, DEVS=D.devs, M=D.M, N=EV.length;
const T0=M[0].t, T1=Math.max(...EV.map(e=>e.a))+5000;
const TZ=-5*3600*1000;
function hms(ms){{ const d=new Date(ms+TZ); return d.toISOString().slice(11,19); }}
const ONLY=new URLSearchParams(location.search).get('con');      /* console only: the deck's slides 25-27 */
const SW=ONLY?1488:1600, SH=ONLY?622:900;
if(ONLY) document.documentElement.classList.add('cononly');
function fit(){{ const s=Math.min(innerWidth/SW,innerHeight/SH); $('#stage').style.transform=`translate(-50%,-50%) scale(${{s}})`; }}
addEventListener('resize',fit); fit();
{con_js}

/* the pumps: each one with its own X.509 certificate (the AWS IoT certificate icon) */
const CERT={json.dumps(cert_icon())};
const SFNIC={json.dumps(sfn_icons())};
const pumps=[];
const POS=[[180,16],[20,20],[340,20],[20,176],[340,176]];
DEVS.forEach((d,i)=>{{
  const el=document.createElement('div'); el.className='pump'; const ring=i===0?'.ring.r0':'.ring.r1';
  el.style.left=POS[i][0]+'px'; el.style.top=POS[i][1]+'px';
  el.innerHTML=`<svg class="ic"><use href="#pump"/></svg><div class="nm">${{d}}</div><div class="ver">v—</div><div class="dec">—</div>
    <div class="bar"><i></i></div><div class="thr"></div><div class="sc">score — · umbral —</div><div class="z">entrada <b>—</b></div><div class="q"></div><div class="tag"></div><div class="pvs"></div>${{CERT?'<img class="cert" alt="certificado X.509" title="AWS IoT · certificado X.509 de la bomba" src="'+CERT+'">':''}}`;
  $('#station '+ring).appendChild(el); pumps.push(el);
}});
const SMAX=.6;      /* the score bar's scale */

/* replay state */
let t=T0, playing=false, speed=4, last=null, cur=-1, eff=4;
/* pacing: ff glides to a moment instead of jumping; stop is where the replay waits for the next click (in the deck);
   between a moment's hold window and the next moment, the dead time runs at QUIET× */
let ff=null, stop=null, plan=null; const QUIET=12, LEAD=4000;
/* in the deck every click lasts the same: STEP_A ms of wall time for the moment's key part (its hold), STEP_B for the rest up to the next stop */
const STEP_A=11000, STEP_B=5000, GLIDE=1400;
const easeIO=x=>x<.5?2*x*x:1-Math.pow(-2*x+2,2)/2;
function fade(el,dy){{ if(el&&el.animate) el.animate([{{opacity:.15,transform:'translateY('+(dy||0)+'px)'}},{{opacity:1,transform:'none'}}],{{duration:450,easing:'ease-out'}}); }}
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
  if(playing && eff>4) return;
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
  /* ticker (kept for the standalone page's data; no box on the stage any more) */
  if($('#tk')) $('#tk').innerHTML=lines.map(e=>{{ const lt=(e.a-e.t)/1000; return '<div class="l"><span class="dim">'+hms(e.a)+'</span>  '+DEVS[e.d]+'  v'+e.v+'  '+(e.al?'<span class="al">ALERT</span>':'<span class="ok">normal</span>')+'  score '+e.s.toFixed(2)+' ('+e.h.toFixed(2)+')  input '+e.z.toFixed(1)+(lt>10?'  <span class="lt">· llegó '+lt.toFixed(0)+' s tarde</span>':'')+(e.f&&!e.al?'  <span class="mf">· falla no oída</span>':'')+(e.sv?'  <span class="sh">· sombra v'+e.sv+' '+(e.sa?'ALERT':'normal')+(e.sm?' · no la oyó':'')+'</span>':'')+'</div>'; }}).join('');
  /* timeline and caption */
  $('#tl-done').style.width=pos(t)+'%';
  let k=0; while(k+1<M.length && M[k+1].t<=t) k++;
  document.querySelectorAll('#tl .mk').forEach((m,j)=>{{ m.className='mk'+(M[j].t<=t?' done':'')+(j===k?' cur':''); }});
  if(k!==cur){{ cur=k; fade($('#cap'),8); $('#c-tag').textContent=M[k].tag; $('#c-tt').textContent=M[k].title; $('#c-tx').textContent=M[k].text;
    renderCon(true); }}
  /* the stopwatch since the fault nobody heard */
  const mf0=M.find(m=>m.k==='noye'), sw=$('#c-sw');
  if(mf0 && t>=mf0.t+6000 && M[k].k!=='fin'){{ const back=D.lam?D.lam.t:null; const end=back&&t>back?back:t; sw.style.display='block'; sw.textContent='desde la falla: '+Math.max(0,Math.round((end-(mf0.t+6000))/1000))+' s'+(back&&t>back?' · vuelta':''); }} else sw.style.display='none';
  renderCon(); provPaint();
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
  const l=document.createElement('div'); l.className='ml'+(j%2?' lo':''); l.style.left=pos(m.t)+'%'; if(j===0) l.style.transform='none'; l.textContent=m.tag.replace(/^ACTO \\d · /,''); $('#tl').appendChild(d); $('#tl').appendChild(l); }});
function goto(j,sp){{ j=Math.max(0,Math.min(M.length-1,j)); const to=M[j].t, nx=M[j+1], s=sp||M[j].speed;
  if(t>=to && (!nx||t<nx.t)) {{ setSpeed(s); }}                                   /* already in that moment: never step back */
  else if(to>t && j===cur+1 && to-t<120000) {{ ff={{from:t, to, sp:s, w0:performance.now()}}; }}  /* the very next moment: glide there */
  else {{ ff=null; step(to); setSpeed(s); paint(); fade($('#stage')); }}
  if(!playing) toggle(true); }}
function setSpeed(s){{ speed=s; document.querySelectorAll('#ctl [data-sp]').forEach(b=>b.classList.toggle('on',+b.dataset.sp===s)); }}
$('#dock').onclick=()=>showOv(); $('#ov').onclick=e=>{{ if(!e.target.closest('#cw')) hideOv(); }};
function toggle(on){{ playing=on===undefined?!playing:on; $('#play').textContent=playing?'❚❚':'▶'; last=null; if(playing) requestAnimationFrame(tick); }}
function tick(now){{ if(!playing) return;
  if(last!==null){{ const dt=now-last;
    if(ff){{ const q=Math.min(1,(now-ff.w0)/GLIDE); eff=99; step(Math.max(t,ff.from+(ff.to-ff.from)*easeIO(q))); if(q>=1){{ setSpeed(ff.sp); ff=null; }} }}
    else {{ const m=M[cur], nx=M[cur+1], quiet=m&&(t-m.t)>(m.hold||15000)&&(!nx||nx.t-t>LEAD);
      eff=plan?(t<plan.h?plan.a:plan.b):quiet?Math.max(speed,QUIET):speed; let to=Math.min(T1,t+dt*eff);
      if(stop!=null&&to>=stop){{ to=stop; }}
      step(to); if(stop!=null&&t>=stop){{ stop=null; paint(); toggle(false); last=null; return; }} }}
    paint(); if(t>=T1) toggle(false); }}
  last=now; requestAnimationFrame(tick); }}
$('#play').onclick=()=>toggle();
document.querySelectorAll('#ctl [data-sp]').forEach(b=>b.onclick=()=>setSpeed(+b.dataset.sp));
addEventListener('keydown',e=>{{ const k=e.key;
  if(k===' '){{ e.preventDefault(); toggle(); }}
  else if(k==='ArrowRight'||k==='PageDown'){{ e.preventDefault(); stop=null; plan=null; goto(cur+1); }}
  else if(k==='ArrowLeft'||k==='PageUp'){{ e.preventDefault(); stop=null; ff=null; plan=null; step(M[Math.max(0,cur-1)].t); goto(cur-1); }}
  else if(k==='Home'){{ step(T0); paint(); }}
  else if('1248'.includes(k)&&k){{ setSpeed(+k); }}
  else if(k.toLowerCase()==='a'){{ e.preventDefault(); conOpen?hideOv():showOv(); }}
  else if(k==='Escape'){{ hideOv(); }}
  else if(k.toLowerCase()==='f'){{ document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen(); }}
}});
window.__st={{seek:ms=>{{ step(ms); paint(); }}, goto, M, T0, T1, toggle}};
/* inside the deck: the slide drives the replay (build_deck: data-station), and the arrows go back to the deck */
const EMBED=window.parent!==window;
if(EMBED){{ document.documentElement.classList.add('embed');
  addEventListener('message',ev=>{{ const m=ev.data||{{}};
    if(m.cmd==='act'){{ const j=M.findIndex(x=>x.k===m.k); fit(); hideOv();
      if(j>=0){{ if(m.back||t>(M[j+1]||{{t:T1}}).t){{ ff=null; step(M[j].t); }} goto(j,m.speed);
        /* wait for the next click just before the next stop (m.until: a marker key, or 'end') */
        const u=m.until==='end'?-1:m.until?M.findIndex(x=>x.k===m.until):j+1; stop=u>=0&&M[u]?M[u].t-1500:null;
        /* the same wall time for every click: the key part in STEP_A, the rest in STEP_B */
        const a0=M[j].t, end=stop!=null?stop:T1, h=Math.min(end,a0+(M[j].hold||15000));
        plan=end-h>2000?{{h, a:Math.max(.5,(h-a0)/STEP_A), b:(end-h)/STEP_B}}:{{h:end, a:Math.max(.5,(end-a0)/(STEP_A+STEP_B)), b:1}}; }} }}
    else if(m.cmd==='pause') toggle(false);
    else if(m.cmd==='play') toggle(true);
    else if(m.cmd==='overlay'){{ m.on?showOv(m.con):hideOv(); if(m.speed) setSpeed(m.speed); if(m.on&&!playing) toggle(true); }}
    else if(m.cmd==='speed') setSpeed(m.s);
    else if(m.cmd==='show'){{ showOv(m.con); }}
    else if(m.cmd==='reset'&&!ONLY){{ toggle(false); ff=null; stop=null; plan=null; hideOv(); step(T0); paint(); }} }});
  addEventListener('keydown',e=>{{ if(['ArrowRight','ArrowDown','PageDown','Enter'].includes(e.key)){{ e.preventDefault(); e.stopImmediatePropagation(); parent.postMessage({{cmd:'nav',d:1}},'*'); }}
    else if(['ArrowLeft','ArrowUp','PageUp','Backspace'].includes(e.key)){{ e.preventDefault(); e.stopImmediatePropagation(); parent.postMessage({{cmd:'nav',d:-1}},'*'); }} }},true);
}}
if(ONLY){{ step(T1); paint(); showOv(ONLY); }} else {{ hideOv(); step(T0); paint(); }}
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
    if lam:
        lam["lines"] = lambda_lines(lam)
    prov = provision(ev[0]["ts"])
    if prov:
        M.insert(0, {"t": prov["t0"], "k": "prov", "tag": "APROVISIONAR", "title": "Terraform, la flota y la v1",
                     "text": f"terraform apply crea {prov['total']} recursos; la flota instala cinco bombas con Greengrass; "
                             "la v1 y la v2 se registran como versiones del componente; Greengrass despliega la v1 a los dos rings. Con eso, la prueba.",
                     "speed": 2, "con": None, "hold": prov.get("dur", 64000)})
    html = page(devs, rows, M, alarm, lam, deploys, judge, day, alarm_history(), prov)
    open(OUT, "w", encoding="utf-8").write(html)
    print(f"✔ {OUT}  ({len(html.encode()) / 1024:.0f} KB · {len(rows)} events · {len(M)} markers: "
          + ", ".join(m["k"] for m in M) + ")")


if __name__ == "__main__":
    main()
