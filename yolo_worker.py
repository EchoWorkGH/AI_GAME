import time
import pyautogui
from mss import mss
from PIL import Image
import tkinter as tk
import threading

from ultralytics import YOLO

# 提高响应速度
pyautogui.PAUSE = 0.01
pyautogui.FAILSAFE = True  # 鼠标移动到屏幕四个角可紧急停止


class YOLOClickerWorker:
    def __init__(self, model_path="yolov8n.pt"):
        self.model = YOLO(model_path)
        self.is_running = False
        self.last_click_time = 0
        self.real_click_mode = True  # True: 真实点击, False: 显示指令
        self.marker_window = None

    def set_click_mode(self, real_click=True):
        """设置点击模式"""
        self.real_click_mode = real_click

    def show_click_instruction(self, x, y):
        """在屏幕上显示红圈标记"""
        try:
            # 如果已有标记窗口，先销毁
            if self.marker_window:
                try:
                    self.marker_window.destroy()
                except:
                    pass
                self.marker_window = None

            # 创建标记窗口
            self.marker_window = tk.Toplevel()
            self.marker_window.attributes("-alpha", 0.8, "-topmost", True, "-transparentcolor", "white")
            self.marker_window.overrideredirect(True)
            
            # 设置窗口位置和大小（红圈直径60像素）
            circle_size = 60
            self.marker_window.geometry(f"{circle_size}x{circle_size}+{int(x-circle_size//2)}+{int(y-circle_size//2)}")
            
            # 创建画布并绘制红圈
            canvas = tk.Canvas(self.marker_window, bg="white", highlightthickness=0, width=circle_size, height=circle_size)
            canvas.pack(fill="both", expand=True)
            
            # 绘制红圈（圆心在窗口中心）
            center = circle_size // 2
            radius = circle_size // 2 - 2
            canvas.create_oval(2, 2, circle_size-2, circle_size-2, outline="red", width=3)
            
            # 2秒后自动清除标记
            def clear_marker():
                try:
                    if self.marker_window:
                        self.marker_window.destroy()
                        self.marker_window = None
                except:
                    pass
            
            self.marker_window.after(2000, clear_marker)
            
        except Exception as e:
            print(f"显示标记时出错: {e}")
            # 确保出错时清理窗口
            try:
                if self.marker_window:
                    self.marker_window.destroy()
                    self.marker_window = None
            except:
                pass

    def start_process(self, region, target_class, interval_ms, cooldown, log_callback, preview_callback):
        self.is_running = True
        # 选区左上角坐标 (L, T)
        L, T = int(region[0]), int(region[1])
        monitor = {"left": L, "top": T, "width": int(region[2]), "height": int(region[3])}

        mode_text = "真实点击" if self.real_click_mode else "显示指令"
        log_callback(f"任务启动：模式 [{mode_text}] | 目标 [{target_class}]")

        with mss() as sct:
            while self.is_running:
                loop_start = time.time()
                try:
                    # 1. 抓取选区
                    sct_img = sct.grab(monitor)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

                    # 2. YOLO 推理
                    results = self.model.predict(img, conf=0.5, verbose=False)

                    # 3. 逻辑判定
                    current_time = time.time()
                    for box in results[0].boxes:
                        label = self.model.names[int(box.cls[0])]
                        if label == target_class:
                            # 冷却检查
                            if current_time - self.last_click_time > cooldown:
                                # 计算绝对屏幕坐标
                                coords = box.xyxy[0].cpu().numpy()
                                target_x = L + (coords[0] + coords[2]) / 2
                                target_y = T + (coords[1] + coords[3]) / 2

                                if self.real_click_mode:
                                    # 执行两次点击：1下激活窗口，1下触发功能
                                    pyautogui.click(target_x, target_y, clicks=2, interval=0.05)
                                    log_callback(f"检测到目标，执行双击激活: ({int(target_x)}, {int(target_y)})")
                                else:
                                    # 显示点击指令
                                    self.show_click_instruction(target_x, target_y)
                                    log_callback(f"检测到目标，显示点击指令: ({int(target_x)}, {int(target_y)})")

                                self.last_click_time = current_time

                    # 4. 预览回调
                    res_plotted = results[0].plot()
                    preview_callback(Image.fromarray(res_plotted[..., ::-1]))

                except Exception as e:
                    log_callback(f"Worker异常: {e}")
                    break

                # 频率控制
                elapsed = (time.time() - loop_start) * 1000
                time.sleep(max(1, interval_ms - elapsed) / 1000.0)

    def stop(self):
        self.is_running = False