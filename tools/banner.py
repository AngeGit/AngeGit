"""Generate the README artwork (banner, buttons, section headings, divider) with subset fonts embedded.

Type system: Oxanium is the voice (name, sign, headings, buttons); JetBrains Mono does the technical bits.

usage (from the repo root):  python3 tools/banner.py assets assets/portrait.jpg
needs:                       pip install fonttools brotli
"""
import base64, io, math, pathlib, random, re, sys

from fontTools import subset as fsub
from fontTools.ttLib import TTFont

HERE = pathlib.Path(__file__).resolve().parent
FONT_FILES = {
    "Oxanium": HERE / "fonts/Oxanium[wght].ttf",
    "JBMono": HERE / "fonts/JetBrainsMono[wght].ttf",
    "JBMonoItalic": HERE / "fonts/JetBrainsMono-Italic[wght].ttf",
}
BASIC = ["kern", "ccmp", "locl", "mark", "mkmk"]
# JetBrains Mono draws its ligatures through calt, so the mono face keeps only the basics.
FEATURES = {"Oxanium": BASIC + ["calt"], "JBMono": BASIC, "JBMonoItalic": BASIC}

BG1 = "#140e20"
INK, INK2, INK3 = "#f6f0ff", "#bdb3cf", "#857a99"
FUCHSIA, ORANGE, VIOLET, MINT = "#e879f9", "#fb923c", "#c4b5fd", "#86efac"
NEON_CORE = "#ffe4fc"
PLUM, PLUM_MUTED = "#3b1446", "#8a6a96"  # heading ink on GitHub's light theme

W, H = 1280, 400
NAME = "Ángeles Martín"
COMMENT = "// technomancer.kt · Madrid, Spain · remote"
ROLE = "ANDROID · KOTLIN MULTIPLATFORM · AI TOOLING"
CMD = ("$ ", "./gradlew ", "lumos", " --target=commonMain")
OUT = "✓ BUILD SUCCESSFUL · 0 mocks harmed"
NAME_PX, NAME_MAX_W = 86, 620
MONO_PX, MONO_CW = 15, 0.6  # JetBrains Mono advance: 600/1000 em
HEADINGS = {  # file stem: (title, muted tail, size[, crest])
    "shifts": ("Day & night shift", "what I build", 26, "daynight"),
    "unrestricted": ("Unrestricted section", "public repos", 26, "book"),
    "house-rules": ("House guardrails", "how I work", 26, "hat"),
    "wand-cores": ("Wand cores", "stack", 26, "wand"),
}

BRAND = f'<linearGradient id="brand" x1="0" x2="1"><stop offset="0" stop-color="{FUCHSIA}"/><stop offset="1" stop-color="{ORANGE}"/></linearGradient>'
REDUCED = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


# ---------- fonts

def font_face(family, text):
    opts = fsub.Options()
    opts.layout_features = FEATURES[family]
    font = TTFont(FONT_FILES[family])
    missing = {c for c in text if ord(c) not in font.getBestCmap() and not c.isspace()}
    if missing:
        print(f"warning: {family} lacks {''.join(sorted(missing))}", file=sys.stderr)
    sub = fsub.Subsetter(opts)
    sub.populate(text=text + " ")
    sub.subset(font)
    font.flavor = "woff2"
    buf = io.BytesIO()
    font.save(buf)
    data = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:'{family}';src:url(data:font/woff2;base64,{data}) format('woff2');font-weight:100 900}}"


_metrics = {}

def width(family, text, size, tracking=0.0):
    """Advance width at the default instance: close enough to size things."""
    if family not in _metrics:
        f = TTFont(FONT_FILES[family])
        _metrics[family] = (f.getBestCmap(), f["hmtx"].metrics, f["head"].unitsPerEm)
    cmap, hmtx, upm = _metrics[family]
    return sum(hmtx[cmap[ord(c)]][0] for c in text if ord(c) in cmap) * size / upm + tracking * len(text)


def xml(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg_open(w, h, title, desc=""):
    labelled = "t d" if desc else "t"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-labelledby="{labelled}">'
            f'<title id="t">{xml(title)}</title>' + (f'<desc id="d">{xml(desc)}</desc>' if desc else ""))


def sparkle(cx, cy, s):
    k = .14 * s
    return (f"M{cx} {cy-s}C{cx+k} {cy-k} {cx+k} {cy-k} {cx+s} {cy}C{cx+k} {cy+k} {cx+k} {cy+k} {cx} {cy+s}"
            f"C{cx-k} {cy+k} {cx-k} {cy+k} {cx-s} {cy}C{cx-k} {cy-k} {cx-k} {cy-k} {cx} {cy-s}Z")


# ---------- banner

def typing(cid, x, baseline, n, begin, per=0.045):
    cw = MONO_CW * MONO_PX
    vals = ";".join(f"{i * cw:.1f}" for i in range(n + 1))
    dur = per * n
    clip = (f'<clipPath id="{cid}"><rect x="{x}" y="{baseline - 16}" height="22" width="0">'
            f'<animate attributeName="width" values="{vals}" calcMode="discrete" begin="{begin:.2f}s" '
            f'dur="{dur:.2f}s" fill="freeze"/></rect></clipPath>')
    return clip, begin + dur


def skyline(seed, base, var, color, win_op, lit_from=None):
    """lit_from: x where windows start switching on (dusk); None lights the whole street."""
    r = random.Random(seed)
    blocks, wins = [], []
    x = -10
    while x < W:
        w, h = r.randint(34, 90), base + r.randint(0, var)
        blocks.append(f'<rect x="{x}" y="{H - h}" width="{w}" height="{h}"/>')
        for wy in range(H - h + 10, H - 6, 13):
            for wx in range(x + 6, x + w - 6, 10):
                ramp = 1 if lit_from is None else min(1, max(0, (wx - lit_from) / 260))
                if r.random() < .09 * ramp:
                    c = r.choice(["#fdba74", "#fdba74", "#67e8f9", "#f0abfc"])
                    cls = f' class="blink" style="animation-delay:{r.uniform(-6, 0):.1f}s"' if r.random() < .2 else ""
                    wins.append(f'<rect{cls} x="{wx}" y="{wy}" width="3" height="5" fill="{c}" opacity="{win_op * r.uniform(.4, 1):.2f}"/>')
        x += w + r.randint(2, 8)
    return f'<g fill="{color}">{"".join(blocks)}</g><g>{"".join(wins)}</g>'


def rain(seed, n=80):
    """Drawn twice, one screen apart, so the falling loop is seamless."""
    r = random.Random(seed)
    lines = []
    for _ in range(n):
        x, y, l = r.uniform(0, W), r.uniform(0, H), r.uniform(12, 30)
        for off in (0, -H):
            lines.append(f'<line x1="{x:.0f}" y1="{y + off:.0f}" x2="{x - 4:.0f}" y2="{y + off + l:.0f}"/>')
    return f'<g class="rain" stroke="#c7d2fe" stroke-opacity=".11" stroke-width="1">{"".join(lines)}</g>'


def neon_text(cls, x, y, text, core, glow, *, wide=True, flick=None, anchor="start"):
    """Halo + tight glow + bright core. `flick` is the index of a letter that misfires now and then."""
    body = text if flick is None else f'{text[:flick]}<tspan class="flick">{text[flick]}</tspan>{text[flick + 1:]}'
    attrs = f'class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}"'
    halo = f'<text {attrs} fill="{glow}" opacity=".6" filter="url(#neonWide)">{body}</text>' if wide else ""
    return (f'{halo}<text {attrs} fill="{glow}" opacity=".95" filter="url(#neonTight)">{body}</text>'
            f'<text {attrs} fill="{core}">{body}</text>')


THEMES = {
    "dark": dict(
        sky='<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#07050d"/><stop offset=".6" stop-color="#140b24"/><stop offset="1" stop-color="#22103a"/></linearGradient>',
        city=("#100a1e", "#170e2b"), lit_from=None, rain=True, grain=".09", frame="#fff",
        bokeh=(("#22d3ee", .22), (FUCHSIA, .34), (ORANGE, .2)),
        comment="#5eead4", name=(NEON_CORE, FUCHSIA, True), role=("#ffd7b0", ORANGE),
        box=("#0a0714", ".72", "#fff", ".09"), cmd=(INK3, INK2, FUCHSIA, INK3), out=MINT,
    ),
    # dusk: day on the left, night falling on the right where the portrait lives
    "light": dict(
        sky=('<linearGradient id="sky" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fbf6ff"/><stop offset=".38" stop-color="#f8e9fb"/>'
             '<stop offset=".52" stop-color="#f3c6e2"/><stop offset=".64" stop-color="#6b2a6e"/><stop offset=".78" stop-color="#1d0f2e"/></linearGradient>'),
        city=("url(#cityBack)", "url(#cityFront)"), lit_from=560, rain=False, grain=".05", frame="#3b1446",
        bokeh=(("#fdba74", .35), (FUCHSIA, .3), ("#fda4af", .3)),
        comment="#0f766e", name=(PLUM, FUCHSIA, False), role=("#c2410c", None),
        box=("#ffffff", ".78", "#3b1446", ".12"), cmd=("#8a7a99", "#5b4a6b", "#c026d3", "#8a7a99"), out="#15803d",
    ),
}


