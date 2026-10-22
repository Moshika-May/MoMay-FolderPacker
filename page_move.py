"""แท็บ 🚚 ย้ายโฟลเดอร์: ย้ายชุดที่จัดแล้ว (NAME/NAME.jpg + NAME/NAME/*.zip) ไปเก็บที่อื่นทั้งโฟลเดอร์"""

import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

from i18n import t
from pack_logic import find_packed, move_folder, moves_into_itself
from ui_jobs import ensure_dir, run_jobs
from ui_theme import folder_card, action_bar, make_tree, status_bar, add_row


class MovePage(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.src, self.dst = tk.StringVar(value=str(Path.home() / "Downloads")), tk.StringVar()
        self.paths = (self.src, self.dst)  # ให้หน้าต่างหลักเก็บ/คืนค่าตอนเปลี่ยนภาษา
        folder_card(self, [(t("move.src"), self.src, self.scan), (t("move.dst"), self.dst, None)])
        action_bar(self, (t("move.scan"), self.scan), (t("move.run"), self.run), t("move.hint"))
        self.tree = make_tree(self, [("name", t("move.col"), 520), ("status", t("common.col_status"), 170)])
        self.status = status_bar(self, t("move.start"))

    def scan(self):
        src = Path(self.src.get())
        self.tree.delete(*self.tree.get_children())
        if not src.is_dir():
            self.status.set(t("move.no_src"))
            return
        found = find_packed(src)
        for d in found:
            add_row(self.tree, d.name, d.name, (t("common.waiting"),))
        self.status.set(t("move.found", n=len(found)))

    def run(self):
        win = self.winfo_toplevel()
        src = Path(self.src.get())
        if not self.dst.get():
            messagebox.showerror(t("move.need_dst_title"), t("move.need_dst"), parent=win)
            return
        dst = Path(self.dst.get())
        if dst.resolve() == src.resolve():
            messagebox.showinfo(t("move.same_title"), t("move.same"), parent=win)
            return
        chosen = self.tree.selection() or self.tree.get_children()
        todo = [n for n in chosen if (src / n).is_dir()]
        if not todo:
            messagebox.showinfo(t("common.no_job"), t("move.nothing"), parent=win)
            return
        if moves_into_itself(src, dst, todo):
            messagebox.showerror(t("move.self_title"), t("move.self"), parent=win)
            return
        if not ensure_dir(dst, win):
            return
        if not messagebox.askyesno(t("common.confirm"), t("move.confirm", n=len(todo), dst=dst), parent=win):
            return
        done = run_jobs(win, self.tree, todo, lambda n, p: move_folder(src / n, p), dst)
        self.status.set(t("move.done", done=done, n=len(todo)))
