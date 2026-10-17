"""The hub's identity: version, title, icon files and what an install copies."""

import hashlib
import os
import re
import struct
import unittest

import main
import version

HERE = os.path.dirname(os.path.abspath(__file__))
ICON = os.path.join(HERE, "icon")


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    assert head[:8] == b"\x89PNG\r\n\x1a\n", path
    return struct.unpack(">II", head[16:24])


class VersionTest(unittest.TestCase):
    def test_one_version_everywhere(self):
        self.assertRegex(version.__version__, r"^\d+\.\d+\.\d+$")
        self.assertTrue(version.TITLE.endswith(" " + version.__version__))
        p = main.installer.plan(main.program(), HERE, env={}, root=os.path.join(HERE, "_never_written"))
        self.assertEqual(p["registry"]["DisplayVersion"], version.__version__)
        self.assertEqual(p["app_id"], "ACME.Hub")

    def test_install_copies_runtime_only(self):
        files = main.program().files
        for needed in ("main.py", "db.py", "seed.py", "icon/app.ico", "data/first_names.txt"):
            self.assertIn(needed, files)
        self.assertFalse([f for f in files if os.path.basename(f).startswith("test_")])
        self.assertNotIn("export_mock.py", files)


class IconTest(unittest.TestCase):
    def test_sizes(self):
        self.assertEqual(png_size(os.path.join(ICON, "silk-database.png")), (16, 16))
        for n in (32, 48, 256):
            self.assertEqual(png_size(os.path.join(ICON, f"app-{n}.png")), (n, n))

    def test_ico_directory(self):
        with open(os.path.join(ICON, "app.ico"), "rb") as f:
            ico = f.read()
        reserved, kind, count = struct.unpack("<HHH", ico[:6])
        self.assertEqual((reserved, kind, count), (0, 1, 4))
        sizes = [ico[6 + 16 * i] or 256 for i in range(count)]
        self.assertEqual(sizes, [16, 32, 48, 256])

    def test_files_match_the_credits(self):
        with open(os.path.join(ICON, "README.md"), encoding="utf-8") as f:
            readme = f.read()
        self.assertIn("Creative Commons Attribution 2.5", readme)
        listed = dict(re.findall(r"\| `([^`]+)` \|[^|]*\| `([0-9a-f]{64})` \|", readme))
        self.assertEqual(len(listed), 6)
        for name, digest in listed.items():
            with open(os.path.join(ICON, name), "rb") as f:
                self.assertEqual(hashlib.sha256(f.read()).hexdigest(), digest, name)
        self.assertIn("CC BY 2.5", version.CREDIT)


if __name__ == "__main__":
    unittest.main()