def banner(face, theme):
    t = THEMES[theme]
    size = NAME_PX
    natural = width("Oxanium", NAME, size)
    if natural > NAME_MAX_W:
        size = round(size * NAME_MAX_W / natural)
    x, px, sx, box_y = 84, 820, 762, 252
    clip1, t1 = typing("ty1", x + 20, box_y + 46, sum(map(len, CMD)), 2.4)
    clip2, t2 = typing("ty2", x + 20, box_y + 70, len(OUT), t1 + .35)
    cursor_x = x + 20 + len(OUT) * MONO_CW * MONO_PX + 5
    sign = "".join(neon_text("sign", sx + 23, 112 + i * 38, ch, "#ffe4c7", ORANGE, wide=False, anchor="middle")
                   for i, ch in enumerate("KOTLIN"))
    name_core, name_glow, name_halo = t["name"]
    name_svg = (neon_text("name", x - 3, 178, NAME, name_core, name_glow, wide=name_halo, flick=NAME.index("t")) if theme == "dark"
                else f'<text class="name" x="{x - 3}" y="182" fill="{FUCHSIA}" fill-opacity=".35" filter="url(#neonTight)">{NAME}</text>'
                     f'<text class="name" x="{x - 3}" y="178" fill="{name_core}">{NAME[:NAME.index("t")]}<tspan class="flick">t</tspan>{NAME[NAME.index("t") + 1:]}</text>')
    role_core, role_glow = t["role"]
    role_svg = (neon_text("role", x, 222, ROLE, role_core, role_glow, wide=False) if role_glow
                else f'<text class="role" x="{x}" y="222" fill="{role_core}">{ROLE}</text>')
    box_fill, box_op, box_stroke, box_stroke_op = t["box"]
    c0, c1, c2, c3 = t["cmd"]
    (b0, o0), (b1, o1), (b2, o2) = t["bokeh"]
    style = f"""{font_face("Oxanium", NAME + "KOTLIN")}{font_face("JBMono", COMMENT + ROLE + "".join(CMD) + OUT)}
 .comment{{font:500 14px 'JBMono',monospace;fill:{t["comment"]};fill-opacity:.8}}
 .role{{font:500 15px 'JBMono',monospace;letter-spacing:4px}}
 .mono{{font:400 {MONO_PX}px 'JBMono',monospace;font-variant-ligatures:none}}
 .name{{font:300 {size}px 'Oxanium',sans-serif}}
 .sign{{font:400 26px 'Oxanium',sans-serif}}
 .ignite{{animation:ignite 2.2s .3s both}}
 @keyframes ignite{{0%{{opacity:0}}7%{{opacity:.9}}9%{{opacity:.1}}15%{{opacity:1}}18%{{opacity:.3}}24%,100%{{opacity:1}}}}
 .fade{{animation:fade 1.2s 1.3s both}}
 @keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
 .breathe{{animation:breathe 7s ease-in-out infinite alternate}}
 @keyframes breathe{{from{{opacity:.7}}to{{opacity:1}}}}
 .flick{{animation:flick 9s 4s infinite}}
 @keyframes flick{{0%,88%,90%,94%,100%{{fill-opacity:1}}89%{{fill-opacity:.12}}92%{{fill-opacity:.3}}}}
 .signflick{{animation:sflick 11s 6s infinite}}
 @keyframes sflick{{0%,60%,62%,65%,100%{{opacity:1}}61%,63%{{opacity:.35}}}}
 .blink{{animation:blink 6s steps(1) infinite}}
 @keyframes blink{{0%,70%{{opacity:.6}}71%,100%{{opacity:.06}}}}
 .rain{{animation:fall 1.5s linear infinite}}
 @keyframes fall{{to{{transform:translateY({H}px)}}}}
 .t1{{clip-path:url(#ty1)}}.t2{{clip-path:url(#ty2)}}
 {REDUCED}
 @media (prefers-reduced-motion:reduce){{.t1,.t2{{clip-path:none}}}}"""
    city_defs = ('<linearGradient id="cityBack" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{W}" y2="0"><stop offset="0" stop-color="#f3e9f9"/><stop offset=".5" stop-color="#ead6f1"/><stop offset=".66" stop-color="#3a1748"/><stop offset="1" stop-color="#140b22"/></linearGradient>'
                 '<linearGradient id="cityFront" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{W}" y2="0"><stop offset="0" stop-color="#ece0f6"/><stop offset=".5" stop-color="#dfc2ea"/><stop offset=".66" stop-color="#2c1038"/><stop offset="1" stop-color="#170e2b"/></linearGradient>'
                 ).replace("{W}", str(W)) if theme == "light" else ""
    return f"""{svg_open(W, H, "Ángeles Martín: Android, Kotlin Multiplatform and AI tooling",
                 "Neon city: the name glows like a neon sign, a vertical KOTLIN sign flickers, a terminal casts lumos, and a cyberpunk portrait melts into the street at night.")}
<defs>{BRAND}{t["sky"]}{city_defs}
 <clipPath id="frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>
 <linearGradient id="fadeX" gradientUnits="userSpaceOnUse" x1="{px}" y1="0" x2="{px + 210}" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff"/></linearGradient>
 <mask id="fade" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><rect x="{px}" width="{W - px}" height="{H}" fill="url(#fadeX)"/></mask>
 <filter id="neonWide" x="-20%" y="-80%" width="140%" height="260%"><feGaussianBlur stdDeviation="12"/></filter>
 <filter id="neonTight" x="-10%" y="-40%" width="120%" height="180%"><feGaussianBlur stdDeviation="2.4"/></filter>
 <filter id="soft" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="42"/></filter>
 <filter id="grain" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" stitchTiles="stitch"/>
  <feColorMatrix type="saturate" values="0"/>
  <feComponentTransfer><feFuncA type="table" tableValues="0 {t["grain"]}"/></feComponentTransfer>
 </filter>
 {clip1}{clip2}
</defs>
<style>{style}</style>
<g clip-path="url(#frame)">
 <rect width="{W}" height="{H}" fill="url(#sky)"/>
 <g filter="url(#soft)">
  <ellipse class="breathe" cx="580" cy="40" rx="120" ry="60" fill="{b0}" fill-opacity="{o0}"/>
  <ellipse class="breathe" style="animation-delay:-3s" cx="800" cy="200" rx="100" ry="140" fill="{b1}" fill-opacity="{o1}"/>
  <ellipse class="breathe" style="animation-delay:-5s" cx="360" cy="410" rx="240" ry="100" fill="{b2}" fill-opacity="{o2}"/>
 </g>
 {skyline(1, 110, 130, t["city"][0], .5, t["lit_from"])}
 {skyline(2, 40, 80, t["city"][1], .75, t["lit_from"])}
 <image href="{face}" x="{px}" y="-8" width="{W - px}" height="{round((W - px) * 540 / 536)}" preserveAspectRatio="xMidYMid slice" mask="url(#fade)"/>
 <g class="signflick">
  <rect x="{sx}" y="78" width="46" height="244" rx="12" fill="none" stroke="{ORANGE}" stroke-width="4" opacity=".5" filter="url(#neonTight)"/>
  <rect x="{sx}" y="78" width="46" height="244" rx="12" fill="none" stroke="#ffd2a8" stroke-width="1.6"/>
  {sign}
 </g>
 {rain(5) if t["rain"] else ""}
 <text class="comment fade" x="{x}" y="92">{COMMENT}</text>
 <g class="ignite">{name_svg}</g>
 <g class="fade">{role_svg}</g>
 <rect x="{x}" y="{box_y}" width="420" height="84" rx="10" fill="{box_fill}" fill-opacity="{box_op}" stroke="{box_stroke}" stroke-opacity="{box_stroke_op}"/>
 <circle cx="{x + 18}" cy="{box_y + 16}" r="3.5" fill="#ff5f57" opacity=".75"/><circle cx="{x + 30}" cy="{box_y + 16}" r="3.5" fill="#febc2e" opacity=".75"/><circle cx="{x + 42}" cy="{box_y + 16}" r="3.5" fill="#28c840" opacity=".75"/>
 <text class="mono t1" x="{x + 20}" y="{box_y + 46}"><tspan fill="{c0}">{CMD[0]}</tspan><tspan fill="{c1}">{CMD[1]}</tspan><tspan fill="{c2}">{CMD[2]}</tspan><tspan fill="{c3}">{CMD[3]}</tspan></text>
 <text class="mono t2" x="{x + 20}" y="{box_y + 70}" fill="{t["out"]}" fill-opacity=".9">{OUT}</text>
 <rect x="{cursor_x:.1f}" y="{box_y + 57}" width="8" height="16" fill="{t["out"]}" opacity="0"><animate attributeName="opacity" values=".8;0" calcMode="discrete" dur="1.1s" begin="{t2:.2f}s" repeatCount="indefinite"/></rect>
 <rect width="{W}" height="{H}" filter="url(#grain)"/>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{t["frame"]}" stroke-opacity=".08"/>
</svg>"""


# ---------- section headings: one file per GitHub theme

def phoenix_feather():
    """Line-art feather on a 48x42 grid: curved shaft, barbs that sweep towards the tip (one vane
    wider, a couple of splits), down at the base and embers rising from the tip. Returns (svg, tip_xy)."""
    p0, p1, p2 = (9, 39), (19, 24), (38, 4)

    def at(t):
        u = 1 - t
        x = u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0]
        y = u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]
        dx = 2 * u * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0])
        dy = 2 * u * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1])
        n = math.hypot(dx, dy)
        return x, y, dx / n, dy / n

    def turn(tx, ty, deg):
        a = math.radians(deg)
        return tx * math.cos(a) - ty * math.sin(a), tx * math.sin(a) + ty * math.cos(a)

    rnd = random.Random(7)
    barbs, down, edge = [], [], {-1: [], 1: []}
    splits = {(-1, 11), (-1, 12), (1, 16)}
    n = 22
    for i in range(5, n):
        t = i / n
        x, y, tx, ty = at(t)
        env = math.sin(math.pi * min(1, (t - .2) / .8)) ** .6 if t < .98 else .1
        for sign, reach in ((-1, 10.5), (1, 6.8)):
            length = reach * env * rnd.uniform(.88, 1.06)
            ox, oy = turn(tx, ty, 62 * sign)  # leaves the shaft wide...
            ex, ey = turn(tx, ty, 34 * sign)  # ...and ends sweeping towards the tip
            cx, cy = x + ox * length * .55, y + oy * length * .55
            fx, fy = x + ex * length, y + ey * length
            edge[sign].append((fx, fy))
            if (sign, i) not in splits:
                barbs.append(f"M{x:.1f} {y:.1f}Q{cx:.1f} {cy:.1f} {fx:.1f} {fy:.1f}")
    for i, sign in ((2, -1), (3, 1), (3, -1), (4, 1), (4, -1)):  # loose down near the quill
        x, y, tx, ty = at(i / n)
        ox, oy = turn(tx, ty, 80 * sign)
        ex, ey = turn(tx, ty, 20 * sign)
        down.append(f"M{x:.1f} {y:.1f}c{ox * 3:.1f} {oy * 3:.1f} {ex * 4 + ox * 2:.1f} {ey * 4 + oy * 2:.1f} {ex * 5:.1f} {ey * 5 + 1:.1f}")
    body = edge[-1] + [p2] + edge[1][::-1] + [at(5 / n)[:2]]
    vane = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in body) + "Z"
    shaft = f"M{p0[0]} {p0[1]} Q{p1[0]} {p1[1]} {p2[0]} {p2[1]}"
    embers = "".join(f'<circle class="ember" style="animation-delay:{d}s" cx="{p2[0] + dx}" cy="{p2[1] + 1}" r="{r}"/>'
                     for d, dx, r in ((0, -2, 1.1), (.6, 1.5, .9), (1.2, -.5, .8)))
    svg = (f'<path d="{vane}" fill="url(#fire)" opacity=".22"/>'
           f'<path d="{" ".join(down)}" stroke="url(#fire)" stroke-width=".7" stroke-linecap="round" fill="none" opacity=".7"/>'
           f'<path d="{" ".join(barbs)}" stroke="url(#fire)" stroke-width=".85" stroke-linecap="round" fill="none"/>'
           f'<path d="{shaft}" stroke="url(#fire)" stroke-width="1.7" stroke-linecap="round" fill="none"/>'
           f'<g fill="#fde68a">{embers}</g>')
    return svg, p2


