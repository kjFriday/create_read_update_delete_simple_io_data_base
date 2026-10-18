"""The hub's identity: version, title, icon files and what an install copies."""

import hashlib
import io
import json
import os
import re
import struct
import tempfile
import unittest
from contextlib import redirect_stdout

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

    def test_uninstall_hands_a_wizard_made_install_to_its_uninstaller(self):
        """--uninstall passes --quiet, --purge and --root on to uninstall.exe and returns its exit code."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        plan = main.installer.plan(main.program(), HERE, env={}, root=tmp.name)
        os.makedirs(plan["install_dir"])
        with open(os.path.join(plan["install_dir"], main.installer.MARKER), "w") as f:
            json.dump({"app_id": version.APP_ID, "name": version.NAME, "version": version.__version__, "files": [],
                       "shortcuts": [], "installer": "ACME Wizard Maker 0.1.0"}, f)
        calls = []

        def refused(p, args):
            calls.append((p["install_dir"], args))
            raise main.installer.UninstallerFailed(4, f"Setup or uninstall of {version.NAME} is already running.")

        self.addCleanup(setattr, main.installer, "run_uninstaller", main.installer.run_uninstaller)
        main.installer.run_uninstaller = refused
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main.main(["--uninstall", "--quiet", "--purge", "--root", tmp.name]), 4)
        self.assertEqual(calls, [(plan["install_dir"], ["-quiet", "-purge", "-root", os.path.abspath(tmp.name)])])
        self.assertIn("already running", out.getvalue())
        self.assertTrue(os.path.isfile(os.path.join(plan["install_dir"], main.installer.MARKER)))
        main.installer.run_uninstaller = lambda p, args: f"Removed {version.NAME} {version.__version__}."
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main.main(["--uninstall", "--quiet", "--root", tmp.name]), 0)
        self.assertIn("Removed", out.getvalue())


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
