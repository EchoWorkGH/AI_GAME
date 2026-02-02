import os
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
from mss import mss
from PIL import Image, ImageTk
from ultralytics import YOLO


class YOLOApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO 实时区域检测控制台 v2.1")
        self.root.geometry("500x850")

        # --- 初始化 YOLO 模型 ---
        self.model = YOLO("yolov8n.pt")

        self.is_running = False
        self.interval_ms = tk.IntVar(value=100)
        self.region = None
        self.output_folder = "yolo_results"

        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        self.setup_ui()

    def setup_ui(self):
        # 1. 区域管理组 (添加了重新调整的逻辑)
        frame_area = ttk.LabelFrame(self.root, text="区域管理")
        frame_area.pack(pady=10, fill="x", padx=20)

        # 点击此按钮即可重新选择区域
        self.btn_select = ttk.Button(frame_area, text="选择/重选识别区域", command=self.select_area)
        self.btn_select.pack(side="left", padx=10, pady=10, expand=True)

        self.btn_show_area = ttk.Button(frame_area, text="显现当前区域", command=self.flash_area, state="disabled")
        self.btn_show_area.pack(side="left", padx=10, pady=10, expand=True)

        # 2. 预览窗口
        self.preview_frame = tk.Frame(self.root, width=400, height=300, bg="black")
        self.preview_frame.pack_propagate(False)
        self.preview_frame.pack(pady=5)
        self.preview_label = tk.Label(self.preview_frame, text="等待识别...", bg="black", fg="white")
        self.preview_label.pack(expand=True, fill="both")

        # 3. 控制面板
        ctrl_frame = ttk.LabelFrame(self.root, text="设置")
        ctrl_frame.pack(pady=10, padx=20, fill="x")

        tk.Label(ctrl_frame, text="识别间隔 (ms):").grid(row=0, column=0, padx=5, pady=5)
        tk.Scale(ctrl_frame, from_=10, to=1000, orient="horizontal", variable=self.interval_ms).grid(row=0, column=1,
                                                                                                     sticky="ew",
                                                                                                     padx=5)

        # 4. 主按钮
        self.btn_toggle = ttk.Button(self.root, text="开启 AI 识别", command=self.toggle_capture, state="disabled")
        self.btn_toggle.pack(pady=10, fill="x", padx=20)

        # 5. Log 打印区域
        tk.Label(self.root, text="YOLO 识别日志:").pack(anchor="w", padx=20)
        self.log_area = scrolledtext.ScrolledText(self.root, height=10, font=("Consolas", 9), bg="#f0f0f0")
        self.log_area.pack(pady=5, padx=20, fill="both", expand=True)
        self.log_area.config(state="disabled")

    def log(self, message):
        self.root.after(0, self._write_to_log, message)

    def _write_to_log(self, message):
        curr_time = time.strftime("%H:%M:%S", time.localtime())
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, f"[{curr_time}] {message}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state="disabled")

    def flash_area(self):
        if not self.region: return
        flash_win = tk.Toplevel(self.root)
        flash_win.attributes("-alpha", 0.5, "-fullscreen", True, "-topmost", True, "-transparentcolor", "white")
        flash_win.overrideredirect(True)
        canvas = tk.Canvas(flash_win, bg="white", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        x, y, w, h = self.region
        canvas.create_rectangle(x, y, x + w, y + h, outline="red", width=3)
        self.root.after(1500, flash_win.destroy)

    def select_area(self):
        """重新调整区域：如果正在运行则强制停止"""
        if self.is_running:
            self.toggle_capture()  # 停止当前识别
            self.log(">>> 重新调整区域，已自动停止识别")

        self.root.iconify()
        selector_window = tk.Toplevel(self.root)
        AreaSelector(selector_window, self.on_area_selected)

    def on_area_selected(self, selection):
        self.region = selection
        self.root.deiconify()
        if self.region and self.region[2] > 5 and self.region[3] > 5:
            self.btn_show_area.config(state="normal")
            self.btn_toggle.config(state="normal")
            self.log(f"区域已重置为: {self.region}")
        else:
            self.log("选区无效，请重新尝试。")

    def toggle_capture(self):
        if not self.is_running:
            self.is_running = True
            self.btn_toggle.config(text="停止识别")
            self.btn_select.config(state="disabled")  # 识别时禁止改区域
            self.log(">>> AI 识别开始")
            threading.Thread(target=self.yolo_loop, daemon=True).start()
        else:
            self.is_running = False
            self.btn_toggle.config(text="开启 AI 识别")
            self.btn_select.config(state="normal")  # 停止后允许改区域
            self.log(">>> AI 识别停止")

    def yolo_loop(self):
        with mss() as sct:
            monitor = {"left": int(self.region[0]), "top": int(self.region[1]),
                       "width": int(self.region[2]), "height": int(self.region[3])}
            while self.is_running:
                start_time = time.time()
                try:
                    sct_img = sct.grab(monitor)
                    img_original = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    results = self.model.predict(img_original, conf=0.4, verbose=False)

                    # 日志处理
                    names = self.model.names
                    detected = results[0].boxes.cls.cpu().numpy()
                    if len(detected) > 0:
                        counts = {}
                        for c in detected:
                            label = names[int(c)]
                            counts[label] = counts.get(label, 0) + 1
                        self.log(f"检测到: {', '.join([f'{k}x{v}' for k, v in counts.items()])}")

                    # 绘图显示
                    res_plotted = results[0].plot()
                    img_plotted = Image.fromarray(res_plotted[..., ::-1])
                    self.root.after(0, self.update_preview, img_plotted)
                except Exception as e:
                    self.log(f"识别出错: {e}")
                    break

                elapsed = (time.time() - start_time) * 1000
                time.sleep(max(1, self.interval_ms.get() - elapsed) / 1000.0)

    def update_preview(self, pil_img):
        pil_img.thumbnail((400, 300))
        tk_img = ImageTk.PhotoImage(pil_img)
        self.preview_label.config(image=tk_img)
        self.preview_label.image = tk_img


class AreaSelector:
    """透明选区工具"""

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
    app = YOLOApp(root)
    root.mainloop()