def wand_crest(h, dark):
    """A wand crossing a phoenix feather (Harry's wand core), for the "Wand cores" title.
    Returns (svg, defs, css, width)."""
    k = h / 42  # drawn on a 48x42 grid
    feather, _ = phoenix_feather()
    glow = f'<g filter="url(#tight)" opacity="{.7 if dark else .3}">{feather}</g>'
    svg = (f'<g transform="scale({k:.3f})">'
           f'<g transform="translate(48 0) scale(-1 1)"><g class="flame">{glow}{feather}</g></g>'
           f'<path d="M6 40 L42 6" stroke="url(#wood)" stroke-width="3.4" stroke-linecap="round"/>'
           f'<path d="M6 40 L13 33" stroke="#4a2c13" stroke-width="5" stroke-linecap="round"/>'
           f'<g class="tip"><circle cx="42" cy="6" r="5" fill="{FUCHSIA}" opacity=".45" filter="url(#tight)"/>'
           f'<path d="{sparkle(42, 6, 5)}" fill="#fff4fe"/></g></g>')
    defs = (f'<linearGradient id="fire" gradientUnits="userSpaceOnUse" x1="9" y1="39" x2="38" y2="4"><stop offset="0" stop-color="#dc2626"/>'
            f'<stop offset=".5" stop-color="{ORANGE}"/><stop offset="1" stop-color="#fde68a"/></linearGradient>'
            f'<linearGradient id="wood" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#6b3f1d"/><stop offset="1" stop-color="#d9b07a"/></linearGradient>')
    css = (".flame{animation:flame 2.2s ease-in-out infinite alternate}@keyframes flame{from{opacity:.85}to{opacity:1}}"
           ".tip{transform-box:fill-box;transform-origin:center;animation:tip 1.8s ease-in-out infinite}"
           "@keyframes tip{50%{transform:scale(.6);opacity:.7}}"
           ".ember{opacity:0;animation:ember 1.8s ease-out infinite}"
           "@keyframes ember{0%{opacity:0;transform:translate(0,0)}25%{opacity:1}100%{opacity:0;transform:translate(2px,-7px)}}")
    return svg, defs, css, round(48 * k)


def day_night_crest(h, dark):
    """Half a sun and a crescent moon sharing one disc, for the "Day & night shift" title.
    Returns (svg, defs, css, width)."""
    k = h / 42  # drawn on a 48x42 grid
    cx, cy, r = 21, 21, 11
    sun = f"M{cx - 1} {cy - r} A{r} {r} 0 0 0 {cx - 1} {cy + r} Z"
    moon = f"M{cx + 1} {cy - r} A{r} {r} 0 0 1 {cx + 1} {cy + r} A5 {r} 0 0 0 {cx + 1} {cy - r} Z"
    rays = " ".join(f"M{cx + 14 * math.cos(math.radians(a)):.1f} {cy + 14 * math.sin(math.radians(a)):.1f}"
                    f"L{cx + 17.5 * math.cos(math.radians(a)):.1f} {cy + 17.5 * math.sin(math.radians(a)):.1f}"
                    for a in (110, 145, 180, 215, 250))
    stars = "".join(f'<path class="star" style="animation-delay:{d}s" d="{sparkle(x, y, sz)}"/>'
                    for x, y, sz, d in ((38, 9, 3.6, 0), (44, 19, 2.4, .9), (39, 31, 2, 1.6)))
    shapes = (f'<path d="{sun}" fill="url(#sun)"/><path d="{moon}" fill="url(#moon)"/>'
              f'<g class="rays"><circle cx="{cx}" cy="{cy}" r="17.5" fill="none"/>'
              f'<path d="{rays}" stroke="{ORANGE}" stroke-width="2.4" stroke-linecap="round"/></g>')
    svg = (f'<g transform="scale({k:.3f})">'
           f'<g filter="url(#tight)" opacity="{.6 if dark else .25}">{shapes}</g>{shapes}'
           f'<g fill="{"#fff4fe" if dark else "#a855f7"}">{stars}</g></g>')
    defs = (f'<radialGradient id="sun" cx=".7" cy=".5" r=".8"><stop offset="0" stop-color="#fde68a"/>'
            f'<stop offset=".55" stop-color="{ORANGE}"/><stop offset="1" stop-color="#ea580c"/></radialGradient>'
            f'<linearGradient id="moon" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{VIOLET}"/>'
            f'<stop offset="1" stop-color="{FUCHSIA}"/></linearGradient>')
    css = (".rays{transform-box:fill-box;transform-origin:center;animation:rays 2.8s ease-in-out infinite alternate}"
           "@keyframes rays{from{transform:scale(.9);opacity:.75}to{transform:scale(1.04);opacity:1}}"
           ".star{transform-box:fill-box;transform-origin:center;animation:star 2.4s ease-in-out infinite}"
           "@keyframes star{50%{transform:scale(.4);opacity:.4}}")
    return svg, defs, css, round(48 * k)


def hat_crest(h, dark):
    """The Sorting Hat sitting on a neon terminal, thinking, for "House rules". Returns (svg, defs, css, width)."""
    k = h / 42  # drawn on a 48x42 grid
    frame = '<rect x="4" y="19" width="39" height="21" rx="4" fill="none" stroke="url(#term)" stroke-width="2.2"/>'
    cone = ("M19 19.5 C20.5 14 23 9.5 26 6.5 C28 4.5 31 4 33.5 5.5 C35.5 6.8 36.8 9 37 11.5 "
            "C35.5 9.8 33.5 9 31.5 9.6 C32.5 13 34.5 16.5 37 19.5 Z")
    brim = "M14.5 20 Q28 24.5 41.5 20 Q28 16.5 14.5 20 Z"
    crease = "M24.5 15 Q28 17.2 31.5 14.8 M25 11.6 Q26.5 10.8 28 11.6 M29.6 11.3 Q31 10.6 32.2 11.4"
    svg = (f'<g transform="scale({k:.3f})">'
           f'<rect x="4" y="19" width="39" height="21" rx="4" fill="{"#1a0f24" if dark else "#fdf4ff"}"/>'
           f'<g filter="url(#tight)" opacity="{.7 if dark else .3}">{frame}</g>{frame}'
           f'<path d="M10 25.5 L14.5 29 L10 32.5" fill="none" stroke="{FUCHSIA}" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>'
           f'<rect class="cursor" x="17" y="31" width="8" height="2.4" rx="1" fill="{ORANGE}"/>'
           f'<g transform="translate(28 20) scale(1.15) translate(-28 -20)"><g class="hat">'
           f'<path d="{brim}" fill="url(#felt)"/><path d="{cone}" fill="url(#felt)"/>'
           f'<path d="M20 17.6 Q28 19.8 36 17.6" fill="none" stroke="#3b2210" stroke-width="1.6" opacity=".7"/>'
           f'<path d="{crease}" fill="none" stroke="#2a1608" stroke-width="1" stroke-linecap="round"/></g></g></g>')
    defs = (f'<linearGradient id="term" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{FUCHSIA}"/>'
            f'<stop offset="1" stop-color="{ORANGE}"/></linearGradient>'
            f'<linearGradient id="felt" x1="0" y1="1" x2=".6" y2="0"><stop offset="0" stop-color="#6b3f1d"/>'
            f'<stop offset="1" stop-color="#c79358"/></linearGradient>')
    css = (".cursor{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
           ".hat{transform-box:fill-box;transform-origin:50% 100%;animation:think 3.2s ease-in-out infinite alternate}"
           "@keyframes think{from{transform:rotate(-4deg)}to{transform:rotate(3deg)}}")
    return svg, defs, css, round(48 * k)


def book_crest(h, dark):
    """An open spellbook from the library's *un*restricted section: a page keeps turning on its own
    and sparks rise from it. Returns (svg, defs, css, width)."""
    k = h / 42  # drawn on a 48x42 grid
    left = "M24 14 C18 11 10 11 4 13 V35 C10 33 18 34 24 38 Z"
    right = "M24 14 C30 11 38 11 44 13 V35 C38 33 30 34 24 38 Z"
    cover = "M2 15 V38 C10 36 18 37 24 41 C30 37 38 36 46 38 V15"
    text = ("M8 18 C12 17 16 17 20 18.5 M8 22.5 C12 21.5 16 21.5 20 23 M8 27 C12 26 16 26 20 27.5 M8 31.5 C11 30.8 13 30.8 15 31.2 "
            "M28 18.5 C32 17 36 17 40 18 M28 23 C32 21.5 36 21.5 40 22.5 M28 27.5 C32 26 36 26 40 27")
    paper = "#1a0f24" if dark else "#fdf4ff"
    book = (f'<path d="{cover}" fill="none" stroke="url(#term)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{left}" fill="{paper}" stroke="url(#term)" stroke-width="1.8" stroke-linejoin="round"/>'
            f'<path d="{right}" fill="{paper}" stroke="url(#term)" stroke-width="1.8" stroke-linejoin="round"/>')
    stars = "".join(f'<path class="star" style="animation-delay:{d}s" d="{sparkle(x, y, sz)}"/>'
                    for x, y, sz, d in ((31, 5, 3.6, 0), (17, 7, 2.6, .8), (39, 9, 2, 1.5)))
    svg = (f'<g transform="scale({k:.3f})">'
           f'<g filter="url(#tight)" opacity="{.6 if dark else .25}">{book}</g>{book}'
           f'<path d="{text}" fill="none" stroke="{VIOLET}" stroke-width="1.1" stroke-linecap="round" opacity=".7"/>'
           f'<path class="flip" d="{right}" fill="{"#2a1840" if dark else "#f5d0fe"}" stroke="url(#term)" stroke-width="1.4" stroke-linejoin="round"/>'
           f'<g fill="{"#fff4fe" if dark else "#a855f7"}">{stars}</g></g>')
    defs = (f'<linearGradient id="term" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{FUCHSIA}"/>'
            f'<stop offset="1" stop-color="{ORANGE}"/></linearGradient>')
    css = (".flip{transform-box:fill-box;transform-origin:0% 50%;opacity:0;animation:flip 3.6s ease-in-out infinite}"
           "@keyframes flip{0%,45%{transform:scaleX(1);opacity:0}50%{opacity:1}80%{transform:scaleX(-1);opacity:1}86%,100%{transform:scaleX(-1);opacity:0}}"
           ".star{transform-box:fill-box;transform-origin:center;animation:star 2.4s ease-in-out infinite}"
           "@keyframes star{50%{transform:scale(.4);opacity:.4}}")
    return svg, defs, css, round(48 * k)


CRESTS = {"wand": wand_crest, "daynight": day_night_crest, "hat": hat_crest, "book": book_crest}


def heading(title, tail, size, dark, icon="sparkle"):
    h = round(size * 1.6)
    if icon in CRESTS:
        crest, crest_defs, crest_css, crest_w = CRESTS[icon](h, dark)
        x0 = crest_w + 10
    else:
        crest = f'<path d="{sparkle(round(size * .38), h / 2, round(size * .34))}" fill="url(#brand)"/>'
        crest_defs, crest_css, x0 = "", "", round(size * .95)
    tail_size = round(size * .64)
    title_w = width("Oxanium", title, size)
    tail_w = width("Oxanium", tail, tail_size, 1) if tail else 0
    w = round(x0 + title_w + (14 + tail_w if tail else 0) + 12)
    base = round(h / 2 + size * .36)
    ink, muted = (NEON_CORE, INK3) if dark else (PLUM, PLUM_MUTED)
    glow = (f'<text class="t" x="{x0}" y="{base}" fill="{FUCHSIA}" opacity=".7" filter="url(#tight)">{xml(title)}</text>'
            if dark else "")
    tail_svg = f'<text class="s" x="{x0 + title_w + 14:.0f}" y="{base}" fill="{muted}">{xml(tail)}</text>' if tail else ""
    label = f"{title} · {tail}" if tail else title
    return f"""{svg_open(w, h, label)}
<defs>{BRAND}<filter id="tight" x="-10%" y="-40%" width="120%" height="180%"><feGaussianBlur stdDeviation="2"/></filter>{crest_defs}</defs>
<style>{font_face("Oxanium", title + tail)}.t{{font:500 {size}px 'Oxanium',sans-serif}}.s{{font:400 {tail_size}px 'Oxanium',sans-serif;letter-spacing:1px}}{crest_css}{REDUCED}</style>
{crest}
{glow}<text class="t" x="{x0}" y="{base}" fill="{ink}">{xml(title)}</text>{tail_svg}
</svg>"""


