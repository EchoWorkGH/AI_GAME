import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from PIL import Image, ImageTk
from yolo_worker import YOLOClickerWorker

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from PIL import Image, ImageTk, ImageGrab
import pygetwindow as gw  # 需安装 pip install pygetwindow
import numpy as np
from yolo_worker import YOLOClickerWorker


class AppUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO 物理模拟自动点击器 v4.0")
        self.root.geometry("550x900")

        self.worker = YOLOClickerWorker()
        self.region = None
        self.target_window = None
        self.setup_ui()

    def on_mode_change(self):
        if self.click_mode_var.get() == "real":
            self.worker.set_click_mode(True)
        else:
            self.worker.set_click_mode(False)

    def setup_ui(self):
        # 1. 区域管理
        area_frame = ttk.LabelFrame(self.root, text="第一步：区域设定")
        area_frame.pack(pady=10, fill="x", padx=20)

        btn_container = tk.Frame(area_frame)
        btn_container.pack(fill="x", padx=10, pady=5)

        ttk.Button(btn_container, text="框选识别区域", command=self.select_area).pack(side="left", padx=5, expand=True,
                                                                                      fill="x")

        self.btn_lock_win = ttk.Button(btn_container, text="锁定对应窗口", command=self.lock_target_window,
                                       state="disabled")
        self.btn_lock_win.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_show_area = ttk.Button(area_frame, text="显现当前区域", command=self.flash_area, state="disabled")
        self.btn_show_area.pack(fill="x", padx=15, pady=5)

        # 2. 预览区域
        preview_container = ttk.LabelFrame(self.root, text="实时预览 (当前识别范围)")
        preview_container.pack(pady=5, padx=20)
        self.view_port = tk.Frame(preview_container, width=400, height=300, bg="black")
        self.view_port.pack_propagate(False)
        self.view_port.pack()
        self.preview_label = tk.Label(self.view_port, bg="black")
        self.preview_label.pack(expand=True, fill="both")

        # 3. 参数配置
        settings = ttk.LabelFrame(self.root, text="第二步：参数配置")
        settings.pack(pady=10, padx=20, fill="x")

        tk.Label(settings, text="目标类别:").grid(row=0, column=0, padx=5, pady=5)
        self.target_entry = ttk.Entry(settings)
        self.target_entry.insert(0, "npc_dianxiaoer")
        self.target_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(settings, text="检测间隔(ms):").grid(row=1, column=0, padx=5, pady=5)
        self.interval_scale = tk.Scale(settings, from_=50, to=1000, orient="horizontal")
        self.interval_scale.set(100)
        self.interval_scale.grid(row=1, column=1, padx=5, sticky="ew")

        tk.Label(settings, text="点击模式:").grid(row=2, column=0, padx=5, pady=5)
        mode_frame = tk.Frame(settings)
        mode_frame.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.click_mode_var = tk.StringVar(value="real")
        tk.Radiobutton(mode_frame, text="真实点击", variable=self.click_mode_var,
                       value="real", command=self.on_mode_change).pack(side="left", padx=5)
        tk.Radiobutton(mode_frame, text="显示指令", variable=self.click_mode_var,
                       value="instruction", command=self.on_mode_change).pack(side="left", padx=5)

        # 4. 开关
        self.btn_toggle = ttk.Button(self.root, text="开启自动执行 (双击唤醒模式)", command=self.toggle_engine,
                                     state="disabled")
        self.btn_toggle.pack(pady=15, fill="x", padx=40)

        # 5. 日志
        tk.Label(self.root, text="日志信息:").pack(anchor="w", padx=20)
        self.log_box = scrolledtext.ScrolledText(self.root, height=12, font=("Consolas", 9), bg="#f4f4f4")
        self.log_box.pack(pady=5, padx=20, fill="both", expand=True)

    def lock_target_window(self):
        """寻找并锁定窗口，同时将识别/预览区域切换为该窗口范围"""
        if not self.region:
            self.write_log("请先框选一个区域再尝试锁定窗口")
            return

        rx, ry, rw, rh = self.region
        rx2, ry2 = rx + rw, ry + rh
        best_win = None
        max_overlap = 0

        for win in gw.getAllWindows():
            if win.width <= 0 or win.height <= 0: continue
            overlap_x1 = max(rx, win.left)
            overlap_y1 = max(ry, win.top)
            overlap_x2 = min(rx2, win.right)
            overlap_y2 = min(ry2, win.bottom)

            if overlap_x2 > overlap_x1 and overlap_y2 > overlap_y1:
                area = (overlap_x2 - overlap_x1) * (overlap_y2 - overlap_y1)
                if area > max_overlap:
                    max_overlap = area
                    best_win = win

        if best_win:
            self.target_window = best_win
            # 重要：将识别区域(self.region)更新为锁定窗口的实际物理范围
            self.region = (best_win.left, best_win.top, best_win.width, best_win.height)

            self.write_log(f"成功锁定窗口: [{best_win.title}]")
            self.write_log(f"预览区域已调整为窗口全量范围")

            # 如果 worker 正在运行，实时更新抓取范围
            if self.worker.is_running:
                self.worker.update_region(self.region)
            self.worker.bind_window(best_win._hWnd)
            self.write_log(f"已锁定句柄: {best_win._hWnd} ({best_win.title})")
            # 立即触发一次预览更新，让用户看到窗口画面
            self._force_refresh_preview()
        else:
            self.write_log("未能在该区域发现有效窗口，请重试")

    def _force_refresh_preview(self):
        """手动截取一次当前区域并更新到预览"""
        if self.region:
            x, y, w, h = self.region
            img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            self.update_preview(img)

    def write_log(self, msg):
        self.root.after(0, lambda: [self.log_box.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n"),
                                    self.log_box.see(tk.END)])

    def update_preview(self, pil_img):
        # 保持比例缩放以适应 400x300 的预览框
        pil_img.thumbnail((400, 300))
        tk_img = ImageTk.PhotoImage(pil_img)
        self.root.after(0, self._set_img, tk_img)

    def _set_img(self, tk_img):
        self.preview_label.config(image=tk_img)
        self.preview_label.image = tk_img

    def flash_area(self):
        if not self.region: return
        flash_win = tk.Toplevel(self.root)
        flash_win.attributes("-alpha", 0.5, "-fullscreen", True, "-topmost", True, "-transparentcolor", "white")
        flash_win.overrideredirect(True)
        canvas = tk.Canvas(flash_win, bg="white", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        x, y, w, h = self.region
        canvas.create_rectangle(x, y, x + w, y + h, outline="red", width=3)
        self.root.after(1000, flash_win.destroy)

    def select_area(self):
        if self.worker.is_running: self.worker.stop()
        self.root.iconify()
        AreaSelector(tk.Toplevel(self.root), self.on_area_done)

    def on_area_done(self, selection):
        self.region = selection
        self.root.deiconify()
        if self.region:
            self.btn_toggle.config(state="normal")
            self.btn_show_area.config(state="normal")
            self.btn_lock_win.config(state="normal")
            # 框选完立即展示一下预览图
            self._force_refresh_preview()

    def toggle_engine(self):
        if not self.worker.is_running:
            self.btn_toggle.config(text="停止运行")
            # 这里的 self.region 已经是被 lock_target_window 更新过的窗口坐标
            t = threading.Thread(target=self.worker.start_process, args=(
                self.region, self.target_entry.get(),
                self.interval_scale.get(), 1.0,
                self.write_log, self.update_preview
            ), daemon=True)
            t.start()
        else:
            self.worker.stop()
            self.btn_toggle.config(text="开启自动执行 (双击唤醒模式)")


# ... AreaSelector 类保持不变 ...


class AreaSelector:
    def __init__(self, window, callback):
        self.window = window
        self.callback = callback
        self.window.attributes('-alpha', 0.3, '-fullscreen', True, "-topmost", True)
        self.canvas = tk.Canvas(self.window, cursor="cross", bg="grey")
        self.canvas.pack(fill="both", expand=True)
        self.start_x = self.start_y = self.rect = None
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def on_press(self, e):
        self.start_x, self.start_y = e.x, e.y
        self.rect = self.canvas.create_rectangle(e.x, e.y, e.x + 1, e.y + 1, outline='red', width=2)

    def on_move(self, e):
        self.canvas.coords(self.rect, self.start_x, self.start_y, e.x, e.y)

    def on_release(self, e):
        selection = (min(self.start_x, e.x), min(self.start_y, e.y), abs(self.start_x - e.x), abs(self.start_y - e.y))
        self.callback(selection)
        self.window.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = AppUI(root)
    root.mainloop()