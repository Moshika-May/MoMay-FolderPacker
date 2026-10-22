"""ข้อความทุกอย่างในโปรแกรม 2 ภาษา (ไทย / English) + จำภาษาที่เลือกไว้
เพิ่มข้อความใหม่: เติมบรรทัดใน TEXT เป็น "key": (ไทย, English) แล้วเรียก t("key", ชื่อ=ค่า)
{ชื่อ} ในข้อความต้องมีครบทั้งสองภาษา (test_organizer.py เช็กให้)"""

import json
import os
from pathlib import Path

TEXT = {
    # ---- ทั่วไป ----
    "app.subtitle": ("จัดรูป + ไฟล์บีบอัด ให้เป็นระเบียบ ♡", "Tidy up images + archives ♡"),
    "tab.pack": ("📦 จัดไฟล์", "📦 Pack"),
    "tab.move": ("🚚 ย้ายโฟลเดอร์", "🚚 Move"),
    "tab.sort": ("🧺 แยกตามอวาตาร์", "🧺 Sort by avatar"),
    "lang.button": ("🌐 English", "🌐 ไทย"),
    "common.browse": ("เลือก...", "Browse..."),
    "common.no_folder": ("ไม่พบโฟลเดอร์", "Folder not found"),
    "common.no_job": ("ไม่มีงาน", "Nothing to do"),
    "common.confirm": ("ยืนยัน", "Confirm"),
    "common.col_status": ("สถานะ", "Status"),
    "common.waiting": ("รอย้าย", "Waiting"),
    "common.manual": ("จัดเอง", "Manual"),
    # ---- แท็บจัดไฟล์ ----
    "pack.src": ("โฟลเดอร์ต้นทาง (ที่ไฟล์โหลดมา)", "Source folder (where the downloads are)"),
    "pack.dst": ("ที่เก็บปลายทาง", "Destination folder"),
    "pack.scan": ("🔍 ค้นหาไฟล์คู่", "🔍 Find pairs"),
    "pack.run": ("📦 จัดไฟล์", "📦 Pack"),
    "pack.hint": ("เลือกบางแถวเพื่อจัดเฉพาะที่เลือก • ไม่เลือก = จัดทั้งหมด",
                  "Select some rows to pack only those • select none = pack all"),
    "pack.col_name": ("ชื่อชุด", "Item"),
    "pack.col_files": ("ไฟล์", "Files"),
    "pack.start": ("กด 'ค้นหาไฟล์คู่' เพื่อเริ่ม", "Press 'Find pairs' to start"),
    "pack.no_src": ("ไม่พบโฟลเดอร์ต้นทาง:\n{src}", "Source folder not found:\n{src}"),
    "pack.waiting": ("รอจัด", "Waiting"),
    "pack.files": ("{n} รูป + {m} ไฟล์บีบอัด: ", "{n} image(s) + {m} archive(s): "),
    "pack.guess_files": ("🤔 เดา: {names}", "🤔 Guess: {names}"),
    "pack.guess_status": ("เดา—เลือกเองถ้าใช่", "Guess - select it if right"),
    "pack.found": ("พบ {n} ชุดที่มีครบคู่ (รูป + ไฟล์บีบอัด)", "Found {n} complete item(s) (image + archive)"),
    "pack.found_guess": ("  •  เดาคู่ได้อีก {n} ชุด (สีเทา ต้องเลือกเอง)",
                         "  •  {n} more guessed pair(s) (grey, select by hand)"),
    "pack.nothing": ("ไม่พบชุดที่มีครบคู่ให้จัด", "No complete items to pack"),
    "pack.confirm": ("จะย้าย {n} ชุดไปที่\n{dst}\n\nดำเนินการต่อ?", "Move {n} item(s) to\n{dst}\n\nContinue?"),
    "pack.done": ("จัดเสร็จ {done}/{n} ชุด", "Packed {done}/{n} item(s)"),
    # ---- แท็บย้ายโฟลเดอร์ ----
    "move.src": ("โฟลเดอร์ที่มีชุดที่จัดแล้ว", "Folder with packed items"),
    "move.dst": ("ย้ายไปที่ (เช่น _VRC Unsorts\\วันที่)", "Move to (e.g. _VRC Unsorts\\date)"),
    "move.scan": ("🔍 ค้นหาโฟลเดอร์", "🔍 Find folders"),
    "move.run": ("🚚 ย้าย", "🚚 Move"),
    "move.hint": ("เลือกบางแถว = ย้ายเฉพาะที่เลือก", "Select some rows to move only those"),
    "move.col": ("โฟลเดอร์", "Folder"),
    "move.start": ("กด 'ค้นหาโฟลเดอร์' เพื่อเริ่ม", "Press 'Find folders' to start"),
    "move.no_src": ("ไม่พบโฟลเดอร์ต้นทาง", "Source folder not found"),
    "move.found": ("พบ {n} โฟลเดอร์ที่จัดแล้ว", "Found {n} packed folder(s)"),
    "move.need_dst_title": ("ยังไม่ได้เลือก", "Not chosen yet"),
    "move.need_dst": ("กรุณาเลือกโฟลเดอร์ 'ย้ายไปที่' ก่อน", "Please choose the 'Move to' folder first"),
    "move.same_title": ("ที่เดียวกัน", "Same folder"),
    "move.same": ("ต้นทางกับปลายทางเป็นโฟลเดอร์เดียวกัน", "Source and destination are the same folder"),
    "move.nothing": ("ไม่พบโฟลเดอร์ให้ย้าย", "No folders to move"),
    "move.self_title": ("ย้ายไม่ได้", "Cannot move"),
    "move.self": ("ไม่สามารถย้ายโฟลเดอร์เข้าไปในตัวมันเองได้", "A folder cannot be moved into itself"),
    "move.confirm": ("จะย้าย {n} โฟลเดอร์ไปที่\n{dst}\n\nดำเนินการต่อ?", "Move {n} folder(s) to\n{dst}\n\nContinue?"),
    "move.done": ("ย้ายเสร็จ {done}/{n} โฟลเดอร์", "Moved {done}/{n} folder(s)"),
    # ---- แท็บแยกตามอวาตาร์ ----
    "sort.src": ("โฟลเดอร์ที่มีชุดที่ยังไม่แยก", "Folder with unsorted items"),
    "sort.cats": ("โฟลเดอร์หมวดอวาตาร์ (เช่น _VRC Clothes)", "Avatar folders location (e.g. _VRC Clothes)"),
    "sort.scan": ("🔍 ตรวจสอบ", "🔍 Check"),
    "sort.run": ("🧺 ย้ายตัวที่แน่ใจ", "🧺 Move the certain ones"),
    "sort.hint": ("คลิกช่อง 'ไปที่' ▾ เพื่อเลือกหมวดเอง • ตัว ❓ ที่ไม่ได้เลือกจะไม่ถูกย้าย",
                  "Click a 'Move to' cell ▾ to pick a folder yourself • ❓ rows you leave are not moved"),
    "sort.col_name": ("โฟลเดอร์", "Folder"),
    "sort.col_target": ("ไปที่", "Move to"),
    "sort.start": ("เลือกโฟลเดอร์ให้ครบทั้งสองช่องแล้วกด 'ตรวจสอบ'", "Choose both folders, then press 'Check'"),
    "sort.need_both": ("เลือกโฟลเดอร์ให้ครบทั้งสองช่องก่อน", "Choose both folders first"),
    "sort.not_found": ("ไม่พบโฟลเดอร์ที่เลือก", "Selected folder not found"),
    "sort.same": ("สองช่องต้องเป็นคนละโฟลเดอร์ ย้ายชุดที่ยังไม่แยกไปไว้อีกโฟลเดอร์ก่อน",
                  "The two boxes must be different folders. Move the unsorted items to another folder first."),
    "sort.skip": ("— ไม่ย้าย (จัดเอง) —", "— Don't move (I'll do it) —"),
    "sort.unsure_target": ("❓ จัดเอง", "❓ Manual"),
    "sort.hand_picked": ("(เลือกเอง)", "(picked by you)"),
    "sort.in_cat_title": ("อยู่หมวดนี้แล้ว", "Already in this category"),
    "sort.in_cat_msg": ("โฟลเดอร์ต้นทางคือ {label} อยู่แล้ว", "The source folder is already {label}"),
    "sort.counts": ("จะย้าย {n} โฟลเดอร์  •  ปล่อยไว้ {m} โฟลเดอร์",
                    "Will move {n} folder(s)  •  leaving {m} folder(s)"),
    "sort.cats_info": ("  •  อ่านหมวดได้ {n} อวาตาร์", "  •  read {n} avatar(s)"),
    "sort.no_plan": ("ยังไม่มีโฟลเดอร์ที่แน่ใจให้ย้าย กด 'ตรวจสอบ' ก่อน",
                     "Nothing certain to move yet. Press 'Check' first."),
    "sort.all_unsure": ("แถวที่เลือกเป็นตัวที่ไม่แน่ใจทั้งหมด", "All selected rows are uncertain"),
    "sort.confirm": ("จะย้าย {n} โฟลเดอร์เข้าหมวดอวาตาร์\n\nดำเนินการต่อ?",
                     "Move {n} folder(s) into avatar folders?\n\nContinue?"),
    "sort.done": ("ย้ายเสร็จ {done}/{n} โฟลเดอร์  •  ตัว ❓ ยังอยู่ที่เดิม",
                  "Moved {done}/{n} folder(s)  •  ❓ items stay where they are"),
    # ---- เหตุผลของ sort_logic ----
    "why.no_avatar": ("ไม่พบชื่ออวาตาร์", "No avatar name found"),
    "why.known_no_folder": ("พบอวาตาร์ {k} แต่ยังไม่มีโฟลเดอร์หมวด", "Found avatar {k} but there is no folder for it"),
    "why.many": ("เจอหลายอวาตาร์: {names}", "Several avatars: {names}"),
    "why.full_and_one": ("มีทั้ง full set และ {name}", "Has both 'full set' and {name}"),
    "why.from_zip": ("เดาจากในซิป", "guessed from inside the zip"),
    "why.in_category": ("อยู่ในหมวดนี้แล้ว", "Already in this category"),
    # ---- กล่องถาม + ตัววิ่งงาน ----
    "job.exists_title": ("มีโฟลเดอร์นี้อยู่แล้ว", "Folder already exists"),
    "job.exists_body": ("มีโฟลเดอร์ \"{name}\" อยู่แล้วใน\n{parent}\n\n"
                        "ใช่ = เลือกที่เก็บอื่น\n"
                        "ไม่ใช่ = ใส่รวมในโฟลเดอร์เดิม (ไฟล์ชื่อซ้ำจะต่อท้าย (1))\n"
                        "ยกเลิก = ข้ามชุดนี้",
                        "A folder \"{name}\" already exists in\n{parent}\n\n"
                        "Yes = choose another location\n"
                        "No = merge into the existing folder (same-name files get (1) added)\n"
                        "Cancel = skip this item"),
    "job.pick_title": ("เลือกที่เก็บสำหรับ {name}", "Choose a location for {name}"),
    "job.nodir_title": ("ไม่มีที่เก็บ", "Folder missing"),
    "job.nodir": ("ยังไม่มีโฟลเดอร์\n{dst}\nสร้างใหม่ไหม?", "The folder\n{dst}\ndoes not exist. Create it?"),
    "job.skipped": ("ข้าม", "Skipped"),
    "job.moving": ("กำลังย้าย...", "Moving..."),
    "job.done": ("✅ เสร็จ", "✅ Done"),
    "job.error": ("❌ ผิดพลาด", "❌ Error"),
    "job.fail_title": ("ย้ายไม่สำเร็จ", "Move failed"),
}

_lang = "th"
SETTINGS = Path(os.environ.get("APPDATA", Path.home())) / "MoMay-FolderPacker" / "settings.json"


def set_lang(lang: str) -> None:
    global _lang
    _lang = lang if lang in ("th", "en") else "th"


def get_lang() -> str:
    return _lang


def t(key: str, **values) -> str:
    th, en = TEXT[key]
    text = en if _lang == "en" else th
    return text.format(**values) if values else text


def load_saved_lang() -> None:
    try:
        set_lang(json.loads(SETTINGS.read_text(encoding="utf-8")).get("lang", "th"))
    except (OSError, ValueError):
        pass  # ยังไม่เคยตั้งค่า หรือไฟล์เสีย = ใช้ภาษาไทยตามเดิม


def save_lang() -> None:
    try:
        SETTINGS.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS.write_text(json.dumps({"lang": _lang}), encoding="utf-8")
    except OSError:
        pass  # จำภาษาไม่ได้ก็แค่เปิดครั้งหน้าเป็นภาษาไทย ไม่ใช่ข้อผิดพลาดของการจัดไฟล์