# ---------- project cards: one SVG per card that themes itself (they sit inside links)

CARDS = {  # file stem: tag, title, description, footer
    "day-job": ("DAY SHIFT · ALTEN", "Shopping at scale",
                "Feature lead on a retail app used by millions: shipped the new shopping cart, moved analytics to GA4 and brought my AI-agent harness into the team.",
                "CLIENT WORK · KOTLIN · COMPOSE"),
    "ariadna": ("NIGHT SHIFT · KMP + CMP · WIP", "ArIAdna",
                "A thread through the agent's labyrinth: a Compose Multiplatform app I'm building to turn live Claude Code sessions into UI, from sub-agents to refusals.",
                "WIP · ASK FOR A SNEAK PEEK →"),
    "harness": ("DAY & NIGHT · AGENT HARNESS · WIP", "Agent harness",
                "50+ typed skills, deterministic quality gates and LLM-as-judge evals. Audited on 8,466 real agent turns: caught 3 gates faking green.",
                "WIP · OPEN SOURCE WHEN IT'S READY →"),
    "lifelog": ("NIGHT SHIFT · KMP + ANDROID", "lifelog",
                "My Pensieve: a personal life log with cheap capture and deferred interpretation. Write it down now, make sense of it later.",
                "PRIVATE · PERSONAL PROJECT"),
    "rickmorty": ("UNRESTRICTED · KMP + CMP", "Rick & Morty KMP",
                  "Shared Compose Multiplatform UI for Android and iOS, across dimensions (and source sets).",
                  "PUBLIC · VIEW REPO →"),
    "chirp": ("UNRESTRICTED · KOTLIN + SPRING BOOT", "Chirp API",
              "Modular backend with user, chat and notification modules, wired together with Gradle convention plugins.",
              "PUBLIC · VIEW REPO →"),
}


def wrap(text, family, size, max_w):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if line and width(family, trial, size) > max_w:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line]


CARD_FILES = {  # file stem: file open in the editor tab, language in the status bar, private (padlock on the tab)
    "day-job": ("ShoppingAtScale.kt", "Kotlin", True),
    "ariadna": ("ArIAdna.kt", "Kotlin", True),
    "harness": ("AGENTS.md", "Markdown", True),
    "lifelog": ("Lifelog.kt", "Kotlin", True),
    "rickmorty": ("RickAndMorty.kt", "Kotlin", False),
    "chirp": ("ChirpApi.kt", "Kotlin", False),
}
CARD_DESC_PX, CARD_LEAD = 12, 19


def card(stem, tag, title, desc, foot):
    """A project as a file open in the editor: window dots, a tab with the file, the tag as a comment,
    the title as a heading, the description with a blinking caret, and the footer in the status bar.
    Always dark, like Angie.kt. Every card gets the height of the longest description so the grid lines up."""
    w, m = 440, 8
    fname, lang, private = CARD_FILES[stem]
    max_w = w - 2 * m - 60
    most = max(len(wrap(c[2], "JBMono", CARD_DESC_PX, max_w)) for c in CARDS.values())
    lines = wrap(desc, "JBMono", CARD_DESC_PX, max_w)
    h = m + 52 + (most + 1) * CARD_LEAD + 10 + 40
    code_x, num_x, top = 44, 30, m + 52
    rows = [("cmt", f"// {tag}"), ("ti", title)] + [("d", line) for line in lines]
    body, y = [], top
    for i, (cls, text) in enumerate(rows):
        y = top + i * CARD_LEAD + (6 if i >= 2 else 0) + (4 if i >= 1 else 0)
        body.append(f'<text class="num" x="{num_x}" y="{y}" text-anchor="end">{i + 1}</text>')
        if cls == "ti":
            body.append(f'<text x="{code_x}" y="{y + 2}"><tspan class="hash"># </tspan><tspan class="ti">{xml(text)}</tspan></text>')
        else:
            body.append(f'<text class="{cls}" x="{code_x}" y="{y}">{xml(text)}</text>')
    caret_x = code_x + width("JBMono", lines[-1], CARD_DESC_PX) + 2
    name_w = width("JBMono", fname, 11.5)
    tab_w = name_w + 40 + (14 if private else 0)
    lock = (f'<g transform="translate({m + 90 + name_w + 7:.1f} {m + 10})"><path d="M2.2 5.2V3.6a2.6 2.6 0 0 1 5.2 0V5.2" fill="none" stroke="#fdba74" stroke-width="1.3"/>'
            f'<rect x=".6" y="5" width="8.4" height="6.4" rx="1.4" fill="#fdba74"/><circle cx="4.8" cy="8" r=".9" fill="{AS["bg"]}"/></g>'
            if private else "")
    if lang == "Kotlin":
        file_icon = f'<g transform="translate({m + 72} {m + 11})"><path d="M0 0H11L5.5 5.5L11 11H0Z" fill="url(#kt)"/></g>'
    else:
        file_icon = (f'<g transform="translate({m + 70} {m + 12})" fill="none" stroke="#9da0a8" stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round">'
                     '<rect width="14" height="10" rx="2"/><path d="M2.5 7.5V2.5L4.75 5L7 2.5V7.5M10.5 2.5V7.5M8.8 5.8L10.5 7.5L12.2 5.8"/></g>')
    cta = foot.endswith("→")
    sb = h - m - 24
    return f"""{svg_open(w, h, f"{title}: {desc}")}
<defs><linearGradient id="kt" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#E44857"/><stop offset=".5" stop-color="#C711E1"/><stop offset="1" stop-color="#7F52FF"/></linearGradient>
<clipPath id="win"><rect x="{m}" y="{m}" width="{w - 2 * m}" height="{h - 2 * m}" rx="12"/></clipPath></defs>
<style>{font_face("JBMono", tag + desc + foot + fname + lang + "#0123456789")}{font_face("JBMonoItalic", "// " + tag)}{font_face("Oxanium", title)}
text{{font-family:'JBMono',monospace;font-variant-ligatures:none}}.num{{font-size:11px;fill:{AS["gutter"]}}}
.cmt{{font-family:'JBMonoItalic',monospace;font-size:11.5px;fill:{AS["cmt"]}}}
.hash{{font-size:20px;font-weight:700;fill:{FUCHSIA}}}.ti{{font:600 21px 'Oxanium',sans-serif;fill:{NEON_CORE}}}
.d{{font-size:{CARD_DESC_PX}px;fill:{AS["text"]}}}.tab{{font-size:11.5px;fill:{AS["tab"]}}}
.sb{{font-size:10.5px;letter-spacing:.5px;fill:{"#fdba74" if cta else "#9da0a8"}}}.lang{{font-size:10.5px;fill:#9da0a8}}
.caret{{animation:blink 1.1s steps(1) infinite}}@keyframes blink{{50%{{opacity:0}}}}{REDUCED}</style>
<g clip-path="url(#win)">
<rect x="{m}" y="{m}" width="{w - 2 * m}" height="{h - 2 * m}" fill="{AS["bg"]}"/>
<rect x="{m}" y="{m}" width="{w - 2 * m}" height="30" fill="{AS["sep"]}"/>
<circle cx="{m + 16}" cy="{m + 15}" r="4" fill="#ff5f57"/><circle cx="{m + 29}" cy="{m + 15}" r="4" fill="#febc2e"/><circle cx="{m + 42}" cy="{m + 15}" r="4" fill="#28c840"/>
<rect x="{m + 60}" y="{m + 4}" width="{tab_w:.0f}" height="26" rx="6" fill="{AS["bg"]}"/>
{file_icon}<text class="tab" x="{m + 90}" y="{m + 21}">{xml(fname)}</text>{lock}
<rect x="{m + 60}" y="{m + 28}" width="{tab_w:.0f}" height="2" fill="{FUCHSIA}"/>
{"".join(body)}
<rect class="caret" x="{caret_x:.1f}" y="{y - 11}" width="1.4" height="14" fill="{AS["text"]}"/>
<rect x="{m}" y="{sb}" width="{w - 2 * m}" height="24" fill="{AS["sep"]}"/>
<text class="sb" x="{m + 14}" y="{sb + 16}">{xml(foot)}</text>
<text class="lang" x="{w - m - 14}" y="{sb + 16}" text-anchor="end">{lang}</text>
</g>
<rect x="{m}" y="{m}" width="{w - 2 * m}" height="{h - 2 * m}" rx="12" fill="none" stroke="#393b40"/>
</svg>"""


# ---------- illustrations: GPT artwork in a neon frame (assets/illus-*.jpg)

ILLUSTRATIONS = {  # file stem: (alt text, displayed width, height)
    # crop of media-src/farewell-over-shoulder.webp at (38, 100, 1242, 399): from her hair to the coat collar
    "farewell": ("Anime illustration of Ángeles looking back over her shoulder on a rainy neon street. "
                 "$ ./gradlew nox ✓ Mischief managed.", 1000, 248),
}


NOX = ("$ ", "./gradlew ", "nox")  # the banner casts lumos; the farewell puts the light out
NOX_OUT = ("✓ ", "Mischief managed.")


def illustration(jpg, alt, w, h):
    """GPT artwork with rounded corners and no frame. The farewell closes the README like the Marauder's
    Map: a terminal line over the city lights, the banner's lumos answered with nox."""
    data = base64.b64encode(jpg.read_bytes()).decode()
    x, y1, y2 = 40, h / 2 - 8, h / 2 + 30
    out_px = 24
    cursor_x = x + len("".join(NOX_OUT)) * MONO_CW * out_px + 6
    mono = "".join(NOX) + "".join(NOX_OUT)
    return f"""{svg_open(w, h, alt)}
<defs><clipPath id="r"><rect width="{w}" height="{h}" rx="16"/></clipPath>
<linearGradient id="shade" x1="0" x2="1"><stop offset="0" stop-color="#07040f" stop-opacity=".78"/><stop offset=".42" stop-color="#07040f" stop-opacity=".35"/><stop offset=".55" stop-color="#07040f" stop-opacity="0"/></linearGradient>
<filter id="glow" x="-10%" y="-60%" width="120%" height="220%"><feGaussianBlur stdDeviation="4"/></filter></defs>
<style>{font_face("JBMono", mono)}
text{{font-family:'JBMono',monospace;font-variant-ligatures:none}}.cmd{{font-size:16px}}.out{{font-size:{out_px}px;font-weight:600}}
.caret{{animation:blink 1.1s steps(1) infinite}}@keyframes blink{{50%{{opacity:0}}}}{REDUCED}</style>
<g clip-path="url(#r)">
<image href="data:image/jpeg;base64,{data}" width="{w}" height="{h}"/>
<rect width="{w}" height="{h}" fill="url(#shade)"/>
</g>
<text class="cmd" x="{x}" y="{y1:.0f}"><tspan fill="{INK3}">{NOX[0]}</tspan><tspan fill="{INK2}">{NOX[1]}</tspan><tspan fill="{FUCHSIA}">{NOX[2]}</tspan></text>
<text class="out" x="{x}" y="{y2:.0f}" fill="{FUCHSIA}" opacity=".85" filter="url(#glow)">{"".join(NOX_OUT)}</text>
<text class="out" x="{x}" y="{y2:.0f}"><tspan fill="{MINT}">{NOX_OUT[0]}</tspan><tspan fill="{NEON_CORE}">{xml(NOX_OUT[1])}</tspan></text>
<rect class="caret" x="{cursor_x:.1f}" y="{y2 - 19:.0f}" width="11" height="23" fill="{MINT}" opacity=".85"/>
</svg>"""


