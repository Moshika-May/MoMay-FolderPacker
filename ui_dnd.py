"""ลากโฟลเดอร์จาก Explorer มาวางในช่องที่อยู่โฟลเดอร์ (Windows เท่านั้น)
ใช้ ctypes เรียก API ของ Windows ตรงๆ เลยไม่ต้องลงไลบรารีเพิ่ม

shortcut: ไม่มีไฮไลต์ช่องตอนลากผ่าน (ต้องใช้ OLE), ถ้าเปิดโปรแกรมแบบ Administrator
Windows จะบล็อกการลากจาก Explorer ปกติ, ถ้าจำเป็นค่อยเพิ่ม ChangeWindowMessageFilterEx
"""

import ctypes
import sys
from ctypes import wintypes
from pathlib import Path

WM_DROPFILES, GWLP_WNDPROC = 0x0233, -4
_targets = {}  # ช่อง Entry -> (StringVar, on_pick)


def register_drop(entry, var, on_pick=None) -> None:
    _targets[entry] = (var, on_pick)


def clear_drops() -> None:
    """เรียกตอนสร้างหน้าใหม่ (เปลี่ยนภาษา) ช่องเก่าถูกทำลายไปแล้ว"""
    _targets.clear()


def folder_of(path: str):
    """ลากโฟลเดอร์มา = ตัวมันเอง, ลากไฟล์มา = โฟลเดอร์ที่ไฟล์นั้นอยู่; ไม่มีอยู่จริง = None"""
    p = Path(path)
    return p if p.is_dir() else p.parent if p.is_file() else None


def _handle_drop(root, shell32, hdrop) -> None:
    try:
        buf = ctypes.create_unicode_buffer(32768)
        shell32.DragQueryFileW(hdrop, 0, buf, len(buf))  # ลากหลายอย่างมา ใช้อันแรก
        pt = wintypes.POINT()
        shell32.DragQueryPoint(hdrop, ctypes.byref(pt))  # จุดที่ปล่อย (พิกัดในหน้าต่าง)
    finally:
        shell32.DragFinish(hdrop)
    widget = root.winfo_containing(root.winfo_rootx() + pt.x, root.winfo_rooty() + pt.y)
    folder = folder_of(buf.value)
    if widget in _targets and folder:
        var, on_pick = _targets[widget]
        var.set(str(folder))
        if on_pick:
            on_pick()


def enable_folder_drop(root) -> None:
    if sys.platform != "win32":
        return
    user32, shell32 = ctypes.windll.user32, ctypes.windll.shell32
    wndproc = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
    user32.GetParent.argtypes, user32.GetParent.restype = [wintypes.HWND], wintypes.HWND
    user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
    user32.SetWindowLongPtrW.restype = ctypes.c_void_p
    user32.CallWindowProcW.argtypes = [ctypes.c_void_p, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.CallWindowProcW.restype = ctypes.c_ssize_t
    shell32.DragAcceptFiles.argtypes = [wintypes.HWND, wintypes.BOOL]
    shell32.DragQueryFileW.argtypes = [ctypes.c_void_p, wintypes.UINT, wintypes.LPWSTR, wintypes.UINT]
    shell32.DragQueryPoint.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.POINT)]
    shell32.DragFinish.argtypes = [ctypes.c_void_p]

    root.update_idletasks()
    hwnd = user32.GetParent(root.winfo_id())  # winfo_id คือหน้าต่างด้านใน Tk; ตัวกรอบอยู่ข้างบน

    def proc(h, msg, wparam, lparam):
        if msg == WM_DROPFILES:
            _handle_drop(root, shell32, wparam)
            return 0
        return user32.CallWindowProcW(old, h, msg, wparam, lparam)

    root._drop_proc = wndproc(proc)  # เก็บไว้ ไม่งั้น Python เก็บกวาดแล้วโปรแกรมล่ม
    old = user32.SetWindowLongPtrW(hwnd, GWLP_WNDPROC, root._drop_proc)
    shell32.DragAcceptFiles(hwnd, True)
