"""Render the LinkedIn cover image (1584 × 396, saved at 2× for sharp screens) from the README banner's pieces.

Same neon city, KOTLIN sign, terminal and portrait as tools/banner.py, but static and without the name:
LinkedIn prints the name right below the cover. The profile photo covers the bottom-left corner
(x < ~400, y > ~205), so the text keeps to the top line and the terminal sits right of the photo.

No fontTools here: the output is a PNG, so the full TTFs go in as they are, and headless Chrome
draws the SVG.

usage (from the repo root):  python3 tools/linkedin_banner.py assets [--no-portrait]
needs:                       Google Chrome or Chromium. On macOS it uses the app in /Applications;
                             elsewhere it looks for google-chrome / chromium on the PATH. CHROME=<path>
                             overrides both.
"""
import base64, os, pathlib, random, shutil, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
W, H, SCALE = 1584, 396, 2

FUCHSIA, ORANGE, MINT = "#e879f9", "#fb923c", "#86efac"
INK2, INK3 = "#bdb3cf", "#857a99"

TAGLINE = "ANDROID · COMPOSE MULTIPLATFORM · AI AGENT TOOLING"
CMD = ("$ ", "./gradlew ", "lumos", " --target=commonMain")
RESULT = "✓ BUILD SUCCESSFUL · 0 mocks harmed"

TAG_X, TAG_Y, TAG_PX = 96, 86, 24          # one quiet line on top: ~12 px on a desktop profile
TERM_X, TERM_Y, TERM_PX = 430, 150, 24     # the terminal is the hero, right of the profile photo
PORTRAIT_X = 1114                          # where the portrait starts fading in


def b64(path):
    return base64.b64encode(path.read_bytes()).decode()


def skyline(seed, base, var, color, win_op):
    r = random.Random(seed)
    blocks, wins = [], []
    x = -10
    while x < W:
        w, h = r.randint(34, 90), base + r.randint(0, var)
        blocks.append(f'<rect x="{x}" y="{H - h}" width="{w}" height="{h}"/>')
        for wy in range(H - h + 10, H - 6, 13):
            for wx in range(x + 6, x + w - 6, 10):
                if r.random() < .09:
                    c = r.choice(["#fdba74", "#fdba74", "#67e8f9", "#f0abfc"])
                    wins.append(f'<rect x="{wx}" y="{wy}" width="3" height="5" fill="{c}" opacity="{win_op * r.uniform(.4, 1):.2f}"/>')
        x += w + r.randint(2, 8)
    return f'<g fill="{color}">{"".join(blocks)}</g><g>{"".join(wins)}</g>'


def rain(seed, n=100):
    r = random.Random(seed)
    lines = []
    for _ in range(n):
        x, y, l = r.uniform(0, W), r.uniform(0, H), r.uniform(12, 30)
        lines.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x - 4:.0f}" y2="{y + l:.0f}"/>')
    return f'<g stroke="#c7d2fe" stroke-opacity=".11" stroke-width="1">{"".join(lines)}</g>'


def neon(cls, x, y, text, core, glow, anchor="start"):
    a = f'class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}"'
    return (f'<text {a} fill="{glow}" opacity=".95" filter="url(#neonTight)">{text}</text>'
            f'<text {a} fill="{core}">{text}</text>')


def sign(sx, top=46, step=46, letter_px=32):
    tube_w, tube_h = 56, step * 6 + 22
    letters = "".join(neon("sign", sx + tube_w / 2, top + 40 + i * step, ch, "#ffe4c7", ORANGE, anchor="middle")
                      for i, ch in enumerate("KOTLIN"))
    return (f'<rect x="{sx}" y="{top}" width="{tube_w}" height="{tube_h}" rx="14" fill="none" stroke="{ORANGE}" stroke-width="4" opacity=".5" filter="url(#neonTight)"/>'
            f'<rect x="{sx}" y="{top}" width="{tube_w}" height="{tube_h}" rx="14" fill="none" stroke="#ffd2a8" stroke-width="1.8"/>'
            f'<style>.sign{{font:400 {letter_px}px "Oxanium",sans-serif}}</style>{letters}')


def terminal(bx, by, px):
    cw = px * 0.6  # JetBrains Mono advance: 600/1000 em
    w, h = round(len("".join(CMD)) * cw + 2 * px * 1.1), round(px * 5.1)
    return (f'<style>.mono{{font:400 {px}px "JBMono",monospace;font-variant-ligatures:none}}</style>'
            f'<rect x="{bx}" y="{by}" width="{w}" height="{h}" rx="12" fill="#0a0714" fill-opacity=".78" stroke="#fff" stroke-opacity=".1"/>'
            f'<circle cx="{bx + 22}" cy="{by + 20}" r="5" fill="#ff5f57" opacity=".75"/><circle cx="{bx + 40}" cy="{by + 20}" r="5" fill="#febc2e" opacity=".75"/><circle cx="{bx + 58}" cy="{by + 20}" r="5" fill="#28c840" opacity=".75"/>'
            f'<text class="mono" x="{bx + px * 1.1:.0f}" y="{by + px * 2.8:.0f}"><tspan fill="{INK3}">{CMD[0]}</tspan><tspan fill="{INK2}">{CMD[1]}</tspan><tspan fill="{FUCHSIA}">{CMD[2]}</tspan><tspan fill="{INK3}">{CMD[3]}</tspan></text>'
            f'<text class="mono" x="{bx + px * 1.1:.0f}" y="{by + px * 4.25:.0f}" fill="{MINT}" fill-opacity=".9">{RESULT}</text>')


