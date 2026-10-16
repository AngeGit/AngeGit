"""Build the Howler video for the README: voice + illustrations + neon subtitles.

usage (from the repo root):
  python3 tools/howler_video.py media-src/howler-voz.m4a media-src/howler.mp4
  python3 tools/howler_video.py --placeholder media-src/howler-draft.mp4   # macOS `say` voice, to test timing
needs: ffmpeg on PATH, pip install pillow

The illustrations come from media-src/ (kept out of git). Cue timing is found from the pauses in the
recording: each line of CUES is snapped to the nearest silence, so no manual timestamps are needed.
"""
import argparse, pathlib, re, subprocess, sys, tempfile

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
MEDIA = HERE.parent / "media-src"
FONT = HERE / "fonts/Oxanium[wght].ttf"
W, H, FPS = 1280, 720, 30

SCENES = [  # image in media-src, 16:9 crop of the original (left, top, right, bottom), motion
    ("howler-envelope.webp", (0, 96, 1536, 960), "shake"),
    ("howler-burst.webp", (0, 70, 1536, 934), "zoom"),
    ("night-shift-coding.webp", (0, 110, 1254, 815), "zoom"),
    ("portrait-anime90s.webp", (0, 230, 1254, 935), "gentle"),
    ("farewell-over-shoulder.webp", (0, 0, 1254, 705), "zoom"),
]
CUES = [  # scene index, subtitle, style. The polite Howler: it looks like it will shout, and it never does.
    (0, "…Hi. Don't worry, I'm not going to shout.", "line"),
    (0, "I'm a very polite Howler. …Almost.", "line"),
    (1, "I'm Angie, an Android and Kotlin Multiplatform developer from Madrid.", "line"),
    (2, "By day I ship Kotlin and Compose to an app used by millions of shoppers.", "line"),
    (2, "Day and night, I build the guardrails that keep AI coding agents honest:", "line"),
    (2, "at work with my team, and at home while I sleep.", "line"),
    (3, "Because when an agent says “all tests pass”,", "line"),
    (3, "my first question is always the same: where's the evidence?", "line"),
    (4, "The rest of my story is in the letter below.", "line"),
    (4, "And if you're building something like that… send an owl.", "line"),
    (4, "Or an email. Email's faster.", "line"),
]
TAIL = 1.2  # seconds of picture after the last word


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


# ---------- audio

def placeholder_audio(path):
    aiff = path.with_suffix(".aiff")
    text = " [[slnc 450]] ".join(text for _, text, _ in CUES).replace("…", "")
    subprocess.run(["say", "-v", "Samantha", "-r", "170", "-o", str(aiff), text], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(aiff), "-af", "adelay=600:all=1,apad=pad_dur=0.6",
                    "-ac", "1", "-ar", "44100", str(path)], check=True)


def silences(audio):
    r = run(["ffmpeg", "-hide_banner", "-i", str(audio), "-af", "silencedetect=noise=-35dB:d=0.25", "-f", "null", "-"])
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr).groups()
    duration = int(h) * 3600 + int(m) * 60 + float(s)
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    ends += [duration] * (len(starts) - len(ends))
    return [(max(0.0, a), b) for a, b in zip(starts, ends)], duration


def align(gaps_all, duration):
    """Spread the cues over the speech by text length, then snap each boundary to the closest pause."""
    s0 = gaps_all[0][1] if gaps_all and gaps_all[0][0] <= 0.05 else 0.0
    s1 = gaps_all[-1][0] if gaps_all and gaps_all[-1][1] >= duration - 0.05 else duration
    gaps = [g for g in gaps_all if g[0] > s0 + 0.05 and g[1] < s1 - 0.05]
    weights = [len(text) + 14 for _, text, _ in CUES]
    total, acc, chosen, last = sum(weights), 0, [], s0
    for wgt in weights[:-1]:
        acc += wgt
        ideal = s0 + (s1 - s0) * acc / total
        near = [g for g in gaps if (g[0] + g[1]) / 2 > last and abs((g[0] + g[1]) / 2 - ideal) < 1.8]
        g = min(near, key=lambda g: abs((g[0] + g[1]) / 2 - ideal)) if near else (ideal, ideal)
        chosen.append(g)
        last = (g[0] + g[1]) / 2
    times, start = [], s0
    for i in range(len(CUES)):
        end = chosen[i][0] if i < len(chosen) else s1
        times.append((start, end))
        if i < len(chosen):
            start = chosen[i][1]
    return times, s1


# ---------- pictures

def font(size, weight):
    f = ImageFont.truetype(str(FONT), size)
    f.set_variation_by_axes([weight])
    return f


def wrap(text, f, max_w):
    """One line if it fits, otherwise two balanced lines (no lonely last word)."""
    if f.getlength(text) <= max_w:
        return [text]
    words = text.split()
    splits = [(" ".join(words[:i]), " ".join(words[i:])) for i in range(1, len(words))]
    return list(min(splits, key=lambda pair: max(f.getlength(pair[0]), f.getlength(pair[1]))))