# ---------- the Howler's letter: the long story, drawn so it can use our fonts and colours

STORY_SHOUT = (  # a Weasley-grade rant, "spoken" one line at a time in the same spot
    "YOU!",
    "HOW DARE YOU MERGE AN AI PR WITHOUT READING IT?!",
    "“ALL TESTS PASS”? WHERE. IS. THE. EVIDENCE?!",
    "MOCKS IN MY TEST SUITE! RUNBLOCKING IN A FLOW TEST!",
    "I AM ABSOLUTELY… DISGUSTED!",
)
STORY_HELLO = "…sorry. I promised you a polite Howler. Let me start again: hi, I'm Angie."
STORY = [
    "I started in **2018**, studying multiplatform app development. In 2020 I shipped my first Android code as an intern, "
    "and over the next two years I built an Android app **from scratch**: architecture, networking, persistence and release. "
    "That's where I learned to like things done properly.",
    "Since 2023 I've been at ALTEN, on an international fashion retail app **used by millions**. I took over the new "
    "shopping cart mid-rewrite and got it **to production**, moved the analytics from GA3 to GA4, and built the Python tool "
    "QA now uses to reconcile events from six analytics SDKs, and brought my AI-agent harness into the team's workflow. "
    "These days I'm on app health: R8 across the app and a high-precision hunt for dead code.",
    "Claude Code is my daily wand, at work and at home, and I'm building a harness around it: **50+ typed "
    "skills**, deterministic quality gates and LLM-as-judge evals. When I audited it on **8,466 real agent turns**, I caught "
    "three gates reporting green without evidence. Since then I ask every AI feature the same question: **what's the evidence?**",
    "That's why I'm building **ArIAdna**, a Compose Multiplatform app that shows what an agent is really doing. Fittingly, it's "
    "being built by one: an unattended agent on my home server opens the pull requests, and I review every one and own every decision.",
    "What I'm looking for: a **remote team** (I'm in Madrid) building Android or KMP products, or developer tooling, where AI "
    "is part of the craft rather than a buzzword. If that's you, send an owl.",
]
STORY_SIGN = "— Angie"
STORY_END = "The envelope bursts into harmless pink sparks."


def story_plain():
    return " ".join([" ".join(STORY_SHOUT), STORY_HELLO] + [para.replace("**", "") for para in STORY] + [STORY_SIGN])


def wrap_rich(text, family, size, max_w):
    """Wrap a paragraph with **highlights** and `code`. A word is a list of (text, style) pieces,
    so punctuation right after a highlight sticks to it instead of floating after a space."""
    words, prev_end_space, hl, code = [], True, False, False
    for token in re.split(r"(\*\*|`)", text):
        if token == "**":
            hl = not hl
            continue
        if token == "`":
            code = not code
            continue
        if not token:
            continue
        style = "code" if code else ("hl" if hl else "")
        parts = token.split()
        if not parts:
            prev_end_space = True
            continue
        if words and not prev_end_space and not token[0].isspace():
            words[-1].append((parts[0], style))
            parts = parts[1:]
        words += [[(w, style)] for w in parts]
        prev_end_space = token[-1].isspace()

    def plain(ws):
        return " ".join("".join(t for t, _ in w) for w in ws)

    lines, line = [], []
    for word in words:
        if line and width(family, plain(line + [word]), size) > max_w:
            lines.append(line)
            line = [word]
        else:
            line.append(word)
    return lines + [line]


def line_svg(x, y, line, cls="p"):
    pieces = []
    for i, word in enumerate(line):
        if i:
            pieces.append((" ", ""))
        pieces += word
    out = "".join(f'<tspan class="{style}">{xml(t)}</tspan>' if style else xml(t) for t, style in pieces)
    return f'<text class="{cls}" x="{x}" y="{y}" xml:space="preserve">{out}</text>'


def letter(envelope_jpg, burst_jpg):
    """The Howler opens: the envelope shakes, bursts into sparks over the burst scene, the shout slams in
    and the letter reveals line by line. Everything stays afterwards, so the letter can be reread."""
    w, pad, body_px, lead = 860, 48, 16, 27
    band_h, cx, cy = 360, 430, 190
    max_w = w - 2 * pad
    t_burst, t_shout = 2.0, 2.4
    shout_px = [34] + [24] * (len(STORY_SHOUT) - 2) + [34]  # it opens and closes loudest
    for i, line in enumerate(STORY_SHOUT):  # shrink a line only if it would not fit
        natural = width("Oxanium", line, shout_px[i], 1.5) * 1.05
        if natural > max_w:
            shout_px[i] = round(shout_px[i] * max_w / natural, 1)
    slot_y = band_h + 6  # every line is spoken in the same spot, like subtitles
    starts, t = [], t_shout
    for line in STORY_SHOUT:
        dur = .75 + .04 * len(line)  # long enough to read it
        starts.append((t, dur))
        t += dur + .08
    t_text = t + .1

    y = slot_y - 30
    parts = []
    y += 38
    parts.append(f'<text class="hello rev" style="animation-delay:{t_text:.2f}s" x="{pad}" y="{slot_y}">{xml(STORY_HELLO)}</text>')
    y = slot_y
    y += 22
    delay = t_text + .15
    for para in STORY:
        y += 18
        for line in wrap_rich(para, "JBMono", body_px, max_w):
            y += lead
            delay += .05
            parts.append(line_svg(pad, y, line).replace('<text class="p"', f'<text class="p rev" style="animation-delay:{delay:.2f}s"', 1))
    y += 40
    delay += .2
    parts.append(f'<text class="sign rev" style="animation-delay:{delay:.2f}s" x="{w - pad}" y="{y}" text-anchor="end">{xml(STORY_SIGN)}</text>')
    y += 36
    parts.append(f'<g class="rev" style="animation-delay:{delay + .2:.2f}s"><path class="spark" d="{sparkle(pad + 6, y - 5, 6)}"/>'
                 f'<text class="end" x="{pad + 20}" y="{y}">{xml(STORY_END)}</text></g>')
    h = y + pad - 8

    rnd = random.Random(9)
    sparks = []
    for i in range(22):
        ang = i / 22 * 6.283 + rnd.uniform(-.15, .15)
        dist = rnd.uniform(140, 330)
        dx, dy = dist * math.cos(ang), dist * math.sin(ang) * .62
        colour = rnd.choice([FUCHSIA, "#f9a8d4", ORANGE, "#fde68a"])
        sparks.append(f'<path class="sp" style="--dx:{dx:.0f}px;--dy:{dy:.0f}px" d="{sparkle(cx, cy, rnd.choice([5, 7, 9]))}" fill="{colour}"/>')

    def jpg(path):
        return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode()

    oxanium_text = "".join(STORY_SHOUT) + STORY_SIGN
    mono_text = STORY_HELLO + "".join(STORY).replace("**", "") + STORY_END
    theme = (f".bg{{fill:#fff}}.fs{{stop-color:#fff}}.shout{{fill:#b91c1c}}.hello{{fill:#6b5b7b}}.p{{fill:#3d2f4a}}.hl{{fill:#a21caf}}"
             f".sign{{fill:{PLUM}}}.end{{fill:#8a7a99}}.spark{{fill:{ORANGE}}}.halo{{opacity:.3}}.shoutglow{{display:none}}"
             f"@media (prefers-color-scheme:dark){{.bg{{fill:url(#paperDark)}}.fs{{stop-color:#180e1e}}.shout{{fill:#fecaca}}.hello{{fill:{INK3}}}"
             f".p{{fill:{INK2}}}.hl{{fill:#f0abfc}}.sign{{fill:{NEON_CORE}}}.end{{fill:{INK3}}}.halo{{opacity:.75}}.shoutglow{{display:inline}}}}")
    motion = f"""
.env{{opacity:0;transform-origin:{cx}px {cy}px;animation:env {t_burst - .3:.2f}s .3s both}}
@keyframes env{{0%{{opacity:1;transform:scale(1.06)}}12%{{transform:scale(1.06) translate(-3px,1px)}}24%{{transform:scale(1.06) translate(3px,-2px)}}
36%{{transform:scale(1.07) translate(-5px,2px)}}48%{{transform:scale(1.07) translate(5px,-3px)}}60%{{transform:scale(1.08) translate(-7px,3px)}}
72%{{transform:scale(1.09) translate(8px,-3px)}}84%{{opacity:1;transform:scale(1.1) translate(-9px,4px)}}100%{{opacity:0;transform:scale(1.35)}}}}
.burst{{transform-origin:{cx}px {cy}px;animation:burst .6s {t_burst:.2f}s both}}
@keyframes burst{{from{{opacity:0;transform:scale(1.2)}}to{{opacity:1;transform:scale(1)}}}}
.flash{{opacity:0;animation:flash .8s {t_burst - .05:.2f}s both}}
@keyframes flash{{0%{{opacity:0}}20%{{opacity:.92}}100%{{opacity:0}}}}
.sp{{opacity:0;transform-box:fill-box;transform-origin:center;animation:sp 1.2s {t_burst:.2f}s both}}
@keyframes sp{{0%{{opacity:1;transform:translate(0,0) scale(.4)}}70%{{opacity:1}}100%{{opacity:0;transform:translate(var(--dx),var(--dy)) scale(1.3)}}}}
.slam{{transform-box:fill-box;transform-origin:left center;animation:slam .55s {t_shout:.2f}s both}}
@keyframes slam{{0%{{opacity:0;transform:scale(1.9)}}65%{{opacity:1;transform:scale(.94)}}100%{{transform:scale(1)}}}}
.say{{opacity:0;transform-box:fill-box;transform-origin:left center;animation-name:say;animation-fill-mode:both;animation-timing-function:ease-out}}
@keyframes say{{0%{{opacity:0;transform:scale(1.35)}}10%{{opacity:1;transform:scale(1)}}14%{{transform:translate(-2px,1px)}}18%{{transform:translate(2px,-1px)}}22%{{transform:none}}82%{{opacity:1}}100%{{opacity:0}}}}
.rev{{animation:rev .6s both}}
@keyframes rev{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}"""
    shout = "".join(
        f'<g class="say" style="animation-delay:{start:.2f}s;animation-duration:{dur:.2f}s">'
        f'<text class="shout shoutglow" style="font-size:{px}px;fill:#ef4444" x="{pad}" y="{slot_y}" filter="url(#tight)">{xml(line)}</text>'
        f'<text class="shout" style="font-size:{px}px" x="{pad}" y="{slot_y}">{xml(line)}</text></g>'
        for line, px, (start, dur) in zip(STORY_SHOUT, shout_px, starts))
    band_w = w - 8
    return f"""{svg_open(w, h, "A letter from Ángeles", story_plain())}
<defs>
 <linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#ef4444"/><stop offset="1" stop-color="{ORANGE}"/></linearGradient>
 <linearGradient id="paperDark" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1a0f1f"/><stop offset="1" stop-color="#0e0918"/></linearGradient>
 <linearGradient id="fade" gradientUnits="userSpaceOnUse" x1="0" y1="{band_h - 150}" x2="0" y2="{band_h + 4}">
  <stop class="fs" offset="0" stop-opacity="0"/><stop class="fs" offset="1" stop-opacity="1"/></linearGradient>
 <clipPath id="card"><rect x="4" y="4" width="{band_w}" height="{h - 8}" rx="20"/></clipPath>
 <filter id="glow" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="3.5"/></filter>
 <filter id="tight" x="-10%" y="-40%" width="120%" height="180%"><feGaussianBlur stdDeviation="3"/></filter>
</defs>
<style>{font_face("Oxanium", oxanium_text)}{font_face("JBMono", mono_text)}
.shout{{font-family:'Oxanium',sans-serif;font-weight:700;letter-spacing:1.5px}}.hello{{font:500 17px 'JBMono',monospace}}
.p{{font:400 {body_px}px 'JBMono',monospace;font-variant-ligatures:none}}.hl{{font-weight:700}}.sign{{font:600 20px 'Oxanium',sans-serif}}

.end{{font:500 12.5px 'JBMono',monospace}}{motion}
{theme}{REDUCED}</style>
<rect class="bg" x="4" y="4" width="{band_w}" height="{h - 8}" rx="20"/>
<g clip-path="url(#card)">
 <image class="burst" href="{jpg(burst_jpg)}" x="4" y="4" width="{band_w}" height="{band_h}" preserveAspectRatio="xMidYMid slice"/>
 <image class="env" href="{jpg(envelope_jpg)}" x="4" y="4" width="{band_w}" height="{band_h}" preserveAspectRatio="xMidYMid slice"/>
 <rect class="flash" x="4" y="4" width="{band_w}" height="{band_h}" fill="#fff0fb"/>
 {"".join(sparks)}
 <rect x="4" y="4" width="{band_w}" height="{band_h + 2}" fill="url(#fade)"/>
</g>
<rect class="halo" x="4" y="4" width="{band_w}" height="{h - 8}" rx="20" fill="none" stroke="url(#g)" stroke-width="3" filter="url(#glow)"/>
<rect x="4" y="4" width="{band_w}" height="{h - 8}" rx="20" fill="none" stroke="url(#g)" stroke-width="1.5"/>
{shout}
{"".join(parts)}
</svg>"""


