"""Alt text for every generated image in README.md, taken from the same text the SVG draws, so the two
can't drift apart. `python3 tools/readme_alts.py` rewrites them in place; tools/test_readme.py checks them.
"""
import html, pathlib, re, sys

TOOLS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import banner as B  # noqa: E402

README = TOOLS.parent / "README.md"


def expected():
    """{img src in README: alt text it must carry}"""
    alts = {
        "intro": B.intro_plain(),
        "night-shift": B.NIGHT_COMMENT + " " + " ".join(B.strip_marks(t) for t in B.NIGHT),
        "house-rules": B.rules_plain(),
        "howler-letter": B.story_plain(),
        "angie-kt": " ".join(line.strip() for line in B.ANGIE_KT.split("\n") if line.strip()),
        "quote-thought": B.quote_plain(),
        "h-hello-light": "Hello, World!",
    }
    for stem, (alt, *_size) in B.ILLUSTRATIONS.items():
        alts[f"illus-{stem}"] = alt
    for stem, (title, tail, *_rest) in B.HEADINGS.items():
        alts[f"h-{stem}-light"] = f"{title} · {tail}"
    return {f"assets/{name}.svg": alt for name, alt in alts.items()}


def alt_pattern(src):
    return re.compile(r'(<img src="' + re.escape(src) + r'"[^>]*? alt=")([^"]*)(")')


def sync(path=README):
    text = path.read_text(encoding="utf-8")
    for src, alt in expected().items():
        text = alt_pattern(src).sub(lambda m: m.group(1) + html.escape(alt, quote=True) + m.group(3), text, count=1)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    sync()
    print(f"alt texts synced in {README.name}")
