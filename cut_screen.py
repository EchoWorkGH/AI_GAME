import os
import time
import threading
import tkinter as tk
from tkinter import ttk
from mss import mss
from PIL import Image, ImageTk
from ultralytics import YOLO  # 导入 YOLO


class YOLOApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO 实时区域检测控制台")
        self.root.geometry("450x700")

        # --- 初始化 YOLO 模型 ---
        # 第一次运行会自动下载 yolov8n.pt (最快的模型)
        self.status_var = tk.StringVar(value="正在加载 YOLO 模型...")
        self.model = YOLO(r"D:\djj\gamecv\runs\detect\train6\weights\best.pt")

        self.is_running = False
        self.interval_ms = tk.IntVar(value=100)  # 识别通常需要更短间隔
        self.region = None
        self.output_folder = "yolo_results"

        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        self.setup_ui()

    def setup_ui(self):
        # 1. 选区按钮
        ttk.Button(self.root, text="1. 选择识别区域", command=self.select_area).pack(pady=10, fill="x", padx=20)

        # 2. 预览窗口 (显示检测后的画面)
        self.preview_frame = tk.Frame(self.root, width=400, height=300, bg="black")
        self.preview_frame.pack_propagate(False)
        self.preview_frame.pack(pady=10)
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
        self.btn_toggle.pack(pady=15, fill="x", padx=20)

        # 5. 状态栏
        tk.Label(self.root, textvariable=self.status_var, fg="green").pack()
        self.status_var.set("模型已就绪，请选择区域")

    def select_area(self):
        self.root.iconify()
        selector_window = tk.Toplevel(self.root)
        AreaSelector(selector_window, self.on_area_selected)

    def on_area_selected(self, selection):
        self.region = selection
        self.root.deiconify()
        if self.region:
            self.status_var.set(f"区域已锁定: {self.region}")
            self.btn_toggle.config(state="normal")

    def toggle_capture(self):
        if not self.is_running:
            self.is_running = True
            self.btn_toggle.config(text="停止识别")
            threading.Thread(target=self.yolo_loop, daemon=True).start()
        else:
            self.is_running = False
            self.btn_toggle.config(text="开启 AI 识别")

    def yolo_loop(self):
        with mss() as sct:
            monitor = {"left": int(self.region[0]), "top": int(self.region[1]),
                       "width": int(self.region[2]), "height": int(self.region[3])}

            while self.is_running:
                start_time = time.time()
                try:
                    # 1. 截屏
                    sct_img = sct.grab(monitor)
                    # YOLO 需要 BGR 或 RGB，我们先转为 PIL 对象
                    img_original = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

                    # 2. YOLO 推理
                    # stream=True 性能更好，conf=0.5 过滤低置信度
                    results = self.model.predict(img_original, conf=0.4, verbose=False)

                    # 3. 绘制检测框
                    # plot() 会返回一个带有渲染结果的 numpy 数组 (BGR 格式)
                    res_plotted = results[0].plot()

                    # 4. 将渲染后的数组转回 PIL 以供 Tkinter 显示
                    # 注意：YOLO plot 返回的是 BGR，需要转 RGB
                    img_plotted = Image.fromarray(res_plotted[..., ::-1])

                    # 5. 更新 UI
                    self.root.after(0, self.update_preview, img_plotted)

                except Exception as e:
                    print(f"推理出错: {e}")
                    break

                elapsed = (time.time() - start_time) * 1000
                time.sleep(max(1, self.interval_ms.get() - elapsed) / 1000.0)

    def update_preview(self, pil_img):
        pil_img.thumbnail((400, 300))
        tk_img = ImageTk.PhotoImage(pil_img)
        self.preview_label.config(image=tk_img)
        self.preview_label.image = tk_img

    # --- 保持 AreaSelector 类不变 ---


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
    app = YOLOApp(root)
    root.mainloop()