WAVE_CSS = (".wave{transform-box:fill-box;transform-origin:70% 85%;animation:wave 2.6s ease-in-out infinite}"
            "@keyframes wave{0%,60%,100%{transform:rotate(0)}10%{transform:rotate(16deg)}20%{transform:rotate(-8deg)}"
            "30%{transform:rotate(16deg)}40%{transform:rotate(-4deg)}50%{transform:rotate(10deg)}}")
HELLO_BASE, HELLO_H = 29, 35  # text sits near the bottom: GitHub lines inline images up by their bottom edge


def hello_hand():
    """The waving hand that opens the greeting. The README follows it with the spinning-earth GIF
    (smoother than anything drawn here) and then the title, so hand + world sit where the other
    headings have their crest."""
    return f"""{svg_open(28, HELLO_H, "👋")}
<style>.e{{font:24px {EMOJI}}}{WAVE_CSS}{REDUCED}</style>
<text class="e wave" x="1" y="{HELLO_BASE}">👋</text>
</svg>"""


def hello(dark):
    """The greeting title: every developer's first program, in the section headings' type (Oxanium 500, 26 px)."""
    title, size = "Hello, World!", 26
    x0 = 3  # hand (28) + globe GIF + 3 lands the text in the same column as the other headings' titles
    w = round(x0 + width("Oxanium", title, size) * 1.01 + 8)
    ink = NEON_CORE if dark else PLUM
    glow = (f'<text class="t" x="{x0}" y="{HELLO_BASE}" fill="{FUCHSIA}" opacity=".7" filter="url(#tight)">{title}</text>'
            if dark else "")
    return f"""{svg_open(w, HELLO_H, "Hello, World!")}
<defs><filter id="tight" x="-10%" y="-40%" width="120%" height="180%"><feGaussianBlur stdDeviation="2"/></filter></defs>
<style>{font_face("Oxanium", title)}.t{{font:500 {size}px 'Oxanium',sans-serif}}</style>
{glow}<text class="t" x="{x0}" y="{HELLO_BASE}" fill="{ink}">{title}</text>
</svg>"""


# ---------- the opening quote as a KDoc comment, and the intro set in JetBrains Mono

QUOTE_TITLE = "A thought for the wand-wielding dev:"
QUOTE = ("Code, in my not-so-humble opinion,", "is our most inexhaustible source of magic.")
QUOTE_AUTHOR = ("Not quite Dumbledore, but definitely", "his vibe in the Jetpack Compose Era.")

INTRO = [  # paragraphs, all in one style; **highlights** only for a few key words
    "Welcome to my **(code)** chamber of secrets. I'm Ángeles, Angie for short: an Android and Kotlin Multiplatform "
    "developer based in Madrid, with 5+ years of shipping real apps. By day I build with **Kotlin** and **Compose** "
    "on an app used by millions of shoppers, where a bug in the checkout is never a small bug.",
    "Day and night, I also build the wards that keep **AI coding agents** honest: specs they must follow, gates they "
    "can't charm their way past, and evidence behind every “tests pass”. At work I brought them into my team's "
    "workflow; at home they write code while I sleep. I wrote you a Howler with the rest of the story, just below. "
    "Don't worry: it's a polite one. Almost.",
]


def quote_plain():
    return f"{QUOTE_TITLE} “{' '.join(QUOTE)}” — {' '.join(QUOTE_AUTHOR)}"


def kdoc_quote():
    """Three quiet lines under the banner: a KDoc comment that never competes with it."""
    size, lead, pad = 13, 20, 10
    cw = MONO_CW * size
    rows = [  # list of (text, class) runs per line
        [("/** ", "c"), (QUOTE_TITLE, "c")],
        [(" *  ", "c"), ("“" + " ".join(QUOTE) + "”", "q")],
        [(" *  ", "c"), ("@author", "a"), (" " + " ".join(QUOTE_AUTHOR) + " */", "c")],
    ]
    longest = max(sum(len(t) for t, _ in row) for row in rows)
    w = round(2 * pad + longest * cw + 10)
    h = 2 * pad + lead * len(rows) - 4
    lines = []
    for i, row in enumerate(rows):
        y = pad + 13 + i * lead
        runs = "".join(f'<tspan class="{cls}">{xml(t)}</tspan>' for t, cls in row)
        lines.append(f'<text x="{pad}" y="{y}" xml:space="preserve">{runs}</text>')
    last = sum(len(t) for t, _ in rows[-1])
    caret_y = pad + 13 + (len(rows) - 1) * lead
    mono_text = "".join(t for row in rows for t, cls in row if cls == "a")
    italic_text = "".join(t for row in rows for t, cls in row if cls != "a")
    theme = (".c{fill:#6e7781}.q{fill:#a21caf}.a{fill:#c2410c}.caret{fill:#a21caf}"
             f"@media (prefers-color-scheme:dark){{.c{{fill:#8b949e}}.q{{fill:#f0abfc}}.a{{fill:{ORANGE}}}.caret{{fill:{FUCHSIA}}}}}")
    return f"""{svg_open(w, h, quote_plain())}
<style>{font_face("JBMono", mono_text)}{font_face("JBMonoItalic", italic_text)}
text{{font:400 {size}px 'JBMonoItalic',monospace;font-variant-ligatures:none}}
.a{{font-family:'JBMono',monospace;font-style:normal;font-weight:600}}.q{{font-weight:500}}
.caret{{animation:blink 1.1s steps(1) infinite}}@keyframes blink{{50%{{opacity:0}}}}
{theme}{REDUCED}</style>
{"".join(lines)}
<rect class="caret" x="{pad + last * cw + 3:.0f}" y="{caret_y - 11}" width="1.6" height="13"/>
</svg>"""


def intro_plain():
    return " ".join(text.replace("**", "") for text in INTRO)


def intro_panel():
    """The intro in JetBrains Mono, one style throughout, no card and no bar (the bar is the cards' accent);
    same margins as the night-shift text."""
    w, pad, tx, size, lead = 860, 6, 6, 16.5, 28
    max_w = w - tx - 8
    y, out = pad, []
    for i, para in enumerate(INTRO):
        y += 0 if i == 0 else 16
        for line in wrap_rich(para, "JBMono", size, max_w):
            y += lead
            out.append(line_svg(tx, y, line))
    h = y + pad + 10
    text_all = intro_plain()
    theme = (f".p{{fill:#3d2f4a}}.hl{{fill:#a21caf}}"
             f"@media (prefers-color-scheme:dark){{.p{{fill:{INK2}}}.hl{{fill:#f0abfc}}}}")
    return f"""{svg_open(w, h, text_all)}
<style>{font_face("JBMono", text_all)}
text{{font-family:'JBMono',monospace;font-variant-ligatures:none}}.p{{font-size:{size}px}}.hl{{font-weight:700}}
{theme}</style>
{"".join(out)}
</svg>"""


# ---------- the rest of the body text, in JetBrains Mono panels

NIGHT_COMMENT = "“With great power comes great responsibility.” — Uncle Ben, clearly talking about AI coding agents"
NIGHT = [
    "Two shifts, one obsession: **Kotlin that ships**, and **agents that can prove what they did**.",
    "The day shift taught me that production is the only reviewer that never sleeps. A checkout used by millions "
    "forgives nothing, so I test the boring paths, measure before I optimise and leave the code a little cleaner "
    "than I found it.",
    "The night shift is where I bring that discipline to AI. Agents write code while I sleep and open pull requests "
    "on my home server; the harness checks them before I do, whether they come from Claude Code, Codex CLI or "
    "Copilot, and I benchmark local models like Qwen and Gemma against the same gates.",
    "Both shifts end with the same question. Not “does it work?”, but **“how do we know?”**",
]
RULES_LEAD = "Clean and modular code from the very first incantation."
RULES = [
    "**Architecture that keeps the balance.** Clean Architecture, SOLID and MVI, with layer rules enforced by tests, "
    "not by code-review mood.",
    "**Testing potions for safe experiments.** Turbine for Flows, virtual time for coroutines, and fakes or mocks, "
    "whichever fits the test.",
    "**Modular by design.** Pure `commonMain`, platform code behind `expect`/`actual`, and convention plugins so many "
    "modules build like one.",
    "**Clarity above all.** Code is read far more often than it's written: by my team, by future me, and now by agents too.",
    "**Agents earn their merges.** Spec → contracts → code → gates → PR. No receipt, no “tests pass”.",
]
BODY_PX, BODY_LEAD = 16, 26


def strip_marks(text):
    return text.replace("**", "").replace("`", "")


