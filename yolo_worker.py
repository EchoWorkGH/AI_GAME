import time
import pyautogui
from mss import mss
from PIL import Image
import tkinter as tk

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
        self.instruction_label = None

    def set_click_mode(self, real_click=True):
        """设置点击模式"""
        self.real_click_mode = real_click

    def set_instruction_label(self, label):
        """设置用于显示指令的Label组件"""
        self.instruction_label = label

    def show_click_instruction(self, x, y):
        """在屏幕上显示点击指令"""
        if self.instruction_label:
            instruction_text = f"点击指令: ({int(x)}, {int(y)})"
            self.instruction_label.config(text=instruction_text)
            # 3秒后清除指令显示
            self.instruction_label.after(3000, lambda: self.instruction_label.config(text=""))

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