def cover(with_portrait):
    ox = b64(HERE / "fonts/Oxanium[wght].ttf")
    jb = b64(HERE / "fonts/JetBrainsMono[wght].ttf")
    px = PORTRAIT_X
    bokeh = [("#22d3ee", .22, 718, 40, 150, 60), (FUCHSIA, .34, 990, 198, 120, 140), (ORANGE, .2, 446, 406, 300, 100)]
    if not with_portrait:
        bokeh.append((FUCHSIA, .30, 1430, 190, 160, 160))
    glows = "".join(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{c}" fill-opacity="{o}"/>' for c, o, cx, cy, rx, ry in bokeh)
    portrait = ""
    if with_portrait:
        pw = W - px
        portrait = (f'<image href="data:image/jpeg;base64,{b64(ROOT / "assets/portrait.jpg")}" x="{px}" y="-24" '
                    f'width="{pw}" height="{pw}" preserveAspectRatio="xMidYMid slice" mask="url(#fade)"/>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs>
 <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#07050d"/><stop offset=".6" stop-color="#140b24"/><stop offset="1" stop-color="#22103a"/></linearGradient>
 <linearGradient id="fadeX" gradientUnits="userSpaceOnUse" x1="{px}" y1="0" x2="{px + 220}" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff"/></linearGradient>
 <mask id="fade" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><rect x="{px}" width="{W - px}" height="{H}" fill="url(#fadeX)"/></mask>
 <filter id="neonTight" x="-10%" y="-40%" width="120%" height="180%"><feGaussianBlur stdDeviation="2.4"/></filter>
 <filter id="soft" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="42"/></filter>
 <filter id="grain" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" stitchTiles="stitch"/>
  <feColorMatrix type="saturate" values="0"/>
  <feComponentTransfer><feFuncA type="table" tableValues="0 .09"/></feComponentTransfer>
 </filter>
</defs>
<style>
 @font-face{{font-family:"Oxanium";src:url(data:font/ttf;base64,{ox}) format("truetype");font-weight:100 900}}
 @font-face{{font-family:"JBMono";src:url(data:font/ttf;base64,{jb}) format("truetype");font-weight:100 900}}
 .tag{{font:500 {TAG_PX}px "JBMono",monospace;letter-spacing:4px}}
</style>
<rect width="{W}" height="{H}" fill="url(#sky)"/>
<g filter="url(#soft)">{glows}</g>
{skyline(1, 110, 130, "#100a1e", .5)}
{skyline(2, 40, 80, "#170e2b", .75)}
{portrait}
{sign(1068 if with_portrait else 1430)}
{rain(5)}
{neon("tag", TAG_X, TAG_Y, TAGLINE, "#f5d0fe", FUCHSIA)}
{terminal(TERM_X, TERM_Y, TERM_PX)}
<rect width="{W}" height="{H}" filter="url(#grain)"/>
</svg>"""


def chrome():
    for candidate in (os.environ.get("CHROME"), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                      shutil.which("google-chrome"), shutil.which("chromium"), shutil.which("chromium-browser")):
        if candidate and pathlib.Path(candidate).exists():
            return candidate
    sys.exit("Chrome/Chromium not found: set CHROME=<path to the browser binary>")


def render(svg, png):
    with tempfile.TemporaryDirectory() as tmp:
        page = pathlib.Path(tmp) / "cover.html"
        page.write_text(f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;background:#000}}svg{{display:block}}</style>{svg}',
                        encoding="utf-8")
        subprocess.run([chrome(), "--headless", "--disable-gpu", "--hide-scrollbars", f"--force-device-scale-factor={SCALE}",
                        f"--window-size={W},{H}", "--virtual-time-budget=3000", f"--user-data-dir={tmp}/profile",
                        f"--screenshot={png}", page.as_uri()], check=True, capture_output=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    out = pathlib.Path(sys.argv[1])
    with_portrait = "--no-portrait" not in sys.argv[2:]
    png = (out / ("linkedin-banner.png" if with_portrait else "linkedin-banner-no-portrait.png")).resolve()
    render(cover(with_portrait), png)
    print(f"wrote {png} ({W * SCALE}×{H * SCALE})")