def mono_panel(w, h, body, alt, text_all, italic_text="", defs="", bar=None, card=True):
    """Frame shared by the body panels; themes itself like the project cards. card=False drops the box."""
    bx, by, bh = bar if bar else (22, 30, h - 60)
    bar_svg = "" if bar is False else f'<rect x="{bx}" y="{by}" width="3" height="{bh}" rx="1.5" fill="url(#bar)"/>'
    theme = (f".pg{{stop-color:#ffffff}}.bg{{fill:#fff;stroke:#ead9f3}}.p{{fill:#3d2f4a}}.hl{{fill:#a21caf}}.code{{fill:#0e7490}}.cmt{{fill:#6e7781}}"
             f".lbl{{fill:#c2410c}}.bul{{fill:{FUCHSIA}}}.lead{{fill:{PLUM}}}.meta{{fill:#8a7a99}}.cta{{fill:#c2410c}}"
             f"@media (prefers-color-scheme:dark){{.pg{{stop-color:#0d1117}}.bg{{fill:url(#cardDark);stroke:#2e2442}}.p{{fill:{INK2}}}.hl{{fill:#f0abfc}}"
             f".code{{fill:#67e8f9}}.cmt{{fill:#8b949e}}.lbl{{fill:#fdba74}}.lead{{fill:{NEON_CORE}}}.meta{{fill:{INK3}}}.cta{{fill:#fdba74}}}}")
    italic_face = font_face("JBMonoItalic", italic_text) if italic_text else ""
    return f"""{svg_open(w, h, alt)}
<defs>
 <linearGradient id="bar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{FUCHSIA}"/><stop offset="1" stop-color="{ORANGE}"/></linearGradient>
 <linearGradient id="cardDark" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#170f26"/><stop offset="1" stop-color="#0e0918"/></linearGradient>
 {defs}
</defs>
<style>{font_face("JBMono", text_all)}{italic_face}
text{{font-family:'JBMono',monospace;font-size:{BODY_PX}px;font-variant-ligatures:none}}
.hl,.lbl{{font-weight:700}}.code{{font-weight:600}}.cmt{{font-family:'JBMonoItalic',monospace;font-size:13px}}
.lead{{font-size:22px;font-weight:700}}.meta{{font-size:13px;font-weight:500;letter-spacing:.5px}}.cta{{font-size:15.5px;font-weight:600}}
{theme}</style>
{f'<rect class="bg" x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="16"/>' if card else ""}
{body}
{bar_svg}
</svg>"""


def night_panel(jpg):
    """The drawing across the full width, no frame, its bottom melting into the page so it frames the text;
    then Uncle Ben on one line and the paragraphs."""
    w, tx = 860, 6
    img_h = round(w * 732 / 1200)  # from the nose down: lips, screens, hands and keyboard
    max_w = w - tx - 8
    data = base64.b64encode(jpg.read_bytes()).decode()
    out = [f'<image href="data:image/jpeg;base64,{data}" x="0" y="0" width="{w}" height="{img_h}" clip-path="url(#pic)"/>',
           f'<rect width="{w}" height="{img_h + 2}" fill="url(#melt)"/>', f'<rect width="{w}" height="{img_h}" fill="url(#sides)"/>']
    y = img_h - 40  # the quote sits on the fade, so the drawing frames it
    text_top = y - 14
    out.append(f'<text class="cmt" x="{tx}" y="{y}" xml:space="preserve">// {xml(NIGHT_COMMENT)}</text>')
    y += 8
    for para in NIGHT:
        y += 14
        for line in wrap_rich(para, "JBMono", BODY_PX, max_w):
            y += BODY_LEAD
            out.append(line_svg(tx, y, line))
    h = y + 14
    defs = (f'<clipPath id="pic"><rect width="{w}" height="{img_h}" rx="14"/></clipPath>'
            # the page colour (GitHub light / dark) so the drawing dissolves into it
            f'<linearGradient id="melt" gradientUnits="userSpaceOnUse" x1="0" y1="{img_h * .72:.0f}" x2="0" y2="{img_h}">'
            f'<stop class="pg" offset="0" stop-opacity="0"/><stop class="pg" offset=".6" stop-opacity=".75"/><stop class="pg" offset="1" stop-opacity="1"/></linearGradient>'
            f'<linearGradient id="sides" x1="0" x2="1"><stop class="pg" offset="0" stop-opacity=".55"/><stop class="pg" offset=".12" stop-opacity="0"/>'
            f'<stop class="pg" offset=".88" stop-opacity="0"/><stop class="pg" offset="1" stop-opacity=".55"/></linearGradient>')
    alt = NIGHT_COMMENT + " " + " ".join(strip_marks(t) for t in NIGHT)
    text_all = "".join(strip_marks(t) for t in NIGHT)
    return mono_panel(w, h, "".join(out), alt, text_all, italic_text="// " + NIGHT_COMMENT, defs=defs,
                      bar=False, card=False)


def rules_panel():
    """House guardrails: no card and no bar (the bar is the cards' accent), on the same left edge as the
    rest of the body text, with sparkles as bullets."""
    w, left = 860, 6
    tx = left + 26
    max_w = w - tx - 8
    y, out = 0, []
    for line in wrap_rich(f"**{RULES_LEAD}**", "JBMono", BODY_PX, w - left - 8):
        y += BODY_LEAD
        out.append(line_svg(left, y, line))
    y += 6
    for rule in RULES:
        y += 10
        for i, line in enumerate(wrap_rich(rule, "JBMono", BODY_PX, max_w)):
            y += BODY_LEAD
            if i == 0:
                out.append(f'<path class="bul" d="{sparkle(left + 7, y - 5, 6)}"/>')
            out.append(line_svg(tx, y, line))
    h = y + 10
    alt = " ".join([RULES_LEAD] + [strip_marks(r) for r in RULES])
    return mono_panel(w, h, "".join(out), alt, alt, bar=False, card=False)


# ---------- the character sheet: Kotlin, highlighted like an IDE in the neon palette

ANGIE_KT = """@OptIn(ExperimentalMagicApi::class)
object Angie : Technomancer {
    override val wand = Kotlin
    override val spareWands = listOf(Java, Python)
    override val wandCores = mapOf(
        "UI" to listOf("Jetpack Compose", "XML views", "Material 3"),
        "Multiplatform" to listOf("Kotlin Multiplatform", "Compose Multiplatform"),
        "Architecture" to listOf("Clean Architecture", "MVI", "MVVM", "SOLID", "modularization"),
        "Async" to listOf("Coroutines", "Flow", "LiveData"),
        "Networking" to listOf("Ktor", "Retrofit", "OkHttp"),
        "Persistence" to listOf("Room", "SQLite"),
        "DI" to listOf("Koin", "Hilt"),
        "Testing" to listOf("JUnit", "Turbine", "MockK", "Mockito", "Espresso", "Compose UI tests"),
        "Backend" to listOf("Spring Boot"),
        "Build" to listOf("Gradle", "convention plugins", "version catalogs", "R8"),
        "Analytics" to listOf("Firebase", "GA4"),
        "Tools" to listOf("Android Studio", "Git", "GitHub Actions", "Figma", "Postman"),
        "AI agents" to listOf("Claude Code", "Codex CLI", "GitHub Copilot", "local LLMs"),
        "Harness" to listOf("MCP servers", "agent skills", "quality gates", "LLM-as-judge evals"),
    )
    override val house: House = TODO("The Sorting Hat is still thinking")

    suspend fun review(pr: AgentPullRequest) {
        require(pr.hasEvidence) { "Where. Is. The. Evidence?!" }
        pr.merge()
    }
}"""
KT_KEYWORDS = {"object", "override", "val", "var", "fun", "suspend", "class", "return", "if", "else"}
KT_TOKEN = re.compile(r'(//.*$)|("(?:[^"\\]|\\.)*")|(@\w+)|([A-Za-z_]\w*)|(\s+)|(.)')
# Android Studio's default dark theme (IntelliJ New UI "Dark"), Kotlin colours
AS = dict(bg="#1E1F22", gutter="#4B5059", text="#BCBEC4", kw="#CF8E6D", str="#6AAB73", ann="#B3AE60", cmt="#7A7E85",
          fn="#56A8F5", prop="#C77DBB", line="#26282E", tab="#DFE1E5", accent="#3574F0", icon="#548AF7", sep="#2B2D30")


def highlight(line):
    """Kotlin highlighting the way Android Studio does it for this snippet:
    declarations, properties, stdlib calls in italics, annotations, strings and comments."""
    runs, prev = [], ""
    for m in KT_TOKEN.finditer(line):
        comment, string, annotation, ident, space, other = m.groups()
        rest = line[m.end():]
        if comment:
            runs.append((comment, "k-cmt"))
        elif string:
            runs.append((string, "k-str"))
        elif annotation:
            runs.append((annotation, "k-ann"))
        elif ident:
            if ident in KT_KEYWORDS:
                cls = "k-kw"
            elif prev in ("fun",):
                cls = "k-fn"
            elif prev in ("val", "var"):
                cls = "k-prop"
            elif runs and runs[-1][0] == "." and not rest.startswith("("):
                cls = "k-prop"
            elif (rest.startswith("(") or rest.startswith("<")) and not (runs and runs[-1][0] == "."):
                cls = "k-call"
            else:
                cls = "k-id"
            runs.append((ident, cls))
        else:
            runs.append((space or other, "k-id"))
        if ident:
            prev = ident
    return runs


def code_panel():
    """The character sheet as an Android Studio editor: tab with the Kotlin icon, gutter with
    line numbers and override markers, the current line highlighted and a blinking caret."""
    w, size, lead = 860, 13, 21
    cw = MONO_CW * size
    lines = ANGIE_KT.split("\n")
    tab_h, top = 34, 14
    num_x, icon_x, code_x = 34, 50, 66
    current = next(i for i, l in enumerate(lines) if "pr.merge()" in l)
    h = tab_h + top + lead * len(lines) + 14
    out = []
    for i, line in enumerate(lines):
        y = tab_h + top + 14 + i * lead
        if i == current:
            out.append(f'<rect x="0" y="{y - 15}" width="{w}" height="{lead}" fill="{AS["line"]}"/>')
        out.append(f'<text class="k-n" x="{num_x}" y="{y}" text-anchor="end">{i + 1}</text>')
        if line.lstrip().startswith("override"):
            out.append(f'<g transform="translate({icon_x} {y - 5})" fill="none" stroke="{AS["icon"]}" stroke-width="1.2" stroke-linecap="round">'
                       f'<circle r="5.5"/><path d="M0 2.6V-2.6M-2.1-.5L0-2.6L2.1-.5"/></g>')
        spans = "".join(f'<tspan class="{cls}">{xml(t)}</tspan>' for t, cls in highlight(line))
        out.append(f'<text x="{code_x}" y="{y}" xml:space="preserve">{spans}</text>')
    caret_x = code_x + len(lines[current]) * cw + 1
    caret_y = tab_h + top + 14 + current * lead
    text_all = ANGIE_KT + "0123456789Angie.kt"
    italic = "".join(t for line in lines for t, cls in highlight(line) if cls in ("k-cmt", "k-call"))
    kotlin_icon = ('<g transform="translate(14 10)"><defs><linearGradient id="kt" x1="0" y1="1" x2="1" y2="0">'
                   '<stop offset="0" stop-color="#E44857"/><stop offset=".5" stop-color="#C711E1"/><stop offset="1" stop-color="#7F52FF"/>'
                   '</linearGradient></defs><path d="M0 0H14L7 7L14 14H0Z" fill="url(#kt)"/></g>')
    return f"""{svg_open(w, h, " ".join(l.strip() for l in lines if l.strip()))}
<style>{font_face("JBMono", text_all)}{font_face("JBMonoItalic", italic)}
text{{font:400 {size}px 'JBMono',monospace;font-variant-ligatures:none;fill:{AS["text"]}}}
.k-n{{font-size:12.5px;fill:{AS["gutter"]}}}.tabtxt{{font-size:13px;fill:{AS["tab"]}}}
.k-kw{{fill:{AS["kw"]}}}.k-str{{fill:{AS["str"]}}}.k-ann{{fill:{AS["ann"]}}}.k-fn{{fill:{AS["fn"]}}}.k-prop{{fill:{AS["prop"]}}}
.k-cmt{{fill:{AS["cmt"]};font-family:'JBMonoItalic',monospace}}.k-call{{font-family:'JBMonoItalic',monospace}}
.caret{{animation:blink 1.1s steps(1) infinite}}@keyframes blink{{50%{{opacity:0}}}}
{REDUCED}</style>
<rect width="{w}" height="{h}" rx="10" fill="{AS["bg"]}"/>
<rect y="{tab_h - 1}" width="{w}" height="1" fill="{AS["sep"]}"/>
{kotlin_icon}<text class="tabtxt" x="36" y="22">Angie.kt</text>
<rect x="8" y="{tab_h - 3}" width="98" height="2" rx="1" fill="{AS["accent"]}"/>
{"".join(out)}
<rect class="caret" x="{caret_x:.1f}" y="{caret_y - 13}" width="1.6" height="17" fill="{AS["text"]}"/>
</svg>"""


