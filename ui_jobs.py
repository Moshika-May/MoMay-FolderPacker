"""กล่องถามผู้ใช้ + ตัววิ่งงานย้ายทีละชุด (ใช้ร่วมกันทุกหน้า)"""

from pathlib import Path
from tkinter import filedialog, messagebox

from i18n import t
from ui_theme import retag

_busy = False


def is_busy() -> bool:
    return _busy


def pick_parent(parent: Path, name: str, win):
    """ถ้าที่ปลายทางมีโฟลเดอร์ชื่อนี้แล้ว ให้ผู้ใช้เลือก: คืนที่เก็บที่จะใช้ หรือ None = ข้าม"""
    while (parent / name).exists():
        ans = messagebox.askyesnocancel(t("job.exists_title"), t("job.exists_body", name=name, parent=parent),
                                        parent=win)
        if ans is None:
            return None
        if ans is False:
            return parent
        d = filedialog.askdirectory(parent=win, title=t("job.pick_title", name=name), initialdir=str(parent))
        if not d:
            return None
        parent = Path(d)  # วนเช็กซ้ำ เผื่อที่ใหม่ก็มีชื่อนี้อยู่แล้ว
    return parent


def ensure_dir(dst: Path, win) -> bool:
    if dst.is_dir():
        return True
    if not messagebox.askyesno(t("job.nodir_title"), t("job.nodir", dst=dst), parent=win):
        return False
    dst.mkdir(parents=True)
    return True


def set_status(tree, name, text, state=""):
    tree.set(name, "status", text)
    retag(tree, name, state)


def run_jobs(win, tree, names, do_one, dst) -> int:
    """ทำงานทีละชุดพร้อมอัปเดตสถานะในตาราง คืนจำนวนที่สำเร็จ
    dst = Path เดียวสำหรับทุกชุด หรือฟังก์ชัน name -> Path (ปลายทางต่างกันแต่ละชุด)"""
    global _busy
    if _busy:  # win.update() ทำให้กดปุ่มซ้ำได้ระหว่างย้าย: กันงานซ้อนกัน
        return 0
    _busy = True
    done = 0
    try:
        for name in names:
            parent = pick_parent(dst(name) if callable(dst) else dst, name, win)
            if parent is None:
                set_status(tree, name, t("job.skipped"))
                continue
            try:
                set_status(tree, name, t("job.moving"))
                win.update()  # shortcut: UI ค้างระหว่างย้ายไฟล์ใหญ่ข้ามไดรฟ์, ถ้าเป็นปัญหาให้ย้ายไปทำใน thread
                do_one(name, parent)
                set_status(tree, name, t("job.done"), "done")
                done += 1
            except OSError as e:
                set_status(tree, name, t("job.error"), "error")
                messagebox.showerror(t("job.fail_title"), f"{name}:\n{e}", parent=win)
    finally:
        _busy = False
    return done
