"""ธีมและชิ้นส่วน UI ที่ใช้ร่วมกันทุกหน้า (ไม่มีตรรกะจัดไฟล์)"""

import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog

from i18n import t
from ui_dnd import register_drop

# ตอนเป็น .exe ไฟล์ที่แนบมาจะอยู่ใน sys._MEIPASS
APP_NAME = "MoMay-FolderPacker"
ASSETS = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))

PINK, PINK_DARK, PINK_SOFT = "#c2557f", "#a3406a", "#fbe4ee"
BG, CARD, ZEBRA, LINE = "#fff8fb", "#ffffff", "#fdf1f6", "#f1d9e4"
TEXT, MUTED, OK, BAD = "#3b2f36", "#8c7d86", "#2f8f5b", "#c0392b"
FONT, FONT_BOLD = ("Segoe UI", 10), ("Segoe UI", 10, "bold")
STATE_TAGS = ("unsure", "guess", "done", "error")


def enable_dpi() -> None:
    """ให้ตัวหนังสือคมบนจอที่ตั้ง scale (125%, 150%) ไม่ถูก Windows ขยายภาพจนเบลอ"""
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass  # ไม่ใช่ Windows หรือตั้งไม่ได้ ก็แค่ภาพไม่คมเท่า


def apply_theme(root: tk.Tk) -> None:
    root.configure(bg=BG)
    root.option_add("*TCombobox*Listbox.font", FONT)
    s = ttk.Style(root)
    s.theme_use("clam")
    s.configure(".", background=BG, foreground=TEXT, font=FONT)
    s.configure("Card.TFrame", background=CARD)
    s.configure("Card.TLabel", background=CARD)
    s.configure("Muted.TLabel", foreground=MUTED)
    s.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground=PINK)
    s.configure("TEntry", fieldbackground=CARD, bordercolor=LINE, lightcolor=LINE, darkcolor=LINE, padding=6)
    s.configure("TCombobox", fieldbackground=CARD, bordercolor=LINE, padding=4)
    s.configure("TButton", background=CARD, bordercolor="#e3b7cb", lightcolor=CARD, darkcolor=CARD,
                padding=(14, 7), relief="flat")
    s.configure("Vertical.TScrollbar", background=PINK_SOFT, troughcolor=BG, arrowcolor=PINK,
                bordercolor=LINE, lightcolor=PINK_SOFT, darkcolor=PINK_SOFT)
    s.map("TButton", background=[("active", PINK_SOFT)])
    s.configure("Accent.TButton", background=PINK, foreground="white", bordercolor=PINK,
                lightcolor=PINK, darkcolor=PINK, font=FONT_BOLD)
    s.map("Accent.TButton", background=[("active", PINK_DARK), ("pressed", PINK_DARK)])
    s.configure("TNotebook", background=BG, borderwidth=0)
    s.configure("TNotebook.Tab", background=PINK_SOFT, foreground=PINK_DARK, padding=(20, 9), font=FONT_BOLD)
    s.map("TNotebook.Tab", background=[("selected", PINK)], foreground=[("selected", "white")])
    s.configure("Treeview", background=CARD, fieldbackground=CARD, borderwidth=0,
                rowheight=round(30 * root.winfo_fpixels("1i") / 96))
    s.configure("Treeview.Heading", background=PINK_SOFT, foreground=PINK_DARK, font=FONT_BOLD,
                relief="flat", padding=(8, 7))
    s.map("Treeview", background=[("selected", "#f6c9dc")], foreground=[("selected", TEXT)])
    s.map("Treeview.Heading", background=[("active", PINK_SOFT)])


def folder_row(parent, row, label, var, on_pick=None):
    ttk.Label(parent, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=5)
    entry = ttk.Entry(parent, textvariable=var)
    entry.grid(row=row, column=1, sticky="ew", padx=10)
    register_drop(entry, var, on_pick)  # ลากโฟลเดอร์จาก Explorer มาวางในช่องได้

    def browse():
        d = filedialog.askdirectory(parent=parent, initialdir=var.get() or str(Path.home()))
        if d:
            var.set(d)
            if on_pick:
                on_pick()
    ttk.Button(parent, text=t("common.browse"), command=browse).grid(row=row, column=2)


def folder_card(parent, rows):
    """กล่องสีขาวรวมช่องเลือกโฟลเดอร์; rows = [(ป้าย, StringVar, on_pick หรือ None)]"""
    card = tk.Frame(parent, bg=CARD, highlightbackground=LINE, highlightthickness=1)
    card.pack(fill="x", padx=16, pady=(16, 0))
    inner = ttk.Frame(card, style="Card.TFrame", padding=14)
    inner.pack(fill="x")
    inner.columnconfigure(1, weight=1)
    for i, (label, var, on_pick) in enumerate(rows):
        folder_row(inner, i, label, var, on_pick)


def action_bar(parent, scan, go, hint=""):
    """แถบปุ่ม: scan/go = (ข้อความ, คำสั่ง); ปุ่ม go เป็นปุ่มหลักสีชมพูชิดขวา"""
    bar = ttk.Frame(parent)
    bar.pack(fill="x", padx=16, pady=(14, 0))
    ttk.Button(bar, text=scan[0], command=scan[1]).pack(side="left")
    ttk.Label(bar, text=hint, style="Muted.TLabel").pack(side="left", padx=14)
    ttk.Button(bar, text=go[0], style="Accent.TButton", command=go[1]).pack(side="right")


def make_tree(parent, columns):
    """ตารางรายการ + scrollbar; columns = [(id, หัวตาราง, ความกว้าง)] คอลัมน์แรกคือชื่อ"""
    box = tk.Frame(parent, bg=CARD, highlightbackground=LINE, highlightthickness=1)
    box.pack(fill="both", expand=True, padx=16, pady=(12, 0))
    tree = ttk.Treeview(box, columns=[c[0] for c in columns[1:]], selectmode="extended")
    for i, (cid, text, width) in enumerate(columns):
        col = "#0" if i == 0 else cid
        tree.heading(col, text=text, anchor="w")
        tree.column(col, width=width, stretch=(i < len(columns) - 1), anchor="w")
    sb = ttk.Scrollbar(box, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    # tag ที่ตั้งทีหลังมีลำดับสูงกว่า: ลายแถบสลับสีต้องมาก่อนสีตัวอักษรของสถานะ
    tree.tag_configure("odd", background=ZEBRA)
    tree.tag_configure("even", background=CARD)
    for tag, color in (("unsure", MUTED), ("guess", MUTED), ("done", OK), ("error", BAD)):
        tree.tag_configure(tag, foreground=color)
    return tree


def status_bar(parent, text="") -> tk.StringVar:
    var = tk.StringVar(value=text)
    ttk.Label(parent, textvariable=var, style="Muted.TLabel", padding=(16, 8)).pack(fill="x")
    return var


def add_row(tree, iid, text, values, state=""):
    """เพิ่มแถวพร้อมลายสลับสี; state = unsure/guess (สีตัวอักษร)"""
    stripe = "odd" if len(tree.get_children()) % 2 else "even"
    tree.insert("", "end", iid=iid, text=text, values=values, tags=(stripe, state) if state else (stripe,))


def retag(tree, iid, state=""):
    """เปลี่ยนสถานะของแถว (สีตัวอักษร) โดยเก็บลายสลับสีไว้"""
    keep = [t for t in tree.item(iid, "tags") if t not in STATE_TAGS]
    tree.item(iid, tags=(*keep, state) if state else tuple(keep))
