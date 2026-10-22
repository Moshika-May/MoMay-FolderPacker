"""
MoMay-FolderPacker — จัดไฟล์คู่ (รูป + ไฟล์บีบอัด ชื่อเดียวกัน) เป็นโครงสร้าง:

    <ที่เก็บ>/NAME/NAME.jpg
    <ที่เก็บ>/NAME/NAME/NAME.zip

ชุดที่ไม่ครบคู่จะไม่ถูกแตะ

ไฟล์นี้มีแค่หน้าต่างหลัก (หัว + แท็บ + ปุ่มเปลี่ยนภาษา) ตรรกะอยู่ที่ pack_logic.py / sort_logic.py,
หน้าแต่ละแท็บอยู่ที่ page_*.py, ธีมกับชิ้นส่วน UI อยู่ที่ ui_*.py, ข้อความ 2 ภาษาอยู่ที่ i18n.py
"""

import tkinter as tk
from tkinter import ttk

import i18n
from i18n import t
from page_move import MovePage
from page_pack import PackPage
from page_sort import SortPage
from ui_dnd import clear_drops, enable_folder_drop
from ui_jobs import is_busy
from ui_theme import APP_NAME, ASSETS, apply_theme, enable_dpi

PAGES = (("tab.pack", PackPage), ("tab.move", MovePage), ("tab.sort", SortPage))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("940x700")
        self.minsize(780, 560)
        apply_theme(self)
        self.pages = []
        self.build()
        enable_folder_drop(self)

    def build(self, keep=None):
        """สร้างหน้าทั้งหมดตามภาษาปัจจุบัน; keep = {ชนิดหน้า: (ที่อยู่โฟลเดอร์, มีตารางอยู่ไหม)} คืนค่าเดิมให้"""
        for w in self.winfo_children():
            w.destroy()
        clear_drops()
        self.build_header()
        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True, padx=16, pady=(14, 16))
        self.pages = []
        for key, page_class in PAGES:
            page = page_class(tabs)
            tabs.add(page, text=t(key))
            self.pages.append(page)
            if keep and page_class in keep:
                paths, had_rows = keep[page_class]
                for var, value in zip(page.paths, paths):
                    var.set(value)
                if had_rows:
                    page.scan()  # ตารางเดิมเป็นภาษาเก่า: สแกนใหม่ให้เป็นภาษาใหม่
        if keep:
            tabs.select(keep["tab"])

    def switch_language(self):
        if is_busy():  # กำลังย้ายไฟล์อยู่: สร้างหน้าใหม่ตอนนี้จะทำให้งานที่วิ่งอยู่พัง
            return
        tabs = next(w for w in self.winfo_children() if isinstance(w, ttk.Notebook))
        keep = {type(p): ([v.get() for v in p.paths], bool(p.tree.get_children())) for p in self.pages}
        keep["tab"] = tabs.index(tabs.select())
        i18n.set_lang("en" if i18n.get_lang() == "th" else "th")
        i18n.save_lang()
        self.build(keep)

    def build_header(self):
        header = ttk.Frame(self, padding=(16, 14, 16, 0))
        header.pack(fill="x")
        try:
            self.logo = tk.PhotoImage(file=str(ASSETS / "app.png"))
            self.iconphoto(True, self.logo)
            self.logo_small = self.logo.subsample(4)  # 256 -> 64 px
            ttk.Label(header, image=self.logo_small).pack(side="left")
        except tk.TclError:
            pass  # ไม่มีไฟล์ไอคอนก็ใช้งานได้ปกติ
        titles = ttk.Frame(header)
        titles.pack(side="left", padx=12)
        ttk.Label(titles, text=APP_NAME, style="Title.TLabel").pack(anchor="w")
        ttk.Label(titles, text=t("app.subtitle"), style="Muted.TLabel").pack(anchor="w")
        ttk.Button(header, text=t("lang.button"), command=self.switch_language).pack(side="right")


if __name__ == "__main__":
    enable_dpi()
    i18n.load_saved_lang()
    App().mainloop()
