"""แท็บ 🧺 แยกตามอวาตาร์: ย้ายชุดเข้าโฟลเดอร์หมวดอวาตาร์ ตัวไม่แน่ใจเลือกหมวดเองจาก dropdown ได้"""

import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

from i18n import t
from pack_logic import move_folder
from sort_logic import plan_sets
from ui_jobs import run_jobs
from ui_theme import folder_card, action_bar, make_tree, status_bar, add_row, retag

TARGET_COL = "#1"  # คอลัมน์ "ไปที่" (คอลัมน์ #0 คือชื่อโฟลเดอร์)
ARROW = "   ▾"  # บอกว่าช่องนี้คลิกแล้วเลือกได้


class SortPage(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.src, self.cats = tk.StringVar(), tk.StringVar()
        self.paths = (self.src, self.cats)  # ให้หน้าต่างหลักเก็บ/คืนค่าตอนเปลี่ยนภาษา
        self.plan = {}     # ชื่อชุด -> โฟลเดอร์ปลายทาง (ตัวที่จะย้าย รวมตัวที่ผู้ใช้เลือกเอง)
        self.folders = {}  # ชื่อโฟลเดอร์หมวด -> Path (ตัวเลือกใน dropdown)
        self.skip = t("sort.skip")
        self.editor = None
        self.cats_info = ""  # ข้อความท้ายแถบสถานะ: จำนวนหมวดที่อ่านได้
        folder_card(self, [(t("sort.src"), self.src, self.scan), (t("sort.cats"), self.cats, self.scan)])
        action_bar(self, (t("sort.scan"), self.scan), (t("sort.run"), self.run), t("sort.hint"))
        self.tree = make_tree(self, [("name", t("sort.col_name"), 360), ("target", t("sort.col_target"), 280),
                                     ("status", t("common.col_status"), 130)])
        self.tree.bind("<ButtonRelease-1>", self.open_editor)  # หลังคลิก แถวถูกเลือกเรียบร้อยแล้ว
        self.tree.bind("<Button-1>", self.close_editor, add="+")
        self.tree.bind("<MouseWheel>", self.close_editor, add="+")
        self.status = status_bar(self, t("sort.start"))

    # ---- สแกน ----
    def scan(self):
        self.close_editor()
        self.tree.delete(*self.tree.get_children())
        self.plan, self.folders = {}, {}
        if not self.src.get() or not self.cats.get():
            self.status.set(t("sort.need_both"))
            return
        src, root = Path(self.src.get()), Path(self.cats.get())
        if not src.is_dir() or not root.is_dir():
            self.status.set(t("sort.not_found"))
            return
        if src.resolve() == root.resolve():
            # ชุดชื่อคำเดียว (Gravity, Meow) แยกไม่ออกจากหมวดอวาตาร์ (Karin, Kipfel)
            self.status.set(t("sort.same"))
            return
        rows, avatars, fullset = plan_sets(src, root)
        self.folders = {d.name: d for d in sorted(root.iterdir()) if d.is_dir()}
        for r in (r for r in rows if r.target):
            self.plan[r.name] = r.target
            add_row(self.tree, r.name, r.name,
                    (r.target.name + (f" ({r.note})" if r.note else "") + ARROW, t("common.waiting")))
        for r in (r for r in rows if not r.target):  # ตัวไม่แน่ใจไว้ท้ายตาราง
            add_row(self.tree, r.name, r.name, (f"❓ {r.note}{ARROW}", t("common.manual")), "unsure")
        self.show_counts(len(avatars), fullset is not None)

    def show_counts(self, n_avatars=None, has_fullset=None):
        if n_avatars is not None:
            self.cats_info = t("sort.cats_info", n=n_avatars) + (" + Fullset" if has_fullset else "")
        total = len(self.tree.get_children())
        self.status.set(t("sort.counts", n=len(self.plan), m=total - len(self.plan)) + self.cats_info)

    # ---- dropdown เลือกหมวดเอง ----
    def open_editor(self, event):
        self.close_editor()
        if event.state & 0x5:  # Shift/Ctrl = กำลังเลือกหลายแถว ไม่เปิด dropdown
            return
        iid = self.tree.identify_row(event.y)
        if (not iid or self.tree.identify_region(event.x, event.y) != "cell"
                or self.tree.identify_column(event.x) != TARGET_COL or not self.folders):
            return
        x, y, w, h = self.tree.bbox(iid, TARGET_COL)
        box = ttk.Combobox(self.tree, values=[self.skip, *self.folders], state="readonly")
        current = self.plan.get(iid)
        box.set(current.name if current and current.name in self.folders else self.skip)
        box.place(x=x, y=y, width=w, height=h)
        box.bind("<<ComboboxSelected>>", lambda e: self.choose(iid, box.get()))
        box.bind("<Escape>", self.close_editor)
        box.focus_set()
        self.editor = box
        box.after(30, lambda: box.tk.call("ttk::combobox::Post", box))  # เปิดรายการให้เลย

    def close_editor(self, event=None):
        if self.editor:
            self.editor.destroy()
            self.editor = None

    def choose(self, iid, label):
        """ใช้ตัวเลือกกับแถวที่ดับเบิลคลิก (ถ้าแถวนั้นถูกเลือกอยู่ในกลุ่ม = ใช้กับทุกแถวที่เลือก)"""
        selected = self.tree.selection()
        for name in (selected if iid in selected else (iid,)):
            self.set_target(name, label)
        self.close_editor()
        self.show_counts()

    def set_target(self, name, label):
        if label == self.skip:
            self.plan.pop(name, None)
            self.tree.set(name, "target", t("sort.unsure_target") + ARROW)
            self.tree.set(name, "status", t("common.manual"))
            retag(self.tree, name, "unsure")
            return
        folder = self.folders[label]
        if folder.resolve() == Path(self.src.get()).resolve():
            messagebox.showinfo(t("sort.in_cat_title"), t("sort.in_cat_msg", label=label), parent=self.winfo_toplevel())
            return
        self.plan[name] = folder
        self.tree.set(name, "target", f"{label} {t('sort.hand_picked')}{ARROW}")
        self.tree.set(name, "status", t("common.waiting"))
        retag(self.tree, name)

    # ---- ย้าย ----
    def run(self):
        win = self.winfo_toplevel()
        src = Path(self.src.get())
        if not self.plan:
            messagebox.showinfo(t("common.no_job"), t("sort.no_plan"), parent=win)
            return
        chosen = self.tree.selection() or self.tree.get_children()
        todo = [n for n in chosen if n in self.plan and (src / n).is_dir()]
        if not todo:
            messagebox.showinfo(t("common.no_job"), t("sort.all_unsure"), parent=win)
            return
        if not messagebox.askyesno(t("common.confirm"), t("sort.confirm", n=len(todo)), parent=win):
            return
        done = run_jobs(win, self.tree, todo, lambda n, p: move_folder(src / n, p), lambda n: self.plan[n])
        self.status.set(t("sort.done", done=done, n=len(todo)))
