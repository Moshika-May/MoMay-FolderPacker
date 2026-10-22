"""ตรรกะจัดไฟล์ (ไม่มี UI): จับคู่รูป + ไฟล์บีบอัด, ย้ายเป็นโครงสร้าง NAME/NAME.jpg + NAME/NAME/*.zip

ชุดที่ไม่ครบคู่จะไม่ถูกแตะ
"""

import re
import shutil
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".jfif"}
ARCHIVE_EXTS = {".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".unitypackage"}
PART_RE = re.compile(r"\.part\d+$", re.IGNORECASE)  # X.part1.rar -> X


def base_name(path: Path) -> str:
    return PART_RE.sub("", path.stem)


def word_in(key: str, text: str) -> bool:
    """key อยู่ใน text เป็นคำเต็ม (moe ตรงกับ 'Sunday Moe' แต่ไม่ตรงกับ 'moeka')"""
    return re.search(rf"(?<![^\W_]){re.escape(key)}(?![^\W_])", text, re.IGNORECASE) is not None


def unique_path(target: Path) -> Path:
    """ไม่เขียนทับไฟล์เดิม: ต่อท้าย (1), (2), ..."""
    candidate, i = target, 1
    while candidate.exists():
        candidate = target.with_name(f"{target.stem} ({i}){target.suffix}")
        i += 1
    return candidate


def _split_files(files) -> tuple:
    """แยกไฟล์เป็น ({ชื่อรูป: [รูป]}, [ไฟล์บีบอัด]) ข้ามไฟล์ประเภทอื่น"""
    images, archives = defaultdict(list), []
    for f in files:
        if f.is_file():
            ext = f.suffix.lower()
            if ext in IMAGE_EXTS:
                images[base_name(f)].append(f)
            elif ext in ARCHIVE_EXTS:
                archives.append(f)
    return images, archives


def find_pairs(src: Path) -> dict:
    """คืน {NAME: (รูป[], ไฟล์บีบอัด[])} เฉพาะชุดที่มีครบทั้งสองอย่าง

    ชื่อรูปอยู่ตรงไหนของชื่อไฟล์บีบอัดก็ได้ (เป็นคำเต็ม):
    CPD.jpeg จับ CPD.zip, CPD_Item_v1.zip และ Common_Days.jpg จับ Shinano_Common_Days_v1.zip
    ต้องมีตัวคั่น (_ - . ช่องว่าง) รอบชื่อ เพื่อไม่ให้ CPD ไปจับ CPDX.zip
    ถ้ามีหลายรูปที่เข้ากันได้ จะเลือกชื่อที่ยาวที่สุด (ตรงที่สุด)
    """
    images, archives = _split_files(src.iterdir())
    groups = {n: (imgs, []) for n, imgs in images.items()}
    by_length = sorted(images, key=len, reverse=True)
    for a in archives:
        for n in by_length:
            if word_in(n, base_name(a)):  # ไม่สนตัวพิมพ์เล็ก/ใหญ่ เหมือน Windows
                groups[n][1].append(a)
                break
    return {n: g for n, g in sorted(groups.items()) if g[1]}


def suggest_pairs(src: Path, pairs: dict, cutoff: float = 0.8) -> dict:
    """เดาคู่จากไฟล์ที่ยังไม่มีคู่ เมื่อชื่อสะกดเพี้ยนนิดหน่อย (fulleffe/fulluffe, foxfull/fox full)
    คืนรูปแบบเดียวกับ find_pairs แต่เป็นการเดา: ต้องให้ผู้ใช้เลือกเองเท่านั้น ห้ามย้ายอัตโนมัติ
    เทียบชื่อรูปกับชื่อไฟล์บีบอัดทั้งชื่อ และกับต้นชื่อที่ยาวเท่ากัน (ชื่อไฟล์บีบอัดมักมีต่อท้าย _v1.0)"""
    used = {f for imgs, arcs in pairs.values() for f in (*imgs, *arcs)}
    images, archives = _split_files(f for f in src.iterdir() if f not in used)

    def score(n, a):
        n, a = n.casefold(), base_name(a).casefold()
        return max(SequenceMatcher(None, n, a).ratio(), SequenceMatcher(None, n, a[:len(n)]).ratio())

    groups = {}
    for a in archives:
        best = max(images, key=lambda n: score(n, a), default=None)
        if best and score(best, a) >= cutoff:
            groups.setdefault(best, (images[best], []))[1].append(a)
    return dict(sorted(groups.items()))


def move_pair(name: str, images: list, archives: list, parent: Path) -> Path:
    outer = parent / name
    inner = outer / name
    inner.mkdir(parents=True, exist_ok=True)
    for f in images:
        shutil.move(str(f), str(unique_path(outer / f.name)))
    for f in archives:
        shutil.move(str(f), str(unique_path(inner / f.name)))
    return outer


def find_packed(src: Path) -> list:
    """โฟลเดอร์ที่จัดแล้ว: NAME/ มีรูปอยู่ข้างใน และ NAME/NAME/ มีไฟล์บีบอัด"""
    found = []
    for d in sorted(src.iterdir()):
        inner = d / d.name
        if (d.is_dir() and inner.is_dir()
                and any(f.is_file() and f.suffix.lower() in IMAGE_EXTS for f in d.iterdir())
                and any(f.is_file() and f.suffix.lower() in ARCHIVE_EXTS for f in inner.iterdir())):
            found.append(d)
    return found


def merge_into(src_dir: Path, dst_dir: Path) -> None:
    """ย้ายของใน src_dir ไปรวมใน dst_dir (ชื่อซ้ำต่อท้าย (1)) แล้วลบ src_dir ที่ว่างแล้ว"""
    if src_dir.resolve() == dst_dir.resolve():
        return
    dst_dir.mkdir(parents=True, exist_ok=True)
    for f in src_dir.iterdir():
        target = dst_dir / f.name
        if f.is_dir() and target.is_dir():
            merge_into(f, target)
        else:
            shutil.move(str(f), str(unique_path(target)))
    src_dir.rmdir()


def moves_into_itself(src: Path, dst: Path, names) -> bool:
    """ปลายทางอยู่ข้างในโฟลเดอร์ที่กำลังจะย้ายหรือไม่ (ย้ายเข้าตัวเองไม่ได้)"""
    src, dst = src.resolve(), dst.resolve()
    return dst.is_relative_to(src) and dst.relative_to(src).parts[0] in names


def move_folder(folder: Path, parent: Path) -> None:
    target = parent / folder.name
    if target.exists():
        merge_into(folder, target)
    else:
        shutil.move(str(folder), str(target))  # ข้ามไดรฟ์ = คัดลอกครบก่อนแล้วค่อยลบต้นฉบับ
