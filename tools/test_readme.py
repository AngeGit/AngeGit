"""Checks that keep the profile README honest. Run them with `python3 -m unittest discover -s tools -v`;
CI runs them on every push (.github/workflows/readme-checks.yml).

No pixel snapshots: the generator is deterministic, so regenerating byte for byte is the snapshot.
"""
import html, pathlib, re, shutil, subprocess, sys, tempfile, unittest
import xml.etree.ElementTree as ET

TOOLS = pathlib.Path(__file__).resolve().parent
ROOT = TOOLS.parent
ASSETS = ROOT / "assets"
README = (ROOT / "README.md").read_text(encoding="utf-8")
sys.path.insert(0, str(TOOLS))
import banner as B  # noqa: E402
import readme_alts  # noqa: E402

INPUTS = ("portrait.jpg", "howler-envelope.jpg", "howler-burst.jpg", "illus-farewell.jpg", "illus-night-shift.jpg")
LOCAL_REF = re.compile(r'(?:src|srcset|href)="(?!https?:|mailto:|#)([^"]+)"')


class GeneratedAssets(unittest.TestCase):
    def test_assets_match_a_fresh_regeneration(self):
        """Editing banner.py without regenerating, or leaving a stale SVG behind, fails here."""
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp)
            for name in INPUTS:
                shutil.copy(ASSETS / name, out / name)
            subprocess.run([sys.executable, str(TOOLS / "banner.py"), str(out), str(out / "portrait.jpg")],
                           check=True, capture_output=True)
            fresh = {p.name for p in out.glob("*.svg")}
            committed = {p.name for p in ASSETS.glob("*.svg")}
            self.assertEqual(committed - fresh, set(), "in assets/ but no longer generated")
            self.assertEqual(fresh - committed, set(), "generated but not committed")
            stale = sorted(n for n in fresh if (out / n).read_bytes() != (ASSETS / n).read_bytes())
            self.assertEqual(stale, [], "out of date: run python3 tools/banner.py assets assets/portrait.jpg")

    def test_every_svg_is_well_formed(self):
        for svg in sorted(ASSETS.glob("*.svg")):
            with self.subTest(svg=svg.name):
                ET.parse(svg)


class Readme(unittest.TestCase):
    def test_local_files_exist(self):
        """Every src, srcset (the phone twins included) and href that points inside the repo."""
        for ref in sorted(set(LOCAL_REF.findall(README))):
            with self.subTest(ref=ref):
                self.assertTrue((ROOT / ref).is_file(), "missing")

    def test_no_blank_line_inside_a_tag(self):
        """A blank line inside an HTML tag (say, in a long alt) ends GitHub's HTML block and spills it as text."""
        self.assertEqual(re.findall(r"<[^<>]*\n[ \t]*\n[^<>]*>", README), [])

    def test_alt_texts_match_what_the_images_draw(self):
        for src, want in readme_alts.expected().items():
            with self.subTest(src=src):
                m = readme_alts.alt_pattern(src).search(README)
                self.assertIsNotNone(m, "image not in README")
                self.assertEqual(html.unescape(m.group(2)), want, "out of date: run python3 tools/readme_alts.py")


class Layout(unittest.TestCase):
    """Text that isn't wrapped by the generator, so nothing else stops it from running off its panel."""

    def test_angie_kt_lines_fit_the_editor(self):
        room = (B.CODE_W - B.CODE_X - 8) / (B.MONO_CW * B.CODE_PX)
        for line in B.ANGIE_KT.split("\n"):
            with self.subTest(line=line.strip()):
                self.assertLessEqual(len(line), room)

    def test_card_headers_and_status_bars_fit(self):
        right = B.CARD_W - B.CARD_M - 8
        for stem, (tag, title, _desc, foot) in B.CARDS.items():
            _file, lang, _private = B.CARD_FILES[stem]
            with self.subTest(card=stem):
                self.assertLessEqual(B.CARD_CODE_X + B.width("JBMonoItalic", "// " + tag, 11.5), right, "comment")
                self.assertLessEqual(B.CARD_CODE_X + B.width("JBMono", "# ", 20) + B.width("Oxanium", title, 21), right, "title")
                status = B.width("JBMono", foot, 10.5, .5) + 16 + B.width("JBMono", lang, 10.5)
                self.assertLessEqual(B.CARD_M + 14 + status, B.CARD_W - B.CARD_M - 14, "status bar")


if __name__ == "__main__":
    unittest.main()
