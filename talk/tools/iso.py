"""
Small isometric kit (SVG) for the talk's figures.

Everything is drawn as polygons of 3D points projected with a fixed
isometric camera. Three-tone shading: the top face lighter,
the +y face in the base tone and the +x face darker. Palette from the
DevOpsDays Bogotá 2026 template.
"""
import math

NAVY, SLATE, MUTED, LIGHT = "#071329", "#475569", "#5C7290", "#F4F7FC"
PURPLE, BLUE, CYAN, MAGENTA = "#6D28D9", "#2448FF", "#00BCEB", "#F000A8"
S100, S200, S300, S400 = "#F1F5F9", "#E2E8F0", "#CBD5E1", "#94A3B8"
WHITE = "#FFFFFF"
FONT = "Calibri, CarlitoX, Carlito, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "'Courier New', ui-monospace, Menlo, Consolas, monospace"

C30 = math.cos(math.radians(30))


def _hex(c):
    c = c.lstrip("#"); return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    A, B = _hex(a), _hex(b)
    return "#%02X%02X%02X" % tuple(round(A[i] + (B[i] - A[i]) * t) for i in range(3))


def tones(base):
    """(top, +y face, +x face)"""
    return mix(base, WHITE, .38), base, mix(base, NAVY, .28)


class Iso:
    def __init__(self, ox, oy, u):
        self.ox, self.oy, self.u = ox, oy, u
        self.out = []

    # ── projection ──
    def P(self, x, y, z=0):
        return (self.ox + (x - y) * C30 * self.u, self.oy + (x + y) * .5 * self.u - z * self.u)

    def add(self, s):
        self.out.append(s)

    def svg(self):
        return "\n".join(self.out)

    # ── primitives ──
    def poly(self, pts, fill, stroke=None, sw=1.2, op=1, extra=""):
        d = " ".join("%.1f,%.1f" % self.P(*p) for p in pts)
        st = f' stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"' if stroke else ""
        o = f' opacity="{op}"' if op != 1 else ""
        self.add(f'<polygon points="{d}" fill="{fill}"{st}{o} {extra}/>')

    def line3(self, pts, stroke, sw=2, dash=None, op=1, extra=""):
        d = " ".join("%.1f,%.1f" % self.P(*p) for p in pts)
        ds = f' stroke-dasharray="{dash}"' if dash else ""
        o = f' opacity="{op}"' if op != 1 else ""
        self.add(f'<polyline points="{d}" fill="none" stroke="{stroke}" stroke-width="{sw}" '
                 f'stroke-linecap="round" stroke-linejoin="round"{ds}{o} {extra}/>')

    def box(self, x, y, z, w, d, h, base, edge=None, op=1, top=None):
        t, l, r = tones(base)
        if top: t = top
        e = edge or mix(base, NAVY, .55)
        self.poly([(x, y + d, z), (x + w, y + d, z), (x + w, y + d, z + h), (x, y + d, z + h)], l, e, .9, op)
        self.poly([(x + w, y, z), (x + w, y + d, z), (x + w, y + d, z + h), (x + w, y, z + h)], r, e, .9, op)
        self.poly([(x, y, z + h), (x + w, y, z + h), (x + w, y + d, z + h), (x, y + d, z + h)], t, e, .9, op)

    def circle_pts(self, c, e1, e2, r, n=48, a0=0, a1=2 * math.pi):
        pts = []
        for k in range(n + 1):
            a = a0 + (a1 - a0) * k / n
            pts.append(tuple(c[i] + r * (math.cos(a) * e1[i] + math.sin(a) * e2[i]) for i in range(3)))
        return pts

    def cyl(self, cx, cy, z, r, h, base, op=1, n=40):
        t, l, rr = tones(base)
        e = mix(base, NAVY, .55)
        bot = self.circle_pts((cx, cy, z), (1, 0, 0), (0, 1, 0), r, n)
        topc = self.circle_pts((cx, cy, z + h), (1, 0, 0), (0, 1, 0), r, n)
        # body: visible half (angles from -45° to 135° face the camera)
        a0, a1 = math.radians(-45), math.radians(135)
        front_b = self.circle_pts((cx, cy, z), (1, 0, 0), (0, 1, 0), r, n // 2, a0, a1)
        front_t = self.circle_pts((cx, cy, z + h), (1, 0, 0), (0, 1, 0), r, n // 2, a0, a1)
        self.poly(front_b + front_t[::-1], mix(l, rr, .35), e, .9, op)
        self.poly(topc, t, e, .9, op)

    def disc_on(self, c, e1, e2, r, fill, stroke=None, sw=1.2, n=48, op=1):
        self.poly(self.circle_pts(c, e1, e2, r, n)[:-1], fill, stroke, sw, op)

    def poly2(self, pts, fill, stroke=None, sw=1.2, op=1, extra=""):
        """Polygon with already projected (screen) points."""
        d = " ".join("%.1f,%.1f" % p for p in pts)
        st = f' stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"' if stroke else ""
        o = f' opacity="{op}"' if op != 1 else ""
        self.add(f'<polygon points="{d}" fill="{fill}"{st}{o} {extra}/>')

    def hcyl(self, a0, a1, c1, c2, r, base, axis="x", op=1, n=36, cap=None):
        """Lying cylinder. axis="x": from x=a0 to x=a1 centered at (y=c1, z=c2);
        axis="y": from y=a0 to y=a1 centered at (x=c1, z=c2). The visible cap is the one at a1."""
        t, l, rr = tones(base)
        e = mix(base, NAVY, .55)
        if axis == "x":
            c0, cE, e1, e2 = (a0, c1, c2), (a1, c1, c2), (0, 1, 0), (0, 0, 1)
            side = l
        else:
            c0, cE, e1, e2 = (c1, a0, c2), (c1, a1, c2), (1, 0, 0), (0, 0, 1)
            side = rr
        pts = [self.P(*p) for p in self.circle_pts(c0, e1, e2, r, n) + self.circle_pts(cE, e1, e2, r, n)]
        self.poly2(_hull(pts), mix(side, t, .15), e, .9, op)
        self.disc_on(cE, e1, e2, r, cap or (rr if axis == "x" else l), e, .9, n, op)


    # ── packets travelling along a path (in the PNG they stay still, spread out) ──
    def flow(self, pts3, n=4, dur=4, r=7, color=PURPLE, static=False, extra=""):
        pts = [self.P(*p) for p in pts3]
        seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
        L = sum(seg) or 1
        if static:
            for k in range(n):
                d = L * (k + .5) / n
                for i, s in enumerate(seg):
                    if d <= s or i == len(seg) - 1:
                        t = d / s if s else 0
                        x = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t
                        y = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t
                        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}" {extra}/>')
                        break
                    d -= s
            return
        path = "M" + " L".join("%.1f,%.1f" % p for p in pts)
        self.add(f'<g {extra}>')
        for k in range(n):
            self.add(f'<circle r="{r}" fill="{color}"><animateMotion dur="{dur}s" begin="{-dur * k / n:.2f}s" '
                     f'repeatCount="indefinite" path="{path}"/></circle>')
        self.add('</g>')

    # ── flat text (screen space) ──
    def text(self, sx, sy, s, size=18, color=NAVY, weight=600, anchor="start", op=1, family=FONT, extra=""):
        o = f' fill-opacity="{op}"' if op != 1 else ""
        self.add(f'<text x="{sx:.1f}" y="{sy:.1f}" font-family="{family}" font-size="{size}" '
                 f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}"{o} {extra}>{s}</text>')

    def label(self, p3, dx, dy, title, sub="", anchor=None, color=NAVY, extra="", at=None):
        """Label with a leader line from a 3D point. `at` = absolute text position."""
        x, y = self.P(*p3)
        tx, ty = at if at else (x + dx, y + dy)
        if anchor is None:
            anchor = "end" if tx < x else "start"
        self.add(f'<g {extra}>')
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}"/>')
        mid = (tx - (12 if anchor == "start" else -12), ty - 6)
        self.add(f'<polyline points="{x:.1f},{y:.1f} {mid[0]:.1f},{ty - 6:.1f} {tx - (4 if anchor == "start" else -4):.1f},{ty - 6:.1f}" '
                 f'fill="none" stroke="{color}" stroke-width="1.5"/>')
        self.text(tx, ty, title, 21, color, 700, anchor)
        if sub:
            self.text(tx, ty + 25, sub, 18, SLATE, 400, anchor)
        self.add('</g>')


def _hull(pts):
    """Convex hull (monotone chain) of 2D points."""
    P = sorted(set((round(x, 2), round(y, 2)) for x, y in pts))
    if len(P) < 3:
        return P
    def cr(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in P:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(P):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]
