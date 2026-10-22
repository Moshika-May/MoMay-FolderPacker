"""ตรรกะแยกชุดเข้าหมวดอวาตาร์ (ไม่มี UI): อ่านโฟลเดอร์หมวด + ตัดสินว่าแต่ละชุดควรไปหมวดไหน"""

import re
import zipfile
from pathlib import Path, PurePosixPath
from typing import NamedTuple, Optional

from i18n import t
from pack_logic import ARCHIVE_EXTS, base_name, word_in

# คำว่า full / full set / fullset (เป็นคำเต็ม) = ชุด fullset; FullBodyController ไม่นับ
FULLSET_RE = re.compile(r"(?<![^\W_])full(\s*set)?(?![^\W_])", re.IGNORECASE)
# "18アバター対応" / "10 Avatar" = ใช้ได้กับหลายตัว (ร้านบอกจำนวนอวาตาร์ที่รองรับ) → fullset
AVATAR_COUNT_RE = re.compile(r"(\d+)\s*(?:アバター対応|avatars?\b)", re.IGNORECASE)


class SortRow(NamedTuple):
    name: str
    target: Optional[Path]  # None = ไม่แน่ใจ ให้ผู้ใช้จัดเอง
    note: str  # ตัวแน่ใจ: ""/FROM_ZIP, ตัวไม่แน่ใจ: เหตุผล


def multi_avatar(name: str) -> bool:
    return any(int(n) > 1 for n in AVATAR_COUNT_RE.findall(name))


def load_categories(root: Path):
    """อ่านโฟลเดอร์หมวดใน root: คืน ({คำค้นอวาตาร์: โฟลเดอร์}, โฟลเดอร์ fullset หรือ None)
    ชื่อโฟลเดอร์ตัด _ - ออกเป็นคำค้น: '_Manuka' -> manuka, '-Airi-' -> airi
    ข้ามโฟลเดอร์ที่ขึ้นต้นด้วย Z (เช่น _ZMisc, Z_Else) เพราะเป็นหมวดเบ็ดเตล็ด"""
    avatars, fullset = {}, None
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        key = d.name.strip("_- ").casefold()
        if FULLSET_RE.fullmatch(key):
            fullset = d
        elif key and not key.startswith("z"):
            avatars[key] = d
    return avatars, fullset


def load_known(root: Path) -> set:
    """ชื่ออวาตาร์จาก _VRC Model (อยู่ข้างๆ โฟลเดอร์หมวด) ที่หมวดนี้อาจยังไม่มีโฟลเดอร์
    shortcut: เดาที่ตั้งจากชื่อ _VRC Model ตายตัว, ถ้าย้ายที่ค่อยทำช่องเลือก"""
    model = root.parent / "_VRC Model"
    # "else" คือโฟลเดอร์เบ็ดเตล็ดของ Model ไม่ใช่อวาตาร์
    return {k for k in load_categories(model)[0] if k != "else"} if model.is_dir() else set()


def classify(name: str, avatars: dict, fullset, known=(), archives=()):
    """คืน (โฟลเดอร์ปลายทาง, เหตุผล) — ปลายทาง None = ไม่แน่ใจ ให้ผู้ใช้จัดเอง
    หาชื่ออวาตาร์จากชื่อชุด + ชื่อไฟล์บีบอัดข้างใน (Shinano_Common_Days.zip → Shinano)
    known = อวาตาร์ที่รู้จักแต่ยังไม่มีโฟลเดอร์หมวด"""
    text = " ".join([name, *archives])
    keys = sorted(k for k in {*avatars, *known} if word_in(k, text))
    label = [avatars[k].name if k in avatars else k for k in keys]
    is_fullset = FULLSET_RE.search(name) is not None
    if len(keys) == 1 and not is_fullset and not multi_avatar(name):
        if keys[0] in avatars:
            return avatars[keys[0]], ""
        return None, t("why.known_no_folder", k=keys[0])
    if fullset and (len(keys) > 1 or multi_avatar(name) or (not keys and is_fullset)):
        return fullset, ""  # หลายอวาตาร์ = ชุดที่รองรับหลายตัว ก็คือ fullset
    if len(keys) > 1:
        return None, t("why.many", names=", ".join(label))  # กรณีไม่มีโฟลเดอร์ Fullset
    if keys:
        return None, t("why.full_and_one", name=label[0])
    return None, t("why.no_avatar")


def archives_in(d: Path) -> list:
    """ไฟล์บีบอัดในชุดที่แพ็กแล้ว (NAME/NAME/*.zip) หรือที่วางตรงๆ ในโฟลเดอร์"""
    inner = d / d.name
    return [f for f in (inner if inner.is_dir() else d).iterdir()
            if f.is_file() and f.suffix.lower() in ARCHIVE_EXTS]


def zip_entry_names(d: Path) -> list:
    """ชื่อโฟลเดอร์/ไฟล์ที่อยู่ข้างใน .zip ของชุด (อ่านแค่สารบัญ ไม่แตกไฟล์)
    shortcut: อ่านได้เฉพาะ .zip, ส่วน .rar/.7z ต้องมีไลบรารีนอก stdlib"""
    names = set()
    for f in archives_in(d):
        if f.suffix.lower() != ".zip":
            continue
        try:
            with zipfile.ZipFile(f) as z:
                for n in z.namelist():
                    p = PurePosixPath(n)
                    names.update((*p.parts[:-1], p.stem))
        except (zipfile.BadZipFile, OSError):
            pass  # ซิปเสียหรืออ่านไม่ได้ = ไม่มีข้อมูลเพิ่ม ไม่ใช่ข้อผิดพลาดของการจัด
    return sorted(names)


def plan_one(d: Path, src: Path, avatars: dict, fullset, known) -> SortRow:
    """ตัดสินชุดเดียว: ดูชื่อชุด + ชื่อซิปก่อน ถ้ายังไม่เจอเลยค่อยเปิดดูข้างในซิป"""
    stems = [base_name(f) for f in archives_in(d)]
    target, why = classify(d.name, avatars, fullset, known, stems)
    note = ""
    if why == t("why.no_avatar"):
        target, why = classify(d.name, avatars, fullset, known, stems + zip_entry_names(d))
        note = t("why.from_zip")
    if target and target.resolve() == src.resolve():
        # ต้นทางคือหมวดนั้นอยู่แล้ว: ย้ายเข้าตัวเองจะทำให้ไฟล์ถูกเปลี่ยนชื่อ
        target, why = None, t("why.in_category")
    return SortRow(d.name, target, note if target else why)


def plan_sets(src: Path, root: Path):
    """คืน ([SortRow ของทุกโฟลเดอร์ใน src], avatars, fullset)"""
    avatars, fullset = load_categories(root)
    known = load_known(root)
    rows = [plan_one(d, src, avatars, fullset, known) for d in sorted(src.iterdir()) if d.is_dir()]
    return rows, avatars, fullset
