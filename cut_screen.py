import os
import time
import threading
import tkinter as tk
from tkinter import ttk
from mss import mss
from PIL import Image, ImageTk


class CaptureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python 区域截图控制台")
        self.root.geometry("400x650")
        # 移除全局置顶，避免遮挡选区过程，但在截图时会自动恢复

        self.is_running = False
        self.interval_ms = tk.IntVar(value=500)
        self.max_frames = tk.IntVar(value=0)
        self.current_count = 0
        self.region = None
        self.output_folder = "captured_images"

        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        self.setup_ui()

    def setup_ui(self):
        # 1. 选区按钮
        self.btn_select = ttk.Button(self.root, text="1. 选择屏幕区域", command=self.select_area)
        self.btn_select.pack(pady=10, fill="x", padx=20)

        # 2. 预览窗口
        self.preview_frame = tk.Frame(self.root, width=320, height=240, bg="black")
        self.preview_frame.pack_propagate(False)
        self.preview_frame.pack(pady=10)
        self.preview_label = tk.Label(self.preview_frame, text="暂无预览", bg="black", fg="white")
        self.preview_label.pack(expand=True, fill="both")

        # 3. 控制面板
        ctrl_frame = ttk.LabelFrame(self.root, text="控制选项")
        ctrl_frame.pack(pady=10, padx=20, fill="x")

        tk.Label(ctrl_frame, text="截图间隔 (ms):").grid(row=0, column=0, padx=5, pady=5)
        self.scale = tk.Scale(ctrl_frame, from_=50, to=2000, orient="horizontal", variable=self.interval_ms)
        self.scale.grid(row=0, column=1, sticky="ew", padx=5)

        tk.Label(ctrl_frame, text="最大帧数 (0为不限):").grid(row=1, column=0, padx=5, pady=5)
        self.entry_limit = ttk.Entry(ctrl_frame, textvariable=self.max_frames, width=10)
        self.entry_limit.grid(row=1, column=1, sticky="w", padx=5)

        # 4. 主按钮
        self.btn_toggle = ttk.Button(self.root, text="开始截图", command=self.toggle_capture, state="disabled")
        self.btn_toggle.pack(pady=15, fill="x", padx=20)

        # 5. 状态栏
        self.status_var = tk.StringVar(value="请先选择区域")
        self.status_label = tk.Label(self.root, textvariable=self.status_var, fg="blue")
        self.status_label.pack()

    def select_area(self):
        """采用 Toplevel 替代独立的 Tk 实例，解决主 UI 消失问题"""
        self.root.iconify()  # 最小化主窗口而不是隐藏
        self.selector_window = tk.Toplevel(self.root)
        AreaSelector(self.selector_window, self.on_area_selected)

    def on_area_selected(self, selection):
        """选区完成后的回调函数"""
        self.region = selection
        self.root.deiconify()  # 恢复主窗口
        self.root.attributes("-topmost", True)  # 恢复置顶
        if self.region:
            self.status_var.set(f"已选区域: {self.region}")
            self.btn_toggle.config(state="normal")
        else:
            self.status_var.set("未选择有效区域")

    def toggle_capture(self):
        if not self.is_running:
            self.is_running = True
            self.current_count = 0
            self.btn_toggle.config(text="停止截屏")
            self.btn_select.config(state="disabled")
            threading.Thread(target=self.capture_loop, daemon=True).start()
        else:
            self.stop_capture()

    def stop_capture(self):
        self.is_running = False
        self.btn_toggle.config(text="开始截图")
        self.btn_select.config(state="normal")
        self.status_var.set(f"已停止。总计保存: {self.current_count} 张")

    def capture_loop(self):
        with mss() as sct:
            monitor = {"left": int(self.region[0]), "top": int(self.region[1]),
                       "width": int(self.region[2]), "height": int(self.region[3])}
            while self.is_running:
                limit = self.max_frames.get()
                if 0 < limit <= self.current_count:
                    self.root.after(0, self.stop_capture)
                    break

                start_time = time.time()
                try:
                    sct_img = sct.grab(monitor)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

                    timestamp = int(time.time() * 1000)
                    file_path = os.path.join(self.output_folder, f"cap_{timestamp}.png")
                    img.save(file_path)

                    self.current_count += 1
                    self.root.after(0, self.update_ui_elements, img, self.current_count)
                except Exception as e:
                    print(f"Error: {e}")
                    break

                elapsed = (time.time() - start_time) * 1000
                time.sleep(max(10, self.interval_ms.get() - elapsed) / 1000.0)

    def update_ui_elements(self, pil_img, count):
        pil_img.thumbnail((320, 240))
        tk_img = ImageTk.PhotoImage(pil_img)
        self.preview_label.config(image=tk_img)
        self.preview_label.image = tk_img
        self.status_var.set(f"正在截屏... 已保存: {count} 张")


class AreaSelector:
    """基于 Toplevel 的选区工具"""

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
        self.window.bind("<Escape>", lambda e: self.close())

    def on_press(self, e):
        self.start_x, self.start_y = e.x, e.y
        self.rect = self.canvas.create_rectangle(e.x, e.y, e.x + 1, e.y + 1, outline='red', width=2)

    def on_move(self, e):
        self.canvas.coords(self.rect, self.start_x, self.start_y, e.x, e.y)

    def on_release(self, e):
        selection = (min(self.start_x, e.x), min(self.start_y, e.y),
                     abs(self.start_x - e.x), abs(self.start_y - e.y))
        self.callback(selection)
        self.close()

    def close(self):
        self.window.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = CaptureApp(root)
    root.mainloop()