def subtitle(text, style, path):
    size, weight, core, glow = {
        "shout": (84, 700, (255, 228, 230, 255), (239, 68, 68, 255)),
        "whisper": (34, 400, (233, 213, 255, 255), (192, 132, 252, 255)),
        "line": (36, 500, (250, 245, 255, 255), (232, 121, 249, 255)),
    }[style]
    f = font(size, weight)
    lines = wrap(text, f, 1060)
    line_h = int(size * 1.32)
    block_h = line_h * len(lines)
    y0 = (H - block_h) // 2 - 40 if style == "shout" else H - 54 - block_h
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if style != "shout":
        bw = max(f.getlength(line) for line in lines) + 60
        ImageDraw.Draw(img).rounded_rectangle(((W - bw) / 2, y0 - 16, (W + bw) / 2, y0 + block_h + 6), 22, fill=(11, 8, 22, 175))
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    for i, line in enumerate(lines):
        hd.text((W / 2, y0 + i * line_h), line, font=f, fill=glow, anchor="ma")
    for radius in ((14, 6) if style == "shout" else (5,)):
        img = Image.alpha_composite(img, halo.filter(ImageFilter.GaussianBlur(radius)))
    d = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        d.text((W / 2, y0 + i * line_h), line, font=f, fill=core, anchor="ma",
               stroke_width=2 if style != "shout" else 3, stroke_fill=(30, 8, 20, 200))
    img.save(path)


def scene_frame(name, crop, path):
    Image.open(MEDIA / name).convert("RGB").crop(crop).resize((W * 2, H * 2), Image.LANCZOS).save(path, quality=92)


# ---------- assembly

def build(audio, out, work):
    gaps, duration = silences(audio)
    times, speech_end = align(gaps, duration)
    total = max(duration, speech_end + TAIL)

    # scene k starts a beat before its first cue; the envelope bursts right as the apology starts
    firsts = [next(i for i, c in enumerate(CUES) if c[0] == k) for k in range(len(SCENES))]
    bounds = [max(0.4, times[firsts[k]][0] - (0.1 if k == 1 else 0.3)) for k in range(1, len(SCENES))]
    trans = [0.35] + [0.6] * (len(bounds) - 1)

    inputs, graph = [], []
    for k, (name, crop, motion) in enumerate(SCENES):
        frame = work / f"scene{k}.jpg"
        scene_frame(name, crop, frame)
        start = 0 if k == 0 else bounds[k - 1] - trans[k - 1] / 2
        end = total if k == len(SCENES) - 1 else bounds[k] + trans[k] / 2
        frames = max(2, round((end - start) * FPS))
        if motion == "shake":
            z = f"1.05+0.07*on/{frames}"
            x = f"iw/2-(iw/zoom/2)+(on/{frames})*22*sin(on*1.9)"
            y = f"ih/2-(ih/zoom/2)+(on/{frames})*12*cos(on*2.3)"
        elif motion == "gentle":
            z = f"1.0+0.04*on/{frames}"
            x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
        else:
            z = f"1.0+0.09*on/{frames}"
            x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
        inputs += ["-i", str(frame)]
        graph.append(f"[{k}:v]zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS},setsar=1,format=yuv420p[s{k}]")

    prev = "s0"
    for k, b in enumerate(bounds):
        kind = "fadewhite" if k == 0 else "fade"
        graph.append(f"[{prev}][s{k + 1}]xfade=transition={kind}:duration={trans[k]}:offset={b - trans[k] / 2:.3f}[x{k}]")
        prev = f"x{k}"

    base = len(SCENES)
    inputs += ["-i", str(audio)]
    for i, ((_, text, style), (a, b)) in enumerate(zip(CUES, times)):
        png = work / f"sub{i}.png"
        subtitle(text, style, png)
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{total:.3f}", "-i", str(png)]
        hold = b + 0.25
        graph.append(f"[{base + 1 + i}:v]format=rgba,fade=in:st={a:.3f}:d=0.15:alpha=1,"
                     f"fade=out:st={hold:.3f}:d=0.2:alpha=1[t{i}]")
        graph.append(f"[{prev}][t{i}]overlay=0:0:enable='between(t,{a:.3f},{hold + 0.2:.3f})'[o{i}]")
        prev = f"o{i}"
    graph.append(f"[{base}:a]apad,atrim=0:{total:.3f},afade=out:st={total - 0.6:.3f}:d=0.6[a]")
    graph.append(f"[{prev}]fade=in:st=0:d=0.4,fade=out:st={total - 0.5:.3f}:d=0.5[v]")

    cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(graph),
           "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}", "-r", str(FPS),
           "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
           "-c:a", "aac", "-b:a", "128k", str(out)]
    r = run(cmd)
    if r.returncode:
        sys.exit(r.stderr[-3000:])
    print(f"{out}  {out.stat().st_size / 1e6:.1f} MB  {total:.1f} s")
    for (_, text, _), (a, b) in zip(CUES, times):
        print(f"  {a:6.2f}–{b:6.2f}  {text}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio", nargs="?")
    ap.add_argument("out")
    ap.add_argument("--placeholder", action="store_true", help="use the macOS `say` voice instead of a recording")
    args = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)
        audio = pathlib.Path(args.audio) if args.audio else work / "placeholder.m4a"
        if args.placeholder:
            placeholder_audio(audio)
        build(audio, pathlib.Path(args.out), work)


if __name__ == "__main__":
    main()
