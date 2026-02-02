import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from PIL import Image, ImageTk
from yolo_worker import YOLOClickerWorker


class AppUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO 物理模拟自动点击器 v4.0")
        self.root.geometry("500x850")

        self.worker = YOLOClickerWorker()
        self.region = None
        self.setup_ui()

    def on_mode_change(self):
        """模式切换回调函数"""
        if self.click_mode_var.get() == "real":
            self.worker.set_click_mode(True)
        else:
            self.worker.set_click_mode(False)

    def setup_ui(self):
        # 1. 区域管理
        area_frame = ttk.LabelFrame(self.root, text="第一步：区域设定")
        area_frame.pack(pady=10, fill="x", padx=20)
        ttk.Button(area_frame, text="框选识别区域", command=self.select_area).pack(side="left", padx=10, pady=10,
                                                                                   expand=True)
        self.btn_show_area = ttk.Button(area_frame, text="显现当前区域", command=self.flash_area, state="disabled")
        self.btn_show_area.pack(side="left", padx=10, pady=10, expand=True)

        # 2. 预览区域 (固定大小)
        preview_container = ttk.LabelFrame(self.root, text="实时预览 (固定画面)")
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

    def write_log(self, msg):
        self.root.after(0, lambda: [self.log_box.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n"),
                                    self.log_box.see(tk.END)])

    def update_preview(self, pil_img):
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

    def toggle_engine(self):
        if not self.worker.is_running:
            self.btn_toggle.config(text="停止运行")
            t = threading.Thread(target=self.worker.start_process, args=(
                self.region, self.target_entry.get(),
                self.interval_scale.get(), 1.0,  # 1.0 为点击冷却(秒)
                self.write_log, self.update_preview
            ), daemon=True)
            t.start()
        else:
            self.worker.stop()
            self.btn_toggle.config(text="开启自动执行 (双击唤醒模式)")


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