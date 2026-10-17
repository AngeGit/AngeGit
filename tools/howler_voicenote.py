"""The Howler as a voice note: a slim player strip with the envelope and the waveform of the recording
filling up as it plays. GitHub can only play audio inside a video, so this is the least visual video that
still plays the voice; it also starts muted there, hence the "turn the sound on" hint. The bottom of the
strip is left empty because GitHub draws its own controls (and the time) over it.

usage (from the repo root):
  python3 tools/howler_voicenote.py media-src/howler-voz.m4a media-src/howler-voicenote.mp4
needs: ffmpeg on PATH, pip install pillow
"""
import argparse, array, math, pathlib, subprocess, sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
MEDIA = HERE.parent / "media-src"
OXANIUM = HERE / "fonts/Oxanium[wght].ttf"
MONO = HERE / "fonts/JetBrainsMono[wght].ttf"
W, H, FPS = 1280, 320, 30
PAGE = (13, 17, 23)  # GitHub's dark page, around the card
FUCHSIA, ORANGE, RED = (232, 121, 249), (251, 146, 60), (239, 68, 68)
DIM = (58, 47, 74)
TAIL = 1.8  # seconds after the last word


def font(path, size, weight):
    f = ImageFont.truetype(str(path), size)
    f.set_variation_by_axes([weight])
    return f


def samples(audio, rate=16000):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(audio), "-ac", "1", "-ar", str(rate), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    a = array.array("h")
    a.frombytes(raw)
    return a, rate


def rms(a, i, j):
    seg = a[max(0, i):max(i + 1, j)]
    return math.sqrt(sum(x * x for x in seg) / max(1, len(seg))) / 32768


def mix(c1, c2, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(c1, c2))


def speech_end(a, rate, floor=.012):
    """Last moment the voice is clearly above the room noise."""
    win = rate // 10
    last = 0
    for i in range(0, len(a), win):
        if rms(a, i, i + win) > floor:
            last = i + win
    return last / rate


def card_base(total):
    """Everything that doesn't move: the card, its border and the envelope avatar."""
    img = Image.new("RGB", (W, H), PAGE)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle((14, 14, W - 14, H - 14), 34, outline=RED + (255,), width=6)
    img.paste(glow.filter(ImageFilter.GaussianBlur(8)), (0, 0), glow.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(img)
    for y in range(18, H - 18):  # paper: dark plum, a touch lighter at the top
        d.line([(18, y), (W - 18, y)], fill=mix((30, 17, 36), (14, 9, 24), (y - 18) / (H - 36)))
    border = Image.new("L", (W, H), 0)
    ImageDraw.Draw(border).rounded_rectangle((14, 14, W - 14, H - 14), 34, outline=255, width=3)
    ramp = Image.linear_gradient("L").rotate(90).resize((W, H))
    img.paste(Image.composite(Image.new("RGB", (W, H), ORANGE), Image.new("RGB", (W, H), RED), ramp), (0, 0), border)
    corners = Image.new("L", (W, H), 255)  # page colour outside the rounded card
    ImageDraw.Draw(corners).rounded_rectangle((14, 14, W - 14, H - 14), 34, fill=0)
    img.paste(PAGE, (0, 0), corners)
    env = Image.open(MEDIA / "howler-envelope.webp").convert("RGB")
    side = min(env.size) * .62
    cx, cy = env.size[0] * .5, env.size[1] * .48
    env = env.crop((cx - side / 2, cy - side / 2, cx + side / 2, cy + side / 2)).resize((196, 196), Image.LANCZOS)
    mask = Image.new("L", (196, 196), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 195, 195), fill=255)
    img.paste(env, (52, 62), mask)
    return img


def speaker(d, x, y, colour):
    """A small speaker with sound waves, drawn (no emoji font needed)."""
    d.polygon([(x, y + 7), (x + 7, y + 7), (x + 15, y), (x + 15, y + 26), (x + 7, y + 19), (x, y + 19)], fill=colour)
    for r in (7, 13):
        d.arc((x + 15 - r, y + 13 - r, x + 15 + r, y + 13 + r), -50, 50, fill=colour, width=3)


def render(audio, out, work):
    a, rate = samples(audio)
    total = min(len(a) / rate, speech_end(a, rate) + TAIL)
    x0, x1, mid, amp = 300, 1220, 168, 52  # waveform box; the bottom 70 px stay free for GitHub's own controls
    bar, gap = 5, 3
    nbars = (x1 - x0) // (bar + gap)
    levels = [rms(a, int(i / nbars * total * rate), int((i + 1) / nbars * total * rate)) for i in range(nbars)]
    top = max(levels) or 1
    levels = [max(.06, math.sqrt(v / top)) for v in levels]
    base = card_base(total)
    title, small = font(OXANIUM, 38, 700), font(MONO, 22, 500)
    frames = round(total * FPS)
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-i", str(audio),
                            "-filter_complex", f"[1:a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,atrim=0:{total:.3f},"
                                               f"afade=out:st={total - 0.6:.3f}:d=0.6[a]",
                            "-map", "0:v", "-map", "[a]", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "slow",
                            "-crf", "24", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "128k",
                            str(out)], stdin=subprocess.PIPE)
    for f in range(frames):
        t = f / FPS
        img = base.copy()
        d = ImageDraw.Draw(img)
        level = min(1, rms(a, int((t - .05) * rate), int((t + .05) * rate)) / top * 1.6)
        ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))  # the envelope glows while the voice is loud
        ImageDraw.Draw(ring).ellipse((44, 54, 256, 266), outline=FUCHSIA + (round(80 + 175 * level),), width=4 + round(5 * level))
        img.paste(ring.filter(ImageFilter.GaussianBlur(3 + 4 * level)), (0, 0), ring.filter(ImageFilter.GaussianBlur(3 + 4 * level)))
        d.ellipse((50, 60, 250, 260), outline=mix(RED, FUCHSIA, level), width=3)
        d.text((x0, 52), "THE POLITE HOWLER", font=title, fill=mix(RED, ORANGE, .4))
        played = t / total
        for i, v in enumerate(levels):
            bx = x0 + i * (bar + gap)
            h = v * amp
            colour = mix(FUCHSIA, ORANGE, i / nbars) if (i + .5) / nbars <= played else DIM
            d.rounded_rectangle((bx, mid - h, bx + bar, mid + h), 2, fill=colour)
        # top right, clear of GitHub's controls (which also show the time); it pulses for the first seconds
        hint = (233, 213, 255) if t >= 6 or int(t * 2) % 2 == 0 else (150, 140, 170)
        label = "turn the sound on"
        speaker(d, x1 - small.getlength(label) - 34, 54, hint)
        d.text((x1, 76), label, font=small, fill=hint, anchor="rs")
        enc.stdin.write(img.tobytes())
    enc.stdin.close()
    if enc.wait():
        sys.exit("ffmpeg failed")
    print(f"{out}  {pathlib.Path(out).stat().st_size / 1e6:.1f} MB  {total:.1f} s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("out")
    args = ap.parse_args()
    render(pathlib.Path(args.audio), pathlib.Path(args.out), None)


if __name__ == "__main__":
    main()
