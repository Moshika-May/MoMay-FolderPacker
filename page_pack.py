"""แท็บ 📦 จัดไฟล์: จับคู่รูป + ไฟล์บีบอัดในโฟลเดอร์ต้นทาง แล้วย้ายเป็นโครงสร้างที่จัดแล้ว"""

import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

from i18n import t
from pack_logic import find_pairs, suggest_pairs, move_pair
from ui_jobs import ensure_dir, run_jobs
from ui_theme import folder_card, action_bar, make_tree, status_bar, add_row


class PackPage(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        downloads = str(Path.home() / "Downloads")
        self.src, self.dst = tk.StringVar(value=downloads), tk.StringVar(value=downloads)
        self.paths = (self.src, self.dst)  # ให้หน้าต่างหลักเก็บ/คืนค่าตอนเปลี่ยนภาษา
        folder_card(self, [(t("pack.src"), self.src, self.scan), (t("pack.dst"), self.dst, None)])
        action_bar(self, (t("pack.scan"), self.scan), (t("pack.run"), self.run), t("pack.hint"))
        self.tree = make_tree(self, [("name", t("pack.col_name"), 220), ("files", t("pack.col_files"), 380),
                                     ("status", t("common.col_status"), 150)])
        self.status = status_bar(self, t("pack.start"))

    def scan(self):
        src = Path(self.src.get())
        self.tree.delete(*self.tree.get_children())
        if not src.is_dir():
            messagebox.showerror(t("common.no_folder"), t("pack.no_src", src=src))
            return
        pairs = find_pairs(src)
        for name, (imgs, arcs) in pairs.items():
            files = t("pack.files", n=len(imgs), m=len(arcs)) + ", ".join(f.name for f in arcs)
            add_row(self.tree, name, name, (files, t("pack.waiting")))
        guesses = suggest_pairs(src, pairs)
        for name, (imgs, arcs) in guesses.items():  # ท้ายตาราง: ไม่ย้ายถ้าไม่ได้เลือกเอง
            add_row(self.tree, name, name,
                    (t("pack.guess_files", names=", ".join(f.name for f in arcs)), t("pack.guess_status")), "guess")
        self.status.set(t("pack.found", n=len(pairs)) + (t("pack.found_guess", n=len(guesses)) if guesses else ""))

    def run(self):
        win = self.winfo_toplevel()
        src, dst = Path(self.src.get()), Path(self.dst.get())
        if not src.is_dir():
            messagebox.showerror(t("common.no_folder"), t("pack.no_src", src=src), parent=win)
            return
        if not ensure_dir(dst, win):
            return

        pairs = find_pairs(src)  # สแกนใหม่ เผื่อไฟล์เปลี่ยนหลังกดค้นหา
        if not self.tree.get_children():
            self.scan()
        guesses = suggest_pairs(src, pairs)
        # ไม่เลือกอะไร = ทั้งหมดที่ครบคู่จริง; แถวที่เดามาย้ายเฉพาะเมื่อเลือกเอง
        chosen = self.tree.selection() or [n for n in self.tree.get_children() if n in pairs]
        pairs = {**guesses, **pairs}
        todo = [n for n in chosen if n in pairs]
        if not todo:
            messagebox.showinfo(t("common.no_job"), t("pack.nothing"), parent=win)
            return
        if not messagebox.askyesno(t("common.confirm"), t("pack.confirm", n=len(todo), dst=dst), parent=win):
            return
        done = run_jobs(win, self.tree, todo, lambda n, p: move_pair(n, *pairs[n], p), dst)
        self.status.set(t("pack.done", done=done, n=len(todo)))
