"""Logic self-checks — run: py test_organizer.py
Works on empty files in temp folders, never touches real files. No tkinter needed (UI is not tested here)."""
import tempfile
import unittest
import zipfile
from pathlib import Path

import i18n
import pack_logic as p
import sort_logic as s
from i18n import t as tr
from pack_logic import moves_into_itself
from ui_dnd import folder_of  # ไม่ใช้ tkinter ตอน import


def make(root: Path, *names):
    for n in names:
        f = root / n
        if n.endswith("/"):
            f.mkdir(parents=True, exist_ok=True)
        else:
            f.parent.mkdir(parents=True, exist_ok=True)
            f.touch()


class Pack(unittest.TestCase):
    def test_pairs(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            make(t, "Common_Days.jpg", "Common_Days_Materialpack_v.1.00.zip", "Shinano_Common_Days_v.1.00.zip",
                 "CPD.jpeg", "CPD_Prefab_Airi_v1.0.zip", "CPDX.zip", "Leisure.jpg", "Leisure.rar",
                 "Ramune.jpg", "RamuneCowkini.zip", "Lonely.zip", "Kit.png", "Kit_Prefab.png",
                 "Kit_Prefab_A.zip", "Kit_Base.zip", "Big.jpg", "Big.part1.rar", "Big.part2.rar")
            got = {n: sorted(f.name for f in a) for n, (i, a) in p.find_pairs(t).items()}
            self.assertEqual(got, {
                "Big": ["Big.part1.rar", "Big.part2.rar"],
                "CPD": ["CPD_Prefab_Airi_v1.0.zip"],
                "Common_Days": ["Common_Days_Materialpack_v.1.00.zip", "Shinano_Common_Days_v.1.00.zip"],
                "Kit": ["Kit_Base.zip"], "Kit_Prefab": ["Kit_Prefab_A.zip"], "Leisure": ["Leisure.rar"]})

    def test_suggest_pairs_typos_only(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            make(t, "fulleffe sapphy.jpg", "fulluffe sapphy.zip", "midnight fox full set.jpg",
                 "midnight foxfull set.rar", "Mimukauwa.jpg", "Mimukawuwa_Outfit_MAT.rar",
                 "Real.jpg", "Real.zip", "Lonely.jpg", "Totally_Different.zip", "PSD.zip")
            pairs = p.find_pairs(t)
            self.assertEqual(list(pairs), ["Real"])  # ของจริงไม่ปนกับที่เดา
            got = {n: sorted(f.name for f in a) for n, (i, a) in p.suggest_pairs(t, pairs).items()}
            self.assertEqual(got, {"fulleffe sapphy": ["fulluffe sapphy.zip"],
                                   "midnight fox full set": ["midnight foxfull set.rar"],
                                   "Mimukauwa": ["Mimukawuwa_Outfit_MAT.rar"]})

    def test_move_pair_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            make(t, "src/A.jpg", "src/A.zip", "dst/A/A.jpg")
            pairs = p.find_pairs(t / "src")
            p.move_pair("A", *pairs["A"], t / "dst")
            self.assertTrue((t / "dst/A/A (1).jpg").exists())
            self.assertTrue((t / "dst/A/A/A.zip").exists())


class Move(unittest.TestCase):
    def test_find_and_merge(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            make(t, "dl/X/X.jpg", "dl/X/X/x.zip", "dl/Plain/p.zip", "dl/Half/Half/h.zip",
                 "out/X/X/x.zip")
            found = [d.name for d in p.find_packed(t / "dl")]
            self.assertEqual(found, ["X"])
            p.move_folder(t / "dl/X", t / "out")
            self.assertFalse((t / "dl/X").exists())
            self.assertTrue((t / "out/X/X/x (1).zip").exists())

    def test_merge_into_self_is_noop(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            make(t, "Karin/karin dress/a.zip")
            p.merge_into(t / "Karin/karin dress", t / "Karin/karin dress")
            self.assertTrue((t / "Karin/karin dress/a.zip").exists())
            self.assertFalse((t / "Karin/karin dress/a (1).zip").exists())

    def test_moves_into_itself(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            make(t, "src/X/X/", "src/Y/")
            self.assertTrue(moves_into_itself(t / "src", t / "src/X/X", ["X"]))
            self.assertFalse(moves_into_itself(t / "src", t / "src/Y", ["X"]))
            self.assertFalse(moves_into_itself(t / "src", t / "elsewhere", ["X"]))


class Language(unittest.TestCase):
    def test_every_text_has_both_languages_with_same_placeholders(self):
        import string
        names = lambda text: {f for _, f, _, _ in string.Formatter().parse(text) if f}
        for key, (th, en) in i18n.TEXT.items():
            self.assertTrue(th.strip() and en.strip(), key)
            self.assertEqual(names(th), names(en), key)  # ขาด {ชื่อ} ในภาษาใดภาษาหนึ่ง = ตอนแสดงผลจะ error

    def test_switch_and_fallback(self):
        try:
            i18n.set_lang("en")
            self.assertEqual(tr("job.done"), "✅ Done")
            self.assertEqual(tr("pack.done", done=1, n=2), "Packed 1/2 item(s)")
            i18n.set_lang("xx")  # ภาษาที่ไม่รู้จัก = ไทย
            self.assertEqual(i18n.get_lang(), "th")
        finally:
            i18n.set_lang("th")

    def test_logic_reasons_follow_language(self):
        with tempfile.TemporaryDirectory() as t_dir:
            make(Path(t_dir), "-Airi-/", "_Fullset/")
            av, fs = s.load_categories(Path(t_dir))
            try:
                i18n.set_lang("en")
                self.assertEqual(s.classify("Gravity", av, fs)[1], "No avatar name found")
            finally:
                i18n.set_lang("th")


class Drop(unittest.TestCase):
    def test_folder_of(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            make(t, "a/b.zip")
            self.assertEqual(folder_of(str(t / "a")), t / "a")        # ลากโฟลเดอร์ = ตัวมันเอง
            self.assertEqual(folder_of(str(t / "a/b.zip")), t / "a")  # ลากไฟล์ = โฟลเดอร์ของมัน
            self.assertIsNone(folder_of(str(t / "nope")))


class Sort(unittest.TestCase):
    CATS = ["_Fullset/", "_Kikyo/", "_Manuka/", "_Rindo/", "_Shinano/", "_ZMisc/", "-Airi-/", "-Chiffon-/",
            "-Lime-/", "Mamehinata/", "-Maya-/", "-Moe-/", "-Selestia-/", "Karin/", "Z_Else/"]

    def test_classify(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            make(t, *self.CATS)
            av, fs = s.load_categories(t)
            self.assertEqual(fs.name, "_Fullset")
            self.assertNotIn("zmisc", av)
            cases = {
                "heart signal manuka [5030045]": "_Manuka",
                "inu tank top mamehinata": "Mamehinata",
                "Sunday Moe [5978197]": "-Moe-",
                "FullBodyController_Airi": "-Airi-",
                "myantom manuka shinano [6346074]": "_Fullset",
                "airy dream lime_chiffon [5467991]": "_Fullset",
                "MiR full set [5832014]": "_Fullset",
                "foiv casual coordination full": "_Fullset",
                "Kikyo full face": None,
                "aloha mame rue": None,
                "Gravity": None,
                "fuller dress": None,
            }
            for name, want in cases.items():
                target, _ = s.classify(name, av, fs)
                self.assertEqual(target.name if target else None, want, name)

    def test_archives_known_and_count(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            make(t, *self.CATS)
            av, fs = s.load_categories(t)
            c = lambda n, **k: (lambda r: r[0].name if r[0] else None)(s.classify(n, av, fs, **k))
            self.assertEqual(c("Common_Days", archives=["Shinano_Common_Days_v.1.00", "Common_Days_Materialpack"]), "_Shinano")
            self.assertEqual(c("Neon_Vortex", archives=["Neon_Vortex_Airi", "Neon_Vortex_Manuka"]), "_Fullset")
            self.assertIsNone(c("Gravity", archives=["Gravity_PSD"]))
            self.assertIsNone(c("cute dress kokoa", known={"kokoa"}))  # รู้จักแต่ไม่มีโฟลเดอร์
            self.assertEqual(c("kokoa airi dress", known={"kokoa"}), "_Fullset")
            self.assertEqual(c("18アバター対応 ⛩️月狐の眼⛩️"), "_Fullset")
            self.assertEqual(c("10 Avatar 『Angelic Night』"), "_Fullset")
            self.assertEqual(c("Karin dress 12アバター対応"), "_Fullset")
            self.assertEqual(c("Karin dress 1 avatar"), "Karin")

    def test_plan_sets_zip_and_self_category(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            make(t, "cats/-Airi-/", "cats/_Fullset/", "cats/Karin/karin dress/", "new/Gravity/Gravity/",
                 "new/Plain/")
            with zipfile.ZipFile(t / "new/Gravity/Gravity/Gravity_Pack.zip", "w") as z:
                z.writestr("Gravity/Airi/dress.fbx", "x")
            (t / "new/Gravity/Gravity/Broken.zip").write_bytes(b"not a zip")  # ซิปเสียต้องไม่ทำให้ล้ม
            (t / "new/Gravity/Gravity/Other.rar").touch()
            rows = {r.name: r for r in s.plan_sets(t / "new", t / "cats")[0]}
            self.assertEqual(rows["Gravity"].target.name, "-Airi-")
            self.assertEqual(rows["Gravity"].note, tr("why.from_zip"))
            self.assertIsNone(rows["Plain"].target)
            # ต้นทางเป็นโฟลเดอร์หมวดเอง: ชุดที่ชี้เข้าหมวดตัวเองต้องไม่ถูกย้าย
            rows = {r.name: r for r in s.plan_sets(t / "cats/Karin", t / "cats")[0]}
            self.assertIsNone(rows["karin dress"].target)
            self.assertEqual(rows["karin dress"].note, tr("why.in_category"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