# ---------- buttons and divider

EMOJI = "'Apple Color Emoji','Segoe UI Emoji','Noto Color Emoji',sans-serif"


def button(emoji, label, sub, c1, c2):
    """Neon outline with its own gradient, a title and a subtitle.
    Themed inside the SVG because GitHub breaks <picture> inside links."""
    title_px, sub_px, track, h = 15, 11.5, 1.5, 58
    text_w = max(width("Oxanium", label, title_px, track), width("JBMono", sub, sub_px))
    w = round(52 + text_w + 22)
    box = f'x="3" y="3" width="{w - 6}" height="{h - 6}" rx="12"'
    theme = (f".bg{{fill:#fff}}.l{{fill:{PLUM}}}.s{{fill:#6b5b7b}}.halo{{opacity:.35}}"
             f"@media (prefers-color-scheme:dark){{.bg{{fill:#0b0816}}.l{{fill:{INK}}}.s{{fill:{VIOLET}}}.halo{{opacity:.75}}}}")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{xml(label.title())}: {xml(sub)}">
<defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>
<filter id="glow" x="-10%" y="-40%" width="120%" height="180%"><feGaussianBlur stdDeviation="3"/></filter></defs>
<style>{font_face("Oxanium", label)}{font_face("JBMono", sub)}
.l{{font:700 {title_px}px 'Oxanium',sans-serif;letter-spacing:{track}px}}.s{{font:500 {sub_px}px 'JBMono',monospace}}.e{{font:20px {EMOJI}}}
.pulse{{animation:p 3s ease-in-out infinite}}@keyframes p{{50%{{stroke-opacity:.5}}}}{theme}{REDUCED}</style>
<rect class="bg" {box}/>
<rect class="halo" {box} fill="none" stroke="url(#g)" stroke-width="3" filter="url(#glow)"/>
<rect class="pulse" {box} fill="none" stroke="url(#g)" stroke-width="2"/>
<text class="e" x="18" y="{h / 2 + 7}">{emoji}</text>
<text class="l" x="52" y="{h / 2 - 2}">{xml(label)}</text>
<text class="s" x="52" y="{h / 2 + 14}">{xml(sub)}</text>
</svg>"""


def howler():
    """The summary of the <details> that holds the long story: a red envelope that shakes now and then,
    no box around it, and the words in a red-to-orange gradient."""
    label, sub = "OPEN THE HOWLER", "my story · read it, or hear it in my voice"
    title_px, sub_px, h = 20, 12, 104
    tx = 118
    text_w = max(width("Oxanium", label, title_px, 2) * 1.04, len(sub) * MONO_CW * sub_px)
    w = round(tx + text_w + 14)
    theme = (".r1{stop-color:#dc2626}.r2{stop-color:#ea580c}.tglow{display:none}"
             "@media (prefers-color-scheme:dark){.r1{stop-color:#ef4444}.r2{stop-color:#fb923c}.tglow{display:inline}}")
    return f"""{svg_open(w, h, "Open the Howler: my story, read it or hear it in my voice")}
<defs>
 <linearGradient id="ink" gradientUnits="userSpaceOnUse" x1="{tx}" y1="0" x2="{tx + text_w:.0f}" y2="0"><stop class="r1" offset="0"/><stop class="r2" offset="1"/></linearGradient>
 <linearGradient id="paper" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ef4444"/><stop offset="1" stop-color="#991b1b"/></linearGradient>
 <filter id="glow" x="-10%" y="-40%" width="120%" height="180%"><feGaussianBlur stdDeviation="3"/></filter>
</defs>
<style>{font_face("Oxanium", label)}{font_face("JBMono", sub)}
.l{{font:700 {title_px}px 'Oxanium',sans-serif;letter-spacing:2px}}.s{{font:600 {sub_px}px 'JBMono',monospace}}
.shake{{transform-origin:64px 56px;animation:shake 4.5s ease-in-out infinite}}
@keyframes shake{{0%,78%,100%{{transform:rotate(0)}}80%{{transform:rotate(-7deg)}}82%{{transform:rotate(6deg)}}84%{{transform:rotate(-5deg)}}86%{{transform:rotate(4deg)}}88%{{transform:rotate(-2deg)}}90%{{transform:rotate(0)}}}}
.puff{{animation:puff 4.5s ease-out infinite;opacity:0}}
@keyframes puff{{0%,80%{{opacity:0;transform:translateY(0)}}86%{{opacity:.9}}100%{{opacity:0;transform:translateY(-14px)}}}}
{theme}{REDUCED}</style>
<g class="shake">
 <rect x="26" y="30" width="76" height="52" rx="6" fill="url(#paper)"/>
 <path d="M28 34 L64 62 L100 34" fill="none" stroke="#7f1d1d" stroke-width="2.5" stroke-linejoin="round"/>
 <path d="M28 80 L54 56 M100 80 L74 56" stroke="#7f1d1d" stroke-width="1.5" opacity=".55"/>
 <circle cx="64" cy="61" r="9" fill="#fbbf24"/><circle cx="64" cy="61" r="6.5" fill="#b45309"/>
 <path d="M60.5 58v6M67.5 58v6M60.5 61h7" stroke="#fde68a" stroke-width="1.6" stroke-linecap="round"/>
</g>
<g fill="{ORANGE}"><circle class="puff" cx="44" cy="26" r="2.5"/><circle class="puff" style="animation-delay:.15s" cx="84" cy="24" r="2"/><path class="puff" style="animation-delay:.3s" d="{sparkle(64, 20, 4)}"/></g>
<text class="l tglow" x="{tx}" y="{h / 2 - 2}" fill="url(#ink)" opacity=".55" filter="url(#glow)">{label}</text>
<text class="l" x="{tx}" y="{h / 2 - 2}" fill="url(#ink)">{label}</text>
<text class="s" x="{tx}" y="{h / 2 + 20}" fill="url(#ink)">{xml(sub)}</text>
</svg>"""


def divider():
    w, h, c = 720, 28, 360
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="divider">
<defs>{BRAND}
 <linearGradient id="l" gradientUnits="userSpaceOnUse" x1="40" y1="0" x2="{c - 18}" y2="0"><stop offset="0" stop-color="{FUCHSIA}" stop-opacity="0"/><stop offset="1" stop-color="{FUCHSIA}" stop-opacity=".75"/></linearGradient>
 <linearGradient id="r" gradientUnits="userSpaceOnUse" x1="{c + 18}" y1="0" x2="{w - 40}" y2="0"><stop offset="0" stop-color="{ORANGE}" stop-opacity=".75"/><stop offset="1" stop-color="{ORANGE}" stop-opacity="0"/></linearGradient>
 <filter id="blur3" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="3"/></filter>
</defs>
<style>.tw{{animation:tw 4s ease-in-out infinite}}@keyframes tw{{50%{{opacity:.45}}}}{REDUCED}</style>
<line x1="40" y1="{h / 2}" x2="{c - 18}" y2="{h / 2}" stroke="url(#l)"/>
<line x1="{c + 18}" y1="{h / 2}" x2="{w - 40}" y2="{h / 2}" stroke="url(#r)"/>
<g class="tw"><path d="{sparkle(c, h / 2, 10)}" fill="url(#brand)" filter="url(#blur3)" opacity=".7"/><path d="{sparkle(c, h / 2, 9)}" fill="url(#brand)"/></g>
</svg>"""


def main():
    out = pathlib.Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    portrait = pathlib.Path(sys.argv[2])
    mime = "image/png" if portrait.suffix.lower() == ".png" else "image/jpeg"
    face = f"data:{mime};base64,{base64.b64encode(portrait.read_bytes()).decode()}"

    files = {
        "banner-dark.svg": banner(face, "dark"),
        "banner-light.svg": banner(face, "light"),
        "btn-cv.svg": button("📜", "UNROLL THE SCROLL", "CV · PDF download", FUCHSIA, ORANGE),
        "btn-linkedin.svg": button("🔗", "LINKEDIN", "connect · network", "#22d3ee", "#a78bfa"),
        "btn-owl.svg": button("🦉", "OWL POST", "angelesmafon@gmail.com", ORANGE, "#22d3ee"),
        "divider.svg": divider(),
        "btn-howler.svg": howler(),
        "howler-letter.svg": letter(out / "howler-envelope.jpg", out / "howler-burst.jpg"),
    }
    for stem, (alt, w, h) in ILLUSTRATIONS.items():
        files[f"illus-{stem}.svg"] = illustration(out / f"illus-{stem}.jpg", alt, w, h)
    for stem, args in CARDS.items():
        files[f"card-{stem}.svg"] = card(stem, *args)
    for theme in ("dark", "light"):
        files[f"h-hello-{theme}.svg"] = hello(theme == "dark")
    files["h-hello-hand.svg"] = hello_hand()
    files["quote-thought.svg"] = kdoc_quote()
    files["intro.svg"] = intro_panel()
    files["night-shift.svg"] = night_panel(out / "illus-night-shift.jpg")
    files["house-rules.svg"] = rules_panel()
    files["angie-kt.svg"] = code_panel()
    for stem, (title, tail, size, *icon) in HEADINGS.items():
        for theme in ("dark", "light"):
            files[f"h-{stem}-{theme}.svg"] = heading(title, tail, size, theme == "dark", *icon)
    for name, svg in files.items():
        (out / name).write_text(svg, encoding="utf-8")
        print(f"{name:26} {len(svg.encode()) / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
